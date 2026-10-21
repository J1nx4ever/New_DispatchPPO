New_DispatchPPO 第一阶段迁移与代码审计报告（2026-10-21）

本阶段已完成 Python 1519D 通信基础设施迁移和离线验收，未启动正式 PPO 训练，未加载旧 31D 模型。全部仿真事实来自 `anylogic/DRL-PPO.alp`。真实 AnyLogic GUI 的编译、资源装载、事件执行和通信行为均为**待真实仿真验证**。

1. **新旧训练接口差异**

| 项目 | 迁移前 Python / 文件现状 | 当前 ALP 契约与迁移结果 |
|---|---|---|
| Observation | `dispatch.v2-31`，31维；proto注释还写27维 | `dispatch.physical.v3`，1519维 |
| 范围 | 前27维[-1,1]，末4维[0,1] | 字段级缩放；全向量不受统一[-1,1]约束 |
| 车辆 | 旧奖励核验分母20 | ALP固定9辆，3种车型，各3辆，容量91.7/147/193吨 |
| 品位 | 目标0.25，旧边界0.24/0.27 | ALP目标0.27，合法区间0.26–0.28，窗口标志含1e-12容差 |
| 矿量目标 | 旧20000吨/窗口、80000吨/班次 | ALP参数4000吨/窗口、16000吨/班次；废石目标4000吨 |
| Reward ID | Python期待`dispatch-reward-v2`，ALP字符串未初始化 | 显式初始化并核验`dispatch-reward-physical-v3` |
| 动作 | `Discrete(4)` | 保留；0=HG1、1=HG2、2=LG、3=WASTE |
| Mask | Python未定义 | 观测零基索引19..22，合法位为1；23..26为可预留吨数/193 |
| 算法入口 | 缺失`.constrained`、`.lagrangian`导入；多算法参数混合 | 只保留普通`EpisodeBudgetPPO`，CLI固定`n_steps=128` |
| protobuf | `proto/`缺少WindowSummary及请求15..18字段；Maven版和原Python生成版已有这些字段 | Maven版为唯一权威来源，镜像一致，重生成Python并核验Java描述符 |
| JAR | dist与target内容哈希不同，入口记录target而ALP引用裸文件名 | ALP与入口统一使用dist，target构建后复制并核验；运行前拒绝过期产物 |

2. **已修改和新增文件**

| 文件/组 | 修改原因 |
|---|---|
| `python/train.py` | 清除缺失算法导入、Dual/PID/Lagrangian参数、分支和专用checkpoint；保留普通PPO优化参数、seed manifest、transition日志、StageStatistics、RolloutDebug、最终完整性审计及SUCCESS产物。拒绝旧schema模型；新模型恢复也强制128步。启动前核验ALP与协议产物。 |
| `python/observation_contract.py`、`observation_schema.json` | 独立1519D观察契约，逐字段顺序/表达式/含义/范围；拒绝schema、长度、NaN/Inf、float32溢出、非法二值及类别编码、ego/terminal不一致。支持实际schema日志比对。 |
| `python/reward_contract.py` | 移除31D观察常量；以当前ALP重建奖励参数、窗口边界和分量核验，诊断量不计入奖励总和。 |
| `python/dispatch_bridge.py` | 使用新观察契约；保留同步阻塞和重复请求一致性，增强连续sequence、上一action、仿真时间差、终止后请求、未知kind检查；不合法mask动作直接报错。 |
| `python/dispatch_env.py` | 更新Box及info.action_mask；保持reset/step/terminal行为及runner预算结束语义。 |
| `python/__init__.py` | 明确包结构，支持`python -m python.train`。 |
| `python/alp_audit.py`、`alp_contract_provenance.json` | 从XML检查奖励参数、物理开关、时间、实验串行配置；记录原ALP摘要和所有原Function Body摘要，校验业务函数未变。 |
| `python/protocol_artifacts.py` | 启动前核验两份proto、两处JAR、Python生成文件与构建清单，拒绝旧产物。 |
| `proto-src/src/main/proto/dispatch.proto`、`proto/dispatch.proto` | 统一内容；更正1519D说明，既有字段编号/类型/语义不变。 |
| `python/generated/dispatch_pb2.py`、`dispatch_pb2_grpc.py` | 从权威proto重新生成；gRPC导入改为包内相对导入。 |
| `proto-src/target/`、`dist/DRL-Dispatching-1.2.0.jar`、`dist/protocol_manifest.json` | Maven离线构建、Java/Python完整描述符比对、部署同一JAR并记录哈希。 |
| `requirements.txt` | 原为空，现记录已验证依赖版本。 |
| `tools/build_observation_schema.py`、`enrich_observation_schema.py` | 可重现静态字段展开和字段说明/范围清单。 |
| `tools/regenerate_protocol.py`、`ProtocolDescriptor.java` | 可重现协议生成、Java描述符提取及部署。 |
| `tools/audit_inventory.py` | 递归文件、Python import、路径字符串、JAR内容、ALP资源和实验参数清单。 |
| `test/test_contracts.py`、`test/test_training_finish.py` | 契约、同步通信、Gym生命周期与受保护PPO的合成回归测试。 |
| `docs/` | 完整报告、1519字段CSV、源码审计证据、ALP精确补丁、路段序号、20次运行seed清单及JUnit结果。 |

