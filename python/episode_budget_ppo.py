"""Episode-budget PPO finish for SB3 2.9.0 (single serial environment).

Collector below follows OnPolicyAlgorithm.collect_rollouts from installed SB3
2.9.0, with stop-after-add and exact-size final-buffer changes. PPO.train and
OnPolicyAlgorithm.learn remain upstream, including singleton normalization guard,
terminal/time-limit bootstrap, schedules and full-rollout minibatch behavior.
Each instance supports one learn() call; load a ZIP into a fresh instance to
continue. Session flags/counters reset in _setup_model(), after ZIP metadata is
restored and before SB3 restores the policy and optimizer state dictionaries.
Upgrades require re-auditing this collector and rerunning test_training_finish.
"""
from __future__ import annotations

import numpy as np
import torch as th
import stable_baselines3
from gymnasium import spaces
from stable_baselines3 import PPO
from stable_baselines3.common.buffers import RolloutBuffer
from stable_baselines3.common.callbacks import BaseCallback
from stable_baselines3.common.utils import obs_as_tensor
from stable_baselines3.common.vec_env import VecEnv


class AuditedRolloutBuffer(RolloutBuffer):
    """Keep current minibatch indices for counting actual optimizer participation."""

    def _get_samples(self, batch_inds, env=None):
        self.current_batch_indices = batch_inds
        return super()._get_samples(batch_inds, env)


