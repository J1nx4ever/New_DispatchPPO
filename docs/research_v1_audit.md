# 露天矿卡调度 V1.0 研究方案：只读理解与审计报告

审计日期：2026-10-22（Asia/Shanghai）。审计对象为本次工作区实际文件，包含暂存、未暂存及未跟踪内容，**不是仅审计 HEAD**。本报告及其字段附录是本轮唯一新增项目交付物；未修改原代码、ALP、奖励、训练配置或已有结果，未启动真实 AnyLogic 或生产训练。执行了现有单元测试，其中少量 Policy 回归测试在临时合成环境中执行 PPO 更新和临时 checkpoint 验证，不构成新的研究训练结果。

证据标签：**VERIFIED**＝源码或本次明确说明的离线检查直接支持；**APPROXIMATION REQUIRED**＝当前观测不能精确恢复目标物理量；**NOT VERIFIED**＝证据不足，包括尚未执行真实运行验证。静态源码一致性不等于运行模型一致性，合成测试通过不等于 AnyLogic 物理核验通过。

## 审计结论与版本身份

现有架构适合开展冻结的状态表征研究，**不需要重新设计 PPO、GAE 或 gRPC**。1519维原始契约、ego、Mask、FIFO余量及破碎速率提供了 P0 所需的状态；P0候选代码和训练/评估接线已经存在。但完整承诺物料 F1 尚未实现，Reward V1.0 尚未落实，当前不能直接开始正式 F0/F1 对照并宣称其符合研究设计。

本轮主要发现：

1. **VERIFIED**：1519个字段的名称、顺序、生成公式和来源与当前 ALP 静态展开一致；P0所用索引与缩放正确。
2. **VERIFIED**：`DispatchMaskedPolicy` 已支持1519/1525维；训练与评估已复用 P0 wrapper。`p0-smoke` 只有FIFO存量贡献，不能作为正式F1。
3. **VERIFIED**：ALP班末累计品位奖励仍为 `6 × gradeReward`，Python也强制验证该项；不符合V1.0“班末仅保留矿/废缺口”的要求。动作品位奖励默认关闭，独立废石缺口惩罚保留，二者没有混为一谈。
4. **VERIFIED**：P0时间/窗口一致性校验不完整，存在错误状态被当成有效投影的反例。
5. **VERIFIED**：评估入口仍强制本地 ALP 审计，未采用训练入口的RPC配置握手；当前离线 provenance 又与三个函数不符，因此当前 `evaluate.main()` 会在加载模型前失败。
6. **VERIFIED**：评估仅保留终端回调的 `closed_windows`，未累积全班四窗；联合生产达标率及完整窗口评价尚未形成正式评估输出。
7. **NOT VERIFIED**：没有本次哈希对应的真实P0状态对账、完整承诺物料批次标签、`no_new_dispatch` 条件仿真及1525维真实训练闭环验收。

| 身份项 | 本次读取值 |
|---|---|
| Git HEAD | `ef644fd82d019b7032a00f1f164e69ef0848b1dd` |
| 工作区 | 已有大量用户变更，包括ALP、训练入口、Policy和未跟踪P0包；HEAD不足以复现当前状态 |
| ALP | `anylogic/DRL-PPO.alp`，仓库内唯一 `.alp`；作为本次V4候选源码审计，未证实GUI实际加载身份 |
| ALP SHA256 | `330489397cd36f9c02f1cefd44c91eaf2df99fc4bc85e3c9cf6d7cd5ff6f1545` |
| 受保护核心 SHA256（前后相同） | `8e4cfa31c622f5e33756e304eea3f7526547db72ae93f7d9f00808845d61ef96` |
| observation schema SHA256 | `01d0f9af3c417229ef7f77f194b2d4b145b33452b2dfff98b6cb5cc255efd753` |
| ALP观测函数集合摘要 | `ba2cf5479b7530cb37273148df7577024f04a98f1ee7170cad725cb89b9645d0` |
| P0文件 SHA256 | `613cba193c91ede56a6afe627bdce8feed0310ced8bf4fbc3b66addf300665c8` |
| wrapper SHA256 | `f26fad791aac778cf60c5016e6f0ec88cbb04f8d5757b9f7e6eb101c1e790e47` |

本文源码位置以本次工作区行号为准。`ALP:L`统一指 `anylogic/DRL-PPO.alp:L`。完整1519项静态字段清单见[字段逐项附录](research_v1_observation_audit.md)，含每项公式、语义及实际ALP函数起始行。

## A. 项目架构理解

### A1. 实际训练交互链路

`AnyLogic 车辆需要派车 → Main.selectNextLoadSite → selectNextLoadSiteAI → buildObservation/buildPhysicalObservation → RLClient同步gRPC → DispatchService → DispatchCallbackBridge → DispatchEnv → 可选FIFOObservationWrapper → Monitor/DummyVecEnv → DispatchMaskedPolicy/EpisodeBudgetPPO → action返回 → ALP预留装载任务并运行至下一决策/班末`。

主要证据：ALP `selectNextLoadSiteAI`（3537）、`buildObservation`（3367，3377转物理观测）、`buildPhysicalObservation`（8079）；`python/dispatch_service.py:12`、`python/dispatch_bridge.py:92`、`python/dispatch_env.py:54`、`python/train.py:421`。

**VERIFIED**：集中式单智能体事件调度，一次为一辆ego选择4个装载点之一。Actor观察所有车辆、站点、FIFO和路网。Action 0/1/2/3分别HG1/HG2/LG/WASTE（ALP:2930–2951）。Mask取决于非终端且站点可预留吨位>1e-6，不应扩大解释为所有交通/卸载约束的即时可行性保证（ALP:8139后；`observation_contract.py:25`）。

ALP的 `enableOnnxDispatch` 是历史命名，当前训练路径实际为同步RPC，不能据此认定运行ONNX。仓库仍有旧结构观测、旧调用函数以及 `ExcludeFromBuild=true` 的装卸状态；它们不是当前有效PML装卸链路（ALP:13356–13461）。

START携带首次待派状态、零reward、previous_action=-1，并要求action；它不是一条先验transition。`reset()`将START保留为pending；`step(a)`响应pending，等待下一DECISION/END，再返回这次action之后累积的reward和新状态。**一次实际action构成一条transition**，事件间隔可能为0或不同秒数（ALP:3557–3682；`dispatch_env.py:75–125`）。