`episode_budget_ppo.py`未修改。`dispatch_service.py`、`episode_runner.py`、`rollout_debug.py`、`stage_statistics.py`保留原实现；已通过导入、实际RPC或合成训练日志测试验证其兼容性。没有创建假模块。

3. **ALP问题、最小修改及未解决项**

精确差异见 `docs/phase1_alp.patch`。仅修改5处XML配置；所有Function Body与原文件逐一摘要比较一致，运输、装卸、破碎、排队、道路、品位及Reward函数完全保留。

| 位置 | 原问题 | 处理与影响 |
|---|---|---|
| Main变量`rewardContractId`，约1591行 | String无InitialValue，启动时episode ID包含null，并可能在protobuf.setRewardContractId触发空指针 | 初始化为新Reward ID；只改变接口身份，数学公式不变。 |
| Main参数`usePhysicalObservation`，约2433行 | 默认false；RL_Training的freeform配置没有覆盖值，因此会进入旧31D构造器 | 默认设true，决策和terminal均走已有1519D物理观察函数。 |
| RL_Training/ModelTimeProperties/FinalTime，约22806行 | 模型时间单位Second，FinalTime=480；班末事件在rlShiftSeconds/60分钟=28800秒 | 改为28800，允许达到既定班末；未改班次长度。与截止时刻同时间的事件顺序、停止时机仍待真实仿真验证。 |
| ModelResources/DRL JAR，约23335行 | 裸JAR路径无法证明与Python记录的target JAR一致 | 指向`../dist/DRL-Dispatching-1.2.0.jar`。 |
| ClassPathEntry/同一JAR，约23705行 | 同上 | 与资源引用同步；AnyLogic实际解析此相对路径待真实仿真验证。 |

RL_Training静态配置：串行（AllowParallelEvaluations=false），UseFreeformParameters=true，NumberOfRuns=20，UseReplication=false；run_index=index+1，experiment_seed=202610160011+index。RangeVariation中的policy=3不是当前freeform路径的覆盖值，但Main默认policy本身也是3。deterministicCheck默认true，obsDryRun=true，enableOnnxDispatch=true，speedDtSec=0.2。训练命令的episode预算与seed manifest应匹配实际实验运行数；随报告提供20行对应清单，未据此启动训练。

当前模型中没有材料可派时，`selectNextLoadSite`返回-1，车辆进入NO_AVAILABLE_MATERIAL；这不是episode terminal。只有`finishEpisodeAndNotify()`在28800秒结算班末、发送EPISODE_END(terminated=true,truncated=false)并finish引擎。若初始化后从未出现第一次派车，START/END链路能否形成仍需实测；Python会拒绝无START的END，不伪造transition。

`getAvailableTons()`在站点不可用时为0，否则max(0,remaining-reserved)。mask只允许可预留吨数>1e-6的站点；预留为min(车辆容量,可预留量)，支持最后不足一整车。选耗尽点会抛异常，无fallback。四点均无可用量时不发动作请求，不能把全零mask解释成额外terminal。当前普通MlpPolicy尚未应用采样mask；Python会拒绝不合法动作，不替换为其他动作。动作掩码Policy属于下一阶段。

Terminal使用已有`buildPhysicalObservation(null)`，同样1519维；global.terminal=1，9个ego=0，mask和actionTons全零。代码静态路径和Python合成测试通过，真实terminal向量待真实仿真验证。

