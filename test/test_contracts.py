from concurrent.futures import ThreadPoolExecutor
import hashlib
import importlib
import json
from pathlib import Path
import pkgutil

import grpc
import numpy as np
import pytest
from python import observation_contract as oc
from python import reward_contract as rc
from python.alp_audit import validate_alp_contract
from python.dispatch_bridge import DispatchCallbackBridge, ProtocolError, observation_array
from python.dispatch_env import DispatchEnv
from python.dispatch_service import DispatchService
from python.episode_runner import ParameterVariationEpisodeRunner
from python.generated import dispatch_pb2 as pb, dispatch_pb2_grpc as rpc
from python.protocol_artifacts import verify_protocol_artifacts

ROOT=Path(__file__).resolve().parents[1]
CORE_HASH='8e4cfa31c622f5e33756e304eea3f7526547db72ae93f7d9f00808845d61ef96'

def obs(terminal=False, truck=0):
    x=np.zeros(1519,dtype=np.float32)
    x[17]=terminal
    if not terminal:
        x[19:23]=1
        x[oc.EGO_INDICES[truck]]=1
    return x

def windows():
    return [pb.WindowSummary(window_index=i,window_start_seconds=i*7200,
        window_end_seconds=(i+1)*7200,ore_tons=4000,metal_tons=1080,grade=.27,
        grade_gap=0,grade_reward_raw=1,grade_reward_weighted=1) for i in range(4)]

def request(kind=pb.EPISODE_START, seq=0, action=-1, time=0):
    terminal=kind==pb.EPISODE_END
    components=dict(wait=0,production=0,grade_2h=0,grade_shift=0,grade_action=0,delta_wait_vehicle_seconds=0)
    if terminal:
        components.update(grade_2h=4,grade_shift=6,grade_gap_shift=0,grade_shift_reward_raw=1,
                          ore_tons_shift=16000,production_fraction_raw=1,production_shortfall=0,shift_grade=.27)
    return pb.DispatchRequest(truck_id=-1 if terminal else 0,
        obs=pb.Observation(schema_id=oc.OBSERVATION_SCHEMA_ID,values=obs(terminal)),
        episode_id='e1',request_id=f'e1-{seq}',kind=kind,decision_sequence=seq,
        action_required=not terminal,previous_action=action,transition_reward=10 if terminal else 0,
        reward_components=components,sim_time_seconds=time,sim_time_delta_seconds=time,
        terminated=terminal,experiment_run_index=1,experiment_seed=202610160011,
        reward_contract_id=rc.REWARD_CONTRACT_ID,closed_windows=windows() if terminal else [])


def test_import_all_modules():
    import python
    for entry in pkgutil.walk_packages(python.__path__, 'python.'):
        importlib.import_module(entry.name)


def test_core_unchanged():
    assert hashlib.sha256((ROOT/'python/episode_budget_ppo.py').read_bytes()).hexdigest()==CORE_HASH


def test_alp_and_artifacts():
    assert validate_alp_contract()['alp_runtime_verified'] is False
    assert verify_protocol_artifacts()['java_python_descriptor_equal']
    assert len(oc.FIELD_NAMES)==len(set(oc.FIELD_NAMES))==1519
    assert oc.FIELD_NAMES[19:23]==tuple(f'actionMask.{i}' for i in range(4))
    assert oc.FIELD_NAMES[1439]=='road.0.from'


def test_observation_float32_and_scaled_values_above_one():
    r=request(); r.obs.values[0]=.123456789; r.obs.values[oc.FIELD_NAMES.index('truck.0.freeSamples')]=100
    x=observation_array(r)
    assert x.shape==(1519,) and x.dtype==np.float32
    assert x[oc.FIELD_NAMES.index('truck.0.freeSamples')]==100
    assert DispatchEnv(DispatchCallbackBridge()).observation_space.contains(x)


@pytest.mark.parametrize('problem',['schema','short','long','nan','inf','mask','ego','terminal','onehot'])
def test_observation_rejects(problem):
    r=request()
    if problem=='schema': r.obs.schema_id='dispatch.v2-31'
    elif problem=='short': r.obs.values.pop()
    elif problem=='long': r.obs.values.append(0)
    elif problem in ('nan','inf'): r.obs.values[99]=float(problem)
    elif problem=='mask': r.obs.values[19]=.5
    elif problem=='ego': r.truck_id=1
    elif problem=='terminal': r.obs.values[17]=1
    elif problem=='onehot':
        r.obs.values[28:31]=[1,1,0]
    with pytest.raises(ProtocolError): observation_array(r)


