"""Independent native contracts, reference/control integrity and signed-graph parity."""
from pathlib import Path
import plistlib,json,re,uuid,hashlib,sys
ROOT=Path(__file__).resolve().parents[1]
MAIN='Quick-Translation';SCREEN='Quick-Translation-Screen'
BASE='https://raw.githubusercontent.com/dammeiosvn/Clipboard-Pro-Data/main/quick-translation/resources/v1/'
def walk(value):
 if isinstance(value,dict):
  yield value
  for child in value.values():yield from walk(child)
 elif isinstance(value,list):
  for child in value:yield from walk(child)
def decode_archive(data):
 import lzfse
 assert data.startswith(b'AEA1')
 # Signed Apple archives may contain several independent 1 MiB LZFSE streams.
 def next_stream(start):
  candidates=[data.find(magic,start) for magic in (b'bvx2',b'bvxn',b'bvx-')]
  return min((p for p in candidates if p>=0),default=-1)
 cursor=next_stream(0);parts=[]
 while cursor>=0:
  end=data.find(b'bvx$',cursor)
  assert end>=0
  parts.append(lzfse.decompress(data[cursor:end+4]))
  cursor=next_stream(end+4)
 payload=b''.join(parts);start=payload.find(b'bplist00');assert start>=4
 length=int.from_bytes(payload[start-4:start],'little');return plistlib.loads(payload[start:start+length])