`DispatchObsWriter.add`已检查double及float转换有限性；FIFO>16、队列>9、重复名称、错误类别、schema顺序变化均抛异常。Python也拒绝非有限值/溢出并保留原值，不截断、不填充、不重归一化。缩放不是clipping，例如freeSamples可能>1、服务年龄/600可能>1、废石交付/4000最高可达7.5；坐标、路线距离和自由流统计的精确上限依赖几何及实际运动，未编造[-1,1]边界。字段CSV明确区分预期物理范围与Python接受边界；确定的二值、one-hot、ID槽及单位区间检查已启用，未证明的连续量保守接受有限float32。

ALP的24项资源在`anylogic/`相对路径下缺失，包括图形文件、grpc-java各运行库、protobuf-java、SpeedControl-1.0.0.jar；具体见inventory。Java协议JAR是thin JAR，不包含这些依赖。它们可能由用户机器的AnyLogic既有工程配置提供，当前工作区无法证明。Main仍引用Fusion.grpc的速度控制类和旧速度控制函数；本阶段未删除或重写该仿真子系统，也未伪造依赖。GUI编译和资源解析待真实仿真验证。

4. **Observation与Reward Contract设计**

逐字段真实索引、缩放Java表达式、物理含义、预期范围和接受边界在 `docs/observation_fields.csv`（1519行）与 `python/observation_schema.json` 中。索引均从0开始。

| 区段 | 索引 | 数量及顺序 |
|---|---|---|
| 全局 | 0..18 | elapsed、remaining、windowIndex、windowRemaining、windowTons、windowMetal、noSupply、shiftOre、shiftMetal、wasteDelivered、wasteShortfall、oreTarget、wasteTarget、gradeLower、gradeUpper、gradeTarget、deterministic、terminal、speedTickPhase |
| 动作mask | 19..22 | HG1、HG2、LG、WASTE；非终止且可预留吨数>1e-6 |
| 动作载荷 | 23..26 | 相同站点顺序，min(ego.capacity,availableTons)/193；terminal为0 |
| 车辆 | 27..1106 | 按truckId=0..8排序，每车120维；ego在27+120*truckId |
| 装载点 | 1107..1294 | siteId=0..3，每点47维 |
| 卸载点 | 1295..1390 | Crusher=0、Dump=1，每点48维 |
| 破碎FIFO | 1391..1438 | 16槽，每槽valid、tons/500、grade；不足补零，溢出报错 |
| 有向道路 | 1439..1518 | 16段，按`from_to`的Java字符串自然排序，每段from、to、length/10000、limit/10、closed |

9个节点的类别顺序是Crusher、dumpNode、intersection1、intersection2、intersection3、ShovelOreHigh1、ShovelOreHigh2、ShovelOreLow、ShovelWaste。道路实际排序映射见`docs/road_indices.json`；不是HashMap迭代顺序。

车辆块依次包含ego，3类车型one-hot，12阶段one-hot，容量/载荷/品位信息，装载目标4类、卸载目标2类、节点9类one-hot，米坐标/10000、速度/10、加速度/3、路段16类one-hot、剩余距离/10000、16段路线次序/16、排位/9、初始派车信息、等待年龄/28800、服务年龄/600、平均服务分钟/10、物料游标/30000、自由流样本数/1000及均值标准差，最后4条运动历史，每条7维。运动历史按ArrayDeque从旧到新，未使用样本为0。

阶段类别：0决策车辆，1未完成首次派车，2前往装载，3等装载资源，4装载中，5前往卸载，6等卸载资源，7等缓冲容量，8待准入，9卸载中，10已完成/无材料，11其他。类别按ALP判断优先级编码；不能以phase=10推断整个episode结束。

装载点20项状态后依次queue/seize/service各9个车辆ID槽；卸载点12项状态后依次queue/seize/capacityWait/service各9槽。ID槽为0表示空位，否则(truckId+1)/9。队列与等待槽遵从模型列表顺序，service槽按truckId排序。正在装载的品位统计来自obsGradeStats，对已观测块使用推知值、未知块使用均匀先验；不泄露未观测随机块品位。

字段顺序可静态展开，但已加载GUI模型仍必须验证其首次`[OBS_SCHEMA_BEGIN]`输出。工具能逐行比对完整索引和名称，合成输出比对已测；尚无真实输出，因此**运行时schema待真实仿真验证**。观测函数源码变化会使离线契约检查失败，要求重新审计。

Reward ID是为当前ALP配置新建的版本标识，独立于Observation Schema。五个可加分量为wait、grade_action、grade_2h、grade_shift、production；其余map键是诊断信息，不能重复加进总奖励。