Bridge使用request_id幂等、连续sequence、previous_action、episode元数据、仿真时间差、四窗有序且仅一次结算、奖励和观测验证；回调处理线程与Gym主线程用ticket/event rendezvous。END无需动作，自动ACK，但仍进入Gym消费队列（`dispatch_bridge.py:113–129,201–317,330–406`）。

### A2. Episode、Reset、终止和种子

**VERIFIED**：480分钟＝28800秒固定时域，7200秒×4窗。`endSimulationEvent`在 `rlShiftSeconds/60` 分钟执行 `finishEpisodeAndNotify()`（ALP:2551–2575）。班末先推进破碎积分、关完4窗、算终端reward，然后发送 `terminated=true,truncated=false` 的全系统物理终端观测并finish（ALP:7209–7477）。这是真正任务终止，不是以TimeLimit truncation处理的班次。

Python实际使用 `ParameterVariationEpisodeRunner`，每个 `reset`等待AnyLogic实验创建新replication，而不是Python重置旧仿真对象。达到预算后的DummyVecEnv自动reset返回缓存终端状态并标记 `experiment_complete`，不会启动第N+1班（`episode_runner.py:15–40`、`dispatch_env.py:64–87`）。另有逐班启动外部进程的 `AnyLogicEpisodeRunner`（同文件43起），当前train未采用。

当前 `RL_Training` 串行20 runs、无额外replication、ModelTimeUnit=Second、FinalTime=28800；同时间戳选择LIFO（ALP:22783起）。有效参数：currentDispatchPolicy=3、deterministicCheck=false、usePhysicalObservation=true、useEndogenousCongestion=true、speedDtSec=0.2秒。有效run_index=`index+1`，seed=`202610160011L+index`；Main启动时用experimentSeed重置默认RNG（ALP:46），矿块品位另用按siteId派生的RNG（ALP:20332）。PPO seed与仿真seed分开；PPO seed不会替代AnyLogic seed。

### A3. 普通PPO与受保护收集器

| 参数 | 当前新训练值 | 证据 |
|---|---|---|
| SB3 | 必须2.9.0 | `masked_policy.py:23`、`episode_budget_ppo.py:151` |
| rollout / batch / epochs | 128 / 默认32 / 10 | `train.py:150–153,446–463` |
| learning rate / entropy | 默认3e-4 / 0.01 | 同上 |
| gamma / GAE lambda | 0.995 / 0.95 | `train.py:453–454` |
| clip / vf clip / advantage norm | 0.2 / None / True | `train.py:455`及本地SB3默认 |
| Actor / Critic | 各[128,128]，Tanh、FlattenExtractor | `train.py:457`及本地ActorCriticPolicy默认 |
| optimizer / vf_coef / max_grad_norm | Adam / 0.5 / 0.5 | 本地SB3 2.9.0构造默认 |
| target_kl / use_sde | None / False | 本地SB3构造默认 |
| 预算 | `--episodes`必填；`learn(total_timesteps=2**62)`只是上限占位 | `train.py:141,472` |

**VERIFIED**：gamma按事件transition折扣，delta秒只是info，不做连续时间折扣。不能称当前实现已是按时间折扣的SMDP-PPO；本研究保持其现状。超大total_timesteps也不是实际训练transition预算。比较样本效率应同时报告班次数和实际transition数。

`EpisodeBudgetPPO`保留上游PPO loss/train，修改的是精确班次预算收尾与审计收集过程。正常128步后GAE并更新；最后一班的terminal先 `rollout_buffer.add`，再停止收集；不足128步时创建仅含真实样本的短buffer，计算GAE、完成最后更新和日志刷新后才保存。callback不能在最终terminal通过返回False丢掉尾样本（`episode_budget_ppo.py:72–129,198–282`；`train.py:70–130`）。

普通rollout未终止时用新状态Critic bootstrap；跨真实terminal时GAE由done截断。time-limit路径保留 `reward += gamma*V(terminal_observation)`，当前ALP正常班末不走它（核心:217–230,250–274）。终端mask全零只供Critic；Actor遇到终端会报错，`predict_values`保持上游实现（`masked_policy.py:36–51,97`）。

**VERIFIED（结构分析）**：wrapper置于DispatchEnv之外、Monitor/VecEnv之内时，reset和step（含terminal）均追加6维，DummyVecEnv保存的 `terminal_observation` 因而也是1525维；buffer按observation_space分配，无需改GAE或collector。现有1525 mask测试与1519收集器测试不能替代1525终端/partial-rollout整链验收，后者 **NOT VERIFIED**。

### A4. 本次离线检查的实际结果

使用 `/home/jinx/miniconda3/envs/anylogic-env/bin/python -B`，关闭pyc及pytest cache写入。执行6个测试文件：`test_window_projection`、`test_masked_policy`、`test_contracts`、`test_reward_v4`、`test_runtime_configuration`、`test_evaluate`。

首次结果：**114 passed / 4 failed**。其中本地gRPC绑定端口受沙箱限制，获准在沙箱外单独复跑后 **1 passed**；其余3项真实失败为 `test_alp_and_artifacts` 和on/off两个 `test_alp_ablations_from_temporary_copies`，均在 `validate_alp_contract` 报 `Main.selectNextLoadSiteAI` 未审计变化。故118项中115项已通过、3项未通过；不是“全部测试通过”。P0文件本身9项全部通过，未运行真实仿真。

进一步只读枚举发现，provenance覆盖外的函数共3个：`Main.selectNextLoadSiteAI`、`Main.finishEpisodeAndNotify`、`Main.buildRewardConfigComponents`。现有测试遇到第一个即停止；不能只登记第一个摘要就宣称审计恢复。对比HEAD可见selectNextLoadSiteAI新增了waste字段、动作开关诊断及RPC配置map，本轮不更新或绕过provenance（`alp_audit.py:94–108`）。

## B. 1519维可重建性矩阵

### B1. 契约及逐项校验范围

**VERIFIED（静态）**：在内存中运行现有静态展开器，并拦截所有 `Path.write_text`，对1519项 `index/name/formula/source` 逐项比较，差异为0；未重写schema。展开器：`tools/build_observation_schema.py:1`。这同时确认模块区间：0–18全局、19–22 Mask、23–26候选吨位、27–1106车辆、1107–1294装载点、1295–1390卸载点、1391–1438 FIFO、1439–1518路网。

边界kind/accepted_range是Python附加规则，不是从运行轨迹测得的范围。`expected_range`含当前场景假设，不能当成ALP动态保证。`validate_observation`只对binary/unit/truck_slot等约束及one-hot、ego、terminal、Mask做检查，大部分scaled仅检查float32有限性；并不验证所有物理守恒、时间与RPC相等或所有字段互相一致（`observation_contract.py:30–69`）。

