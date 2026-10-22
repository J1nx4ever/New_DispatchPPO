"""Mask probability/gradient checks and real PPO updates on synthetic episodes."""
import hashlib
import json
import sys
from pathlib import Path
import gymnasium as gym
from gymnasium import spaces
import numpy as np
import pytest
import torch as th
from stable_baselines3.common.policies import ActorCriticPolicy
from stable_baselines3.common.callbacks import BaseCallback
from stable_baselines3.common.logger import configure
from python.masked_policy import DispatchMaskedPolicy, POLICY_CONTRACT_ID
from python.observation_contract import OBSERVATION_LOW, OBSERVATION_HIGH
from python.episode_budget_ppo import EpisodeBudgetPPO
from python.train import TrainingProgressCallback, _validate_resume_contract
from python.reward_contract import REWARD_CONTRACT_ID


def observation_space():
    return spaces.Box(np.asarray(OBSERVATION_LOW,dtype=np.float32),
                      np.asarray(OBSERVATION_HIGH,dtype=np.float32),dtype=np.float32)


def observations(masks):
    obs=th.zeros(len(masks),1519)
    obs[:,19:23]=th.tensor(masks,dtype=th.float32)
    return obs


@pytest.fixture
def policy():
    th.set_num_threads(1)
    th.manual_seed(7)
    return DispatchMaskedPolicy(observation_space(),spaces.Discrete(4),lambda _:3e-4,
                                net_arch=dict(pi=[8],vf=[8]))


@pytest.mark.parametrize('shared',[True,False])
def test_sampling_predict_and_update_probabilities_agree(shared):
    th.set_num_threads(1)
    p=DispatchMaskedPolicy(observation_space(),spaces.Discrete(4),lambda _:3e-4,
                           share_features_extractor=shared,net_arch=dict(pi=[8],vf=[8]))
    masks=[[1,0,1,0],[0,1,0,0],[0,0,0,1],[1,1,1,1]]*64
    obs=observations(masks)
    # Force huge invalid preferences; masking must dominate even deterministic inference.
    with th.no_grad(): p.action_net.bias.copy_(th.tensor([100.,200.,300.,400.]))
    actions,values,old_log=p(obs)
    mask=obs[:,19:23].bool()
    assert th.all(mask.gather(1,actions[:,None]))
    probs=p.get_distribution(obs).distribution.probs.clone()
    assert th.all(probs[~mask]==0)
    th.testing.assert_close(probs.sum(1),th.ones(len(obs)))
    expected=th.softmax(p.action_net(p._latents(obs)[0]).masked_fill(~mask,-th.inf),1)
    th.testing.assert_close(probs,expected)
    values2,new_log,entropy=p.evaluate_actions(obs,actions)
    th.testing.assert_close(values,values2)
    th.testing.assert_close(old_log,new_log)
    th.testing.assert_close(th.exp(new_log-old_log),th.ones(len(obs)))
    assert th.isfinite(entropy).all() and th.isfinite(new_log).all()
    th.testing.assert_close(entropy[1::4],th.zeros(64))
    for deterministic in [False,True]:
        predicted,_=p.predict(obs.numpy(),deterministic=deterministic)
        assert th.all(mask.gather(1,th.tensor(predicted)[:,None]))
    single,_=p.predict(obs[1].numpy(),deterministic=True)
    assert int(single)==1


def test_masked_logits_have_zero_gradient(policy):
    obs=observations([[1,0,1,0],[0,1,1,0]])
    captured=[]
    def retain(module,args,output):
        output.retain_grad();captured.append(output)
    hook=policy.action_net.register_forward_hook(retain)
    try:
        _,logp,entropy=policy.evaluate_actions(obs,th.tensor([0,1]))
        (-logp.mean()-.01*entropy.mean()).backward()
    finally: hook.remove()
    gradient=captured[0].grad
    assert th.all(gradient[~obs[:,19:23].bool()]==0)
    assert th.any(gradient[obs[:,19:23].bool()]!=0)
    assert all(th.isfinite(p.grad).all() for p in policy.parameters() if p.grad is not None)


