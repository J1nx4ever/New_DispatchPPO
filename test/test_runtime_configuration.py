from concurrent.futures import ThreadPoolExecutor
import json
import pytest
from python.reward_config import RewardConfiguration, configuration_from_components, configuration_to_components
from python.dispatch_bridge import DispatchCallbackBridge, ProtocolError
from python.generated import dispatch_pb2 as pb
from test_contracts import request


def runtime_request(cfg, kind=pb.EPISODE_START, seq=0, action=-1, time=0):
    r=request(kind,seq,action,time)
    r.reward_components.update(configuration_to_components(cfg))
    if kind==pb.EPISODE_END:
        # Base request reports waste target=4000, fully achieved; tailor actual diagnostics.
        r.reward_components.update(waste_tons_shift=cfg.waste_target_tons,waste_target_tons=cfg.waste_target_tons,
                                  waste_fraction_raw=1 if cfg.waste_target_tons else 0,waste_shortfall=0,waste=0)
    return r


def test_runtime_handshake_does_not_consume_first_callback():
    cfg=RewardConfiguration()
    b=DispatchCallbackBridge(runtime_configuration=True)
    assert b.reward_config is None
    r=runtime_request(cfg);ticket=b._register(r)
    assert b.wait_for_configuration(timeout=0)==cfg
    assert b.next_callback(timeout=0) is ticket
    assert not ticket.response_ready.is_set()
    b.respond_action(ticket,1)
    end=runtime_request(cfg,pb.EPISODE_END,1,1,28800)
    b._register(end)
    b.close()


@pytest.mark.parametrize('field',['grade_action_enabled','config.waste_shortfall_weight','config.w_wait'])
def test_missing_metadata_not_guessed(field):
    b=DispatchCallbackBridge(runtime_configuration=True);r=runtime_request(RewardConfiguration())
    del r.reward_components[field]
    with pytest.raises(ProtocolError,match='configuration missing'):b._register(r)
    assert b.reward_config is None
    with pytest.raises(TimeoutError):b.wait_for_configuration(timeout=0)


def test_invalid_start_cannot_lock_configuration():
    b=DispatchCallbackBridge(runtime_configuration=True);r=runtime_request(RewardConfiguration())
    r.obs.schema_id='wrong'
    with pytest.raises(ProtocolError):b._register(r)
    assert b.reward_config is None
    valid=runtime_request(RewardConfiguration(False));b._register(valid)
    assert b.wait_for_configuration(0)==RewardConfiguration(False)
    b.close()


@pytest.mark.parametrize('key,value',[('config.waste_shortfall_weight',2),('config.target_waste_tons_shift',2000),('grade_action_enabled',1)])
def test_parameters_cannot_change_during_run(key,value):
    b=DispatchCallbackBridge(runtime_configuration=True);cfg=RewardConfiguration(False)
    start=b._register(runtime_request(cfg));b.next_callback(timeout=0);b.respond_action(start,0)
    r=runtime_request(cfg,pb.DECISION,1,0,1);r.reward_components[key]=value
    with pytest.raises(ProtocolError,match='frozen|runtime parameter'):b._register(r)
    b.close()


def test_unknown_formula_constant_rejected_not_silently_assumed():
    r=runtime_request(RewardConfiguration(False));r.reward_components['config.w_wait']=5
    with pytest.raises(ValueError,match='unsupported V1.0'):configuration_from_components(r.reward_components)


def test_close_releases_rpc_waiting_for_action():
    b=DispatchCallbackBridge(runtime_configuration=True)
    with ThreadPoolExecutor(max_workers=1) as pool:
        future=pool.submit(b.submit_callback,runtime_request(RewardConfiguration(False)),10)
        b.next_callback(timeout=3)
        b.close()
        with pytest.raises(RuntimeError,match='closed'):future.result(timeout=3)


def test_full_training_bootstrap_without_local_alp(monkeypatch,tmp_path):
    from python import train
    cfg=RewardConfiguration()
    seeds=tmp_path/'seeds.json';seeds.write_text(json.dumps([dict(run_index=1,experiment_seed=202610160011)]))
    output=tmp_path/'run'
    monkeypatch.setattr('sys.argv',['train','--episodes','1','--anylogic-seed-manifest',str(seeds),
                                   '--output-dir',str(output),'--callback-timeout','10'])
    def forbidden(*args):raise AssertionError('runtime training must never read or audit ALP')
    monkeypatch.setattr(train,'validate_alp_contract',forbidden)
    # Real bridge rendezvous plus real masked PPO; test client replaces AnyLogic GUI only.
    with ThreadPoolExecutor(max_workers=1) as pool:
        futures=[]
        def create_server(bridge,**kwargs):
            class Server:
                def start(self):
                    assert not output.exists()  # No variant or model is created before handshake.
                    def simulate():
                        first=bridge.submit_callback(runtime_request(cfg),timeout=10)
                        decision=runtime_request(cfg,pb.DECISION,1,first.action,100)
                        second=bridge.submit_callback(decision,timeout=10)
                        end=runtime_request(cfg,pb.EPISODE_END,2,second.action,28800)
                        end.sim_time_delta_seconds=28700
                        ack=bridge.submit_callback(end,timeout=10)
                        assert not ack.has_action
                    futures.append(pool.submit(simulate))
                def stop(self,grace=0):return self
                def wait(self):pass
            return Server()
        monkeypatch.setattr(train,'create_server',create_server)
        train.main()
        for f in futures:f.result(timeout=10)
    manifest=json.loads((output/'run_manifest.json').read_text())
    success=json.loads((output/'SUCCESS.json').read_text())
    assert manifest['configuration_source']=='anylogic_rpc' and manifest['alp_sha256'] is None
    assert manifest['reward_configuration']==cfg.to_dict() and success['reward_configuration']==cfg.to_dict()
    assert success['completed_episodes']==1
    assert success['training_finish']['collected_transitions']==2
    assert success['training_finish']['unique_updated_transitions']==2
    assert success['training_finish']['last_rollout_valid_length']==2
    assert not (output/'transitions.jsonl').exists() and not (output/'rollout_audit').exists()


def test_numeric_config_identity_is_canonical():
    assert RewardConfiguration(False,4,4000).fingerprint == RewardConfiguration(False,4.0,4000.0).fingerprint
