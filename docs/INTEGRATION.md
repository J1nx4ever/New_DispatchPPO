# V4 Python P0 及观测切换接入指南

> 当前奖励与评估入口已迁移至[Reward V1.0冻结规范](reward_v1_freeze.md)。下文保留P0接入历史说明；V4奖励模型不能冒充V1.0模型，真实运行前先完成新规范中的3项ALP手动参数修改。P0开发模式不等于正式F1。

> 最新[状态可重建性与P0审计](p0_state_reconstructability.md)已确认当前ALP通过Reward V1.0离线契约；P0更新为 `fifo-p0-dev.v2`，严格交叉校验观测中的已用/剩余班时和剩余窗时。新实现仍独立输出6维，未接入正式PPO训练；历史仅填elapsed而不填remaining的合成快照应按实际ALP公式补齐，不能靠缺省0绕过校验。

匹配仓库：`J1nx4ever/New_DispatchPPO`，已核对 `python/dispatch_env.py`、`python/dispatch_bridge.py`、`python/observation_contract.py`、`python/masked_policy.py`、`python/train.py` 的 main 分支源码（2026-10-22读取）。建议按固定 commit/sha 使用，别在未审查的新版本直接覆盖。

## 本包提供什么

- `python/window_projection.py`：**已实现 P0**。从原1519维 obs 的FIFO出料顺序、余量、品位、2500t/h归一化破碎速率，以及当前时刻，计算未来4个窗口已有FIFO物料的增量产出；六维顺序 `[Q_current/5000, M_current/5000, valid_current, Q_next/5000, M_next/5000, valid_next]`。不含当前窗口已产出量；不含在途、卸载中及尚未装载物料。执行时既不读取也不修改ALP未来状态。
- `python/observation_projection_wrapper.py`：Gymnasium包装器，使1519维原始gRPC保持不变；1525维仅在本地输入策略。原动作掩码仍是19:23。
- `python/tests/test_window_projection.py`：合成FIFO的守恒、跨窗、空窗口、尾窗和错误处理。

## 部署到现有仓库

1. 将代码目录中的三个文件各自复制到仓库相同相对位置。
2. 在 `python/masked_policy.py` 将维度检查由仅接受1519改成允许1519或1525（具体见下）。`_decision_mask`中mask仍取19:23。
3. 在 `python/train.py` 新增 `--obs-mode`，取值 `f0`（正常正式原始基线）、`p0-smoke`（仅验证P0附加特征通信/训练链路）。**切勿将 `p0-smoke` 的结果在论文中标记为正式F1**。
4. 在生成 `base_env=DispatchEnv(...)` 之后、`env = Monitor(...)` 之前，根据模式加包装器。需要一模一样地应用于`evaluate.py`、`inference_server.py`接收策略观察的位置。切勿让推理1519维模型接收1525维输入，或反之。
5. 正式F1必须等待P1/P2/P3完成并通过核验后，将同一包装器的`project_fifo_only`替换为完整已承诺物料预测器；确保6个字段的名称语义从“FIFO-only”转换为“Committed material”。不要默默复用旧模型。

### masked_policy.py：最小替换

原：
```python
if not isinstance(observation_space, spaces.Box) or observation_space.shape != (OBSERVATION_SIZE,):
    raise ValueError('DispatchMaskedPolicy requires the 1519D physical observation')
```
改：
```python
if not isinstance(observation_space, spaces.Box) or observation_space.shape not in {(OBSERVATION_SIZE,), (1525,)}:
    raise ValueError('DispatchMaskedPolicy requires 1519D or 1525D observation')
```
原：
```python
if obs.ndim != 2 or obs.shape[1] != OBSERVATION_SIZE:
    raise ValueError('expected batched 1519D observations')
```
改：
```python
if obs.ndim != 2 or obs.shape[1] not in (OBSERVATION_SIZE, 1525):
    raise ValueError('expected batched 1519D or 1525D observations')
```

### train.py：最小增量

在文件头部加：
```python
from .observation_projection_wrapper import FIFOObservationWrapper, PROJECTION_CONTRACT_ID
```

在 `parse_args()` 返回前加：
```python
parser.add_argument('--obs-mode', choices=('f0', 'p0-smoke'), default='f0')
```

在现有 `base_env=DispatchEnv(...)` 之后、`env=Monitor(...)` 之前加：
```python
if args.obs_mode == 'p0-smoke':
    base_env = FIFOObservationWrapper(base_env)
```

在 `_manifest` 返回结构增加：
```python
'agent_observation_mode': args.obs_mode,
'agent_observation_dimension': 1519 if args.obs_mode=='f0' else 1525,
'projection_contract_id': None if args.obs_mode=='f0' else PROJECTION_CONTRACT_ID,
```

保留 `observation_schema_id='dispatch.physical.v3'` 和 `observation_dimension=1519`，表示gRPC原始契约；不要用1525替换bridge原始校验。

