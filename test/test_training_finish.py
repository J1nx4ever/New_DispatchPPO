"""Synthetic regression checks only: no AnyLogic and no real PPO training run."""
import gymnasium as gym
import numpy as np
import pytest
import torch
from gymnasium import spaces
from stable_baselines3.common.callbacks import BaseCallback
from stable_baselines3.common.logger import configure
from python.episode_budget_ppo import EpisodeBudgetPPO
from python.train import TrainingProgressCallback
from python.rollout_debug import RolloutDebug
from python.stage_statistics import StageStatisticsCallback
import json

class SerialEpisodes(gym.Env):
    def __init__(self,lengths,truncated=False):
        self.observation_space=spaces.Box(-1,1,(1519,),dtype=np.float32)
        self.action_space=spaces.Discrete(4)
        self.lengths=lengths; self.truncated=truncated
        self.episode=-1; self.tick=0; self.reset_steps=[]; self.total=0
    def reset(self,*,seed=None,options=None):
        super().reset(seed=seed)
        self.reset_steps.append(self.total)
        self.episode+=1; self.tick=0
        return np.zeros(1519,dtype=np.float32),{}
    def step(self,action):
        assert self.episode < len(self.lengths), 'collector stepped after budget end'
        self.tick+=1; self.total+=1
        done=self.tick==self.lengths[self.episode]
        x=np.full(1519,self.tick/2000,dtype=np.float32)
        return x,1.0,done and not self.truncated,done and self.truncated,{'episode_id':str(self.episode)}

class CheckGAE(BaseCallback):
    def __init__(self):
        super().__init__(); self.rollouts=[]
    def _on_step(self): return True
    def _on_rollout_end(self):
        b=self.locals['rollout_buffer']
        expected=np.zeros_like(b.advantages)
        carry=0.
        last=self.locals['values'].detach().cpu().numpy().flatten()
        dones=self.locals['dones']
        for i in reversed(range(b.buffer_size)):
            nonterminal=1.-(dones if i==b.buffer_size-1 else b.episode_starts[i+1])
            next_value=last if i==b.buffer_size-1 else b.values[i+1]
            delta=b.rewards[i]+b.gamma*next_value*nonterminal-b.values[i]
            carry=delta+b.gamma*b.gae_lambda*nonterminal*carry
            expected[i]=carry
        np.testing.assert_allclose(b.advantages,expected,rtol=1e-5,atol=1e-5)
        self.rollouts.append(dict(length=b.buffer_size,starts=b.episode_starts.copy(),
                                  rewards=b.rewards.copy(),last_value=last.copy(),dones=dones.copy()))

@pytest.mark.parametrize('lengths',[[140],[5,6],[128],[129],[260]])
def test_rollout_tail_bootstrap_episodes_and_save(lengths,tmp_path):
    torch.set_num_threads(1)
    env=SerialEpisodes(lengths)
    model=EpisodeBudgetPPO('MlpPolicy',env,n_steps=128,batch_size=32,n_epochs=2,
        gamma=.995,gae_lambda=.95,seed=7,device='cpu',policy_kwargs=dict(net_arch=dict(pi=[8],vf=[8])))
    model.set_logger(configure(str(tmp_path),['csv']))
    initial={k:v.clone() for k,v in model.policy.state_dict().items()}
    progress=TrainingProgressCallback(len(lengths),None if lengths==[5,6] else tmp_path/'transitions.jsonl',ppo_seed=7)
    check=CheckGAE()
    debug=None
    if lengths==[140]:
        debug=RolloutDebug(tmp_path/'rollout_audit',source_kind='synthetic_test',capture_rollouts=True)
        model._rollout_debug=debug
    model.learn(total_timesteps=10000,callback=[StageStatisticsCallback(tmp_path),progress,check])
    if debug is not None:
        debug.close(status='complete')
        snapshots=sorted((tmp_path/'rollout_audit').glob('rollout_*.json'))
        assert len(snapshots)==2
        assert [json.loads(p.read_text())['valid_length'] for p in snapshots]==[128,12]
        assert all(json.loads(p.read_text())['update_completed'] for p in snapshots)
    assert len((tmp_path/'stage_episodes.jsonl').read_text().splitlines())==len(lengths)
    audit=model.finish_audit()
    count=sum(lengths)
    assert audit['collected_transitions']==audit['unique_updated_transitions']==count
    assert audit['discarded_transitions']==0
    assert audit['last_terminal_transition_updated'] and audit['final_logger_flushed']
    assert [r['length'] for r in check.rollouts]==[128]*(count//128)+([count%128] if count%128 else [])
    assert env.reset_steps==[0]+list(np.cumsum(lengths))
    assert progress.completed_episodes==len(lengths)
    assert any(not torch.equal(v,initial[k]) for k,v in model.policy.state_dict().items())
    if lengths==[5,6]:
        assert not (tmp_path/'transitions.jsonl').exists()
        assert np.flatnonzero(check.rollouts[0]['starts'][:,0]).tolist()==[0,5]
    if lengths==[140]:
        assert not check.rollouts[0]['dones'][0] and check.rollouts[1]['dones'][0]
        assert env.reset_steps==[0,140]  # No reset at rollout boundary 128.
    assert check.rollouts[-1]['rewards'][-1,0]==1 # Real terminal never gets timeout bootstrap.
    model.save(tmp_path/'synthetic')
    assert model.finish_audit()['events'][-3:]==['ppo_update_completed','final_logger_flushed','model_saved']
    assert (tmp_path/'progress.csv').is_file()
    assert 'train/value_loss' in (tmp_path/'progress.csv').read_text()
    loaded=EpisodeBudgetPPO.load(tmp_path/'synthetic',device='cpu')
    assert all(torch.equal(v,loaded.policy.state_dict()[k]) for k,v in model.policy.state_dict().items())
    assert not loaded._learn_started
    with pytest.raises(RuntimeError,match='one learn'): model.learn(total_timesteps=1)


def test_time_limit_bootstrap_boundary(tmp_path):
    torch.set_num_threads(1)
    env=SerialEpisodes([3],truncated=True)
    model=EpisodeBudgetPPO('MlpPolicy',env,n_steps=128,batch_size=32,n_epochs=1,
                         gamma=.9,device='cpu',policy_kwargs=dict(net_arch=dict(pi=[8],vf=[8])))
    # Constant critic makes timeout bootstrap independent of initialization.
    with torch.no_grad():
        model.policy.value_net.weight.zero_(); model.policy.value_net.bias.fill_(2)
    model.set_logger(configure(str(tmp_path),['csv']))
    check=CheckGAE(); progress=TrainingProgressCallback(1,tmp_path/'transitions.jsonl',ppo_seed=1)
    model.learn(total_timesteps=100,callback=[progress,check])
    assert check.rollouts[0]['rewards'][-1,0]==pytest.approx(1+.9*2)
    assert model.finish_audit()['discarded_transitions']==0
