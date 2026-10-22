当前ALP奖励分析、grade_action消融与训练日志（2026-10-22）

流程更新：日常训练已改为通过AnyLogic RPC识别配置，不再要求每次本地审核或上传ALP。请先完成[一次性配置传递补充](anylogic_runtime_configuration.md)，之后同一训练命令自动识别on/off；下文的本地源码审计仅作为可选离线工具。

本次以anylogic/DRL-PPO.alp为事实来源，未修改ALP或episode_budget_ppo.py，未启动训练。当前Reward ID为dispatch-reward-physical-v4，Observation仍为dispatch.physical.v3、1519维。obsInit、collectPhysicalObservation及字段写出函数的来源摘要与已核验schema一致。

1. 当前奖励结构

每个transition总奖励是六项之和：wait + grade_action + grade_2h + grade_shift + production + waste。grade_action_enabled是配置诊断，不是奖励；吨数、比例、缺口等诊断也不能加进总奖励。

| 项 | 当前公式/范围 | 何时结算与归属 |
|---|---|---|
| wait | -clip(delta_wait_vehicle_seconds / 9 / 200,0,1)，每步[-1,0] | 下一次DECISION或END，对上一动作至当前事件的等待积分计费 |
| grade_action | 启用且选择矿石点时，0.15×(0.7×窗口反事实偏差改善 + 0.3×班次反事实偏差改善)；两种改善各clip到[-0.10,0.10]，单次范围[-0.015,0.015] | 当前动作响应后计算并存入pending，到下一次DECISION/END返回；关闭或选择WASTE时严格为0 |
| grade_2h | 每窗1×gradeReward；四窗总范围[-4,4] | 每7200秒按已破碎矿量/金属量封窗，pending累计到下一次DECISION/END |
| grade_shift | 6×gradeReward(0.27-shiftGrade)，范围[-6,6] | 28800秒班末，归入最后动作的terminal transition |
| production | -4×clip(1-crusherOreTons/16000,0,1)，范围[-4,0] | 班末矿量缺口；达标/超产为0，无额外超产奖励 |
| waste | -wWasteShortfall×clip(1-totalWasteMoved/targetWasteTonsShift,0,1)；当前权重4、目标4000吨，范围[-4,0] | 班末已交付废石缺口；目标为0时按ALP返回0，达标/超额均为0 |

品位函数保持原式：gap=0.27-grade，gap<0时allowance=0.28-0.27，否则为0.27-0.26；deviation=clip(abs(gap)/allowance,0,3)，gradeReward=clip(1-deviation,-1,1)。目标品位得1，0.26/0.28边界得0，偏离目标至少0.02时饱和为-1。空窗口仍按无供料的gap=targetGrade处理，违规标志保留原吨数和1e-12容差判断。

grade_action的反事实先验吨数为max(20000,车辆capacity)，候选载荷用max(1,capacity)，候选品位用装载点名义品位，窗口与班次分别计算加入候选载荷前后的gradeDeviation改善。临近耗尽时它仍按车辆capacity而非实际剩余可装吨数估计；本次保留此规则。代码注释中的0.25是历史描述，实际计算使用targetGrade=0.27，未据注释改公式。

与v3的重要差异：新增班末waste项；选择WASTE时原先的-wWasteLag×落后比例即时惩罚已移除，grade_action统一为0。因此v3不能作为本次grade_action消融的off组。旧ALP仍存在wWasteLag、productionLagTolerance变量，但当前v4奖励函数已不使用它们；Python新契约不再将这些无效参数列入冻结公式。

2. 结构分析与消融口径