**重要**：原 `--resume-model` 检查基于原始1519维/schema，并未包含agent维度；加包装器后必须额外在 `_validate_resume_contract` 对比 manifest 中的 `agent_observation_mode` 和维度，防止F0权重被加载进1525维模型。最简安全实现是禁止 `p0-smoke` 模式使用 `--resume-model`，并强制F0新训练（正式研究阶段F0/F1应从头独立训练）。

### 运行

在仓库根目录，且必要依赖已安装：
```bash
python -m pytest -q python/tests/test_window_projection.py
# 原方案（不加六维）
python -m python.train --episodes 2 --anylogic-seed-manifest path/to/seeds.json --obs-mode f0
#仅验证前处理管线（不作为正式论文F1）
python -m python.train --episodes 2 --anylogic-seed-manifest path/to/seeds.json --obs-mode p0-smoke
```

### 数据真实性和奖励前提

ALP V4 `global.shiftElapsed` = timeSec/28800，`windowIndex` = index/4；FIFO槽位`t/500`，品位原值；`dump.0.bufferTons` = crusherStoredTons/500；`dump.0.crusherRate` = crusherRateTph/2500。原始传输使用float32，有精度限制。

此包**不修改任何奖励**。V1.0的训练前置门槛仍然必须完成：`enableGradeActionReward=false`、`wGradeShift=0`、矿/废班末缺口项有效、四窗真实品位项有效，并冻结奖励权重、环境参数、随机种子与训练预算。相同奖励下才有公平F0/F1。

目前单元测试基于合成观察；尚无真实AnyLogic反事实运行对账。别将其称为P0物理模型的动态验证通过。

## 本仓库的初步融合状态（2026-10-22）

已按上文落地 P0 管线，原始 1519 维 gRPC 契约保持不变。本仓库测试目录是 `test/`，不是 `python/tests/`。

| 位置 | 改动 |
| --- | --- |
| [python/window_projection.py](../python/window_projection.py) | 原样落地 P0 FIFO 投影（含守恒断言与 schema 字段校验）。 |
| [python/observation_projection_wrapper.py](../python/observation_projection_wrapper.py) | 原样落地 Gymnasium 包装器；`AGENT_DIM=1525`。 |
| [test/test_window_projection.py](../test/test_window_projection.py) | 投影测试 + 包装器测试（追加六维、原始 1519 维逐位不变、维度错误拒绝）。 |
| [python/observation_contract.py](../python/observation_contract.py) | 新增 `AGENT_OBSERVATION_SIZE = 1525`（仅 agent 侧；`observation_dimension` 仍为 1519）。 |
| [python/masked_policy.py](../python/masked_policy.py) | 观测空间与批次校验允许 1519 或 1525；掩码仍取 `19:23`，终端判定仍取 `17`；新增 1525 维有限性校验。 |
| [python/train.py](../python/train.py) | 新增 `--obs-mode {f0,p0-smoke}`（默认 `f0`）；在 `DispatchEnv` 之后、`Monitor` 之前套包装器；manifest/SUCCESS 增加 `agent_observation_mode`、`agent_observation_dimension`、`projection_contract_id`。 |
| [python/evaluate.py](../python/evaluate.py) | 由训练 manifest 推断 agent 观测模式，校验 checkpoint 维度与投影契约，`p0-smoke` 时应用同一包装器（不再硬性要求 1519）。 |

Resume 规则（比上文更严格）：

- `--obs-mode p0-smoke` 与 `--resume-model` 互斥，直接拒绝，F0/F1 必须各自从零训练。
- `_validate_resume_contract` 额外比对 `agent_observation_mode` 与 `agent_observation_dimension`；缺少这两个字段的旧运行按 `f0`/1519 处理，避免历史 checkpoint 被静默迁移。

运行（Conda 环境）：

```bash
/home/jinx/miniconda3/envs/anylogic-env/bin/python -m pytest -q test/test_window_projection.py test/test_masked_policy.py
/home/jinx/miniconda3/envs/anylogic-env/bin/python -m python.train --episodes 2 --anylogic-seed-manifest docs/rl_training_seed_manifest.json --obs-mode f0
/home/jinx/miniconda3/envs/anylogic-env/bin/python -m python.train --episodes 2 --anylogic-seed-manifest docs/rl_training_seed_manifest.json --obs-mode p0-smoke
```

```bash
/home/jinx/miniconda3/envs/anylogic-env/bin/python -m python.evaluate --model runs/.../dispatch_ppo.zip \
  --episodes 2 --anylogic-seed-manifest docs/ppo_holdout_seed_manifest.json \
  --alp-path anylogic/DRL-PPO.alp --output-dir runs/eval-p0-smoke
```

尚未完成（保持原判定）：

- 未修改任何 ALP；P1–P3 未实现，`p0-smoke` 不得标记为正式 F1。
- 仓库内没有 `inference_server.py`，观测入口目前只有 `train.py` 与 `evaluate.py`；新增入口必须复用同一 `FIFOObservationWrapper`。
- 只用合成观察做了管线自检，仍需真实 AnyLogic 反事实对账。
