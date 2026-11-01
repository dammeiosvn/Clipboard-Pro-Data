"""Small deterministic emitter for Apple Shortcuts plist, not a runtime dependency."""
import json
import uuid
import hashlib
import re
import unicodedata

NS = uuid.UUID('adb69ec2-fd95-4b85-957f-9229c1c424e2')


def variable(name):
    return {'Type': 'Variable', 'VariableName': name}


def ref(value, coercion=None):
    value = dict(value)
    if coercion:
        value['Aggrandizements'] = value.get('Aggrandizements', []) + [
            {'Type': 'WFCoercionVariableAggrandizement', 'CoercionItemClass': coercion}]
    return {'Value': value, 'WFSerializationType': 'WFTextTokenAttachment'}


def token(*parts):
    text, spans = '', {}
    for part in parts:
        if isinstance(part, dict):
            # Apple's ranges are UTF-16 offsets. Emoji are often two UTF-16 units.
            spans['{%d, 1}' % (len(text.encode('utf-16-le')) // 2)] = part
            text += '\ufffc'
        else:
            text += str(part)
    return {'Value': {'string': text, 'attachmentsByRange': spans},
            'WFSerializationType': 'WFTextTokenString'}


def dictionary_value(items):
    fields = []
    for key, value in items.items():
        if isinstance(value, dict) and value.get('Type') not in ('Variable', 'ActionOutput'):
            kind, field = 1, dictionary_value(value)
        elif isinstance(value, list):
            assert all(isinstance(x, str) for x in value)
            kind, field = 2, {'Value': value, 'WFSerializationType': 'WFArrayParameterState'}
        else:
            kind, field = 0, token(value)
        fields.append({'WFItemType': kind, 'WFKey': token(key), 'WFValue': field})
    return {'Value': {'WFDictionaryFieldValueItems': fields},
            'WFSerializationType': 'WFDictionaryFieldValue'}


def string_parameter(*parts):
    """Use native scalar storage for literals; tokens only for substitutions."""
    return token(*parts) if any(isinstance(p, dict) for p in parts) else ''.join(map(str, parts))


class Workflow:
    def __init__(self, name):
        self.name = name
        self.actions = []
        self.loops = []
        self.constant_variable = None
        self.empty_variable = None
        self.constants = {}
        self.constant_keys = {}

    def enable_constants(self, variable_name, empty_variable):
        self.constant_variable = variable_name
        self.empty_variable = empty_variable

    def literal(self, value):
        value = str(value)
        if value == '':
            return variable(self.empty_variable)
        if value not in self.constant_keys:
            known = {'0': 'zero', '1': 'one', '20': 'defaultInteractionLimit'}
            slug = re.sub(r'[^A-Za-z0-9]+', '_', unicodedata.normalize('NFKD', value)).strip('_')[:36]
            key = known.get(value) or (slug + '_' + hashlib.sha256(value.encode()).hexdigest()[:8])
            self.constant_keys[value] = key
            self.constants[key] = value
        return {'Type': 'Variable', 'VariableName': self.constant_variable, 'Aggrandizements': [
            {'Type': 'WFDictionaryValueVariableAggrandizement', 'DictionaryKey': self.constant_keys[value]}]}

    def uid(self, kind):
        # Workflow-local references need uniqueness, not random entropy. A
        # stable prefix and counter compress well in the signed archive.
        prefix = str(uuid.uuid5(NS, self.name))[:8]
        tag = hashlib.sha256(kind.encode()).hexdigest()[:4]
        return f'{prefix}-0000-5000-8000-{len(self.actions):08x}{tag}'.upper()

    def action(self, kind, params=None, name=None):
        identifier = kind if '.' in kind and kind.startswith('com.') else 'is.workflow.actions.' + kind
        p = dict(params or {})
        p['UUID'] = self.uid(kind)
        if name:
            p['CustomOutputName'] = name
        self.actions.append({'WFWorkflowActionIdentifier': identifier, 'WFWorkflowActionParameters': p})
        return {'Type': 'ActionOutput', 'OutputUUID': p['UUID'], 'OutputName': name or kind}

    def text(self, *parts, name='Text'):
        if self.constant_variable:
            if all(not isinstance(p, dict) for p in parts):
                return self.literal(''.join(map(str, parts)))
            # Keep dynamic coercion/composition at its execution point. Static
            # JSON fragments, diagnostics and regex fragments live in the one
            # top Dictionary; whitespace remains visible for readable layout.
            parts = tuple(self.literal(p) if not isinstance(p, dict) and str(p).strip() else p for p in parts)
        return self.action('gettext', {'WFTextActionText': token(*parts)}, name)

    def set(self, name, value):
        self.action('setvariable', {'WFInput': ref(value), 'WFVariableName': name})
        return variable(name)

    def assign(self, name, *parts):
        return self.set(name, self.text(*parts, name=name))

    def get(self, source, *key, name='Dictionary value'):
        # Walk nested dictionaries explicitly. Each action has one literal or
        # dynamic key, with no dependency on dotted-path coercion at import.
        segments = [[]]
        for part in key:
            if isinstance(part, dict):
                segments[-1].append(part)
            else:
                for i, piece in enumerate(str(part).split('.')):
                    if i:
                        segments.append([])
                    if piece:
                        segments[-1].append(piece)
        for segment in segments:
            assert segment, ('Empty dictionary path segment', key)
            source = self.action('getvalueforkey', {'WFInput': ref(source),
                'WFGetDictionaryValueType': 'Value', 'WFDictionaryKey': string_parameter(*segment)}, name)
        return source

    def keys(self, source):
        return self.action('getvalueforkey', {'WFInput': ref(source), 'WFGetDictionaryValueType': 'All Keys'}, 'Keys')

    def put(self, source, key, value):
        return self.action('setvalueforkey', {'WFDictionary': ref(source),
            'WFDictionaryKey': token(key), 'WFDictionaryValue': token(value)}, 'Updated dictionary')

    def empty_dict(self, name):
        return self.set(name, self.action('dictionary', {'WFItems': dictionary_value({})}, name))

    def empty_list(self, name):
        return self.set(name, self.action('list', {'WFItems': []}, name))

    def append(self, name, value):
        self.action('appendvariable', {'WFVariableName': name, 'WFInput': ref(value)})

    def count(self, value, kind='Items'):
        return self.action('count', {'Input': ref(value), 'WFCountType': kind}, 'Count ' + kind)

    def match(self, value, *pattern):
        return self.action('text.match', {'text': token(value),
            'WFMatchTextPattern': token(*pattern), 'WFMatchTextCaseSensitive': True}, 'Matches')

    def replace(self, value, pattern, replacement='', regex=True):
        return self.action('text.replace', {'WFInput': token(value),
            'WFReplaceTextFind': token(pattern), 'WFReplaceTextReplace': token(replacement),
            'WFReplaceTextRegularExpression': regex, 'WFReplaceTextCaseSensitive': True}, 'Normalized text')

    def if_eq(self, value, *other):
        # Materialize Text before If: don't let a Dictionary Value's inferred type
        # change the condition editor/runtime comparison after importing on iOS.
        value = self.text(value, name='Condition text')
        g = self.uid('if')
        self.action('conditional', {'WFInput': {'Type': 'Variable', 'Variable': ref(value, 'WFStringContentItem')},
            'WFCondition': 4, 'WFConditionalActionString': string_parameter(*other),
            'GroupingIdentifier': g, 'WFControlFlowMode': 0})
        return g

    def if_gt(self, value, n=0):
        g = self.uid('if')
        self.action('conditional', {'WFInput': {'Type': 'Variable', 'Variable': ref(value, 'WFNumberContentItem')},
            'WFCondition': 2, 'WFNumberValue': ref(n) if isinstance(n, dict) else n,
            'GroupingIdentifier': g, 'WFControlFlowMode': 0})
        return g

    def if_has(self, value):
        g = self.uid('if')
        self.action('conditional', {'WFInput': {'Type': 'Variable', 'Variable': ref(value)},
            'WFCondition': 100, 'GroupingIdentifier': g, 'WFControlFlowMode': 0})
        return g

    def if_match(self, value, *pattern):
        return self.if_gt(self.count(self.match(value, *pattern)))

    def otherwise(self, g):
        self.action('conditional', {'GroupingIdentifier': g, 'WFControlFlowMode': 1})

    def end_if(self, g):
        self.action('conditional', {'GroupingIdentifier': g, 'WFControlFlowMode': 2})

    def each(self, values):
        # Repeat Item's display name is fragile in mixed/nested repeat scopes.
        # Snapshot the list, then address its current element by the native
        # Repeat Index (whose suffix includes ALL enclosing repeat scopes).
        list_name = 'LoopItems_' + str(len(self.actions))
        self.set(list_name, values)
        g = self.uid('repeat')
        self.action('repeat.each', {'WFInput': ref(variable(list_name)), 'GroupingIdentifier': g, 'WFControlFlowMode': 0})
        self.loops.append(('repeat.each', g))
        n = len(self.loops)
        index = variable('Repeat Index' + (' ' + str(n) if n > 1 else ''))
        item = self.action('getitemfromlist', {'WFInput': ref(variable(list_name)),
            'WFItemSpecifier': 'Item At Index', 'WFItemIndex': token(index)}, 'Current loop item')
        return g, item

    def times(self, n):
        g = self.uid('repeat')
        # Repeat Count is a substitutable numeric field, not a content-input
        # field. Dynamic values use a text token, as in Cherri's makeRepeatAction.
        self.action('repeat.count', {'WFRepeatCount': token(n) if isinstance(n, dict) else n,
            'GroupingIdentifier': g, 'WFControlFlowMode': 0})
        self.loops.append(('repeat.count', g))
        return g

    def end_loop(self, g):
        kind, identifier = self.loops.pop()
        assert identifier == g
        self.action(kind, {'GroupingIdentifier': g, 'WFControlFlowMode': 2})

    def first(self, values):
        return self.action('getitemfromlist', {'WFInput': ref(values), 'WFItemSpecifier': 'First Item'}, 'First item')

    def choose(self, values, prompt):
        return self.action('choosefromlist', {'WFInput': ref(values),
            'WFChooseFromListActionPrompt': token(prompt), 'WFChooseFromListActionSelectMultiple': False,
            'WFChooseFromListActionSelectAll': False}, 'Selected menu row')

    def hash(self, value):
        return self.action('hash', {'WFInput': ref(value), 'WFHashType': 'SHA256'}, 'Row key')

    def label(self, key):
        return {'Type': 'Variable', 'VariableName': 'Strings', 'Aggrandizements': [
            {'Type': 'WFDictionaryValueVariableAggrandizement', 'DictionaryKey': key}]}

    def alert(self, message, stop=False, title=None):
        self.action('alert', {'WFAlertActionTitle': token(title) if title is not None else 'AppList Pro',
            'WFAlertActionMessage': token(message), 'WFAlertActionCancelButtonShown': False})
        if stop:
            self.action('exit')

    def notify(self, key):
        self.action('notification', {'WFNotificationActionTitle': '',
            'WFNotificationActionBody': token(self.label(key)), 'WFNotificationActionSound': False})

    def named_json(self, value, filename):
        return self.action('setitemname', {'WFInput': ref(value, 'WFStringContentItem'),
            'WFName': filename, 'WFDontIncludeFileExtension': False}, filename)

    def header(self):
        assert not self.loops
        return {'WFWorkflowName': self.name, 'WFWorkflowActions': self.actions,
            'WFWorkflowClientVersion': '3036.0.4.2', 'WFWorkflowMinimumClientVersion': 900,
            'WFWorkflowMinimumClientVersionString': '900',
            'WFWorkflowIcon': {'WFWorkflowIconStartColor': 4292093695, 'WFWorkflowIconGlyphNumber': 59509},
            'WFWorkflowImportQuestions': [], 'WFWorkflowInputContentItemClasses': ['WFURLContentItem'],
            'WFWorkflowOutputContentItemClasses': [], 'WFWorkflowTypes': ['ActionExtension'],
            'WFQuickActionSurfaces': [], 'WFWorkflowHasShortcutInputVariables': True,
            'WFWorkflowNoInputBehavior': {}}
