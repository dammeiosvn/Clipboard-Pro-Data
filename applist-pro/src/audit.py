"""Structural audit and signed-to-source action graph comparison."""
from pathlib import Path
import hashlib
import json
import plistlib
import re
import sys
import uuid

ROOT = Path(__file__).resolve().parents[1]
SIGNED = ROOT / 'dist/AppList-Pro-1.1-beta5.shortcut'


def walk(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk(child)


def audit(signed=False):
    raw = (ROOT / 'dist/AppList-Pro.unsigned.bplist').read_bytes()
    workflow = plistlib.loads(raw)
    assert workflow == plistlib.loads((ROOT / 'dist/AppList-Pro.unsigned.shortcut').read_bytes())
    seen, stack, prior_actions = set(), [], {}
    spans = 0
    for index, action in enumerate(workflow['WFWorkflowActions']):
        kind, p = action['WFWorkflowActionIdentifier'], action['WFWorkflowActionParameters']
        uuid.UUID(p['UUID'])
        assert p['UUID'] not in seen
        for node in walk(p):
            if node.get('Type') == 'ActionOutput':
                assert node['OutputUUID'] in seen, (index, node)
            if node.get('WFSerializationType') == 'WFTextTokenString':
                value = node['Value']
                raw_text = value['string'].encode('utf-16-le')
                for span in value['attachmentsByRange']:
                    match = re.fullmatch(r'\{(\d+), 1\}', span)
                    assert match
                    start = int(match[1]) * 2
                    assert raw_text[start:start+2] == b'\xfc\xff', (index, span)
                    spans += 1
        if 'GroupingIdentifier' in p:
            group, mode = p['GroupingIdentifier'], p['WFControlFlowMode']
            if mode == 0:
                stack.append((group, kind, False))
            elif mode == 1:
                assert stack[-1][:2] == (group, kind) and not stack[-1][2]
                stack[-1] = (group, kind, True)
            else:
                assert mode == 2 and stack.pop()[:2] == (group, kind)
        seen.add(p['UUID'])
        prior_actions[p['UUID']] = action
    assert not stack
    identifiers = [a['WFWorkflowActionIdentifier'] for a in workflow['WFWorkflowActions']]
    contract = json.loads((ROOT / 'config/native-actions.json').read_text())
    unknown = set(identifiers) - set(contract['identifiers'])
    assert not unknown, ('Unknown native action identifiers', unknown)
    assert 'is.workflow.actions.runworkflow' not in identifiers
    assert 'is.workflow.actions.makepdf' not in identifiers
    assert 'is.workflow.actions.showwebpage' not in identifiers
    assert 'is.workflow.actions.getrichtextfromhtml' not in identifiers
    assert workflow['WFWorkflowInputContentItemClasses'] == ['WFURLContentItem']
    for a in workflow['WFWorkflowActions']:
        p = a['WFWorkflowActionParameters']
        # Beta1's device failures: no item-existence checks for empty text,
        # and no obsolete picker flag on the modern Get File action.
        if a['WFWorkflowActionIdentifier'] == 'is.workflow.actions.conditional':
            assert p.get('WFCondition') not in (99, 100)
            if p.get('WFControlFlowMode') == 0:
                if p['WFCondition'] == 4:
                    assert p.get('WFConditionalActionString') is not None
                    rhs = p['WFConditionalActionString']
                    if isinstance(rhs, dict):
                        for node in walk(rhs):
                            if node.get('Type') == 'ActionOutput':
                                origin = prior_actions[node['OutputUUID']]
                                assert origin['WFWorkflowActionIdentifier'] == 'is.workflow.actions.gettext', 'Dynamic equality RHS must be materialized as Text'
                elif p['WFCondition'] == 2:
                    assert p.get('WFNumberValue') is not None
                else:
                    raise AssertionError(('Unreviewed native predicate', p))
        if a['WFWorkflowActionIdentifier'] == 'is.workflow.actions.documentpicker.open':
            assert not p.get('WFShowFilePicker')
            assert p.get('WFGetFilePath')
        if a['WFWorkflowActionIdentifier'] == 'is.workflow.actions.file.select':
            assert p.get('SelectMultiple') is False
            assert 'WFShowFilePicker' not in p
        if a['WFWorkflowActionIdentifier'] == 'is.workflow.actions.downloadurl':
            assert p['WFHTTPMethod'] == 'GET'
            assert not any(k in p for k in ('WFHTTPBody', 'WFFormValues', 'WFJSONValues'))
        if a['WFWorkflowActionIdentifier'] == 'is.workflow.actions.text.combine':
            assert p.get('text') and p.get('WFTextSeparator') == 'New Lines'
    report = {'balancedControlFlow': True, 'uniqueActionUUIDs': True,
              'validUTF16TokenSpans': spans, 'actionReferencesVerified': True,
              'actions': len(identifiers), 'binaryBytes': len(raw),
              'nativeIdentifiersChecked': len(set(identifiers)),
              'unsupportedArrayContainsRemoved': True,
              'dynamicComparisonOperandsMaterialized': True,
              'stateEnvelopeBase64Removed': 'is.workflow.actions.base64encode' not in identifiers,
              'signedActionGraphEqual': None, 'nativeDeviceVerified': False}
    if signed:
        import lzfse
        archive = SIGNED.read_bytes()
        assert archive.startswith(b'AEA1')
        payload = lzfse.decompress(archive[archive.find(b'bvx2'):])
        position = payload.find(b'bplist00')
        assert position >= 4
        length = int.from_bytes(payload[position-4:position], 'little')
        actual = plistlib.loads(payload[position:position+length])
        assert actual['WFWorkflowActions'] == workflow['WFWorkflowActions']
        assert actual['WFWorkflowInputContentItemClasses'] == workflow['WFWorkflowInputContentItemClasses']
        report.update(signedActionGraphEqual=True, signedBytes=len(archive),
                      signedSHA256=hashlib.sha256(archive).hexdigest())
    (ROOT / 'qa/structural-audit.json').write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    print(json.dumps(audit('--signed' in sys.argv)))
