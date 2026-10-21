from __future__ import annotations

import json
import os
import random
import signal
import subprocess
import threading
import uuid
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, Optional


class ParameterVariationEpisodeRunner:
    """Wait for replications started by an AnyLogic experiment."""

    def __init__(self, total_episodes: Optional[int] = None) -> None:
        if total_episodes is not None and total_episodes <= 0:
            raise ValueError("total_episodes must be positive")
        self.total_episodes = total_episodes
        self.episodes_started = 0

    def start_episode(
        self,
        seed: Optional[int],
        options: Optional[dict[str, Any]],
    ) -> bool:
        # AnyLogic Parameter Variation owns replication and seed scheduling.
        if (
            self.total_episodes is not None
            and self.episodes_started >= self.total_episodes
        ):
            return False
        self.episodes_started += 1
        return True

    def close(self) -> None:
        # The user-managed AnyLogic experiment is not a child process.
        return None


class AnyLogicEpisodeRunner:
    """Launch one fresh AnyLogic process for each Gymnasium episode."""

    def __init__(
        self,
        command: Sequence[str],
        *,
        cwd: Optional[str | Path] = None,
        env: Optional[Mapping[str, str]] = None,
        startup_grace_seconds: float = 0.2,
        shutdown_timeout_seconds: float = 5.0,
    ) -> None:
        if not command or not all(isinstance(part, str) for part in command):
            raise ValueError("command must be a non-empty sequence of strings")
        if startup_grace_seconds < 0 or shutdown_timeout_seconds < 0:
            raise ValueError("process timeouts must be non-negative")

        self.command = tuple(command)
        self.cwd = str(cwd) if cwd is not None else None
        self.env = dict(env or {})
        self.startup_grace_seconds = startup_grace_seconds
        self.shutdown_timeout_seconds = shutdown_timeout_seconds
        self._process: Optional[subprocess.Popen[bytes]] = None
        self._seed_rng: Optional[random.Random] = None
        self._lock = threading.Lock()

    def start_episode(
        self,
        seed: Optional[int],
        options: Optional[dict[str, Any]],
    ) -> None:
        with self._lock:
            self._stop_process()

            episode_id = str(uuid.uuid4())
            if seed is not None:
                seed_value = str(seed)
                self._seed_rng = random.Random(seed)
            else:
                if self._seed_rng is None:
                    self._seed_rng = random.Random()
                seed_value = str(self._seed_rng.getrandbits(63))
            options_json = json.dumps(
                options or {}, ensure_ascii=True, separators=(",", ":")
            )
            substitutions = {
                "{seed}": seed_value,
                "{episode_id}": episode_id,
                "{options_json}": options_json,
            }
            command = tuple(
                self._substitute(argument, substitutions)
                for argument in self.command
            )

            process_env = os.environ.copy()
            process_env.update(self.env)
            process_env.update(
                {
                    "DISPATCH_EPISODE_SEED": seed_value,
                    "DISPATCH_EPISODE_ID": episode_id,
                    "DISPATCH_EPISODE_OPTIONS": options_json,
                }
            )

            try:
                process = subprocess.Popen(
                    command,
                    cwd=self.cwd,
                    env=process_env,
                    start_new_session=(os.name == "posix"),
                )
            except OSError as exc:
                raise RuntimeError(
                    f"failed to launch AnyLogic command: {command[0]}"
                ) from exc

            self._process = process
            try:
                return_code = process.wait(timeout=self.startup_grace_seconds)
            except subprocess.TimeoutExpired:
                return

            self._process = None
            raise RuntimeError(
                "AnyLogic process exited before the episode started "
                f"(exit code {return_code})"
            )

    def close(self) -> None:
        with self._lock:
            self._stop_process()

    @staticmethod
    def _substitute(argument: str, substitutions: Mapping[str, str]) -> str:
        for placeholder, value in substitutions.items():
            argument = argument.replace(placeholder, value)
        return argument

    def _stop_process(self) -> None:
        process = self._process
        self._process = None
        if process is None or process.poll() is not None:
            return

        try:
            if os.name == "posix":
                os.killpg(process.pid, signal.SIGTERM)
            else:
                process.terminate()
        except ProcessLookupError:
            pass

        try:
            process.wait(timeout=self.shutdown_timeout_seconds)
        except subprocess.TimeoutExpired:
            try:
                if os.name == "posix":
                    os.killpg(process.pid, signal.SIGKILL)
                else:
                    process.kill()
            except ProcessLookupError:
                pass
            process.wait()