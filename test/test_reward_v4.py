import csv
import json
import hashlib
from pathlib import Path
import numpy as np
import pytest
from types import SimpleNamespace
from stable_baselines3.common.logger import configure
from python.reward_config import RewardConfiguration
from python.reward_contract import validate_reward_accounting,REWARD_CONTRACT_ID,ADDITIVE_COMPONENTS
from python.alp_audit import validate_alp_contract
from python.dispatch_bridge import DispatchCallbackBridge,ProtocolError
from python.generated import dispatch_pb2 as pb
from python.stage_statistics import StageStatisticsCallback
from python.train import _validate_resume_contract
from python.masked_policy import POLICY_CONTRACT_ID
from test_contracts import request


def terminal(enabled=False,tons=2000,weight=4,target=4000):
    r=request(pb.EPISODE_END,1,0,28800)
    r.reward_components['grade_action_enabled']=int(enabled)
    fraction=tons/target if target>0 else 0
    shortfall=max(0,min(1,1-fraction)) if target>0 else 0
    r.reward_components.update(waste_tons_shift=tons,waste_target_tons=target,
                              waste_fraction_raw=fraction,waste_shortfall=shortfall,waste=-weight*shortfall)
    r.transition_reward=sum(r.reward_components[k] for k in ADDITIVE_COMPONENTS)
    return r,RewardConfiguration(enabled,weight,target)


@pytest.mark.parametrize('enabled',[True,False])
def test_start_flag_is_metadata_and_variant_is_enforced(enabled):
    r=request();r.reward_components['grade_action_enabled']=int(enabled)
    config=RewardConfiguration(enabled)
    DispatchCallbackBridge._validate_request(r,config=config)
    with pytest.raises(ProtocolError,match='configuration'):
        DispatchCallbackBridge._validate_request(r,config=RewardConfiguration(not enabled))


@pytest.mark.parametrize('tons,weight,target',[(0,4,4000),(2000,4,4000),(4000,4,4000),(6000,4,4000),(2000,0,4000),(2000,2.5,4000),(2000,4,0)])
def test_terminal_waste_formula(tons,weight,target):
    r,cfg=terminal(tons=tons,weight=weight,target=target)
    DispatchCallbackBridge._validate_request(r,config=cfg)
    assert r.reward_components['waste']==pytest.approx(-weight*max(0,1-tons/target) if target else 0)


def test_disabled_cannot_leak_shaping_and_enabled_negative_bound():
    r,cfg=terminal()
    r.reward_components['grade_action']=.001;r.transition_reward+=.001
    with pytest.raises(ProtocolError,match='exactly zero'): DispatchCallbackBridge._validate_request(r,config=cfg)
    r,cfg=terminal(enabled=True);r.reward_components['grade_action']=-.015;r.transition_reward-=.015
    DispatchCallbackBridge._validate_request(r,config=cfg)
    r.reward_components['grade_action']=-.02;r.transition_reward-=.005
    with pytest.raises(ProtocolError,match='clipping'): DispatchCallbackBridge._validate_request(r,config=cfg)


@pytest.mark.parametrize('field,value',[('waste',0),('waste_shortfall',0),('waste_fraction_raw',9),('waste_target_tons',2000),('grade_action_enabled',2)])
def test_incorrect_v4_diagnostics_rejected(field,value):
    r,cfg=terminal();r.reward_components[field]=value
    r.transition_reward=sum(r.reward_components[k] for k in ADDITIVE_COMPONENTS)
    with pytest.raises(ProtocolError):DispatchCallbackBridge._validate_request(r,config=cfg)


def test_no_v3_or_early_terminal_rewards():
    r=request();r.reward_contract_id='dispatch-reward-physical-v3'
    with pytest.raises(ProtocolError,match='reward_contract_id'):DispatchCallbackBridge._validate_request(r)
    r=request(pb.DECISION,1,0,100);r.reward_components['waste']=-1;r.transition_reward=-1
    with pytest.raises(ProtocolError,match='terminal-only'):DispatchCallbackBridge._validate_request(r)


def test_flag_cannot_change_after_start():
    b=DispatchCallbackBridge(reward_config=RewardConfiguration(True));r=request();r.reward_components['grade_action_enabled']=1
    t=b._register(r);b.next_callback(timeout=1);b.respond_action(t,0)
    r=request(pb.DECISION,1,0,1)
    with pytest.raises(ProtocolError,match='configuration'):b._register(r)


@pytest.mark.parametrize('enabled',[True,False])
def test_alp_ablations_from_temporary_copies(enabled,tmp_path):
    from test_alp_experiment import model,override,write_model
    root,main,exp=model();override(main,exp,'enableGradeActionReward',str(enabled).lower())
    override(main,exp,'wWasteShortfall','2.5')
    result=validate_alp_contract(write_model(tmp_path,root))
    assert result['reward_configuration']==RewardConfiguration(enabled,2.5).to_dict()
    assert result['ablation_variant']==('grade-action-on' if enabled else 'grade-action-off')


