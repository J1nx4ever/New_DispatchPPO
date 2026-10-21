"""Write recursive file/import/path evidence; no simulation is started."""
import ast
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET
import zipfile

ROOT=Path(__file__).resolve().parents[1]

def main():
    files=[]; imports={}; paths={}; jars={}
    for folder in ('anylogic','python','proto','proto-src','dist','test'):
        for p in sorted((ROOT/folder).rglob('*')):
            if not p.is_file(): continue
            rel=str(p.relative_to(ROOT))
            files.append(dict(path=rel,bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
            if p.suffix=='.py':
                tree=ast.parse(p.read_text())
                imports[rel]=[ast.unparse(n) for n in ast.walk(tree) if isinstance(n,(ast.Import,ast.ImportFrom))]
                paths[rel]=sorted({n.value for n in ast.walk(tree) if isinstance(n,ast.Constant) and isinstance(n.value,str) and (n.value.endswith(('.json','.jsonl','.csv','.jar','.proto','.alp','.zip','.npz')) or '/' in n.value)})
            if p.suffix=='.jar':
                with zipfile.ZipFile(p) as z: jars[rel]=z.namelist()
    p=ROOT/'requirements.txt'
    files.append(dict(path='requirements.txt',bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
    r=ET.parse(ROOT/'anylogic/DRL-PPO.alp').getroot()
    resources=[]
    for e in r.findall('./Model/ModelResources/Resource'):
        path=e.findtext('Path')
        resources.append(dict(path=path,exists_relative_to_alp=(ROOT/'anylogic'/path).is_file()))
    experiments=[]
    for e in r.iter('ParamVariationExperiment'):
        experiments.append(dict(name=e.findtext('Name'),number_of_runs=e.findtext('NumberOfRuns'),
            serial=e.findtext('AllowParallelEvaluations')=='false',freeform=e.findtext('UseFreeformParameters'),
            use_replication=e.findtext('./ReplicationsProperties/UseReplication'),
            final_time=e.findtext('./ModelTimeProperties/FinalTime'),
            arguments=e.findtext('CommandLineArguments'),vm_args=e.findtext('VmArgs'),
            overrides=[dict(id=x.findtext('Id'),expression=x.findtext('./Expression/Code')) for x in e.findall('FreeformParamValue')]))
    evidence=dict(files=files,python_imports=imports,python_path_strings=paths,jar_entries=jars,
                  alp_resources=resources,parameter_variations=experiments)
    (ROOT/'docs/phase1_inventory.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(files=len(files),python_modules=len(imports),jars=len(jars),
        unresolved_alp_resources=[x['path'] for x in resources if not x['exists_relative_to_alp']]),ensure_ascii=False,indent=2))

if __name__=='__main__': main()