ALP生成值以float强转，经 `repeated float values` 传输，Python再转float32，没有全局裁剪（ALP:8089、`proto/dispatch.proto:53`）。因此“直接恢复”均指**在float32精度内恢复**，不等于恢复Java原始double。运行CSV比较函数只比较index/name，不证明缩放公式一致（`observation_contract.py:76–89`）；公式一致性还需版本/源码身份或定点值核验。训练默认不强制读取schema-log，schema_id相同也不能证明模型内容相同。

以下用 `T=27+120i`（i=0..8）、`L=1107+47j`（j=0..3）、`D=1295+48d`（d=0..1）、`F=1391+3k`（k=0..15）、`R=1439+5s`（s=0..15）。所有区间含端点。状态缩放下列均为原始obs到物理值的乘数；grade为质量分数，不乘100。

| 预测物理量 | 观测索引 | ALP源码位置 | 反归一化 | 是否可直接恢复 | 缺失信息 | 所需近似 |
|---|---|---|---|---|---|---|
| 已用/剩余班时 | 0,1 | collectPhysicalObservation:8120 | ×28800秒 | VERIFIED | Java时刻有float32舍入 | 约毫秒以下量级时间容差，按量化误差设定 |
| 当前窗口/剩余窗时 | 2,3 | 同函数:8122 | ×4取整数；×7200秒 | VERIFIED | 当前检查未保证与时间一致 | 必须交叉验证，不能默默修正窗口 |
| 当前窗已破碎吨/金属 | 4,5；无供料6 | 同函数:8125 | ×5000吨；binary | VERIFIED | 无 | 预测不得重复累计 |
| 班次已破碎吨/金属、废石 | 7,8,9 | 同函数:8128 | ×20000、×20000、×4000吨 | VERIFIED | 不等于所有已装载/到站量 | 无 |
| 计划、品位界限、终端、速度tick相位 | 10–18 | 同函数:8131 | 缺口/废目标×4000，矿目标×20000；13–18原值 | VERIFIED | tick周期/拥堵开关不在这19维完整给出 | 固定配置有来源及版本 |
| 可选动作及候选预留吨位 | 19–26 | 同函数:8140 | Mask原值；吨位×193 | VERIFIED | Mask不涵盖未来卸载容量 | 不改变Mask |
| ego、车型、阶段 | T+0..15 | Truck.appendDispatchObservation:15572 | binary/one-hot | VERIFIED | executionPhase字符串被离散映射 | 按12态映射，不能从旧状态图猜测 |
| 载重能力、loaded、ore | T+16..18 | 同函数:15614 | capacity×193，标志原值 | VERIFIED | 空车ore依赖已预留任务 | 先读状态再解释标志 |
| 已装载/未装完预留吨位 | T+19,20 | 同函数:15617 | ×193吨 | VERIFIED | 不含任务批次唯一ID | 状态互斥去重，不能与site reservation相加 |
| 已装载品位及已知标志 | T+21,22 | 同函数:15619 | 原值 | VERIFIED | 空载时隐藏payloadGrade不可读 | 不读取仿真内部品位 |
| 当前装载品位统计 | T+23..25 | 同函数:15621；obsGradeStats:20790 | 均值/标准差原值，inferred标志 | VERIFIED统计值；真实品位APPROXIMATION REQUIRED | 未揭露矿块品位 | 使用公开均值/条件已知部分，不称真实值 |
| 当前装载/卸载目标 | T+26..31 | Truck同函数:15625 | one-hot | VERIFIED | ego装载目标清空；未装载无dumpTarget | 从ore与目标站规则恢复，不给ego新任务 |
| 节点/位置/速度/加速度 | T+32..44 | 同函数:15627 | 节点one-hot，x/y×10000m，v×10m/s，a×3m/s² | VERIFIED | 隐藏自由速度因素 | 确定性动力学近似 |
| 路段、段剩余/路线剩余、路线次序 | T+45..78 | 同函数:15632 | 段one-hot；距离×10000m；order×16 | VERIFIED当前编码 | 尚未生成的后续路程、重复路段不支持 | 从固定路由规则生成后续段；禁用简单全程ETA替代FIFO |
| 同段顺序、初次派车前驱 | T+79..81 | 同函数:15648 | rank×9；predecessor×9−1；0为无 | VERIFIED | engine事件插入序、精确laneEntrySeq未直接暴露 | 同时事件需固定规则并标注近似 |
| 装载/卸载等待年龄 | T+82,83 | 同函数:15655 | ×28800秒 | VERIFIED | 不是服务剩余时间 | 不混淆等待与服务 |
| 已装载服务年龄/均值/物料起点 | T+84..86 | 同函数:15657 | age×600秒；mean×10分钟；start×30000吨 | VERIFIED公开量 | 预抽样duration、未装载任务未来起点 | 条件剩余时间及排队物料游标推进 |
| 卸载服务年龄/均值 | T+87,88 | 同函数:15660 | ×600秒、×10分钟 | VERIFIED公开量；精确剩余APPROXIMATION REQUIRED | delay实际抽样完工时刻 | 条件剩余，而非直接mean−age |
| 自由流统计 | T+89..91 | 同函数:15662 | 样本数×1000，均值/std原值 | VERIFIED统计量 | 当前腿真实速度factor不直接暴露 | 基于公开统计推断；无样本用有版本先验 |
| 4条运动历史 | T+92+7h..98+7h | 同函数:15666 | valid/front标志；age×28800；速度×10；加速度×3；gap×10000 | VERIFIED观测 | 不是全部交通历史/RNG状态 | 可用于交通近似，不读隐藏factor |
| 装载点可用/矿石/名义grade/半宽 | L+0..3 | LoadSite.appendDispatchObservation:20829 | 原值 | VERIFIED | 不等于未来实际矿块品位 | 未知均值按场景先验 |
| 源初始、剩余、预留、可用、已装吨位、cursor | L+4..9 | 同函数:20844 | ×30000吨 | VERIFIED | reservation不是额外一份物料 | 与truck交叉守恒，不双计 |
| 品位块大小/游标块相位/最后已知块 | L+10..13 | 同函数:20850 | block×500吨；fraction原值；非零block×60−1；grade原值 | VERIFIED公开摘要 | 不直接传完整obsKnownGrades/blockGrades | 未来块仅用已知摘要及条件先验 |
| 铲容量/占用/装载人数/在途人数 | L+14..17 | 同函数:20855 | 前三者原值；incoming×9 | VERIFIED | PML细粒度微事件状态 | 单铲事件模型，边界核验 |
| 每铲吨位/单铲分钟 | L+18,19 | 同函数:20859 | ×30吨；分钟原值 | VERIFIED | 当前服务随机factor | 均值公式0.70+singleServe×ceil(tons/bucket) |
| 装载队列/seize/service | L+20..46 | 同函数:20861 | 每9槽一组；非零×9−1 | VERIFIED成员和暴露顺序 | service按ID排序，不是完工排序 | 结合服务年龄求预计完工 |
| 卸载站可用/矿石/容量/占用/服务数 | D+0..4 | DumpSite.appendDispatchObservation:17777 | 标志原值，后三项×3 | VERIFIED | seize已占用但未卸载者需单独处理 | 不能occupied=service |
| FIFO存量、卸载预约、可用空间、容量 | D+5..8 | 同函数:17799 | ×500吨 | VERIFIED | reservation不是FIFO | B+Q+truckTons≤capacity；Q只作约束 |
| 破碎速率 | D+9（Ore=1304） | 同函数:17803 | ×2500t/h，再/3600 | VERIFIED | 配置未来变化不在当前P0版本内 | 固定rate场景；不能把5000尺度当产量计划 |
| 待准入锁/车辆 | D+10,11 | 同函数:17804 | binary；非零×9−1 | VERIFIED | free后的engine微事件排程 | 必须恢复锁，不能直接重复预约 |
| 卸载queue/seize/capacityWait/service | D+12..47 | 同函数:17806 | 四组9槽；非零×9−1 | VERIFIED成员及序 | service按ID排序；内部排程未暴露 | 三/二并行事件模型及条件剩余 |
| FIFO顺序、余吨、grade | F..F+2 | appendCrusherFifoObservation:17816 | valid原值、吨×500、grade原值 | VERIFIED | 无批次/车辆ID、无历史已破碎份额 | P0只需余量；P1–P3核验需离线批次追踪 |
| 路网端点、长度、限速、封闭 | R..R+4 | collectPhysicalObservation:8159 | 端点非零×9−1；长度×10000m；速度×10m/s | VERIFIED | 节点几何、固定路由/动力学参数并非全在80维 | 固定参数清单；公开状态推进交通 |

