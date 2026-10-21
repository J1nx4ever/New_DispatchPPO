AnyLogic 单班次通信检查（不训练）

准备状态：anylogic-env下61项离线测试通过；当前ALP的deterministicCheck=false、物理观测实际启用，静态契约审计通过。真实AnyLogic链路尚未运行，本文件是待用户执行的操作步骤。

1. 在AnyLogic中打开当前工作区的anylogic/DRL-PPO.alp。手动将RL_Training的运行次数NumberOfRuns临时设为1（之前为20），保持串行且不启用额外replication。原因：检查服务只接收一个完整episode；运行20次会导致后续episode连接到已经停止的服务。该设置只减少实验运行次数，不改变单班次运输或奖励公式。检查后可恢复为20，未来训练时与seed manifest匹配。本次代理没有编辑ALP。

2. 核对RL_Training的usePhysicalObservation=true、currentDispatchPolicy=3、deterministicCheck为合法true/false；Main.obsDryRun=true、enableOnnxDispatch=true，连接127.0.0.1:50051。当前文件中这些设置已符合要求，不要为了这次检查改Reward公式或业务函数。先保存并编译，处理缺失JAR/资源错误。

3. 在项目根目录的终端执行：

```bash
conda run --no-capture-output -n anylogic-env python -m python.smoke_dispatch --output-dir runs/smoke-001
```

输出目录必须尚不存在；重复检查使用smoke-002等新目录，避免覆盖证据。看到Communication check提示后，再手动启动一次AnyLogic RL_Training。该命令只创建通信检查服务，没有PPO、optimizer或模型加载；代理尚未执行此命令启动真实服务。

4. 等待28800仿真秒的班末事件。服务对每次请求校验1519维schema、有限值、mask/ego、episode/sequence/previous_action、Reward和窗口，返回当前第一个合法动作。这个规则只用于通信检查，不能作为训练结果或策略性能评估；品位违规或产量不足可能是该简单规则的结果，不能仅凭此判断Reward实现错误。全过程没有128步rollout，也不会在中途重置episode。

5. 将AnyLogic控制台输出保存为runs/smoke-001/anylogic_console.log，必须保留完整的[OBS_SCHEMA_BEGIN]至[OBS_SCHEMA_END]，然后执行：

```bash
conda run -n anylogic-env python -m python.alp_audit --schema-log runs/smoke-001/anylogic_console.log
```

成功标准为runtime_schema_log_matches=true。该结果仅证明日志中的字段顺序与磁盘契约匹配，不能单独证明日志来自预期的加载模型或所有业务行为正确。

6. 检查runs/smoke-001/status.json：status=complete、terminated=true、truncated=false。若显式开启transition记录，还可在最后一条确认sim_time_seconds=28800及终止观测。若报错，保留status.json、已开启的详细记录和AnyLogic控制台日志定位；不要关闭校验或填补非法观测。只有实际接收到终止回调才会写complete。

产物说明：默认只写status.json，记录静态来源哈希、运行状态、transition数、总reward及逐字段最小/最大值。需要定位问题时才添加--record-transitions；需要逐条完整观测时显式添加--capture-observations（同时开启transition记录）。只有显式开启后才会生成transitions.jsonl。alp_runtime_verified保持false，完整GUI编译、来源身份、仿真时钟阻塞、业务机制和班末事件顺序仍需结合实际日志确认。

单班次检查通过后再实现普通PPO的masked ActorCriticPolicy，确保采样和evaluate_actions使用相同mask，继续保持episode_budget_ppo.py不变。尚未开始此阶段，也未开始正式训练。

记录偏好更新：训练入口默认也不生成transitions.jsonl、逐请求sync_events或rollout快照。--record-transitions显式开启逐transition记录；--audit-rollouts显式开启请求事件和rollout快照。汇总、episode统计及受保护PPO核心的完整性计数继续保留，历史文件不删除。

掩码Policy已实现，可用--action-rule masked-untrained进行不训练的推理联调；具体步骤见[掩码验证记录](masked_policy_validation.md)。默认详细记录仍关闭。
