"""Offline ALP provenance checks. These do not certify AnyLogic GUI execution."""
from __future__ import annotations
import argparse
import hashlib
import json
from math import isfinite
from pathlib import Path
import xml.etree.ElementTree as ET
from .observation_contract import OBSERVATION_ALP_PATH, validate_schema_output
from .reward_contract import FROZEN_REWARD_PARAMETERS, REWARD_CONTRACT_ID

PARAMETERS = {
    'numTrucks':'num_trucks', 'targetGrade':'target_grade', 'waitRefSeconds':'wait_ref_seconds',
    'targetOreTons2h':'target_ore_tons_2h', 'targetOreTonsShift':'target_ore_tons_shift',
    'gradeLowerBound':'grade_lower', 'gradeUpperBound':'grade_upper',
    'targetWasteTonsShift':'target_waste_tons_shift', 'wWait':'w_wait',
    'wGrade2h':'w_grade_2h','wGradeShift':'w_grade_shift','wProduction':'w_production',
    'wGradeAction':'w_grade_action','gradePriorTons':'grade_prior_tons',
    'gradeActionDeltaClip':'grade_action_delta_clip','wWasteLag':'w_waste_lag',
    'productionLagTolerance':'production_lag_tolerance',
}

def load_alp(path):
    root=ET.parse(path).getroot()
    main=next(c for c in root.iter('ActiveObjectClass') if c.findtext('Name')=='Main')
    variables={v.findtext('Name'):v for v in main.findall('./Variables/Variable')}
    def value(name):
        prop=variables[name].find('Properties')
        return (prop.findtext('./DefaultValue/Code') or prop.findtext('./InitialValue/Code') or '').strip()
    return root, main, value


def experiment_value(main, experiment, name):
    """Resolve the active experiment's literal override, then the Main default.

    Java expressions are returned as source, never evaluated as Python. Callers
    must reject expressions they cannot prove compatible with the contract.
    """
    variable = next(v for v in main.findall('./Variables/Variable')
                    if v.findtext('Name') == name)
    if variable.get('Class') == 'Parameter':
        freeform = experiment.findtext('UseFreeformParameters')
        if freeform not in ('true', 'false'):
            raise ValueError('unknown experiment parameter mode')
        tag = 'FreeformParamValue' if freeform == 'true' else 'RangeVariationParamValue'
        entries = [e for e in experiment.findall(tag)
                   if e.findtext('Id') == variable.findtext('Id')]
        if len(entries) > 1:
            raise ValueError(f'duplicate experiment override: {name}')
        if entries:
            entry = entries[0]
            if tag == 'RangeVariationParamValue' and entry.findtext('Type') != 'FIXED':
                raise ValueError(f'varying parameter requires a separate contract: {name}')
            code = entry.findtext('./Expression/Code')
            if code and code.strip():
                return code.strip()
    properties = variable.find('Properties')
    return (properties.findtext('./DefaultValue/Code') or
            properties.findtext('./InitialValue/Code') or '').strip()


def observation_source_digest(root):
    bodies=[]
    for c in root.iter('ActiveObjectClass'):
        name=c.findtext('Name')
        if not name: continue
        for f in c.findall('./Functions/Function'):
            n=f.findtext('Name')
            if n in ('obsInit','collectPhysicalObservation','buildPhysicalObservation','appendDispatchObservation','appendCrusherFifoObservation','obsNodeIndex','obsSegmentIndex'):
                bodies.append([name,n,f.findtext('Body')])
    for c in root.iter('JavaClass'):
        if c.findtext('Name')=='DispatchObsWriter': bodies.append(['JavaClass',c.findtext('Name'),c.findtext('Text')])
    return hashlib.sha256(json.dumps(bodies,ensure_ascii=False).encode()).hexdigest()


def validate_alp_contract(path=None):
    path=Path(path) if path else Path(__file__).resolve().parents[1]/OBSERVATION_ALP_PATH
    root,main,_default_value=load_alp(path)
    exp=next(e for e in root.iter('ParamVariationExperiment') if e.findtext('Name')=='RL_Training')
    def value(name):
        return experiment_value(main, exp, name)
    for alp,key in PARAMETERS.items():
        actual = float(value(alp))
        if not isfinite(actual) or abs(actual-FROZEN_REWARD_PARAMETERS[key])>1e-9:
            raise ValueError(f'ALP parameter {alp} disagrees with reward contract')
    for name,expected in [('rlShiftSeconds','28800.0'),('rlWindowSeconds','7200.0')]:
        if float(value(name))!=float(expected): raise ValueError(f'ALP {name} mismatch')
    if value('rewardContractId') != json.dumps(REWARD_CONTRACT_ID):
        raise ValueError('ALP rewardContractId missing or incompatible')
    if value('usePhysicalObservation')!='true': raise ValueError('physical observation is disabled')
    if exp.findtext('AllowParallelEvaluations')!='false': raise ValueError('serial experiment required')
    if root.findtext('./Model/ModelTimeUnit')!='Second': raise ValueError('re-audit experiment time units')
    if float(exp.findtext('./ModelTimeProperties/FinalTime'))<28800:
        raise ValueError('experiment stops before terminal callback')
    evidence=json.loads(Path(__file__).with_name('alp_contract_provenance.json').read_text())
    if observation_source_digest(root)!=evidence['observation_source_sha256']:
        raise ValueError('observation functions changed; re-extract and re-audit schema')
    for c in root.iter('ActiveObjectClass'):
        if not c.findtext('Name'): continue
        for f in c.findall('./Functions/Function'):
            key=c.findtext('Name')+'.'+f.findtext('Name')
            digest=hashlib.sha256((f.findtext('Body') or '').encode()).hexdigest()
            if evidence['unchanged_function_body_sha256'].get(key)!=digest:
                raise ValueError(f'ALP business function changed: {key}; re-audit required')
    deterministic = value('deterministicCheck')
    if deterministic not in ('true', 'false'):
        raise ValueError(f'RL_Training deterministicCheck must be true or false, got {deterministic!r}')
    if value('currentDispatchPolicy') != '3':
        raise ValueError('RL_Training requires currentDispatchPolicy=3')
    return dict(observation_schema='dispatch.physical.v3',dimension=1519,
                reward_contract=REWARD_CONTRACT_ID,alp_runtime_verified=False,
                use_physical_observation=True, deterministic_check=deterministic == 'true')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--alp',type=Path)
    parser.add_argument('--schema-log',type=Path)
    args=parser.parse_args()
    result=validate_alp_contract(args.alp)
    if args.schema_log:
        validate_schema_output(args.schema_log.read_text())
        result['runtime_schema_log_matches']=True
    print(json.dumps(result,indent=2))

if __name__=='__main__': main()