阶段映射（ALP:15593–15611）：0当前ego，1未首次派车，2去装载，3等装载资源，4装载中，5去卸载，6等卸载资源，7等缓冲容量，8已放行待预约，9卸载中，10完成/无料，11其他。卸载容量等待车辆通常已持有卸载resource，不能只按phase9计算resource占用。

不能从“未传RNG/已抽样服务时间”直接推出原1519维不满足业务所需的Markov性，也不能把“新增6维”描述成新增外部信息。研究命题应保持为同一公开观测的任务相关变换是否改善学习，需实验检验。

## C. FIFO和卸载事件流程

### C1. 实际物理配置

**VERIFIED**：9车分3组，每组3辆，载重91.7/147/193吨（ALP:3023–3030）。4装载点各单铲、初始储量各30000吨，HG1/HG2/LG名义品位0.38/0.30/0.15，WASTE为0；单铲基础服务0.45分钟，桶容/密度见ALP:2930–2951。矿块500吨、随机品位半宽0.005（ALP:19944–19973）。

Ore卸载并行3位，Waste并行2位，resource与delay容量同步设置（ALP `initDumpSite`:17325起）；Ore缓冲500吨、crusherRateTph=2500（ALP:16912–16939）。初始化传入的旧 `svcTime=2.5/2.0` **不是当前逐车型delay服务时长公式**。实际Ore均值1.8/2.0/2.3分钟、Waste为1.5/1.7/2.0分钟，随机乘 triangular(0.9,1,1.1)（ALP:17419–17438,18459）。

### C2. 从到站到破碎

有效PML连接为 `enterDump → queueDump → seizeDump → waitCrusherCapacity → delayDump → releaseDumpl → exitDump`（ALP:17050–17240）。**先seize资源、再等缓冲容量**；容量等待本身可占服务资源并延长后车等待，不能建成“先容量可用才进入resource队列”的另一套系统。

`waitCrusherCapacity.onEnter`按进入次序将车追加 `dumpCapacityWaitOrder`（ALP:19219–19229）。`tryAdmitDumpTruck`只检查队首，不允许小车越过不满足容量的大车；如果pending锁已置位，不再放行。Ore先推进破碎至当前时刻，再检查 `B+Q+payload≤500+1e-6`。通过则pending=true、记录obsAdmissionTruck、移除队首并free到delay（ALP:17709–17751）。

`delayDump.onEnter`复查准入锁与容量，将整车吨位加入Q，记录卸载开始时刻、结束等待积分、置DUMPING，然后清锁并尝试下辆（ALP:18483–18549）。注意只有此刻开始卸载，之前的resource/capacity等待都算dump wait。

delay结束、release资源、exitDump触发 `Truck.onDumpingFinished → DumpSite.completeUnloading`；矿石调用 `receiveCrusherBatch`，废石调用 `recordWasteDelivery`。之后清车上载荷并发送restart重新派车（ALP:18160–18169,15435–15471,17496–17524）。**并行服务下按实际完成事件顺序入FIFO，不按到站ETA、service槽位顺序或truckId排序**。

### C3. FIFO数据结构、积分与窗边界

`crusherFifo` 是 `ArrayDeque<double[]>`，每批只有 `[remainingTons, grade]`（ALP:16942–16952），没有永久batchId。`receiveCrusherBatch`先 `advanceCrusherTo(now)`消化旧料，再Q减整车吨位、`addLast`新批、B增加（ALP:17463–17489）；新料不会反向补算过去产量。

`advanceCrusherTo`按当前窗口边界切段，以rate/3600×时长形成处理能力。取 `peekFirst`，处理min(能力,批余量)，调用 `updateCrusherGrade`累计真实矿/金属及当前窗口量，再扣批余量/B；≤1e-9移除头批。正在处理的物料就是队首的当前剩余量，没有另外一份“破碎在制批次”应额外相加（ALP:17530–17627、`updateCrusherGrade`:3145）。