- 建议比较v4内的on/off两组，只改变enableGradeActionReward；其余奖励权重、废石目标、初始模型、PPO超参数、训练预算、PPO seed及AnyLogic seed manifest保持一致。
- 两组都保留品位窗口/班次奖励和矿石/废石任务奖励。关闭grade_action仅删除矿石动作的即时品位塑形，不等于关闭所有品位目标。
- 该塑形不是经过证明的gamma×Phi(s')-Phi(s)形式，不能宣称保持最优策略不变；消融反映塑形对学习与最终行为的实际影响。
- wait逐步累计，终端矿石/废石惩罚各最多4、班次品位幅值6，四窗幅值共4。决策次数变化会影响等待累积与塑形次数，不能只按单项权重判断强弱。保持当前PPO gamma=0.995；它按决策步折扣，不按仿真秒折扣，稀疏班末目标的早期折扣会随决策数变化。本次没有修改gamma或任何奖励公式。
- 主比较指标应包括共同口径base_return=raw_return-grade_action总和，以及矿量、废石交付量/缺口、班次品位、窗口违规率、等待vehicle-seconds。两组raw_return属于不同训练目标，不能单独比较其大小就认定策略优劣。
- 建议对多个PPO seed重复，每对使用同一AnyLogic seed列表；初始随机种子相同不保证不同策略经过不同事件路径后仍消费完全相同的随机数序列。最终模型还应在固定、独立于训练的种子集上评估，本次只准备训练和日志，不声称已完成统计消融。

当前磁盘配置：enableGradeActionReward=false（自由参数表未覆盖，使用Main默认false），wWasteShortfall=4.0，废石目标4000吨，RL_Training NumberOfRuns=20，deterministicCheck=false。

3. 发现的额外ALP差异

LoadSite.obsRecordCompletedGrade也有变动：同一品位块内的纯块整车完成测量现在直接更新已知品位并return；跨块逻辑仍走原推断路径，异常信息新增详细数值。新分支会跳过原先对已知块重复测量的金属量一致性检查，因此不只是错误信息调整。它可能改变已知品位的数值更新及异常触发行为，虽字段顺序没变，两组实验仍须使用同一版本。此差异已单独存入reward_v4_provenance.json；未修改它，也不把它算作grade_action开关的作用。真实边界浮点行为待实际仿真验证。

原alp_contract_provenance.json保留，不覆盖历史审计。v4来源记录仅登记本次读到并审阅的三个已修改Main奖励/请求函数、三个新增Reward helper及这一LoadSite函数，运行时同时检查原业务基线和v4覆盖摘要。未知后续业务函数变化仍会阻断启动。

4. Python迁移与运行保护

- reward_contract.py升级为v4，严格校验六项总和、grade_action_enabled为0/1并符合期望配置、关闭时塑形恰为0、塑形新范围、班末废石吨数/目标/比例/缺口/加权公式。所有数值必须有限。非终止回调不允许出现waste、production、grade_shift等班末奖励。
- reward_config.py集中保存grade_action_enabled、废石权重和目标，并生成包含奖励公式参数及Contract ID的稳定配置指纹。
- alp_audit.py读取RL_Training实际参数覆盖，检查新开关和废石参数，保持独立Observation/Reward检查及既有业务来源保护。
- dispatch_bridge.py按本次运行的期望配置检查每个请求，防止开关在episode内或运行中静默改变。START允许grade_action_enabled=1这个非零诊断标志，但仍要求全部奖励、等待积分和窗口为空/零；修复原先把所有map值均当作奖励的检查。
- train.py增加--grade-action auto/on/off。它是期望值核验，不会替用户修改ALP，不会在Python侧裁掉ALP已经给出的塑形。Python不再读取本地ALP的运行次数，而是按--episodes和请求元数据验收；AnyLogic运行次数由用户匹配本次预算。--resume-model必须来自同一v4奖励配置与掩码Policy，跨开关/权重恢复及旧v3结果均拒绝；消融主实验建议每组从零训练。
- 默认输出到runs/dispatch-reward-physical-v4/grade-action-on或grade-action-off/seed-<PPO seed>/<时间与唯一后缀>/。显式--output-dir仍可使用，但拒绝混入非空旧目录；manifest、SUCCESS、episode记录都标明组别/配置指纹。训练失败会将manifest写为failed并记录原因，不生成SUCCESS。
- smoke_dispatch.py也从ALP加载新配置，保持不训练的通信检查能力。proto字段和JAR无需修改，新组件通过原reward_components map传输。

5. 日志管理

| 文件 | 默认行为与用途 |
|---|---|
| run_manifest.json / SUCCESS.json | 运行身份、RPC配置来源和协议摘要、PPO参数、种子、开关、配置指纹及完成状态 |
| episodes.csv | 每个episode一行：run_id、PPO seed、组别、episode ID/长度、原始/训练/base回报、六项奖励、矿量、品位、废石、等待积分、窗口违规率 |
| stage_episodes.jsonl | 每episode一条，包含精确奖励分解、独立terminal_metrics、四窗摘要、开关元数据和指纹；不是逐transition日志 |
| stage_statistics.json | 全运行与滚动回报、独立物理指标均值、窗口违规率及配置 |
| stage_metrics.csv / TensorBoard | PPO更新指标、六项奖励聚合、physical/*物理指标和config/*开关/废石权重；汇总频率不变 |
| monitor.csv | 保留SB3标准episode回报和长度，比较/分析优先使用episodes.csv，不单独用此文件判断消融效果 |
| training_finish.json | 原核心样本参与、尾部更新、最终日志刷新与保存审计，完全保留 |
| transitions.jsonl / rollout_audit | 默认不创建，仅明确排错时通过原显式开关开启；旧文件不删除 |

诊断flag不累加、终端物理指标不混入奖励分量。保存4条窗口摘要/episode用于评价窗口违规，不开启逐事件或全量观测记录。完整TensorBoard标签保留在文件，控制台仍聚焦训练/episode汇总。

6. 手动运行步骤（尚未启动）

当前off组已配置。先编译当前ALP，确保NumberOfRuns=20、串行、不开额外replication。先启动Python，看到监听提示后再手动启动AnyLogic RL_Training：

```bash
conda run --no-capture-output -n anylogic-env python -m python.train --episodes 20 --anylogic-seed-manifest docs/rl_training_seed_manifest.json --seed 123
```

on组需用户手动操作：在AnyLogic的RL_Training自由参数表找到enableGradeActionReward（ID1792626220025），将空值/false改为true；其余字段不变，保存当前工作区文件并编译。理由：启用原ALP已有矿石品位塑形；影响：grade_action允许非零，1519字段、业务机制及其他五项奖励不变。不要只改Main默认值而忽略实验中已有的显式覆盖。

```bash
conda run --no-capture-output -n anylogic-env python -m python.train --episodes 20 --anylogic-seed-manifest docs/rl_training_seed_manifest.json --seed 123
```

查看首个请求握手后记录的ablation_variant和reward_configuration，运行结果在新组目录中。--grade-action on本身不会切换ALP；若未手动切换，Python会在收到首个请求后、创建训练目录和产生动作前拒绝不一致。回到off时在同一实验参数处设false、保存并同样核验。废石权重保持wWasteShortfall=4.0；若修改它，已经不是单一grade_action因素的对照。多PPO seed时，两组都使用同一seed集合，不跨组加载模型。

建议先各做一次小预算v4接线验收再扩展实验：用户手动将RL_Training NumberOfRuns改为2并保存，命令相应改为--episodes 2和docs/ppo_acceptance_seed_manifest.json；完成后再恢复20及20行清单。v3训练成功不能替代v4废石终端分量和开关的真实回调验证。

7. 离线验收与限制

使用anylogic-env，pytest位于/tmp/new_dispatchppo_test_deps。检查命令：

```bash
PYTHONPATH=/tmp/new_dispatchppo_test_deps /home/jinx/miniconda3/envs/anylogic-env/bin/python -m pytest -q test --junitxml=docs/reward_v4_tests.xml
```

最终112项通过，0失败、0跳过。覆盖on/off起始诊断、关闭泄漏拒绝、运行内翻转拒绝、新塑形上下限、废石零/不足/达标/超额、目标0/权重0/自定义权重、公式和诊断不一致、ALP覆盖解析、CLI防误配、跨消融恢复拒绝、低频日志分离，以及所有原gRPC、Mask Policy和受保护PPO合成回归。真实v4 AnyLogic回调尚未执行；不宣称已经完成真实消融或收敛验证。

本次修改前后核心SHA256均为：

8e4cfa31c622f5e33756e304eea3f7526547db72ae93f7d9f00808845d61ef96

本次读取的ALP摘要为7a5d74dec5eaea3f4fba0c506507bc5c2cf02e9e88673a59c6e18d11304fd46e，完成后相同。历史runs/ppo-acceptance-001等v3产物保留原样。
