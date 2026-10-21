"""Statically expand writer calls in the audited ALP; run from repository root.

This narrow extractor fails on unsupported syntax. Always compare the first
real [OBS_SCHEMA_BEGIN] output using python -m python.alp_audit --schema-log.
"""
import re,xml.etree.ElementTree as E,json
from pathlib import Path
r=E.parse('anylogic/DRL-PPO.alp').getroot()
classes={c.findtext('Name'):c for c in r.iter('ActiveObjectClass') if c.findtext('Name')}
def body(c,n):
 return next(f.findtext('Body') for f in classes[c].iter('Function') if f.findtext('Name')==n)
fields=[]
def add(name,formula,source,kind='scaled'):
 fields.append(dict(index=len(fields),name=name,formula=formula,source=source,kind=kind))
def expand(c,prefix):
 b=body(c,'appendDispatchObservation')
 # Operations occur in lexical order; only the motion loop nests writer calls.
 pat=r'w\.(add|oneHot|truckSlots)\((.*?)\);'
 for m in re.finditer(pat,b,re.S):
  op,args=m.groups(); name,expr=args.split(',',1); name=name.strip(); expr=expr.strip()
  if name.startswith('hp+'):
   continue
  suffix=re.search(r'"([^"]*)"',name).group(1)
  if op=='oneHot':
   value,count=expr.rsplit(',',1)
   for i in range(int(count)): add(prefix+suffix+str(i),f'oneHot({value.strip()}, {i})',c,'binary')
  elif op=='truckSlots':
   for i in range(9): add(prefix+suffix+str(i),'i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0',c,'truck_slot')
  elif '+i' in name:
   assert suffix=='routeOrder.'
   for i in range(16): add(prefix+suffix+str(i),f'routeOrder[{i}] = (j-currentSegmentIndex+1.0)/16.0 or 0',c,'unit')
  else: add(prefix+suffix,expr,c,'binary' if '?1:0' in expr or '?0:1' in expr else 'scaled')
 if c=='Truck':
  for i in range(4):
   for m in re.finditer(r'w.add\(hp\+"([^"]+)",(.*?)\);',b):
    suffix,expr=m.groups(); add(prefix+f'motion.{i}.'+suffix,expr,c,'binary' if suffix in ('valid','hasFront') else 'scaled')
b=body('Main','collectPhysicalObservation')
for m in re.finditer(r'w.add\("(global\.[^"]+)",(.*?)\);',b):
 name,expr=m.groups(); add(name,expr,'Main','binary' if '?1:0' in expr else 'scaled')
for i in range(4): add(f'actionMask.{i}','!terminal && getLoadSiteById(i).getAvailableTons()>1e-6 ? 1 : 0','Main','binary')
for i in range(4): add(f'actionTons.{i}','!terminal ? min(ego.capacity,getLoadSiteById(i).getAvailableTons())/193.0 : 0','Main','unit')
for i in range(9): expand('Truck',f'truck.{i}.')
for i in range(4): expand('LoadSite',f'load.{i}.')
for i in range(2): expand('DumpSite',f'dump.{i}.')
for i in range(16):
 for suffix,expr,kind in [('valid','batch present ? 1 : 0','binary'),('tons','batch present ? b[0]/500.0 : 0','scaled'),('grade','batch present ? b[1] : 0','unit')]: add(f'fifo.{i}.{suffix}',expr,'DumpSite.appendCrusherFifoObservation',kind)
for i in range(16):
 for suffix,expr,kind in [('from','(obsNodeIndex(s.from)+1.0)/9.0','unit'),('to','(obsNodeIndex(s.to)+1.0)/9.0','unit'),('length','s.length/10000.0','scaled'),('limit','s.speedLimit/10.0','scaled'),('closed','s.closed?1:0','binary')]: add(f'road.{i}.{suffix}',expr,'Main',kind)
assert len(fields)==1519,len(fields)
assert len({f['name'] for f in fields})==1519
Path('python/observation_schema.json').write_text(json.dumps(fields,ensure_ascii=False,indent=2)+'\n')
print([(prefix,sum(f['name'].startswith(prefix) for f in fields)) for prefix in ['global.','actionMask.','actionTons.','truck.','load.','dump.','fifo.','road.']])

import runpy
runpy.run_path(str(Path(__file__).with_name("enrich_observation_schema.py")), run_name="__main__")