每段必须先积分并更新crusherClock，再结算边界。前三窗由 `advanceCompletedGradeWindows`关闭，第四窗在finish中关闭；`settleCurrent2hWindow`要求时钟恰在窗末，写吨/金属/grade/违规标志，然后index++、窗内累计归零（ALP:7078–7240）。一个批次允许跨窗，以实际处理份额划分金属，空窗grade=0并算低品位违规。

crusher tick周期0.2秒（ALP:17252–17294），还有建观测、卸载入料及准入时的lazy advance。预测P1容量释放不宜一律连续即时准入：实模还取决于下一次tick/其他触发推进及准入尝试。P0已有FIFO的固定速率积分本身不依赖这种准入触发频率。

班末严格截止：`receiveCrusherBatch/completeUnloading/onDumpingFinished`均在 `time>=28800`直接返回，不再记新增交付；已有FIFO积分到28800仍计入最后一窗。恰好边界卸入的新矿石不属于此前窗口。源代码这些业务守卫是VERIFIED；与实验FinalTime/terminal事件恰好同刻的引擎执行是否始终发送终端RPC仍需真实运行核验。

### C4. 同时间戳与物理核验边界

**VERIFIED**：实验显式LIFO（ALP:22789），局部函数先后关系可读；**NOT VERIFIED**：仅凭源代码不能列出所有PML资源释放、消息restart、tick、到站事件的全局插入顺序，更不能假设同刻按ID稳定排序。P1–P3应定义与实模一致的tie规则并专门核验，不应把服务槽位排序当引擎排序。

已有 `auditDumpBalance` 检查B=FIFO、Q=卸载中矿车吨数、received=crushed+B及金属守恒（ALP:17654）。这些聚合审计可以复用，但无法回答“某个决策时刻的某个承诺批次最终在哪窗破碎”，不能替代未来标签追踪。

## D. P0–P3实现差距与通过标准

### D1. P0候选代码的独立结论

可复用：`window_projection.py:68–196` 的Batch/Projection、decode_fifo、project_fifo_only；`observation_projection_wrapper.py:24–49`；`test/test_window_projection.py:9–115`。

**VERIFIED（给定有效状态和固定rate）**：P0正确读取FIFO顺序和队首余量；不加buffer/reserved/carried第二份物料；仅计算t之后增量；按窗分割吨/金属；6维严格 `[Qw/5000,Mw/5000,1,Qnext/5000,Mnext/5000,vnext]`，不裁剪；空FIFO仍valid，末窗next无效，班末双无效；异常通过raise暴露。遍历到班末的4窗是内部守恒计算，对外仍只有当前/下一窗。其数学积分与ALP固定rate FIFO相符，**不是完整承诺物料预测**。

缺口及本次可复现反例：

| 问题 | 本次观察 | 后续建议（本轮未修改） |
|---|---|---|
| 窗口滞后未拒绝 | 合成 `t=15000s,index=0,FIFO=100t@0.3` 被接受，特征为 `[0,0,1,0,0,1]`；吨数被分到window2，而“当前/下一窗”错误标有效 | 校验非终端时间属于当前窗，允许float32边界容差，交叉验证windowRemaining |
| 过早terminal未拒绝 | `t=100s,index=4,terminal=1` 输出全0无效位，未报错 | 校验terminal/time/index三者一致；不要以“无效位”掩盖数据坏状态 |
| 终端bit本地转换 | `bool(a[17])`本身不检查0/1；训练链raw validator通常会拦住 | 独立预测器公开入口也要明确输入契约，防止离线绕过 |
| 测试覆盖不足 | 现有9项包含跨窗、空、末窗、terminal、mass mismatch、洞、exact boundary、wrapper保真/维度；未全面覆盖16槽、rate/grade/NaN/负吨、time错位、班末残余等 | 补边界、变形/独立参考积分及错误路径；不能只增加镜像实现断言 |
| 固定常数与版本 | 当前有scale和contract_id，但未自动记录参数来源表/文件hash | 把来源ALP哈希、rate尺度、时域、FIFO编码及拟合数据=无写入manifest |

**NOT VERIFIED**：真实观测B/FIFO float32误差门槛适用性、边界舍入及真实运行投影对账。9项通过只能证实所覆盖的合成行为。float32时刻在接近班末可能舍入到28800；需要结合RPC double时刻进行一致性核验，但预测值仍只从1519维产生，不能暗中把RPC时刻变成第1520个输入。

P0启动合成研究没有物理信息阻断；开始真实对账前应补上述严格性检查及明确运行版本。进入P1前：独立积分器对所有有效合成状态守恒、错误状态明确拒绝；真实抽样状态对旧FIFO贡献在固定rate下误差符合float32误差预算，所有失败可定位，不能静默填0。ALP已有FIFO超过16槽直接抛错而非截断（ALP:17829），Python质量检查能发现大多数遗漏，但不等于已经测试过槽位溢出。

### D2. P1：卸载中和等待卸载

可复用B/Q/容量、4组车辆槽、pending锁、车上grade/吨位、dumpAge/dumpMean、车型，以及P0积分。建议新增独立 `CommittedStateDecoder`、`DumpEventProjector`、`ConditionalServiceResidual`（名称为接口建议，仓库目前无这些类）。

**APPROXIMATION REQUIRED**：实际预抽样服务时间未公开。对服务总时长 `S=mu×X`、X为triangular(0.9,1,1.1)，已执行年龄a，应采用 `E[S-a | S>a]` 等明确条件剩余估计；a低于最短时长时才退化为mu−a。年龄超过随机支持上界（加传输误差）应报错；不能把负remaining截0并声称正确。单次按条件均值推进的离散事件结果仍只是机理近似，不是最终Q/M的条件期望。

要保留先seize再容量等待、队首阻塞、pending微状态、Q予約、并行逆序完工、tick准入时相及废石资源。测试覆盖：3位并行后到先完、占用但未卸载、Q边界、队首大车/后方小车、同时完工、卸载恰窗边/班末、释放后仍正常退出。通过标准：确定性条件仿真事件/吨/金属逐项对齐；随机版误差按服务阶段、车型和离边界距离分层报告，并保留显式有效性语义。

### D3. P2：增加已装载运输任务

可复用当前路线order、段余距、各车运动历史、段限速、前车关系与车型；建议新增 `RouteResolver`、`TransportProjector` 并与P1事件日历耦合。不能独立估算每车ETA后一次排序就模拟FIFO。