def test_all_legal_matches_original_actor_and_critic(policy):
    original=ActorCriticPolicy(observation_space(),spaces.Discrete(4),lambda _:3e-4,
                               net_arch=dict(pi=[8],vf=[8]))
    original.load_state_dict(policy.state_dict())
    obs=observations([[1,1,1,1]]*3)
    a,v,l=policy(obs,deterministic=True)
    a2,v2,l2=original(obs,deterministic=True)
    th.testing.assert_close(a,a2);th.testing.assert_close(v,v2);th.testing.assert_close(l,l2)
    _,logp,entropy=policy.evaluate_actions(obs,a)
    _,logp2,entropy2=original.evaluate_actions(obs,a)
    th.testing.assert_close(logp,logp2);th.testing.assert_close(entropy,entropy2)


@pytest.mark.parametrize('terminal',[False,True])
def test_zero_mask_actor_rejected_critic_works(policy,terminal):
    obs=observations([[0,0,0,0]]);obs[:,17]=terminal
    assert th.isfinite(policy.predict_values(obs)).all()
    with pytest.raises(ValueError): policy(obs)
    with pytest.raises(ValueError): policy.get_distribution(obs)
    with pytest.raises(ValueError): policy.evaluate_actions(obs,th.tensor([0]))
    with pytest.raises(ValueError): policy.predict(obs.numpy())


@pytest.mark.parametrize('mask',[[1,.5,0,0],[1,float('nan'),0,0],[1,float('inf'),0,0]])
def test_corrupt_mask_rejected(policy,mask):
    with pytest.raises(ValueError,match='zero or one'): policy(observations([mask]))


@pytest.mark.parametrize('action',[1,4,-1,2.5,float('nan')])
def test_invalid_stored_actions_rejected(policy,action):
    with pytest.raises(ValueError): policy.evaluate_actions(observations([[1,0,1,0]]),th.tensor([action]))


def test_mixed_terminal_batch_and_nonfinite_logits_rejected(policy):
    obs=observations([[1,0,0,0],[0,0,0,0]]);obs[1,17]=1
    assert th.isfinite(policy.predict_values(obs)).all()
    with pytest.raises(ValueError,match='critic-only'): policy(obs)
    with th.no_grad(): policy.action_net.bias[1]=float('nan')
    with pytest.raises(ValueError,match='logits'): policy(observations([[1,0,0,0]]))


class ChangingMasks(gym.Env):
    def __init__(self,lengths):
        self.observation_space=observation_space();self.action_space=spaces.Discrete(4)
        self.lengths=lengths;self.episode=-1;self.tick=0;self.total=0;self.resets=[]
    def obs(self,terminal=False):
        x=np.zeros(1519,dtype=np.float32);x[17]=terminal
        if not terminal:
            masks=[[1,1,0,0],[0,1,0,0],[0,0,1,1],[0,0,0,1]]
            x[19:23]=masks[self.tick%4];x[27]=1
        return x
    def reset(self,*,seed=None,options=None):
        super().reset(seed=seed)
        self.episode+=1;self.tick=0;self.resets.append(self.total)
        return self.obs(terminal=self.episode>=len(self.lengths)),{}
    def step(self,action):
        assert self.episode<len(self.lengths)
        assert self.obs()[19+int(action)]==1, 'policy executed an illegal action'
        self.tick+=1;self.total+=1
        done=self.tick==self.lengths[self.episode]
        return self.obs(terminal=done),float(action==1),done,False,{}


class CheckOldProbabilities(BaseCallback):
    def __init__(self):super().__init__();self.lengths=[]
    def _on_step(self):return True
    def _on_rollout_end(self):
        b=self.locals['rollout_buffer'];self.lengths.append(b.buffer_size)
        x=th.as_tensor(b.observations[:,0],device=self.model.device)
        a=th.as_tensor(b.actions[:,0,0],device=self.model.device).long()
        with th.no_grad(): _,logp,entropy=self.model.policy.evaluate_actions(x,a)
        np.testing.assert_allclose(logp.cpu().numpy(),b.log_probs[:,0],rtol=1e-5,atol=1e-5)
        assert th.isfinite(entropy).all()


