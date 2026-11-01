"""Execute the generated native graph with simulated iOS I/O, not a second app implementation."""
from dataclasses import dataclass
import base64
import hashlib
import json
from pathlib import Path

from icu import matches, replace


@dataclass
class File:
    name: str
    body: str


class Halt(Exception):
    pass


def stringify(value):
    if value is None:
        return ''
    if isinstance(value, File):
        return value.body
    if isinstance(value, list):
        return '\n'.join(map(stringify, value))
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False, separators=(',', ':'))
    return str(value)


def run(workflow, menus=(), answers=(), disk=None, files=(), network=None, apps=(), incoming=None,
        rewrite_json=False, fail_save=None, corrupt_save=None, unavailable_apps=(), on_read=None,
        native_empty_dict_text=False, native_state_reorder=False, strict_native=True):
    actions = workflow['WFWorkflowActions']
    blocks, stack = {}, []
    for i, action in enumerate(actions):
        p = action['WFWorkflowActionParameters']
        if 'GroupingIdentifier' not in p:
            continue
        mode = p['WFControlFlowMode']
        if mode == 0:
            blocks[i] = {'else': None}
            stack.append(i)
        elif mode == 1:
            blocks[stack[-1]]['else'] = i
        else:
            blocks[stack.pop()]['end'] = i
    assert not stack
    menu_iter, answer_iter, file_iter = iter(menus), iter(answers), iter(files)
    result = {'menus': [], 'alerts': [], 'notifications': [], 'opened': [], 'requests': [], 'reads': [],
              'writes': [], 'exports': [], 'disk': dict(disk or {}), 'variables': {}, 'executed': 0,
              'status': 'done', 'firstMenuActions': None, 'filePickers': 0, 'ignoredLegacyPickers': 0}
    variables, outputs = result['variables'], {}
    depth = 0
    json_reads = 0
    contract = json.loads((Path(__file__).resolve().parents[1] / 'config/native-actions.json').read_text())
    known_ids = set(contract['identifiers'])

    def as_text(value):
        nonlocal json_reads
        if native_empty_dict_text and isinstance(value, dict) and not value:
            return ''
        if native_state_reorder and isinstance(value, File):
            try:
                data = json.loads(value.body)
            except ValueError:
                pass
            else:
                if isinstance(data, dict) and data.get('product') == 'applist-pro':
                    return json.dumps(data, ensure_ascii=False, sort_keys=True, indent=2)
        if rewrite_json and isinstance(value, File) and value.name.endswith('.json'):
            try:
                data = json.loads(value.body)
            except ValueError:
                return value.body
            json_reads += 1
            return json.dumps(data, ensure_ascii=json_reads % 2 == 0,
                              sort_keys=json_reads % 2 == 0, indent=2 if json_reads % 2 else 4)
        return stringify(value)

    def evaluate(value):
        if not isinstance(value, dict):
            return value
        serial = value.get('WFSerializationType')
        if serial in ('WFTextTokenAttachment', 'WFDictionaryFieldValue', 'WFArrayParameterState'):
            return evaluate(value['Value'])
        if serial == 'WFTextTokenString':
            text = value['Value']['string'].encode('utf-16-le')
            edits = []
            for span, item in value['Value'].get('attachmentsByRange', {}).items():
                start, count = map(int, span.strip('{}').split(','))
                edits.append((start, count, as_text(evaluate(item))))
            for start, count, replacement in sorted(edits, reverse=True):
                assert text[start*2:(start+count)*2] == b'\xfc\xff'
                text = text[:start*2] + replacement.encode('utf-16-le') + text[(start+count)*2:]
            return text.decode('utf-16-le')
        if 'WFDictionaryFieldValueItems' in value:
            return {stringify(evaluate(x['WFKey'])): evaluate(x['WFValue']) for x in value['WFDictionaryFieldValueItems']}
        if value.get('Type') == 'Variable' and 'Variable' in value:
            return evaluate(value['Variable'])
        kind = value.get('Type')
        if kind == 'Variable':
            assert value['VariableName'] in variables, ('unassigned variable', value)
            answer = variables[value['VariableName']]
        elif kind == 'ActionOutput':
            assert value['OutputUUID'] in outputs, ('unexecuted action', value)
            answer = outputs[value['OutputUUID']]
        elif kind == 'ExtensionInput':
            answer = incoming
        else:
            return value
        for transform in value.get('Aggrandizements', []):
            typ = transform['Type']
            if typ == 'WFDictionaryValueVariableAggrandizement':
                answer = answer.get(transform['DictionaryKey'])
            elif typ == 'WFCoercionVariableAggrandizement':
                if transform['CoercionItemClass'] == 'WFStringContentItem':
                    answer = as_text(answer)
                elif transform['CoercionItemClass'] == 'WFNumberContentItem':
                    answer = float(as_text(answer))
                else:
                    raise AssertionError(transform)
            else:
                raise AssertionError(transform)
        return answer

    def seq(value):
        return [] if value is None else value if isinstance(value, list) else [value]

    def execute(first, last):
        nonlocal depth
        i = first
        while i < last:
            result['executed'] += 1
            assert result['executed'] < 150000, 'Runaway flow'
            a = actions[i]
            p = a['WFWorkflowActionParameters']
            kind = a['WFWorkflowActionIdentifier'].removeprefix('is.workflow.actions.')
            if strict_native and a['WFWorkflowActionIdentifier'] not in known_ids:
                result['status'] = 'unknown-action'
                result['nativeErrorAction'] = a['WFWorkflowActionIdentifier']
                raise Halt()
            if i in blocks:
                block = blocks[i]
                if kind == 'conditional':
                    condition, lhs = p['WFCondition'], evaluate(p['WFInput'])
                    if condition == 4:
                        yes = stringify(lhs) == stringify(evaluate(p['WFConditionalActionString']))
                    elif condition == 99:
                        rhs = stringify(evaluate(p['WFConditionalActionString']))
                        assert isinstance(lhs, list), 'Only exact array membership is used'
                        if strict_native:
                            result['status'] = 'missing-native-parameter'
                            result['nativeErrorAction'] = 'Array Contains (beta2 iOS template)'
                            raise Halt()
                        yes = rhs in lhs
                    elif condition == 100:
                        # A Text item can exist while its characters are empty.
                        # The device video exposed this distinction in beta1.
                        yes = lhs is not None and lhs != [] and lhs != {}
                    elif condition == 2:
                        yes = float(stringify(lhs)) > float(stringify(evaluate(p['WFNumberValue'])))
                    else:
                        raise AssertionError(condition)
                    middle = block['else'] if block['else'] is not None else block['end']
                    if yes:
                        execute(i+1, middle)
                    elif block['else'] is not None:
                        execute(middle+1, block['end'])
                else:
                    depth += 1
                    index_name = 'Repeat Index' + (' ' + str(depth) if depth > 1 else '')
                    values = seq(evaluate(p['WFInput'])) if kind == 'repeat.each' else range(int(stringify(evaluate(p['WFRepeatCount']))))
                    for index, _ in enumerate(values, 1):
                        variables[index_name] = index
                        execute(i+1, block['end'])
                    depth -= 1
                i = block['end'] + 1
                continue
            answer = None
            if kind == 'dictionary':
                answer = evaluate(p['WFItems'])
            elif kind == 'list':
                answer = [evaluate(item.get('WFValue', item)) for item in p['WFItems']]
            elif kind == 'gettext':
                answer = as_text(evaluate(p['WFTextActionText']))
            elif kind == 'setvariable':
                variables[p['WFVariableName']] = evaluate(p['WFInput'])
            elif kind == 'appendvariable':
                variables[p['WFVariableName']] = seq(variables.get(p['WFVariableName'])) + [evaluate(p['WFInput'])]
            elif kind == 'getvalueforkey':
                obj = evaluate(p['WFInput'])
                assert isinstance(obj, dict), (kind, type(obj), obj)
                typ = p.get('WFGetDictionaryValueType', 'Value')
                answer = list(obj) if typ == 'All Keys' else list(obj.values()) if typ == 'All Values' else obj.get(stringify(evaluate(p['WFDictionaryKey'])))
            elif kind == 'setvalueforkey':
                answer = dict(evaluate(p['WFDictionary']))
                answer[stringify(evaluate(p['WFDictionaryKey']))] = evaluate(p['WFDictionaryValue'])
            elif kind == 'count':
                value = evaluate(p['Input'])
                answer = len(stringify(value)) if p['WFCountType'] == 'Characters' else len(seq(value))
            elif kind == 'text.match':
                answer = matches(stringify(evaluate(p['WFMatchTextPattern'])), stringify(evaluate(p['text'])))
            elif kind == 'text.replace':
                source = stringify(evaluate(p['WFInput']))
                pattern = stringify(evaluate(p['WFReplaceTextFind']))
                target = stringify(evaluate(p['WFReplaceTextReplace']))
                answer = replace(pattern, source, target) if p['WFReplaceTextRegularExpression'] else source.replace(pattern, target)
            elif kind == 'text.split':
                assert p['WFTextSeparator'] == 'New Lines'
                answer = stringify(evaluate(p['text'])).split('\n')
            elif kind == 'text.combine':
                assert p['WFTextSeparator'] == 'New Lines'
                answer = '\n'.join(map(stringify, seq(evaluate(p['text']))))
            elif kind == 'hash':
                answer = hashlib.sha256(stringify(evaluate(p['WFInput'])).encode()).hexdigest()
            elif kind == 'detect.dictionary':
                answer = json.loads(as_text(evaluate(p['WFInput'])))
            elif kind == 'detect.text':
                answer = as_text(evaluate(p['WFInput']))
            elif kind == 'base64encode':
                value = stringify(evaluate(p['WFInput']))
                if p['WFEncodeMode'] == 'Encode':
                    assert p['WFBase64LineBreakMode'] == 'None'
                    answer = base64.b64encode(value.encode()).decode()
                else:
                    answer = File('decoded', base64.b64decode(value, validate=True).decode())
            elif kind == 'file':
                assert p['WFFile']['fileLocation']['WFFileLocationType'] == 'Shortcuts'
                answer = 'Shortcuts'
            elif kind == 'file.createfolder':
                assert evaluate(p['WFFolder']) == 'Shortcuts' and p['WFFilePath'] == 'AppListPro'
                answer = 'AppListPro'
            elif kind == 'documentpicker.open':
                if p.get('WFShowFilePicker'):
                    # iOS 15+ split Select File into its own action. This old
                    # flag on Get File is not an interactive picker anymore.
                    result['ignoredLegacyPickers'] += 1
                    answer = None
                else:
                    path = stringify(evaluate(p['WFGetFilePath']))
                    result['reads'].append(path)
                    if on_read:
                        on_read(path, result)
                    answer = result['disk'].get(path)
            elif kind == 'file.select':
                assert p.get('SelectMultiple', False) is False
                assert 'WFShowFilePicker' not in p and 'WFSelectMultiple' not in p
                result['filePickers'] += 1
                answer = next(file_iter)
                if answer is None:
                    result['status'] = 'cancelled'
                    raise Halt()
            elif kind == 'setitemname':
                answer = File(p['WFName'], as_text(evaluate(p['WFInput'])))
            elif kind == 'documentpicker.save':
                file = evaluate(p['WFInput'])
                if isinstance(file, dict):
                    # Native Save File accepts a Dictionary and serializes it
                    # as JSON, as the original device-tested shortcut does.
                    file = File('Dictionary.json', json.dumps(file, ensure_ascii=False))
                elif not isinstance(file, File):
                    file = File('Text.txt', as_text(file))
                if p['WFAskWhereToSave']:
                    result['exports'].append(file)
                else:
                    path = stringify(evaluate(p['WFFileDestinationPath']))
                    assert path.startswith('AppListPro/') and '..' not in path
                    if fail_save == path:
                        result['status'] = 'io-error'
                        raise Halt()
                    if rewrite_json:
                        try:
                            data = json.loads(file.body)
                        except ValueError:
                            pass
                        else:
                            file = File(file.name, json.dumps(data, ensure_ascii=False, sort_keys=True, indent=2))
                    if callable(corrupt_save):
                        file = corrupt_save(path, file)
                    elif corrupt_save == path:
                        data = json.loads(file.body)
                        data['namesJSON'] = '{truncated'
                        file = File(file.name, json.dumps(data))
                    result['disk'][path] = file
                    result['writes'].append(path)
                    answer = file
            elif kind == 'choosefromlist':
                options = seq(evaluate(p['WFInput']))
                if result['firstMenuActions'] is None:
                    result['firstMenuActions'] = result['executed']
                choice = next(menu_iter, None)
                if choice is None:
                    result['status'] = 'cancelled'
                    raise Halt()
                if isinstance(choice, int):
                    answer = options[choice]
                else:
                    matches_choice = []
                    for option in options:
                        s = stringify(option)
                        row_id = variables.get('RowMap', {}).get(hashlib.sha256(s.encode()).hexdigest())
                        fixed_id = variables.get('FixedMenuMap', {}).get(s)
                        if choice in (s, row_id, fixed_id):
                            matches_choice.append(option)
                    assert len(matches_choice) == 1, (choice, options, variables.get('FixedMenuMap'))
                    answer = matches_choice[0]
                result['menus'].append({'options': list(map(stringify, options)), 'choice': choice,
                                       'prompt': stringify(evaluate(p['WFChooseFromListActionPrompt']))})
            elif kind == 'getitemfromlist':
                items = seq(evaluate(p['WFInput']))
                index = 0 if p['WFItemSpecifier'] == 'First Item' else int(stringify(evaluate(p['WFItemIndex'])))-1
                assert 0 <= index < len(items), (index, items)
                answer = items[index]
            elif kind == 'filter.files':
                answer = sorted(seq(evaluate(p['WFContentItemInputParameter'])), key=stringify)
            elif kind == 'ask':
                answer = next(answer_iter)
                if answer is None:
                    result['status'] = 'cancelled'
                    raise Halt()
            elif kind == 'searchappstore':
                result['requests'].append('native-app-store-search:' + stringify(evaluate(p['WFSearchTerm'])))
                answer = list(apps)
            elif kind == 'properties.appstore':
                app = evaluate(p['WFInput'])
                answer = app[{'Name': 'name', 'Bundle Identifier': 'bundle', 'Store URL': 'url'}[p['WFContentItemPropertyName']]]
            elif kind == 'downloadurl':
                assert p['WFHTTPMethod'] == 'GET'
                assert not any(key in p for key in ('WFHTTPBody', 'WFFormValues', 'WFJSONValues'))
                url = stringify(evaluate(p['WFURL']))
                assert url.startswith(('https://raw.githubusercontent.com/dammeiosvn/Clipboard-Pro-Data/main/applist-pro/', 'https://itunes.apple.com/lookup?id='))
                result['requests'].append(url)
                if network is None or url not in network or network[url] is None:
                    result['status'] = 'network-error'
                    raise Halt()
                answer = network[url]
            elif kind in ('detect.link', 'detect.urls'):
                answer = seq(evaluate(p['WFInput']))
            elif kind in ('openapp', 'openurl'):
                value = stringify(evaluate(p['WFSelectedApp'] if kind == 'openapp' else p['WFInput']))
                if value in unavailable_apps:
                    result['status'] = 'app-error'
                    raise Halt()
                result['opened'].append(value)
            elif kind == 'alert':
                assert stringify(evaluate(p['WFAlertActionTitle'])) == 'AppList Pro · © Sentechtipsvn'
                result['alerts'].append(stringify(evaluate(p['WFAlertActionMessage'])))
            elif kind == 'notification':
                result['notifications'].append(stringify(evaluate(p['WFNotificationActionBody'])))
            elif kind == 'exit':
                raise Halt()
            else:
                raise AssertionError(kind)
            outputs[p['UUID']] = answer
            i += 1
    try:
        execute(0, len(actions))
    except Halt:
        pass
    return result
