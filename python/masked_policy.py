"""Ordinary SB3 PPO policy with the ALP action mask in observations[19:23].

Only the Categorical logits are masked. PPO losses, optimizer, critic,
rollout collection and GAE remain upstream. Terminal observations are value-only.
"""
from __future__ import annotations

import stable_baselines3
import torch as th
from gymnasium import spaces
from stable_baselines3.common.distributions import CategoricalDistribution
from stable_baselines3.common.policies import ActorCriticPolicy, BasePolicy

from .observation_contract import ACTION_MASK_SLICE, OBSERVATION_SIZE

POLICY_CONTRACT_ID = 'dispatch-masked-categorical-v1'


class DispatchMaskedPolicy(ActorCriticPolicy):
    def __init__(self, observation_space, action_space, lr_schedule, **kwargs):
        if stable_baselines3.__version__ != '2.9.0':
            raise RuntimeError('DispatchMaskedPolicy requires audited SB3 2.9.0')
        if not isinstance(observation_space, spaces.Box) or observation_space.shape != (OBSERVATION_SIZE,):
            raise ValueError('DispatchMaskedPolicy requires the 1519D physical observation')
        if not isinstance(action_space, spaces.Discrete) or action_space.n != 4 or action_space.start != 0:
            raise ValueError('DispatchMaskedPolicy requires Discrete(4), starting at zero')
        super().__init__(observation_space, action_space, lr_schedule, **kwargs)
        if not isinstance(self.action_dist, CategoricalDistribution):
            raise ValueError('Categorical action distribution required')

    @staticmethod
    def _decision_mask(obs):
        if obs.ndim != 2 or obs.shape[1] != OBSERVATION_SIZE:
            raise ValueError('expected batched 1519D observations')
        mask = obs[:, ACTION_MASK_SLICE]
        if not th.all((mask == 0) | (mask == 1)):
            raise ValueError('action mask must contain exactly zero or one')
        if not th.all(obs[:, 17] == 0):
            raise ValueError('terminal observations are critic-only; no action may be requested')
        mask = mask.bool()
        if not th.all(mask.any(dim=1)):
            raise ValueError('nonterminal action request has an all-zero mask')
        return mask

    def _masked_distribution(self, latent_pi, mask):
        logits = self.action_net(latent_pi)
        if not th.isfinite(logits).all():
            raise ValueError('actor produced non-finite logits')
        # -inf gives exactly zero probability and gradient to illegal logits.
        return self.action_dist.proba_distribution(logits.masked_fill(~mask, -th.inf))

    def _latents(self, obs):
        features = self.extract_features(obs)
        if self.share_features_extractor:
            return self.mlp_extractor(features)
        pi_features, vf_features = features
        return (self.mlp_extractor.forward_actor(pi_features),
                self.mlp_extractor.forward_critic(vf_features))

    def forward(self, obs, deterministic=False):
        mask = self._decision_mask(obs)
        latent_pi, latent_vf = self._latents(obs)
        values = self.value_net(latent_vf)
        distribution = self._masked_distribution(latent_pi, mask)
        actions = distribution.get_actions(deterministic=deterministic)
        log_prob = distribution.log_prob(actions)
        return actions.reshape((-1, *self.action_space.shape)), values, log_prob

    def get_distribution(self, obs):
        mask = self._decision_mask(obs)
        features = BasePolicy.extract_features(self, obs, self.pi_features_extractor)
        latent_pi = self.mlp_extractor.forward_actor(features)
        return self._masked_distribution(latent_pi, mask)

    def evaluate_actions(self, obs, actions):
        mask = self._decision_mask(obs)
        actions = actions.reshape(-1)
        if (actions.shape[0] != obs.shape[0] or not th.isfinite(actions).all()
                or not th.all(actions == actions.long())
                or not th.all((actions >= 0) & (actions < 4))):
            raise ValueError('expected one integer action in [0,3] per observation')
        if not th.all(mask.gather(1, actions.long().unsqueeze(1))):
            raise ValueError('cannot evaluate an action masked out by its observation')
        latent_pi, latent_vf = self._latents(obs)
        distribution = self._masked_distribution(latent_pi, mask)
        return self.value_net(latent_vf), distribution.log_prob(actions.long()), distribution.entropy()

    # predict() -> inherited _predict() -> get_distribution(), so inference uses
    # the same mask. predict_values() stays upstream and accepts terminal masks.