**APPROXIMATION REQUIRED**：当前腿隐藏速度factor、后续路由/转段和加速度模型固定参数、同刻交通事件次序；`applyDynamicSpeed`使用车型自由速度、限速、跟驰/制动及拥堵开关（ALP:6370起、6490–6575）。原观测有丰富交通量，但不是完整引擎/RNG快照。当前开启内生拥堵，因此已承诺废石车辆不能从道路预测删除。

测试覆盖：单车多路段、前车制动、同路段入序、交汇/转段、关闭路段、不同车型、所有矿车/废石车共存、抵达卸载后容量联动；确定性基准对齐路段与队列事件，随机版报告ETA及入FIFO时间误差。通过标准：不读取真实factor或未来状态；no_new_dispatch的退出车辆不额外堵路/堵卸载位；近窗边误差单独报告。首版不需要GraphETA。

### D4. P3：增加已指派未装完任务

可复用 `reservedLoadTons`、loadTarget/ore、load queue/seize/service、单铲容量、bucket服务公式、loadAge/Mean、loadMaterialStart、公开品位统计；建议新增 `LoadEventProjector`、`ObservableGradeEstimator`、`CommittedMaterialProjector`组合P0–P3。

ALP在装载阶段抽取物料grade，而完成前obs不公开真实payloadGrade（ALP:20552、15587–15624）。正在装载者可用公开loadingGradeMean/std/inferred；去装/排队任务需随预测装载顺序推进公开cursor，再按已知块摘要/名义均值预测。不同车可能共享未知矿块，若后续发展到MC，必须建相关性，不能逐车独立抽grade。当前确定性首版不需要新增学习模型。

**APPROXIMATION REQUIRED**：未揭露块品位、未来服务随机性和交通干扰。测试：预留后尚在途、单铲队列、部分载荷、末尾尾矿、同块/跨块、先前观测可推知部分、空车无承诺、当前ego不承诺、源reservation和truck守恒。通过标准：承诺集合精确且无重计，未揭露真实grade永不作为输入，参数和近似有版本，P1/P2/装载部分联合闭环通过。

### D5. 三类核验与 no_new_dispatch

1. **合成/条件仿真**：可设计单次快照与无新增派车分支，保持已有任务执行，任务卸完沿正常退出通道停车。当前四动作接口没有stop/no-op，不能以非法action或暂停RPC模拟无新增派车；需要后续独立核验分支/工具，保留生产gRPC四动作契约。本轮未新增分支，也未修改ALP。
2. **正常运行批次追踪**：现有activeDecisionId可提供任务来源线索，但FIFO只有double[2]，没有完整加载→卸载→FIFO→跨窗破碎的批次ID；应另设只用于标签的任务/批次账本，统计决策时承诺集合的未来实际贡献。禁止把标签账本、真实预抽样duration、未知块grade传入fθ。
3. **后续新增调度干扰分析**：比较同一承诺集合在条件分支和持续PPO分支中的入FIFO时间、破碎份额与窗归属。对固定rate且已经在FIFO的P0集合，后来入料排在其后，通常不会改变这些旧FIFO批次的处理贡献；对尚未入FIFO的P1–P3集合，新增任务可改变道路和卸载顺序，不能拿正常持续派车的全部最终产量直接当反事实预测真值。

P0–P3是逐步扩展与核验，不自动构成四个独立算法消融。正式F1定义是完整承诺集合的no_new_dispatch投影；开发中P0特征仍用独立dev contract，不能静默更名成F1。

## E. F0/F1最小侵入接入方案

### E1. 已经落实的部分

| 位置 | 当前实现 | 审计结论 |
|---|---|---|
| `observation_contract.py:17–28` | raw=1519，agent=1525，Mask19:23 | VERIFIED，gRPC未拓宽 |
| `masked_policy.py:21–51` | 1519/1525维接受，Mask仍取原位置 | VERIFIED，不再写死1519 |
| `observation_projection_wrapper.py:24–49` | 拼接6维，原raw逐位保留；吨/金属非负且不裁剪到1 | VERIFIED |
| `train.py:160,373,421–425` | f0默认；p0-smoke包wrapper；禁止p0 resume | VERIFIED |
| `train.py:238–275,297–303` | resume模式/agent维度检查、manifest模式与投影ID | VERIFIED；新正式F1仍需专属版本检查 |
| `evaluate.py:274–289,341–342` | 从manifest恢复agent模式并用同一wrapper | VERIFIED观测转换；配置握手仍有缺口 |
| 独立 `inference_server.py` | 仓库不存在 | NOT VERIFIED，不应虚构已有服务；当前独立推理由evaluate模型预测路径承担 |

### E2. 审核后需要修改/新增的边界

**必须修改（后续阶段，本轮未执行）**：

- `window_projection.py`：补严格时间一致性检查和独立输入错误校验；正式F1由组合预测器实现，保留P0诊断语义。
- `observation_projection_wrapper.py`：接完整纯函数预测器与显式版本；terminal一致地追加6维；任何预测失败继续raise。
- `train.py`：显式区分f0、p0-smoke、正式f1；记录预测器源码摘要、固定参数/来源/拟合数据（无则写无）；新旧模式/同维不同语义模型禁止混载；保持wrapper在VecEnv内。
- `evaluate.py`：改为与train同样的RPC运行配置握手和锁定，local ALP审计保留显式选项；校验训练模型Reward版本/指纹；累积四窗，输出生产联合达标和各物理指标。
- `reward_contract.py`、配置/来源/相关测试及ALP人工操作：后续统一Reward V1.0，现有冻结w_grade_shift=6导致仅把ALP设0也会被Python拒绝。必须同步版本化，不能在Python接收后直接减奖励以绕过。
- `stage_statistics.py`及独立评价汇总：增加生产联合达标率、完整窗口指标、更新调用次数汇总。维持低频日志。

**可以只新增独立模块/测试**：公开观测decoder、条件剩余时间、装卸/运输事件投影、固定参数来源清单、合成参考积分、离线批次标签核验、干扰分析工具。必须以raw1519为预测输入；任务追踪仅在核验工具侧。若未来新增推理服务，必须调用同一观测变换工厂。

**严禁修改的核心逻辑**：`episode_budget_ppo.py`的收集、GAE、bootstrap、短rollout、终止收尾、PPO loss；上游SB3算法；4动作语义和Mask原索引；gRPC原1519协议。Policy现在已满足输入维度要求，正式F1仍为1525，无需为预测重写Actor/Critic。

“原网络结构相同”应准确表述为同样Actor/Critic隐藏层和训练超参；1525输入必然令首层权重数比1519多 `6×128×2=1536`，不能声称参数总数严格相等。正式两组从零独立训练，禁止把F0 checkpoint续训成F1。

