"""Sign only generated public workflows with Shortcuty's documented signing API."""
from pathlib import Path
import base64,hashlib,json,plistlib,urllib.request,uuid
ROOT=Path(__file__).resolve().parents[1]
ENDPOINT='https://sign.shortcuty.app/api/v1/sign?response=json'
def main():
 reports={}
 for name in ('Quick-Translation','Quick-Translation-Screen'):
  source=ROOT/('dist/'+name+'.unsigned.bplist');raw=source.read_bytes()
  assert plistlib.loads(raw)==plistlib.loads((ROOT/('dist/'+name+'.unsigned.shortcut')).read_bytes())
  boundary='QuickTranslation-'+uuid.uuid4().hex
  header=('--'+boundary+'\r\nContent-Disposition: form-data; name="file"; filename="'+name+'.shortcut"\r\nContent-Type: application/octet-stream\r\n\r\n').encode()
  body=header+raw+('\r\n--'+boundary+'--\r\n').encode()
  req=urllib.request.Request(ENDPOINT,data=body,headers={'Content-Type':'multipart/form-data; boundary='+boundary,'User-Agent':'QuickTranslation-Build/1.0','Accept':'application/json'})
  with urllib.request.urlopen(req,timeout=55) as response:result=json.load(response)
  assert result.get('success') is True,result.get('error')
  item=result['file'];content=base64.b64decode(item['content_base64'],validate=True)
  assert item['input_sha256']==hashlib.sha256(raw).hexdigest()
  assert item['signed_sha256']==hashlib.sha256(content).hexdigest()
  assert item['format']=='AEA1' and item['signing_mode']=='anyone' and content.startswith(b'AEA1') and len(content)==item['size']
  (ROOT/('dist/'+name+'.shortcut')).write_bytes(content)
  reports[name]={'signed':True,'mode':'anyone','format':'AEA1','bytes':len(content),'sha256':item['signed_sha256'],'inputSHA256':item['input_sha256']}
  print(json.dumps({name:reports[name]}),flush=True)
 report={'version':'1.0-beta1','workflows':reports,'nativeDeviceVerified':False}
 (ROOT/'qa/signing.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