- `wait=-1*clip((delta_wait_vehicle_seconds/9)/200,0,1)`；等待积分包含仍在排队的车辆，单位vehicle-seconds。
- `deviation=clip(abs(gap)/allowance,0,3)`；gap=0.27-grade，gap<0时allowance=0.28-0.27，否则为0.27-0.26。`gradeReward=clip(1-deviation,-1,1)`。
- 每个7200秒窗口以实际已完成破碎的吨数/金属量结算。前3窗由crusher积分推进和advanceCompletedGradeWindows关闭，另有120分钟周期event调用推进检查；第4窗由班末函数关闭。加权窗口Reward为1*gradeReward，先积入pending，随下一次DECISION/END报告，窗口事件本身不生成Gym step。
- `grade_shift=6*gradeReward(班次gap)`，`production=-4*clip(1-crusherOreTons/16000,0,1)`，均在班末结算。
- `grade_action`在当前动作响应后计算，存入pending，到下一次DECISION/END才归属这次动作。矿石：窗口及班次加入名义品位、expectedTons=max(1,capacity)的反事实改善，各clip到±0.10，按0.70/0.30混合后乘0.15；priorTons=max(20000,expectedTons)。废石：`-0.02*clip((班次进度-矿量进度)/0.05,0,1)`。其中20000是当前ALP真实先验参数，未从旧项目推断；接近耗尽时动作奖励仍按capacity估计，未擅自改变此规则。

START(previous_action=-1)只有观测和首个动作，Reward为0。Gym的一个transition是“上一START/DECISION观测及其返回action → 下一DECISION/END观测及其transition_reward”。决策是全系统事件驱动，不保证下一请求仍来自同一车辆，允许同时刻的连续决策和0秒时间差。episode_id/run_index/seed保持一致，request_id不可复用为不同内容，decision_sequence按0、1、2…连续，previous_action必须匹配上一响应。128步rollout边界既不生成AnyLogic事件，也不改变这一归属关系。

Python独立核验五项之和、wait积分、窗口吨/金属/品位/gap/raw/weighted/违规标志、grade_2h与本次窗口列表之和、terminal raw/weighted品位、矿量比例和产量缺口，所有奖励及诊断量必须有限。grade_action验证可报告范围和归属；完整反事实计算的真实业务结果仍待仿真对照，不声称Python已重放生产系统。

5. **导入、路径和依赖完整性**

验证解释器：`/home/jinx/miniconda3/envs/DRL/bin/python`（Python 3.11）。系统默认Python缺少训练依赖，因此所有训练模块/测试命令均明确使用DRL解释器；未改动用户conda环境、未安装额外包。requirements锁定SB3 2.9.0、NumPy 1.26.4、Gymnasium 1.3.0、Torch 2.11.0、grpcio 1.82.1、grpcio-tools 1.80.0、protobuf 6.33.5、TensorBoard 2.20.0、pytest 9.1.1，逐项与已安装版本匹配。当前Torch为2.11.0+cu128，符合2.11.0依赖约束；合成测试在CPU运行。

`python`包内全部模块（含generated）可导入；`python -m python.train --help`成功，compileall成功。不存在对缺失算法的运行时导入，也不需要sb3-contrib。递归import和路径清单见`docs/phase1_inventory.json`，包含proto-src生成源码、构建产物及JAR条目。旧CPython 3.10的__pycache__只是复制残留，不作为协议或源码权威。

Python生成代码要求protobuf 6.33.5及兼容gRPC运行时；Java使用protobuf 3.25.3、gRPC 1.64.0，Maven --release 11。两种语言的库主版本不必相同；本次用完整FileDescriptorProto验证wire协议一致（仅消除不同protoc版本对默认json_name的显式化差异）。Java描述符提取在本机JDK21执行，不等于已在AnyLogic嵌入JVM测试。

唯一权威proto为`proto-src/src/main/proto/dispatch.proto`，`proto/dispatch.proto`仅镜像。`tools/regenerate_protocol.py`重生成Python、修复相对导入、Maven离线构建、提取并对比Java/Python描述符、复制dist并写manifest。Maven离线构建依赖本机已有缓存；全新机器需先准备Maven依赖。当前dist和target JAR SHA256均为：

`7fe4d7dc6db1fc0705d1ad2c9170133d3df15d42696ed86ecb63269316af2218`