class EpisodeBudgetPPO(PPO):
    def _setup_model(self):
        if stable_baselines3.__version__ != "2.9.0":
            raise RuntimeError("EpisodeBudgetPPO requires SB3 2.9.0")
        if self.rollout_buffer_class not in (None, RolloutBuffer, AuditedRolloutBuffer):
            raise RuntimeError("Unsupported custom rollout buffer")
        self.rollout_buffer_class = AuditedRolloutBuffer
        super()._setup_model()
        self._episode_budget_reached = False
        self._collected_transitions = 0
        self._updated_transitions = 0
        self._last_terminal_id = None
        self._last_terminal_updated = False
        self._last_rollout_length = 0
        self._finish_events = []
        self._learn_started = False
        self._final_logger_flushed = False
        self._rollout_debug = None

    def _excluded_save_params(self):
        return super()._excluded_save_params() + ["_rollout_debug"]

    def learn(
        self, total_timesteps, callback=None, log_interval=1,
        tb_log_name="PPO", reset_num_timesteps=True, progress_bar=False,
    ):
        # Reject before _setup_learn() can reset/step the finite environment.
        if self._learn_started:
            raise RuntimeError(
                "EpisodeBudgetPPO supports one learn() call per instance; "
                "load a checkpoint into a fresh instance to continue training"
            )
        self._learn_started = True
        return super().learn(
            total_timesteps=total_timesteps, callback=callback,
            log_interval=log_interval, tb_log_name=tb_log_name,
            reset_num_timesteps=reset_num_timesteps, progress_bar=progress_bar,
        )

    def request_episode_budget_stop(self):
        """Called by progress callback on the final terminal; never abort on_step."""
        self._episode_budget_reached = True

    def train(self):
        buffer = self.rollout_buffer
        debug = self._rollout_debug
        if debug is not None:
            debug.before_update(self)
        used = set()

        def record_update(optimizer, args, kwargs):
            used.update(int(i) for i in buffer.current_batch_indices)

        # Count only minibatches whose optimizer step completed (not repeated
        # epochs, or minibatches rejected by target_kl).
        hook = self.policy.optimizer.register_step_post_hook(record_update)
        try:
            super().train()
        finally:
            hook.remove()
        if debug is not None:
            debug.after_update(self)
        self._updated_transitions += len(used)
        if self._last_terminal_id is not None:
            local_id = self._last_terminal_id - buffer.transition_offset
            self._last_terminal_updated = local_id in used
        self._finish_events.append("ppo_update_completed")
        if self._episode_budget_reached:
            # Upstream learn() dumps BEFORE train(). With no next rollout, its
            # last train/* values would remain in memory. SB3's CSV and TB
            # writers flush on dump(); do this only for the final update.
            self.logger.dump(step=self.num_timesteps)
            self._final_logger_flushed = True
            self._finish_events.append("final_logger_flushed")

    def finish_audit(self):
        return {
            "collected_transitions": self._collected_transitions,
            "unique_updated_transitions": self._updated_transitions,
            "discarded_transitions": self._collected_transitions - self._updated_transitions,
            "last_rollout_valid_length": self._last_rollout_length,
            "last_terminal_transition_updated": self._last_terminal_updated,
            "episode_budget_reached": self._episode_budget_reached,
            "final_logger_flushed": self._final_logger_flushed,
            "events": list(self._finish_events),
            "stable_baselines3_version": stable_baselines3.__version__,
        }

    def save(self, path, exclude=None, include=None):
        if self._episode_budget_reached and (
            not self._last_terminal_updated
            or self._updated_transitions != self._collected_transitions
            or not self._final_logger_flushed
        ):
            raise RuntimeError("Refusing final save: incomplete transition update or final logger flush")
        super().save(path, exclude=exclude, include=include)
        self._finish_events.append("model_saved")

    def collect_rollouts(
        self,
        env: VecEnv,
        callback: BaseCallback,
        rollout_buffer: RolloutBuffer,
        n_rollout_steps: int,
    ) -> bool:
        """
        Collect experiences using the current policy and fill a ``RolloutBuffer``.
        The term rollout here refers to the model-free notion and should not
        be used with the concept of rollout used in model-based RL or planning.

        :param env: The training environment
        :param callback: Callback that will be called at each step
            (and at the beginning and end of the rollout)
        :param rollout_buffer: Buffer to fill with rollouts
        :param n_rollout_steps: Number of experiences to collect per environment
        :return: True for a complete or valid final rollout ready to update;
            False on the next call after the budget stop, or callback abort.
        """
        if stable_baselines3.__version__ != "2.9.0":
            raise RuntimeError("EpisodeBudgetPPO requires SB3 2.9.0; re-audit collector on upgrade")
        if env.num_envs != 1:
            raise RuntimeError("EpisodeBudgetPPO supports the serial Dispatch environment only")
        if self._episode_budget_reached:
            return False  # Previous rollout has already been updated by learn().
        assert self._last_obs is not None, "No previous observation was provided"
        # Switch to eval mode (this affects batch norm / dropout)
        self.policy.set_training_mode(False)

        n_steps = 0
        rollout_buffer.reset()
        debug = self._rollout_debug
        if debug is not None:
            debug.begin(self)
        # Sample new weights for the state dependent exploration
        if self.use_sde:
            self.policy.reset_noise(env.num_envs)

        callback.on_rollout_start()

        while n_steps < n_rollout_steps:
            if self.use_sde and self.sde_sample_freq > 0 and n_steps % self.sde_sample_freq == 0:
                # Sample a new noise matrix
                self.policy.reset_noise(env.num_envs)

            with th.no_grad():
                # Convert to pytorch tensor or to TensorDict
                obs_tensor = obs_as_tensor(self._last_obs, self.device)  # type: ignore[arg-type]
                actions, values, log_probs = self.policy(obs_tensor)
            actions = actions.cpu().numpy()
            if debug is not None:
                debug.sampled(self, actions)

            # Rescale and perform action
            clipped_actions = actions

            if isinstance(self.action_space, spaces.Box):
                if self.policy.squash_output:
                    # Unscale the actions to match env bounds
                    # if they were previously squashed (scaled in [-1, 1])
                    clipped_actions = self.policy.unscale_action(clipped_actions)
                else:
                    # Otherwise, clip the actions to avoid out of bound error
                    # as we are sampling from an unbounded Gaussian distribution
                    clipped_actions = np.clip(actions, self.action_space.low, self.action_space.high)

            new_obs, rewards, dones, infos = env.step(clipped_actions)
            if debug is not None:
                debug.transition(infos, dones)

            self.num_timesteps += env.num_envs
            self._collected_transitions += env.num_envs

            # Give access to local variables
            callback.update_locals(locals())
            if not callback.on_step():
                return False

            self._update_info_buffer(infos, dones)
            n_steps += 1

            if isinstance(self.action_space, spaces.Discrete):
                # Reshape in case of discrete action
                actions = actions.reshape(-1, 1)

            # Handle timeout by bootstrapping with value function
            # see GitHub issue #633
            for idx, done in enumerate(dones):
                if (
                    done
                    and infos[idx].get("terminal_observation") is not None
                    and infos[idx].get("TimeLimit.truncated", False)
                ):
                    terminal_obs = self.policy.obs_to_tensor(infos[idx]["terminal_observation"])[0]
                    if debug is not None:
                        debug.event("timeout_bootstrap_start", infos[idx])
                    with th.no_grad():
                        terminal_value = self.policy.predict_values(terminal_obs)[0]  # type: ignore[arg-type]
                    rewards[idx] += self.gamma * terminal_value
                    if debug is not None:
                        debug.event("timeout_bootstrap_end", infos[idx])

            rollout_buffer.add(
                self._last_obs,  # type: ignore[arg-type]
                actions,
                rewards,
                self._last_episode_starts,  # type: ignore[arg-type]
                values,
                log_probs,
            )
            self._last_obs = new_obs  # type: ignore[assignment]
            self._last_episode_starts = dones
            if self._episode_budget_reached:
                if not bool(dones[0]):
                    raise RuntimeError("Episode budget stop must occur on a real terminal transition")
                self._last_terminal_id = self._collected_transitions - 1
                break

        if debug is not None:
            debug.bootstrap_start(self, new_obs, dones, infos)
        with th.no_grad():
            # Compute value for the last timestep
            values = self.policy.predict_values(obs_as_tensor(new_obs, self.device))  # type: ignore[arg-type]
        if debug is not None:
            debug.bootstrap_end(values)

        # Allocate an exactly-sized buffer and copy only real samples. Never mark
        # the unfilled standard buffer full or run GAE over its unused tail.
        if n_steps < rollout_buffer.buffer_size:
            valid = AuditedRolloutBuffer(
                n_steps, self.observation_space, self.action_space,
                device=self.device, gamma=self.gamma, gae_lambda=self.gae_lambda,
                n_envs=env.num_envs,
            )
            for name in ("observations", "actions", "rewards", "episode_starts",
                         "values", "log_probs"):
                getattr(valid, name)[:] = getattr(rollout_buffer, name)[:n_steps]
            valid.pos = n_steps
            valid.full = True  # All slots in this new buffer contain real samples.
            self.rollout_buffer = rollout_buffer = valid
        rollout_buffer.transition_offset = self._collected_transitions - n_steps
        self._last_rollout_length = n_steps
        rollout_buffer.compute_returns_and_advantage(last_values=values, dones=dones)
        if debug is not None:
            debug.event("gae_completed", infos[0])

        callback.update_locals(locals())

        callback.on_rollout_end()

        return True
