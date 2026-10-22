import json

import numpy as np
import pytest

from python.evaluate import _evaluate_episode, _load_seed_manifest, _summary
from python.compare_heldout import compare
from python.reward_contract import window_summary_to_dict
from test_contracts import windows


class FakeModel:
    def predict(self, observation, deterministic=True):
        assert deterministic
        mask = observation[19:23]
        return np.asarray([int(np.flatnonzero(mask)[0])]), None


class FakeEnv:
    def __init__(self):
        self.steps = 0

    def reset(self):
        observation = np.zeros(1519, dtype=np.float32)
        observation[19] = 1
        return observation, {
            "episode_id": "holdout-1",
            "experiment_run_index": 21,
            "experiment_seed": 202610160031,
            "action_mask": [1, 0, 0, 0],
        }

    def step(self, action):
        assert action == [0, 1][self.steps]
        self.steps += 1
        terminal = self.steps == 2
        observation = np.zeros(1519, dtype=np.float32)
        if not terminal:
            observation[20] = 1
        info = {
            "episode_id": "holdout-1",
            "action_mask": [0, 0, 0, 0] if terminal else [0, 1, 0, 0],
            "reward_components": {
                "delta_wait_vehicle_seconds": 10.0,
                "ore_tons_shift": 16000.0 if terminal else 0.0,
                "shift_grade": 0.27 if terminal else 0.0,
                "waste_tons_shift": 4000.0 if terminal else 0.0,
            },
            "closed_windows": [window_summary_to_dict(w) for w in (windows()[2:] if terminal else windows()[:2])],
        }
        return observation, 1.0, terminal, False, info


def test_load_seed_manifest_rejects_duplicates(tmp_path):
    path = tmp_path / "seeds.json"
    path.write_text(
        json.dumps(
            [
                {"run_index": 21, "experiment_seed": 31},
                {"run_index": 21, "experiment_seed": 32},
            ]
        )
    )
    with pytest.raises(SystemExit, match="run_index values must be unique"):
        _load_seed_manifest(path, 2)


def test_evaluate_episode_collects_metrics_and_mask_counts():
    record = _evaluate_episode(FakeEnv(), FakeModel(), deterministic=True)
    assert record["length"] == 2
    assert record["episode_return"] == 2.0
    assert record["action_counts"] == [1, 1, 0, 0]
    assert record["decision_mask_counts"] == {"1000": 1, "0100": 1}
    assert record["terminal_reward_components"]["ore_tons_shift"] == 16000.0
    assert [w['window_index'] for w in record['closed_windows']] == [0,1,2,3]
    assert record['production_joint_met'] and record['all_windows_compliant']
    assert _summary([record])['production_joint_attainment_rate'] == 1.0
    assert _summary([record])["wait_vehicle_seconds"]["mean"] == 20.0


def test_compare_heldout_pairs_by_seed(tmp_path):
    ppo = tmp_path / "ppo.jsonl"
    ppo.write_text(
        json.dumps(
            {
                "run_index": 21,
                "experiment_seed": 202610160031,
                "episode_return": -2.0,
                "wait_vehicle_seconds": 90.0,
                "terminal_reward_components": {
                    "ore_tons_shift": 1200.0,
                    "shift_grade": 0.27,
                },
            }
        )
        + "\n"
    )
    baseline_dir = tmp_path / "baseline"
    baseline_dir.mkdir()
    (baseline_dir / "policy2_run21_seed202610160031.jsonl").write_text(
        json.dumps(
            {
                "type": "terminal",
                "policy": 2,
                "run_index": 21,
                "experiment_seed": 202610160031,
                "ore_tons_shift": 1000.0,
                "shift_grade": 0.26,
                "wait_vehicle_seconds": 110.0,
            }
        )
        + "\n"
    )
    result = compare(ppo, baseline_dir)
    assert result["metric_summary"]["ore_tons_shift"]["mean_ppo_minus_baseline"] == 200.0
    assert result["metric_summary"]["wait_vehicle_seconds"]["mean_ppo_minus_baseline"] == -20.0


@pytest.mark.parametrize('problem', ['missing', 'duplicate', 'out_of_order', 'ore_balance', 'metal_balance'])
def test_evaluation_rejects_incomplete_or_inconsistent_windows(problem):
    class BrokenEnv(FakeEnv):
        def step(self, action):
            observation, reward, terminal, truncated, info = super().step(action)
            if terminal:
                if problem == 'missing':
                    info['closed_windows'].pop()
                elif problem == 'duplicate':
                    info['closed_windows'][0] = window_summary_to_dict(windows()[1])
                elif problem == 'out_of_order':
                    info['closed_windows'].reverse()
                elif problem == 'ore_balance':
                    info['reward_components']['ore_tons_shift'] += 10
                else:
                    info['reward_components']['shift_grade'] = .28
            return observation, reward, terminal, truncated, info
    with pytest.raises(ValueError, match='window'):
        _evaluate_episode(BrokenEnv(), FakeModel(), deterministic=True)


def test_production_joint_metric_does_not_include_grade():
    class LowGradeEnv(FakeEnv):
        def step(self, action):
            from python.reward_contract import grade_reward
            observation, reward, terminal, truncated, info = super().step(action)
            for w in info['closed_windows']:
                w.update(grade=.25, metal_tons=w['ore_tons']*.25, grade_gap=.02,
                         grade_reward_raw=grade_reward(.02), grade_reward_weighted=grade_reward(.02),
                         violation_lower=True)
            if terminal:
                info['reward_components']['shift_grade'] = .25
            return observation, reward, terminal, truncated, info
    record = _evaluate_episode(LowGradeEnv(), FakeModel(), deterministic=True)
    assert record['production_joint_met']
    assert record['window_compliance_rate'] == 0
    summary = _summary([record])
    assert summary['production_joint_attainment_rate'] == 1
    assert summary['all_windows_compliant_rate'] == 0


