# 项目工作约定

- 本项目使用 Conda 环境 `anylogic-env`。运行 Python、pip 和测试时，使用 `/home/jinx/miniconda3/envs/anylogic-env/bin/python`，或 `conda run -n anylogic-env`。不要默认使用系统 Python 或 `DRL` 环境。
- 涉及 AnyLogic `.alp` 文件的变更时，提供供用户手动操作的步骤，包括对象/函数/参数的精确位置、修改前后内容、修改理由、影响和验证方法。不要直接编辑 `.alp` 文件，除非用户后续明确授权直接修改。
- `python/episode_budget_ppo.py` 是受保护的 PPO 核心，不修改其算法逻辑。迁移兼容问题优先在环境层、训练入口或 Policy 解决；相关工作前后验证该文件 SHA256。

- 默认关闭逐 transition、逐请求事件、全量观测和 rollout 快照等高频详细记录；仅在用户明确要求或定位问题确有必要时显式启用。保留训练汇总、episode统计、异常信息及核心训练完整性计数。已有审计记录不删除。

- 训练与通信检查默认以AnyLogic RPC传入的配置为准，不要求用户每次上传或本地审核ALP；本地ALP审计仅作为显式选择的离线工具。必须保留运行配置、schema及通信一致性检查，不能从缺失参数或零奖励猜测配置。
