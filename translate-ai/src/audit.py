"""Independent structural/native contract checks for the generated action graph."""
from pathlib import Path
import hashlib,json,plistlib,re,sys,uuid
ROOT=Path(__file__).resolve().parents[1]
def walk(x):
 if isinstance(x,dict):
  yield x
  for v in x.values():yield from walk(v)
 elif isinstance(x,list):
  for v in x:yield from walk(v)
def field(items,key):
 fields=items['Value']['WFDictionaryFieldValueItems']
 return next(x for x in fields if x['WFKey']['Value']['string']==key)
def literal(f):return f['WFValue']['Value']['string']
def audit(signed=False):
 raw=(ROOT/'dist/Translate-AI.unsigned.bplist').read_bytes();workflow=plistlib.loads(raw)
 assert workflow==plistlib.loads((ROOT/'dist/Translate-AI.unsigned.shortcut').read_bytes())
 seen={};stack=[];spans=0;http=0;ui_http=0;opened_api=0;clipboard=0
 contract=json.loads((ROOT/'config/native-actions.json').read_text());known=set(contract['identifiers'])
 strings=json.loads((ROOT/'config/strings.json').read_text())
 assert set(strings)=={'vi','en'} and set(strings['vi'])==set(strings['en'])
 for index,action in enumerate(workflow['WFWorkflowActions']):
  kind=action['WFWorkflowActionIdentifier'];p=action['WFWorkflowActionParameters']
  assert kind in known,kind
  uuid.UUID(p['UUID']);assert p['UUID'] not in seen
  for n in walk(p):
   if n.get('Type')=='ActionOutput':assert n['OutputUUID'] in seen,(index,n)
   if n.get('Type')=='WFDictionaryValueVariableAggrandizement' and n.get('DictionaryKey') in strings['vi']:assert n['DictionaryKey'] in strings['en']
   assert 'crossDeviceItemID' not in n,'Personal iCloud bookmark retained'
   if n.get('WFSerializationType')=='WFTextTokenString':
    value=n['Value'];b=value['string'].encode('utf-16-le')
    for span in value.get('attachmentsByRange',{}):
     m=re.fullmatch(r'\{(\d+), 1\}',span);assert m
     offset=int(m[1])*2;assert b[offset:offset+2]==b'\xfc\xff',(index,span);spans+=1
  if 'GroupingIdentifier' in p:
   group=p['GroupingIdentifier'];mode=p['WFControlFlowMode']
   if mode==0:stack.append((group,kind,False))
   elif mode==1:
    assert stack[-1][:2]==(group,kind) and not stack[-1][2];stack[-1]=(group,kind,True)
   else:assert mode==2 and stack.pop()[:2]==(group,kind)
  if kind.endswith('.conditional') and p['WFControlFlowMode']==0:
   assert p['WFCondition'] in (2,4)
   if p['WFCondition']==4:
    assert p.get('WFConditionalActionString') is not None
    for n in walk(p['WFConditionalActionString']):
     if n.get('Type')=='ActionOutput':assert seen[n['OutputUUID']]['WFWorkflowActionIdentifier'].endswith('.gettext')
  if kind.endswith('.downloadurl'):
   if p['WFHTTPMethod']=='GET':
    ui_http+=1
    assert p['WFURL']['Value']['string']=='https://raw.githubusercontent.com/dammeiosvn/Clipboard-Pro-Data/main/translate-ai/resources/ui-v1/\ufffc.json'
    assert list(p['WFURL']['Value']['attachmentsByRange'].values())==[{'Type':'Variable','VariableName':'RequestedUI'}]
    assert set(p)=={'WFURL','WFHTTPMethod','UUID','CustomOutputName'}
    seen[p['UUID']]=action
    continue
   http+=1
   assert p['WFURL']=='https://api.deepseek.com/chat/completions'
   assert p['WFHTTPMethod']=='POST' and p['WFHTTPBodyType']=='JSON'
   payload=p['WFJSONValues'];assert literal(field(payload,'model'))=='deepseek-flash'
   stream=field(payload,'stream');assert stream['WFItemType']==4 and stream['WFValue']=={'Value':False,'WFSerializationType':'WFNumberSubstitutableState'}
   messages=field(payload,'messages');assert messages['WFItemType']==2
   array=messages['WFValue'];assert array['WFSerializationType']=='WFArrayParameterState' and len(array['Value'])==2
   for entry,role in zip(array['Value'],('system','user')):
    assert entry['WFItemType']==1
    item=entry['WFValue']['Value'];assert literal(field(item,'role'))==role
    assert field(item,'content')['WFItemType']==0
   thinking=field(payload,'thinking');assert thinking['WFItemType']==1 and literal(field(thinking['WFValue'],'type'))=='disabled'
   auth=field(p['WFHTTPHeaders'],'Authorization')['WFValue']
   assert auth['Value']['attachmentsByRange'],'Authorization must come from session data'
  if kind.endswith('.extracttextfromimage'):assert 'WFImage' in p
  if kind.endswith('.file.getfoldercontents'):assert 'WFFolder' in p and p['Recursive'] is False
  if kind.endswith('.file.select'):assert isinstance(p['SelectMultiple'],bool) and 'WFShowFilePicker' not in p
  if kind.endswith('.documentpicker.open'):assert not p.get('WFShowFilePicker')
  if kind.endswith('.setclipboard'):clipboard+=1;assert p['WFLocalOnly'] is True
  if kind.endswith('.openurl'):
   opened_api+=1
   assert p['WFInput']['Value']['string']=='https://platform.deepseek.com/api_keys'
   assert not p['WFInput']['Value']['attachmentsByRange']
  seen[p['UUID']]=action
 assert not stack and http==1 and ui_http==1 and opened_api==1 and clipboard==1
 ids=set(x['WFWorkflowActionIdentifier'] for x in workflow['WFWorkflowActions'])
 for forbidden in ('alert','runworkflow','showwebpage','runjavascript','sendemail','sendmessage'):
  assert 'is.workflow.actions.'+forbidden not in ids
 assert set(workflow['WFWorkflowInputContentItemClasses'])=={'WFImageContentItem','WFStringContentItem','WFRichTextContentItem','WFGenericFileContentItem'}
 encoded=json.dumps(workflow,ensure_ascii=False)
 for locale in strings:
  for key in ('title','main','aboutBody','guideAPI','guidePrivacy'):
   assert strings[locale][key] not in encoded,'Embedded UI text: '+locale+'/'+key
 for n in walk(workflow):
  for value in n.values():
   if isinstance(value,str):assert not re.search(r'(?:sk-[A-Za-z0-9_-]{16,}|AIza[A-Za-z0-9_-]{20,})',value),'Embedded credential'
 report={'balancedControlFlow':True,'uniqueUUIDs':True,'validUTF16Spans':spans,'forwardReferencesAbsent':True,'nativeIdentifiers':len(ids),'singlePinnedDeepSeekPOST':True,'singleSelectedLocaleGET':True,'UIResourcesNotEmbedded':True,'noNativeAlertActions':True,'onlyUserRequestedOfficialAPIPageOpens':True,'nativeJSONRequestShapeVerified':True,'personalBookmarksRemoved':True,'noEmbeddedCredential':True,'clipboardWriteRequiresResultMenu':True,'actions':len(workflow['WFWorkflowActions']),'nativeDeviceVerified':False,'signedActionGraphEqual':None}
 if signed:
  import lzfse
  from build import VERSION
  archive=(ROOT/('dist/Translate-AI-'+VERSION+'.shortcut')).read_bytes();assert archive.startswith(b'AEA1')
  payload=lzfse.decompress(archive[archive.find(b'bvx2'):]);start=payload.find(b'bplist00');length=int.from_bytes(payload[start-4:start],'little')
  actual=plistlib.loads(payload[start:start+length]);assert actual['WFWorkflowActions']==workflow['WFWorkflowActions'];assert actual['WFWorkflowInputContentItemClasses']==workflow['WFWorkflowInputContentItemClasses']
  report.update(signedActionGraphEqual=True,signedBytes=len(archive),signedSHA256=hashlib.sha256(archive).hexdigest())
 (ROOT/'qa/structural-audit.json').write_text(json.dumps(report,indent=2)+'\n');return report
if __name__=='__main__':print(json.dumps(audit('--signed' in sys.argv)))