def audit(signed=False):
 contract=json.loads((ROOT/'config/native-actions.json').read_text());known=set(contract['identifiers'])
 labels=json.loads((ROOT/'config/strings.json').read_text());assert set(labels['vi'])==set(labels['en'])
 reports={}
 for name in (MAIN,SCREEN):
  raw=(ROOT/('dist/'+name+'.unsigned.bplist')).read_bytes();workflow=plistlib.loads(raw)
  assert workflow==plistlib.loads((ROOT/('dist/'+name+'.unsigned.shortcut')).read_bytes())
  actions=workflow['WFWorkflowActions'];seen={};stack=[];spans=0;counts={}
  for i,action in enumerate(actions):
   kind=action['WFWorkflowActionIdentifier'];p=action['WFWorkflowActionParameters']
   assert kind in known,(i,kind);uuid.UUID(p['UUID']);assert p['UUID'] not in seen
   counts[kind]=counts.get(kind,0)+1
   for node in walk(p):
    assert 'crossDeviceItemID' not in node
    if node.get('Type')=='ActionOutput':assert node['OutputUUID'] in seen,(i,node)
    if node.get('WFSerializationType')=='WFTextTokenString':
     value=node['Value'];data=value['string'].encode('utf-16-le')
     for span in value.get('attachmentsByRange',{}):
      m=re.fullmatch(r'\{(\d+), 1\}',span);assert m
      assert data[int(m[1])*2:int(m[1])*2+2]==b'\xfc\xff';spans+=1
   if 'GroupingIdentifier' in p:
    group=p['GroupingIdentifier'];mode=p['WFControlFlowMode']
    if mode==0:stack.append((group,kind,False))
    elif mode==1:
     assert stack[-1][:2]==(group,kind) and not stack[-1][2];stack[-1]=(group,kind,True)
    else:assert mode==2 and stack.pop()[:2]==(group,kind)
   if kind.endswith('.conditional') and p['WFControlFlowMode']==0:
    assert p['WFCondition'] in (2,4)
    if p['WFCondition']==4:
     for node in walk(p['WFConditionalActionString']):
      if node.get('Type')=='ActionOutput':assert seen[node['OutputUUID']]['WFWorkflowActionIdentifier'].endswith('.gettext')
   if kind.endswith('.downloadurl'):
    assert name==MAIN and p['WFHTTPMethod']=='GET'
    assert not p.get('WFHTTPHeaders') and not p.get('WFJSONValues') and not p.get('WFHTTPBodyType')
    if isinstance(p['WFURL'],str):assert p['WFURL']==BASE+'catalog.json'
    else:
     assert p['WFURL']['Value']['string']==BASE+'ui/\ufffc.json'
     assert list(p['WFURL']['Value']['attachmentsByRange'].values())==[{'Type':'Variable','VariableName':'RequestedUI'}]
   if kind.endswith('.text.translate'):
    assert name==MAIN and set(p)-{'UUID','CustomOutputName'} in ({'WFInputText','WFSelectedLanguage'},{'WFInputText','WFSelectedLanguage','WFSelectedFromLanguage'})
    assert p['WFInputText']['WFSerializationType']=='WFTextTokenString'
    assert p['WFSelectedLanguage']['WFSerializationType']=='WFTextTokenAttachment'
   if kind.endswith('.detectlanguage'):assert set(p)-{'UUID','CustomOutputName'}=={'WFInput'}
   if kind.endswith('.previewdocument'):assert set(p)-{'UUID','CustomOutputName'}=={'WFInput'}
   if kind.endswith('.showresult'):assert set(p)-{'UUID','CustomOutputName'}=={'Text'}
   if kind.endswith('.splitpdf'):assert set(p)-{'UUID','CustomOutputName'}=={'WFInput'}
   if kind.endswith('.gettextfrompdf'):assert p['WFCombinePages'] is True and 'WFInput' in p
   if kind.endswith('.makeimagefrompdfpage'):assert p['WFMakeImageFromPDFPageResolution']=='150' and p['WFMakeImageFromPDFPageColorspace']=='RGB'
   if kind.endswith('.properties.files'):assert 'WFFolder' in p and p['WFContentItemPropertyName'] in ('File Extension','File Size')
   if kind.endswith('.extracttextfromimage'):assert set(p)-{'UUID','CustomOutputName'}=={'WFImage'}
   if kind.endswith('.file.select'):assert isinstance(p['SelectMultiple'],bool) and 'WFShowFilePicker' not in p
   if kind.endswith('.documentpicker.open'):
    assert not p.get('WFShowFilePicker') and p['WFFileErrorIfNotFound'] is False
    assert p['WFGetFilePath']['Value']['string'].startswith('QuickTranslation/')
   if kind.endswith('.documentpicker.save') and not p['WFAskWhereToSave']:
    assert p['WFFileDestinationPath']['Value']['string'].startswith('QuickTranslation/')
   if kind.endswith('.file.getfoldercontents'):assert p['Recursive'] is False and 'WFFolder' in p
   if kind.endswith('.setclipboard'):assert p['WFLocalOnly'] is True
   if kind.endswith('.getdevicedetails'):assert p['WFDeviceDetail']=='System Version'
   if kind.endswith('.runworkflow'):
    assert name==SCREEN and p['WFWorkflowName']==MAIN
    assert p['WFInput']['Value']['OutputUUID']==actions[0]['WFWorkflowActionParameters']['UUID']
   seen[p['UUID']]=action
  assert not stack
  for forbidden in ('alert','showwebpage','runjavascript','base64encode','openurl','sendemail','sendmessage','savetocameraroll','file.delete'):
   assert 'is.workflow.actions.'+forbidden not in counts
  assert workflow['WFWorkflowNoInputBehavior'].get('Name')!='WFWorkflowNoInputBehaviorGetClipboard'
  if name==MAIN:
   assert counts['is.workflow.actions.downloadurl']==2 and counts['is.workflow.actions.text.translate']==2
   assert counts['is.workflow.actions.previewdocument']>10 and counts['is.workflow.actions.setclipboard']==1
   assert 'is.workflow.actions.runworkflow' not in counts
   assert set(workflow['WFWorkflowInputContentItemClasses'])=={'WFImageContentItem','WFStringContentItem','WFRichTextContentItem','WFPDFContentItem','WFGenericFileContentItem'}
   encoded=json.dumps(workflow,ensure_ascii=False)
   for code in labels:
    for key in ('title','main','guideInputs','guidePDF','guideScreen','guideData'):assert labels[code][key] not in encoded,(code,key)
   assert 'deepseek' not in encoded.lower() and 'Sentechtipsvn/' not in encoded
  else:
   assert len(actions)==4 and actions[0]['WFWorkflowActionIdentifier']=='is.workflow.actions.takescreenshot'
   assert actions[0]['WFWorkflowActionParameters']['WFTakeScreenshotScreenshotType']=='Full Screen'
   assert counts['is.workflow.actions.runworkflow']==1 and not workflow['WFWorkflowTypes']
  for node in walk(workflow):
   for value in node.values():
    if isinstance(value,str):assert not re.search(r'(?i)sk-[A-Za-z0-9_-]{16,}|AIza[A-Za-z0-9_-]{20,}|navigator\.language|BEGIN:VCARD',value)
  report={'actions':len(actions),'nativeIdentifiers':len(counts),'balancedControls':True,'uniqueUUIDs':True,'noForwardActionReferences':True,'validUTF16Spans':spans,'noPersonalBookmarks':True,'noEmbeddedLocalePacks':name==MAIN,'noDirectTranslationHTTP':True,'noAutomaticClipboardRead':True,'signedGraphEqual':None}
  if signed:
   archive=(ROOT/('dist/'+name+'.shortcut')).read_bytes();actual=decode_archive(archive)
   assert actual['WFWorkflowActions']==workflow['WFWorkflowActions']
   assert actual['WFWorkflowInputContentItemClasses']==workflow['WFWorkflowInputContentItemClasses']
   report.update(signedGraphEqual=True,signedBytes=len(archive),signedSHA256=hashlib.sha256(archive).hexdigest())
  reports[name]=report
 output={'version':'1.0-beta1','workflows':reports,'nativeDeviceVerified':False}
 (ROOT/'qa/structural-audit.json').write_text(json.dumps(output,indent=2)+'\n');return output
if __name__=='__main__':print(json.dumps(audit('--signed' in sys.argv)))