def test_resume_rejects_cross_ablation(tmp_path):
    checkpoint=tmp_path/'model.zip';checkpoint.write_bytes(b'metadata fixture')
    cfg=RewardConfiguration(True)
    metadata=dict(reward_contract_id=REWARD_CONTRACT_ID,policy_contract_id=POLICY_CONTRACT_ID,
                  reward_configuration_fingerprint=cfg.fingerprint,observation_schema_id='dispatch.physical.v3',
                  model_sha256=hashlib.sha256(checkpoint.read_bytes()).hexdigest())
    for name in ['run_manifest.json','SUCCESS.json']:(tmp_path/name).write_text(json.dumps(metadata))
    _validate_resume_contract(checkpoint,cfg)
    with pytest.raises(SystemExit,match='ablation'):_validate_resume_contract(checkpoint,RewardConfiguration(False))


def test_episode_logs_separate_rewards_physics_and_flags(tmp_path):
    cfg=RewardConfiguration(True)
    callback=StageStatisticsCallback(tmp_path,cfg)
    callback.model=SimpleNamespace(num_timesteps=0,logger=configure(str(tmp_path),['csv']))
    # Stage init only needs SB3 episode deques and its logger.
    callback.model.ep_info_buffer=None;callback.model.ep_success_buffer=None;callback.model._stats_window_size=100
    callback._on_training_start()
    first=request();first.reward_components['grade_action_enabled']=1
    end,cfg=terminal(enabled=True);end.reward_components['grade_action']=.01;end.transition_reward+=.01
    for i,r in enumerate([first,end]):
        callback.model.num_timesteps=i+1
        info=dict(transition_reward_raw=r.transition_reward,reward_components=dict(r.reward_components),
                  closed_windows=[dict(window_index=w.window_index,violation_upper=w.violation_upper,
                                       violation_lower=w.violation_lower) for w in r.closed_windows],episode_id='test')
        callback.locals=dict(rewards=np.array([r.transition_reward]),infos=[info],dones=np.array([i==1]))
        callback._on_step()
    callback._on_training_end()
    row=json.loads((tmp_path/'stage_episodes.jsonl').read_text())
    assert set(row['reward_components'])==set(ADDITIVE_COMPONENTS)
    assert row['grade_action_enabled'] is True  # not sum(flag)=2
    assert row['terminal_metrics']['waste_tons_shift']==2000
    assert row['base_return']==pytest.approx(row['raw_return']-.01)
    assert len(row['closed_windows'])==4 and row['window_violation_rate']==0
    with (tmp_path/'episodes.csv').open() as f:csv_rows=list(csv.DictReader(f))
    assert len(csv_rows)==1 and csv_rows[0]['waste']=='-2.0'
    assert not (tmp_path/'transitions.jsonl').exists()


@pytest.mark.parametrize('enabled,expected',[(False,'on'),(True,'off')])
def test_cli_expectation_checks_runtime_switch(enabled,expected):
    from python.train import _validate_expected_variant
    with pytest.raises(SystemExit,match='runtime configuration'):
        _validate_expected_variant(expected,RewardConfiguration(enabled))
    _validate_expected_variant('auto',RewardConfiguration(enabled))


def test_manifest_does_not_read_alp_by_default(monkeypatch,tmp_path):
    from python import train
    seeds=tmp_path/'seeds.json'
    seeds.write_text(json.dumps([dict(run_index=i+1,experiment_seed=10+i) for i in range(2)]))
    monkeypatch.setattr('sys.argv',['train','--episodes','2','--anylogic-seed-manifest',str(seeds)])
    def forbidden(*args):raise AssertionError('must not audit a local ALP by default')
    monkeypatch.setattr(train,'validate_alp_contract',forbidden)
    args=train.parse_args()
    manifest=train._manifest(args,tmp_path/'not-created',RewardConfiguration(True))
    assert manifest['alp_path'] is None and manifest['alp_sha256'] is None
    assert manifest['configuration_source']=='anylogic_rpc'
    assert manifest['ablation_variant']=='grade-action-on'


def test_waste_action_has_no_grade_shaping_even_when_enabled():
    r,cfg=terminal(enabled=True);r.previous_action=3
    DispatchCallbackBridge._validate_request(r,config=cfg)
    r.reward_components['grade_action']=.001;r.transition_reward+=.001
    with pytest.raises(ProtocolError,match='WASTE action'):
        DispatchCallbackBridge._validate_request(r,config=cfg)