@pytest.mark.parametrize('lengths',[[140],[5,6],[129]])
def test_masked_policy_with_untouched_collector_and_checkpoint(lengths,tmp_path):
    th.set_num_threads(1)
    env=ChangingMasks(lengths)
    model=EpisodeBudgetPPO(DispatchMaskedPolicy,env,n_steps=128,batch_size=32,n_epochs=2,
        seed=7,device='cpu',policy_kwargs=dict(net_arch=dict(pi=[8],vf=[8])))
    model.set_logger(configure(str(tmp_path),['csv']))
    actor_before=model.policy.action_net.weight.detach().clone()
    critic_before=model.policy.value_net.weight.detach().clone()
    callback=CheckOldProbabilities()
    model.learn(total_timesteps=10000,callback=[TrainingProgressCallback(len(lengths),None,ppo_seed=7),callback])
    audit=model.finish_audit();n=sum(lengths)
    assert audit['collected_transitions']==audit['unique_updated_transitions']==n
    assert audit['discarded_transitions']==0 and audit['last_terminal_transition_updated']
    assert callback.lengths==([128]*(n//128)+([n%128] if n%128 else []))
    assert env.resets==[0]+list(np.cumsum(lengths))
    assert not th.equal(actor_before,model.policy.action_net.weight)
    assert not th.equal(critic_before,model.policy.value_net.weight)
    assert not (tmp_path/'transitions.jsonl').exists()
    model.save(tmp_path/'masked')
    assert model.finish_audit()['events'][-3:]==['ppo_update_completed','final_logger_flushed','model_saved']
    loaded=EpisodeBudgetPPO.load(tmp_path/'masked',device='cpu')
    assert type(loaded.policy) is DispatchMaskedPolicy
    obs=observations([[1,0,1,0],[0,1,0,0]])
    with th.no_grad():
        p=model.policy.get_distribution(obs).distribution.probs.clone()
        q=loaded.policy.get_distribution(obs).distribution.probs.clone()
    th.testing.assert_close(p,q,rtol=0,atol=0)
    assert all(th.equal(v,loaded.policy.state_dict()[k]) for k,v in model.policy.state_dict().items())


def test_unmasked_checkpoint_metadata_rejected_before_loading(tmp_path):
    checkpoint=tmp_path/'old.zip';checkpoint.write_bytes(b'not a model: must never load')
    payload=dict(reward_contract_id=REWARD_CONTRACT_ID,
                 observation_schema_id='dispatch.physical.v3',
                 model_sha256=hashlib.sha256(checkpoint.read_bytes()).hexdigest())
    for name in ['run_manifest.json','SUCCESS.json']:
        (tmp_path/name).write_text(json.dumps(payload))
    with pytest.raises(SystemExit,match='masked policy'): _validate_resume_contract(checkpoint)
    payload['policy_contract_id']=POLICY_CONTRACT_ID
    for name in ['run_manifest.json','SUCCESS.json']:(tmp_path/name).write_text(json.dumps(payload))
    _validate_resume_contract(checkpoint) # This checks metadata only, not ZIP loading.


def augmented_observation_space():
    from python.dispatch_bridge import DispatchCallbackBridge
    from python.dispatch_env import DispatchEnv
    from python.observation_projection_wrapper import FIFOObservationWrapper
    return FIFOObservationWrapper(DispatchEnv(DispatchCallbackBridge())).observation_space


@pytest.mark.parametrize('dim',[1524,1526])
def test_policy_rejects_unexpected_observation_dimensions(dim):
    space=spaces.Box(np.zeros(dim,dtype=np.float32),np.ones(dim,dtype=np.float32))
    with pytest.raises(ValueError,match='1519D physical'):
        DispatchMaskedPolicy(space,spaces.Discrete(4),lambda _:3e-4,net_arch=dict(pi=[8],vf=[8]))


def test_policy_masks_augmented_observation_at_raw_slice():
    th.set_num_threads(1)
    space=augmented_observation_space()
    p=DispatchMaskedPolicy(space,spaces.Discrete(4),lambda _:3e-4,net_arch=dict(pi=[8],vf=[8]))
    o=th.zeros(2,space.shape[0]);o[:,19:23]=th.tensor([[1.,0.,1.,0.],[0.,1.,0.,0.]])
    with th.no_grad():p.action_net.bias.copy_(th.tensor([100.,200.,300.,400.]))
    actions,values,logp=p(o)
    mask=o[:,19:23].bool()
    assert th.all(mask.gather(1,actions[:,None]))
    probs=p.get_distribution(o).distribution.probs.clone()
    assert th.all(probs[~mask]==0)
    th.testing.assert_close(probs.sum(1),th.ones(2))
    p.evaluate_actions(o,actions)
    o[0,1524]=float('nan')
    with pytest.raises(ValueError,match='finite'):p.get_distribution(o)


def test_resume_rejects_agent_observation_mode_mismatch(tmp_path):
    checkpoint=tmp_path/'model.zip';checkpoint.write_bytes(b'augmented model fixture')
    payload=dict(reward_contract_id=REWARD_CONTRACT_ID,policy_contract_id=POLICY_CONTRACT_ID,
                 observation_schema_id='dispatch.physical.v3',agent_observation_mode='p0-smoke',
                 agent_observation_dimension=1525,
                 model_sha256=hashlib.sha256(checkpoint.read_bytes()).hexdigest())
    for name in ['run_manifest.json','SUCCESS.json']:(tmp_path/name).write_text(json.dumps(payload))
    _validate_resume_contract(checkpoint,None,'p0-smoke')
    with pytest.raises(SystemExit,match='agent observation mode'):
        _validate_resume_contract(checkpoint,None,'f0')


def test_p0_smoke_mode_cannot_resume(tmp_path,monkeypatch):
    from python.train import main
    checkpoint=tmp_path/'model.zip';checkpoint.write_bytes(b'x')
    seeds=tmp_path/'seeds.json';seeds.write_text(json.dumps([dict(run_index=1,experiment_seed=11)]))
    monkeypatch.setattr(sys,'argv',['train','--episodes','1','--anylogic-seed-manifest',str(seeds),
                                    '--resume-model',str(checkpoint),'--obs-mode','p0-smoke'])
    with pytest.raises(SystemExit,match='p0-smoke cannot resume'):
        main()


def test_masked_inference_smoke_rule_never_updates_optimizer(policy):
    from python.smoke_dispatch import run_episode
    class Callbacks(ChangingMasks):
        def info(self,x):return dict(action_mask=x[19:23].astype(bool).tolist(),request_id=str(self.total),episode_id='synthetic')
        def reset(self,**kwargs):
            x,_=super().reset(**kwargs);return x,self.info(x)
        def step(self,action):
            x,r,t,tr,_=super().step(action);return x,r,t,tr,self.info(x)
    env=Callbacks([9]);before={k:v.clone() for k,v in policy.state_dict().items()}
    calls=[]
    def select(obs,info):
        calls.append(info['request_id'])
        return int(policy.predict(obs,deterministic=False)[0])
    def disallow_update(*args):raise AssertionError('inference smoke must not optimize')
    hook=policy.optimizer.register_step_post_hook(disallow_update)
    try: result=run_episode(env,action_selector=select)
    finally: hook.remove()
    assert result['terminated'] and result['transitions']==9 and len(calls)==9
    assert sum(result['action_counts'])==9
    assert result['decision_mask_counts']=={'1100':3,'0100':2,'0011':2,'0001':2}
    assert all(th.equal(v,policy.state_dict()[k]) for k,v in before.items())


def test_smoke_rejects_selector_instead_of_replacing_action():
    from python.smoke_dispatch import run_episode
    class Callbacks:
        def reset(self):return np.zeros(1519,dtype=np.float32),dict(action_mask=[1,0,0,0],request_id='a')
        def step(self,action):raise AssertionError('must reject before executing action')
    with pytest.raises(ValueError,match='illegal dispatch'):
        run_episode(Callbacks(),action_selector=lambda obs,info:1)


def test_masked_policy_timeout_bootstrap_uses_terminal_critic(tmp_path):
    class Timeout(ChangingMasks):
        def step(self,action):
            x,r,done,_,info=super().step(action)
            return x,r,False,done,info
    class CheckTimeout(CheckOldProbabilities):
        def _on_rollout_end(self):
            super()._on_rollout_end()
            # Last action at tick2 must be 2 or3, so reward is0; timeout adds gamma*2.
            assert self.locals['rollout_buffer'].rewards[-1,0]==pytest.approx(.9*2)
    model=EpisodeBudgetPPO(DispatchMaskedPolicy,Timeout([3]),n_steps=128,batch_size=32,
        n_epochs=1,gamma=.9,device='cpu',policy_kwargs=dict(net_arch=dict(pi=[8],vf=[8])))
    with th.no_grad():
        model.policy.value_net.weight.zero_();model.policy.value_net.bias.fill_(2)
    model.set_logger(configure(str(tmp_path),['csv']))
    model.learn(total_timesteps=100,callback=[TrainingProgressCallback(1,None,ppo_seed=7),CheckTimeout()])
    assert model.finish_audit()['discarded_transitions']==0
