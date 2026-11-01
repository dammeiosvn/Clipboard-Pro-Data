from pathlib import Path
import json,sys,plistlib
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'tests'))
import test_workflow as t
from interpreter import run
baseline_path=root/'dist/AppList-Pro-1.1-beta4.shortcut'
beta4=None
if baseline_path.exists():
 import lzfse
 raw=baseline_path.read_bytes()
 payload=lzfse.decompress(raw[raw.find(b'bvx2'):]); start=payload.find(b'bplist00'); length=int.from_bytes(payload[start-4:start],'little')
 beta4=plistlib.loads(payload[start:start+length])
results=[]
for size in (10,50,100):
 records=[('App '+str(i).zfill(3),'com.example.App'+str(i),'1' if i<3 else '0') for i in range(size)]
 data=t.state(records)
 for version,workflow,disk in ([('beta4',beta4,t.Beta5UpgradeTests().legacy_disk(data))] if beta4 else []) + [('beta5',t.WORKFLOW,t.disk_of(data))]:
  direct=run(workflow,menus=[t.uid(records[-1][1])],disk=disk)
  repeated=run(workflow,menus=['manage','main']*3+[t.uid(records[-1][1])],disk=disk)
  assert direct['opened']==repeated['opened']==[records[-1][1]]
  assert not direct['writes'] and not repeated['writes'] and not direct['requests'] and not repeated['requests']
  results.append({'version':version,'apps':size,'actionsBeforeFirstMenu':direct['firstMenuActions'],'meanAdditionalActionsPerManageAndBack':(repeated['executed']-direct['executed'])/3})
 first=run(t.WORKFLOW,menus=['manage','pickEdit',t.uid(records[0][1]),'rename'],answers=['Renamed app'],disk=t.disk_of(data))
 assert not first['alerts'],first['alerts']
 again=run(t.WORKFLOW,menus=[t.uid(records[0][1])],disk=first['disk'])
 assert again['opened']==[records[0][1]]
 assert len(t.read_state(again)['names'])==size
report={'measurement':'Executed actions in the host graph interpreter; not iPhone timing','nativeDeviceTimingMeasured':False,'normalLaunchWrites':0,'normalLaunchNetworkRequests':0,'largeListEditReloadPassed':[10,50,100],'results':results}
(root/'qa/menu-workload.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))