### E3. 必需的整链验证（不改训练核心）

后续用1525维合成环境覆盖：reset、常规step、真实terminal、timeout bootstrap、跨episode完整rollout、1条/多条尾rollout、最后预算自动reset、checkpoint round-trip。断言collector收到的terminal_observation也是1525；Mask19–22和ego前缀不变；尾terminal进入更新，discarded_transitions=0；F0不进入预测器。真实AnyLogic接线验收另做，不把合成结果标为真实运行证明。

## F. Reward差异审计

### F1. 当前实际Reward

| 分量 | 实际公式/权重 | 触发与统计边界 | 与V1.0关系 |
|---|---|---|---|
| load/dump wait合并 `wait` | `-1×clip(ΔW/(9×200s),0,1)` | 每次下一决策及terminal结算；W是累计装/卸等待vehicle-seconds，包含尚未开始服务车辆的等待年龄 | 统计边界可保留；当前合并后clip，不等于两个分量各clip再相加 |
| `grade_2h` | `g=clip(1−clip(abs(target−grade)/allowance,0,3),−1,1)`；w=1 | 实际破碎每窗结算，下一callback交付，可一次携带多个窗 | 基本符合真实破碎窗结算；权重仍需V1.0统一冻结 |
| `grade_shift` | `6×g(班次target−grade)` | 仅班末 | **明确不符合**：V1.0禁止额外累计品位项 |
| `production` | `−4×clip(1−crushedOre/16000,0,1)` | 仅班末，按真实已破碎量 | 符合矿量缺口软惩罚结构，无超产奖金 |
| `waste` | `−4×clip(1−deliveredWaste/4000,0,1)`；目标≤0时0 | 仅班末，按完成卸载交付量 | 符合独立废石缺口惩罚；关闭gradeAction不能删除它 |
| `grade_action` | 默认开关false，函数最前返回0；若on，矿石动作按名义grade的窗口/班次虚拟配矿改进组合，w=0.15，clip=0.10，prior=20000t，范围±0.015 | 当前action之后的下一DECISION/END发回；WASTE分支直接0 | 当前默认off符合；auto模式允许on，不足以强制V1.0 |

证据：ALP `getCumulativeWaitVehicleSeconds`:7051、`selectNextLoadSiteAI`:3537、`settleCurrent2hWindow`:7078、`finishEpisodeAndNotify`:7209、`calculateGradeActionReward`:7504、`calculateShiftGradeReward`:8210、`calculateOreShortfallReward`:8226、`calculateWasteShortfallReward`:8246；Python `reward_contract.py:9–45,128–232`。

当前已实现gradeAction中的WASTE直接返回0；没有应继续保留的WASTE动作进度引导。启用时矿石项精确为 `0.15×(0.70×windowImprovement+0.30×shiftImprovement)`，两个improvement各自裁剪到±0.10（ALP:7580–7619）。独立waste终端项仍存在，这是正确区分。`--grade-action off`只是期望核验，**不会代替ALP关闭开关**；默认auto接受ALP传来的on/off（`train.py:146,351`）。

装载等待从enter/queue到delay开始，卸载等待包含queue、seize及容量等待，至delayDump真正开始；未开始服务的班末等待也结算。没有在RL总奖励中加入电铲idle项。当前terminal只按已破碎矿量处罚，没有另立“已采运矿量最低计划”的独立罚项；若V1.0要求两个不同矿石最低量，需要另行确认，不能擅加奖励。

### F2. 参数与未确认业务口径

**VERIFIED（当前源码）**：targetGrade=0.27，窗口界限[0.26,0.28]；矿班计划16000t，废班计划4000t，targetOreTons2h=4000t；破碎每窗最大能力5000t。targetOreTons2h在当前窗口品位reward公式中不作为独立产量达标奖励，5000是能力参考归一化尺度，不是4000的替代目标。

**NOT VERIFIED（业务冻结）**：用户本次任务没有给V1.0合规区间的具体数值，也没有独立签署参数文件，因此不能把当前[0.26,0.28]自动宣称为“V1.0已确认业务值”。应在冻结表中确认上下界、矿/废计划及wait/窗grade/缺口权重；若不同，报告差异并统一版本，不用旧场景代替。proto中 `violation_upper` 仍有旧 `gap < -0.02` 注释（`proto/dispatch.proto:77`附近）；执行代码已按0.28判断，该注释不能作为参数依据。

### F3. 后续ALP人工操作建议（本轮不实施）

| 精确位置 | 修改前→建议后 | 理由/影响 | 验证 |
|---|---|---|---|
| Main → Variables → `wGradeShift`，ID1790406210939，ALP:1294–1306 | 初值 `6` → `0`（或后续审定的等价明确关闭方式） | 消除班末累计grade项；班末仅剩矿/废缺口与最后等待/窗口结算；不改物理产量 | 必须同步新版Python契约/指纹；RPC config.w_grade_shift=0；终端grade_shift始终0且总reward可重算 |
| Main → Parameters → `enableGradeActionReward`，ID1792626220025，ALP:2426；RL_Training → Freeform参数对应同ID（22887附近） | Main默认false，实验空覆盖 → 明确保持/填写false | 保证所有动作gradeAction=0，独立waste项保留 | 每个callback flag=0且grade_action严格0；waste不足班末仍非零 |
| Main → gradeLowerBound/gradeUpperBound/各权重 | 当前0.26/0.28及上表值 → **待业务冻结后再确定，不给臆造替代值** | 决定奖励及评价口径 | 同一RPC配置、新版本参数表、四窗汇总一致 |

上述只是供审核的后续操作，不应现在单独改ALP再运行旧Python：`reward_config.py:57–62`会拒绝w_grade_shift≠6；`reward_contract.py:193–200`还会要求weighted=6×raw。来源哈希也必须在真正复核后更新，不应关闭校验。

## G. 实验复现要求

### G1. 应冻结与记录的身份