原dist为`85acafc080d039c71fb48c37b38c80a0bc2dbf585db2136d49d836fabcfa82f4`，原target为`560e32483f5864222e2ed871ec9039f02ae5b0c9cce0bf0dc08942d4d10dca54`。原两者都可见请求15..18字段，但哈希不同不足以证明旧dist语义错误；已用重新构建和描述符核对消除歧义。

当前目录的.git是受限占位目录，不能运行git status或提交；本阶段未创建commit。

6. **测试通过与失败项目**

最终验收命令：

```bash
/home/jinx/miniconda3/envs/DRL/bin/python -m pytest -q test --junitxml=docs/phase1_tests.xml
/home/jinx/miniconda3/envs/DRL/bin/python -m python.alp_audit
/home/jinx/miniconda3/envs/DRL/bin/python -m python.train --help
/home/jinx/miniconda3/envs/DRL/bin/python -m compileall -q python test tools
```

最终 **46 passed，0 failed，0 skipped**；JUnit证据为`docs/phase1_tests.xml`。

覆盖模块导入、1519D float32、schema/长度/NaN/Inf/溢出/ego/mask/one-hot、schema日志比对、Reward分量及窗口、请求响应序列化、相关ID/sequence/上一action/时间差、窗口顺序与数量、班末时刻、重复请求和非法动作、终止后请求、seed manifest、过期proto/JAR/Python生成文件拒绝、ALP函数漂移拒绝。

真实gRPC测试在本机127.0.0.1临时端口运行，客户端和服务端都使用生成stub，按START→DECISION→END与Gym reset/step交互，核验终止ACK及预算耗尽后的无新episode reset。初次普通沙箱执行因socket Operation not permitted失败；通过本机测试执行权限后同一真实回环测试通过。这不是AnyLogic链路测试。

合成PPO分别检查episode长度140、5+6、128、129、260以及3步time-limit；包含满rollout继续同一episode、一个rollout多个episode、单样本尾部、多个满rollout、真正终止及time-limit bootstrap边界。独立递推核对GAE；核验所有transition实际参加optimizer更新、尾部未丢弃、critic/actor参数更新、最终日志包含train值、最后终止样本已优化后才保存、保存加载权重一致、同实例二次learn拒绝。RolloutDebug实际生成128+12的NPZ/JSON快照，StageStatistics输出实际episode记录。仅合成环境发生PPO优化和临时模型保存，未运行生产训练。

未验证项目统一为**待真实仿真验证**：AnyLogic GUI编译及缺失资源解析、Loaded ALP身份、真实1519字段输出、真实Reward轨迹、道路/车辆统计范围、9辆车初次派车与串行20次运行、28800秒终止事件与实验停止的执行顺序、仿真阻塞等待动作期间的全局时钟行为、耗尽后不再派车到班末的完整流程。没有把这些列为测试通过。

7. **受保护核心SHA256**

修改前：`8e4cfa31c622f5e33756e304eea3f7526547db72ae93f7d9f00808845d61ef96`

完成后：`8e4cfa31c622f5e33756e304eea3f7526547db72ae93f7d9f00808845d61ef96`

完全一致。测试还将该摘要固定为断言；没有修改Actor/Critic更新、rollout收集、Bootstrap、GAE、尾部缓冲、优化参与计数、最终日志刷新和保存保护逻辑。

8. **下一阶段动作掩码与PPO联调建议**

先补齐GUI所需真实资源并确认使用当前ALP/dist JAR；以obsDryRun导出首次完整schema日志，运行`python -m python.alp_audit --schema-log <日志路径>`逐字段核对。先做短时通信检查和一次完整班次，核对真实START/DECISION/END、窗口及Reward记录，仍不加载旧31D模型。

然后在SB3 2.9.0普通ActorCriticPolicy的Categorical分布层实现mask：采样、predict、evaluate_actions/log_prob/entropy使用相同19..22切片，动作概率归一化只在合法集合内进行。保留普通PPO损失、Actor/Critic优化和受保护collector；不可在env中替换动作，否则存入rollout的action/log_prob与执行动作会失配。终止全零mask观测应允许critic求值；不得把它作为正常动作状态，价值预测不能依赖mask存在合法动作。

用混合mask/接近耗尽/全点耗尽/终止全零mask合成案例核验采样、重算概率和保存加载，再与真实仿真联调。真实仿真还应确认partial payload、无材料车辆等待到班末及simultaneous events。大规模训练前可另行评估1519D快照与桥接重复请求缓存的内存占用；本阶段未改变原缓存生命周期。

本阶段到此停止，不启动正式训练。