def test_float32_overflow():
    values=obs().astype(np.float64); values[100]=1e100
    with pytest.raises(ValueError,match='overflow'): oc.validate_observation(oc.OBSERVATION_SCHEMA_ID,values)


def test_schema_csv_comparison():
    output='[OBS_SCHEMA_BEGIN]\nindex,name\n'+''.join(f'{i},{n}\n' for i,n in enumerate(oc.FIELD_NAMES))+'[OBS_SCHEMA_END]'
    assert oc.validate_schema_output(output)
    with pytest.raises(ValueError): oc.validate_schema_output(output.replace('truck.0.ego','wrong'))
    with pytest.raises(ValueError): oc.validate_schema_output('')


def test_reward_current_alp_math():
    assert rc.FROZEN_REWARD_PARAMETERS['num_trucks']==9
    assert rc.grade_reward(-.01)==pytest.approx(0)
    assert rc.grade_reward(.01)==pytest.approx(0)
    assert rc.grade_reward(0)==1
    assert rc.grade_reward(.1)==-1
    c=dict(request().reward_components); c.update(wait=-.5,delta_wait_vehicle_seconds=900)
    rc.validate_reward_accounting(-.5,c,[])
    for w in windows(): rc.validate_window_summary(rc.window_summary_to_dict(w))
    r=request(pb.EPISODE_END,1,0,28800)
    rc.validate_reward_accounting(10,dict(r.reward_components),[rc.window_summary_to_dict(w) for w in r.closed_windows])


@pytest.mark.parametrize('problem',['sum','diagnostic_nan','wait','window','terminal','missing'])
def test_reward_rejects(problem):
    r=request(pb.EPISODE_END,1,0,28800)
    if problem=='sum': r.transition_reward+=1
    elif problem=='diagnostic_nan': r.reward_components['diagnostic']=float('nan')
    elif problem=='wait': r.reward_components['delta_wait_vehicle_seconds']=900
    elif problem=='window': r.closed_windows[0].violation_upper=True
    elif problem=='terminal': r.reward_components['production_fraction_raw']=5
    elif problem=='missing': del r.reward_components['grade_action']
    with pytest.raises(ProtocolError): DispatchCallbackBridge._validate_request(r)


def test_serialization():
    r=request(pb.EPISODE_END,1,0,28800)
    assert pb.DispatchRequest.FromString(r.SerializeToString())==r
    response=pb.DispatchResponse(action=3,has_action=True,episode_id='e1',decision_sequence=1,logits=[1,2,3,4])
    assert pb.DispatchResponse.FromString(response.SerializeToString())==response
    assert pb.DispatchRequest.DESCRIPTOR.fields_by_name['reward_contract_id'].number==18


@pytest.mark.parametrize('problem',['sequence','previous_action','metadata','time_delta','terminal_flag','unknown_kind'])
def test_bridge_correlation_rejects(problem):
    b=DispatchCallbackBridge(); ticket=b._register(request()); b.respond_action(ticket,2)
    r=request(pb.DECISION,1,2,100)
    if problem=='sequence': r.decision_sequence=2
    elif problem=='previous_action': r.previous_action=1
    elif problem=='metadata': r.experiment_seed+=1
    elif problem=='time_delta': r.sim_time_delta_seconds=99
    elif problem=='terminal_flag': r.terminated=True
    elif problem=='unknown_kind': r.kind=9
    with pytest.raises(ProtocolError): b._register(r)


def test_duplicate_and_mask_rejection():
    b=DispatchCallbackBridge(); r=request(); r.obs.values[19]=0
    t=b._register(r)
    assert b._register(r) is t
    with pytest.raises(ProtocolError,match='masked'): b.respond_action(t,0)
    b.respond_action(t,1)
    r.truck_id=2
    with pytest.raises(ProtocolError): b._register(r)