@pytest.mark.parametrize('key,value', [('reward_contract_id','dispatch-reward-physical-v4'),
                                      ('reward_configuration_fingerprint','wrong'),
                                      ('reward_configuration',None)])
def test_checkpoint_reward_identity_must_match_frozen_contract(key,value):
    from python.evaluate import _validate_reward_identity
    from python.reward_contract import REWARD_CONTRACT_ID
    from python.reward_config import RewardConfiguration
    cfg = RewardConfiguration()
    payload = dict(reward_contract_id=REWARD_CONTRACT_ID, reward_configuration=cfg.to_dict(),
                   reward_configuration_fingerprint=cfg.fingerprint)
    payload[key] = value
    with pytest.raises(SystemExit):
        _validate_reward_identity(payload, 'checkpoint')


def test_inference_bootstrap_uses_rpc_and_collects_split_windows(monkeypatch,tmp_path):
    """Real bridge and policy, fake AnyLogic client; no learn()/optimizer step."""
    from concurrent.futures import ThreadPoolExecutor
    from python import evaluate
    from python.dispatch_bridge import DispatchCallbackBridge
    from python.dispatch_env import DispatchEnv
    from python.reward_config import RewardConfiguration
    from python.reward_contract import REWARD_CONTRACT_ID
    from python.masked_policy import DispatchMaskedPolicy, POLICY_CONTRACT_ID
    from python.generated import dispatch_pb2 as pb
    from stable_baselines3 import PPO
    from test_runtime_configuration import runtime_request

    cfg = RewardConfiguration()
    training = tmp_path/'fixture_training'
    training.mkdir()
    checkpoint = training/'model.zip'
    model = PPO(DispatchMaskedPolicy, DispatchEnv(DispatchCallbackBridge()), n_steps=2, batch_size=2)
    model.save(checkpoint)
    metadata = dict(status='complete', policy_contract_id=POLICY_CONTRACT_ID,
                    observation_schema_id='dispatch.physical.v3', reward_contract_id=REWARD_CONTRACT_ID,
                    reward_configuration=cfg.to_dict(), reward_configuration_fingerprint=cfg.fingerprint,
                    model_sha256=evaluate._sha256(checkpoint))
    for name in ['run_manifest.json','SUCCESS.json']:
        (training/name).write_text(json.dumps(metadata))
    seed_manifest = tmp_path/'seeds.json'
    seed_manifest.write_text(json.dumps([dict(run_index=1, experiment_seed=202610160011)]))
    output = tmp_path/'evaluation'
    monkeypatch.setattr('sys.argv', ['evaluate','--model',str(checkpoint),'--episodes','1',
                                    '--anylogic-seed-manifest',str(seed_manifest),
                                    '--output-dir',str(output),'--callback-timeout','10'])
    def forbidden(*args, **kwargs):
        raise AssertionError('inference must not audit local ALP or update the policy')
    monkeypatch.setattr('python.alp_audit.validate_alp_contract', forbidden)
    monkeypatch.setattr(PPO,'learn',forbidden)
    monkeypatch.setattr(PPO,'train',forbidden)
    futures = []
    observed_bridges = []
    with ThreadPoolExecutor(max_workers=1) as pool:
        def create_server(bridge,*args,**kwargs):
            assert bridge.runtime_configuration and bridge.reward_config is None
            observed_bridges.append(bridge)
            class Server:
                def start(self):
                    def simulate():
                        start = bridge.submit_callback(runtime_request(cfg), timeout=10)
                        decision = runtime_request(cfg,pb.DECISION,1,start.action,15000)
                        decision.closed_windows.extend(windows()[:2])
                        decision.reward_components['grade_2h'] = 2
                        decision.transition_reward = 2
                        second = bridge.submit_callback(decision, timeout=10)
                        end = runtime_request(cfg,pb.EPISODE_END,2,second.action,28800)
                        end.sim_time_delta_seconds = 13800
                        del end.closed_windows[:2]
                        end.reward_components['grade_2h'] = 2
                        end.transition_reward = 2
                        bridge.submit_callback(end, timeout=10)
                    futures.append(pool.submit(simulate))
                def stop(self,grace=0): return self
                def wait(self): pass
            return Server()
        monkeypatch.setattr(evaluate,'create_server',create_server)
        original_predict = DispatchMaskedPolicy.predict
        def checked_predict(self,*args,**kwargs):
            manifest = json.loads((output/'evaluation_manifest.json').read_text())
            assert manifest['runtime_reward_configuration_received']
            assert observed_bridges[0].reward_config == cfg
            return original_predict(self,*args,**kwargs)
        monkeypatch.setattr(DispatchMaskedPolicy,'predict',checked_predict)
        evaluate.main()
        for future in futures:
            future.result(timeout=10)
    manifest = json.loads((output/'evaluation_manifest.json').read_text())
    record = json.loads((output/'evaluation_episodes.jsonl').read_text())
    summary = json.loads((output/'evaluation_summary.json').read_text())
    assert manifest['configuration_source'] == 'anylogic_rpc'
    assert manifest['alp_contract'] is None and not manifest['local_alp_audit_requested']
    assert manifest['reward_configuration_fingerprint'] == cfg.fingerprint
    assert len(record['closed_windows']) == 4 and record['episode_return'] == 4
    assert 'config.w_wait' not in record['reward_component_sums']
    assert summary['window_compliance_rate'] == summary['production_joint_attainment_rate'] == 1
    assert (output/'SUCCESS.json').exists()