| 项目 | 当前已有 | 正式F0/F1应补充或明确 |
|---|---|---|
| ALP身份 | train可选local audit时记录磁盘hash，并明确runtime_verified=false | 每个实验批次归档一次V4源hash/编译导出身份，标明磁盘与实际运行关系；保持默认RPC配置，不要求每班上传ALP |
| Git | manifest含commit和dirty status | 当前dirty状态不能只记commit；保存实验源码快照或相关文件hash及diff归档 |
| predictor | 当前dev contract_id、raw/agent维度 | 完整版本、源hash、固定参数逐项来源/单位、拟合数据ID及划分；P0未拟合应写无 |
| Reward | contract_id、参数、动态配置与fingerprint | 新V1.0独立版本；F0/F1指纹相同且grade_action=off、grade_shift=0 |
| PPO seed | `train.py:328`，默认123 | 预先确定多个seed，两个组使用同一集合，不跨组resume |
| AnyLogic seed | seed manifest及hash；RPC逐班核对run_index/seed | 训练与holdout分离；不同策略同seed不保证不同路径后随机数逐项配对 |
| 班次数 | requested、callback实际completed、stage summary | 每个点仅用已完成班；异常/未完成班单列，不混入分母 |
| transition | model.num_timesteps、核心collected/updated/discarded | 同时报每阶段净计数及累计计数，比较事件数不只比较班数 |
| PPO更新 | 核心events含ppo_update_completed；SB3 train/n_updates | 明确“train调用次数/rollout更新”与“epoch计数/optimizer step次数”不同；保存低频汇总，不能把n_updates=10视为10个rollout |
| schema/通信 | raw schema_id、1519、agent_mode/1525、Mask位置、proto/JAR hash | 加schema JSON hash、实际运行字段/缩放证明和版本；相同ID不等于相同内容 |
| 完整性 | finish_audit，final terminal updated，final logger flushed | 断言实际所有transition参与更新，短rollout无空槽；保留核心hash |
| 评价 | train每episode四窗、吨位/等待、Reward分解 | 修复evaluate累积四窗和RPC配置，再输出以下指标 |

现有记录证据：`train.py:277–349,483–519`、`episode_budget_ppo.py:108–129`、`stage_statistics.py:85–178`。默认逐transition、全obs、rollout快照关闭（`train.py:158–159`）；继续只记录训练汇总、episode统计、异常和完整性计数。真实对账需要详细样本时单独显式启用，既有审计不删除。

### G2. 最终评价口径

- 主要结果：每窗grade合规率（供料为0按违规）、全班4窗全合规率；矿/废生产各自达标率及**生产联合达标率** `I(Qcrushed≥QorePlan 且 QwasteDelivered≥QwastePlan)`。不要把“生产联合”默默扩展成再包含grade；若需要另报“生产+品位联合”明确命名。
- 实际矿石破碎吨/金属、矿石完成卸载量/期末FIFO、废石完成交付吨与缺口；grade以破碎量加权，不能平均每车或每窗grade代替整体金属/吨比。
- 装载等待、卸载等待vehicle-seconds及总和；当前RPC提供合并delta_wait，训练记录仅有合并总量，若要分别评价需后续独立诊断字段或经核验的ALP汇总，不能由总wait奖励反推，因为clip不可逆。
- 学习曲线分别以实际transition、完成班次和PPO更新调用次数为横轴；报告达到预设阈值所需样本及多PPO seed不确定性。阈值、评估频率、总预算在实验前冻结，不预言F1胜出。
- 同一holdout环境seed集上配对比较F0/F1；固定评估deterministic/stochastic模式。对预测器另报Q/M误差、入FIFO时间误差、窗口归属错误、失败率，并区分条件分支/正常持续派车标签。
- 总回报为辅，不能用有额外grade_shift或不同gradeAction配置的回报直接证明输入表征改进。

**VERIFIED的评估缺陷**：`evaluate.py:116–175`每次step更新info，但 `closed_windows` 只在return时取最后info；已在先前callback交付的窗会丢失。`_summary:178–227`不计算完整四窗、废石与生产联合达标。`stage_statistics.py:96,121`在训练侧是跨transition累积窗，因此不是ALP没有四窗，而是评估汇总存在缺口。当前compare_heldout以矿量/班grade/总wait与规则策略配对（`compare_heldout.py:61–115`），也不是正式F0/F1联合指标评价器。

## H. 风险与阻断项

| 等级/阶段 | 项目 | 当前状态与退出条件 |
|---|---|---|
| P0合成开始 | 1519中FIFO/rate/时间是否足够 | VERIFIED足够，无需改ALP/协议或等待P3；现有P0可作为候选继续审查 |
| P0真实对账前 | 错误time/index被标valid、边界float32、输入守恒/槽位错误 | 补输入契约与边界测试，建立误差预算；不能以全部零特征掩盖错误 |
| P0真实对账前 | 运行模型身份及真实样本 | 当前NOT VERIFIED；使用当前RPC配置、schema一致性及已归档版本验证，取得真实快照对账证据 |
| 离线审计/现有evaluate立即阻断 | 3个函数provenance不匹配 | 本次3项测试失败；独立审阅全部差异后才能登记新hash，禁止跳过 |
| P1 | 并行卸载、先seize后容量、tick准入、条件剩余、同刻排序 | 现有观测大部分足够建近似事件模型；服务真实剩余不能精确恢复，必须声明近似并验证 |
| P2 | 隐藏速度、交通交互、路由、退出停车 | 固定配置清单+公开交通推进+条件仿真；保留废石交通 |
| P3 | 未揭露grade、物料游标、跨块相关性 | 仅公开条件估计；不得读取blockGrades或未公开payloadGrade |
| P1–P3核验 | no_new_dispatch条件分支及批次账本缺失 | 后续规划独立核验机制，现有四动作RPC没有合法停车动作；保证卸完不堵路/服务位 |
| 正式F0/F1前 | Reward V1.0未落实，grade界限业务值未签定 | 确认业务参数、新版Reward契约与Python/ALP一致，grade_action=0、grade_shift=0，独立废石项保留 |
| 正式F0/F1前 | 目前F1仍只有P0 | P1–P3完成、核验通过、纯函数与版本/来源清单冻结，才能启用正式f1模式 |
| 正式F0/F1前 | evaluate仍依赖强制local ALP和默认off配置 | 复用训练RPC握手与模型指纹检查；本地审计成为显式离线选项 |
| 正式F0/F1前 | 四窗/联合指标/分项wait输出不足 | 完成评价输出与口径核验，不依赖raw return代替物理指标 |
| 正式F0/F1前 | 1525终端/短rollout/保存整链证据缺失 | 外围集成测试及真实接线验收通过，保护核心hash不变 |

建议审核顺序为：先确认本报告中的源码版本和业务冻结参数，再审查P0严格性与真实对账方案，随后按P1→P2→P3逐级开发；正式F0/F1训练统一安排在Reward、预测器与评价链路冻结之后。本轮不执行上述开发和训练。