def test_real_grpc_gym_lifecycle():
    b=DispatchCallbackBridge()
    server=grpc.server(ThreadPoolExecutor(max_workers=2))
    rpc.add_DispatchServiceServicer_to_server(DispatchService(b),server)
    port=server.add_insecure_port('127.0.0.1:0'); assert port
    server.start()
    env=DispatchEnv(b,ParameterVariationEpisodeRunner(1),callback_timeout=5)
    try:
        with grpc.insecure_channel(f'127.0.0.1:{port}') as channel:
            stub=rpc.DispatchServiceStub(channel)
            def simulate():
                a=stub.GetNextDestination(request(),timeout=10)
                assert a.has_action and a.action==2 and a.episode_id=='e1' and a.decision_sequence==0
                r=request(pb.DECISION,1,a.action,100)
                a=stub.GetNextDestination(r,timeout=10)
                assert a.action==1 and a.decision_sequence==1
                r=request(pb.EPISODE_END,2,a.action,28800); r.sim_time_delta_seconds=28700
                ack=stub.GetNextDestination(r,timeout=10)
                assert not ack.has_action
            with ThreadPoolExecutor(max_workers=1) as pool:
                future=pool.submit(simulate)
                x,info=env.reset(seed=1); assert x.shape==(1519,) and info['action_mask']==[True]*4
                x,reward,term,trunc,info=env.step(2)
                assert reward==0 and not term and not trunc and info['previous_action']==2
                with pytest.raises(RuntimeError): env.reset()
                x,reward,term,trunc,info=env.step(1)
                assert reward==10 and term and not trunc and x[17]==1 and x[19:27].sum()==0
                assert info['previous_action']==1
                with pytest.raises(RuntimeError): env.step(0)
                final,info=env.reset(); assert info['experiment_complete'] and np.array_equal(final,x)
                future.result(timeout=10)
    finally:
        env.close(); server.stop(0).wait()

@pytest.mark.parametrize('problem',['early_terminal','incomplete_windows','reordered_windows','post_terminal','seed_manifest'])
def test_episode_and_window_boundaries(problem):
    b=DispatchCallbackBridge(expected_episode_metadata=[(1,202610160011)])
    start=request()
    if problem=='seed_manifest':
        start.experiment_seed+=1
        with pytest.raises(ProtocolError,match='manifest'): b._register(start)
        return
    t=b._register(start); b.next_callback(timeout=1); b.respond_action(t,0)
    end=request(pb.EPISODE_END,1,0,28800)
    if problem=='early_terminal': end.sim_time_seconds=128
    elif problem=='incomplete_windows':
        del end.closed_windows[-1]; end.reward_components['grade_2h']=3; end.transition_reward=9
    elif problem=='reordered_windows':
        a=pb.WindowSummary(); a.CopyFrom(end.closed_windows[0])
        end.closed_windows[0].CopyFrom(end.closed_windows[1]); end.closed_windows[1].CopyFrom(a)
    if problem!='post_terminal':
        with pytest.raises(ProtocolError): b._register(end)
    else:
        b._register(end)
        r=request(pb.DECISION,2,0,100)
        with pytest.raises(ProtocolError,match='after episode terminal'): b._register(r)

@pytest.mark.parametrize('artifact',['proto/dispatch.proto','dist/DRL-Dispatching-1.2.0.jar','python/generated/dispatch_pb2.py'])
def test_stale_artifacts_rejected(artifact,tmp_path):
    import shutil
    for relative in ['proto/dispatch.proto','proto-src/src/main/proto/dispatch.proto',
                     'dist/protocol_manifest.json','dist/DRL-Dispatching-1.2.0.jar',
                     'proto-src/target/DRL-Dispatching-1.2.0.jar',
                     'python/generated/dispatch_pb2.py','python/generated/dispatch_pb2_grpc.py']:
        destination=tmp_path/relative; destination.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(ROOT/relative,destination)
    changed=tmp_path/artifact; changed.write_bytes(changed.read_bytes()+b'\n')
    with pytest.raises(ValueError): verify_protocol_artifacts(tmp_path)


def test_alp_disabled_or_changed_rejected(tmp_path):
    original=(ROOT/'anylogic/DRL-PPO.alp').read_text()
    p=tmp_path/'changed.alp'
    p.write_text(original.replace('Math.min(now,rlShiftSeconds)/28800.0','Math.min(now,rlShiftSeconds)/480.0'))
    with pytest.raises(ValueError,match='observation functions changed'): validate_alp_contract(p)
