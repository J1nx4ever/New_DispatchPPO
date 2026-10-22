# Reward V1.0状态可重建性审计与P0 FIFO窗口投影

审计日期：2026-10-22。范围是当前工作区的Reward V1.0、1519维观测、FIFO存量投影；未执行真实AnyLogic运行或生产训练，未修改ALP、gRPC、Reward及受保护PPO核心。已有开发用wrapper保留，但本轮没有将P0接入正式训练，也没有启动既有 `p0-smoke` 训练入口。

结论用 **VERIFIED**（源码/所列离线验证直接证实）、**APPROXIMATION REQUIRED**（只能估计）、**UNAVAILABLE**（当前单次公开观测不能精确取得）、**NOT VERIFIED**（尚无实际运行证据）区分。后两者不同：隐藏真实服务时间是未公开信息，GUI加载身份则是尚未核验。

## 1. 当前版本和总体结论

| 项目 | 本轮核对 |
|---|---|
| 最新ALP | `anylogic/DRL-PPO.alp` |
| ALP SHA256（修改前后相同） | `f69fea9e0853270637c85b661a65af21d25cb09403f56765bdc9e4c6bb8ca691` |
| Reward | `dispatch-reward-v1.0`；当前ALP完整离线契约审计通过 |
| 奖励参数 | grade目标0.27、范围[0.26,0.28]，矿16000t/废4000t；gradeAction开关false、wGradeAction=0、wGradeShift=0 |
| 原始schema | `dispatch.physical.v3`，1519维，schema SHA256=`01d0f9af3c417229ef7f77f194b2d4b145b33452b2dfff98b6cb5cc255efd753` |
| ALP观测函数集合摘要 | `ba2cf5479b7530cb37273148df7577024f04a98f1ee7170cad725cb89b9645d0` |
| P0版本 | `dispatch.physical.v3+fifo-p0-dev.v2`，非完整承诺物料F1 |
| 固定参数与来源 | `python/window_projection_parameters.json`，记录ALP/schema哈希、源码函数、单位、误差预算、无拟合数据 |
| PPO核心 SHA256（前后相同） | `8e4cfa31c622f5e33756e304eea3f7526547db72ae93f7d9f00808845d61ef96` |

**VERIFIED**：当前1519维公开观测足以恢复P0需要的FIFO顺序、每批余吨/品位、当前窗口、班末截止及破碎速率。P0不需要近似车辆ETA、装卸服务时间或未揭露品位；不存在通过新增内部字段补齐P0状态的必要。它是从既有观测计算任务相关表征，不新增未来信息，不预先判定1519维不满足Markov性，也不预言有学习收益。

本轮将ALP静态展开器在内存中执行，拦截其文件写入；与当前schema逐项比较1519个 `index/name/formula/source`，差异为0。展开器对one-hot、truck槽和FIFO等有模板，关键公式另外直接核对了ALP。完整字段清单可沿用[1519项字段附录](research_v1_observation_audit.md)：本轮重新比对通过，观测函数摘要未变。该附录的旧研究总报告属于历史审计；本报告确认当前ALP已完成Reward V1.0参数迁移，不能继续套用历史“ALP奖励待修改”的结论。

**NOT VERIFIED**：磁盘ALP与GUI运行模型的相同性、当前版本真实快照的P0对账。离线source/schema通过不等于已运行AnyLogic验证。

## 2. 逐项索引、单位与可重建性

以下索引是0基闭区间。缩放均是观测值恢复物理量的乘数；除one-hot外，0编码ID表示无对象，非零 `id=round(9x)-1`。原始传输为float32，因此“直接恢复”指传输精度内恢复，不能恢复Java double舍入前的最后若干位。

### 2.1 P0直接使用的全部字段

| 字段 | 索引/恢复公式 | ALP生成位置 | 判定和注意事项 |
|---|---|---|---|
| shiftElapsed | 0，`x×28800 s` | Main.collectPhysicalObservation，ALP:8120 | VERIFIED；接近班末可能舍入到1，不能独自判断终端 |
| shiftRemaining | 1，`x×28800 s`，当前时刻候选 `28800−remaining` | 同函数，ALP:8121 | VERIFIED；用于三时钟一致性及提升近班末精度 |
| windowIndex | 2，`x×4`必须为整数0..4 | 同函数，ALP:8122 | VERIFIED；0..3活动窗，4表示所有窗口已关闭 |
| windowRemaining | 3，`x×7200 s`，时刻候选 `(index+1)×7200−remaining` | 同函数，ALP:8123–8124 | VERIFIED；非终端必须正；终端为0 |
| terminal | 17，严格0或1 | 同函数，ALP:8138附近 | VERIFIED；与time/index共同检查，不能用bool任意非零转换 |
| bufferTons | 1300，`x×500 t` | DumpSite.appendDispatchObservation，ALP:17799 | VERIFIED；等于FIFO总余吨，不是独立一份物料 |
| crusherRate | 1304，`x×2500 t/h`，再除3600得t/s | 同函数，ALP:17803 | VERIFIED；2500是缩放尺度，实际rate从观测恢复，不用硬编码2500代替观测 |
| fifo.k.valid | `1391+3k`，k=0..15，严格0/1 | DumpSite.appendCrusherFifoObservation，ALP:17816–17850 | VERIFIED；所有有效槽必须连续位于开头 |
| fifo.k.tons | `1392+3k`，`x×500 t` | 同函数 | VERIFIED；为该批尚未破碎的余量；有效槽必须正 |
| fifo.k.grade | `1393+3k`，质量分数原值[0,1] | 同函数 | VERIFIED；不乘100，不作为金属吨直接使用；金属吨=余吨×grade |

P0导入时核对上述所有使用字段，包括全部16个FIFO槽的名称/位置，原始向量必须为 `(1519,)` 且全部值有限并可表示为float32。独立预测器不替代原始全系统业务观测校验；实际RPC继续由 `observation_contract.validate_observation` 验证schema、ego和Mask（`python/observation_contract.py:34–69`）。

### 2.2 其他物理量：哪些直接恢复、哪些只能估计

令 `T=27+120i`（i=0..8），`L=1107+47j`（j=0..3），`D=1295+48d`（d=0..1），`R=1439+5s`（s=0..15）。下表覆盖所有模块；每个展开后的具体字段公式见1519项附录。

| 状态 | 索引及反归一化 | 判定 | 不能混淆/缺失内容 | 源码 |
|---|---|---|---|---|
| 当前窗已产吨/金属/无供料 | 4,5各×5000t；6标志 | VERIFIED | 是已实现产出，P0绝不能再次加上 | Main.collectPhysicalObservation，ALP:8125 |
| 累计已破碎矿/金属/已交付废 | 7,8×20000t；9×4000t | VERIFIED | 已装载量和到站量不能替代破碎产出 | 同函数，ALP:8128 |
| 废缺口/矿目标/废目标 | 10×4000；11×20000；12×4000t | VERIFIED | 计划和缩放尺度是两回事 | 同函数，ALP:8131 |
| 品位范围/目标、确定性标志、速度tick相位 | 13..18原值；17为terminal | VERIFIED | 相位不能独自恢复tick周期/全部动力学参数 | 同函数，ALP:8134 |
| Mask/可指派吨位 | 19..22原值；23..26×193t | VERIFIED | Mask由可预留物料判断，不保证未来卸载无等待 | 同函数，ALP:8140 |
| ego/车型/阶段 | T+0..15，标志/one-hot | VERIFIED | 12态来自当前观测映射，不能使用被ExcludeFromBuild排除的旧状态图 | Truck.appendDispatchObservation，ALP:15572–15613 |
| 容量/loaded/ore/载荷/预留装载吨位 | T+16×193t；17,18标志；19,20×193t | VERIFIED | 车预留与站点预留是同一任务的不同视图，不可相加 | 同函数，ALP:15614 |
| 已装矿品位 | T+21已知标志、22原值 | VERIFIED | 空载时真实payloadGrade隐藏，只能读公开统计 | 同函数，ALP:15619 |
| 装载中品位均值/std/inferred | T+23..25原值 | VERIFIED统计量；真实grade需近似 | 未推知矿块不能反查真实blockGrades | 同函数，ALP:15621；LoadSite.obsGradeStats:20790 |
| 装/卸目标、当前节点 | T+26..40，one-hot | VERIFIED | ego装载目标清空；未装载者卸载目标未直接编码 | Truck同函数，ALP:15625 |
| 位置/速度/加速度 | T+41,42×10000m；43×10m/s；44×3m/s² | VERIFIED | 当前速度不是未来匀速ETA | 同函数，ALP:15628 |
| 当前段/段余距/路线余距/路线次序 | T+45..60 one-hot；61,62×10000m；63..78×16 | VERIFIED当前编码 | 未生成的下一腿路线需固定路由规则；精确交通未来需近似 | 同函数，ALP:15632 |
| 同段排行/首次派车标志/前驱 | T+79×9；80标志；81 ID编码 | VERIFIED公开顺序 | 不等于完整引擎事件插入序 | 同函数，ALP:15648 |
| 装/卸等待年龄 | T+82,83×28800s | VERIFIED | 不代表剩余服务时间 | 同函数，ALP:15655 |
| 装载年龄/均值/物料起点 | T+84×600s；85×10min；86×30000t | VERIFIED公开量 | 已抽样服务总时长UNAVAILABLE，剩余时间APPROXIMATION REQUIRED | 同函数，ALP:15657 |
| 卸载年龄/均值 | T+87×600s；88×10min | VERIFIED公开量 | 应按服务年龄作条件剩余估计，不能一律mean−age | 同函数，ALP:15660 |
| 自由流样本数/比值均值/std | T+89×1000，90..91原值 | VERIFIED统计量 | 隐藏实际速度factor不能直接读；运输预测需近似 | 同函数，ALP:15662 |
| 四条运动历史 | T+92+7h..98+7h；标志，age×28800s，v×10，a×3，gap×10000m，front_v×10 | VERIFIED有限历史 | 不是全量历史，也不包含RNG状态 | 同函数，ALP:15666 |
| 装载点可用/类型/均值grade/随机半宽 | L+0..3原值 | VERIFIED | 名义grade不等于下一批真实grade | LoadSite.appendDispatchObservation，ALP:20829 |
| 初始/剩余/预留/可用/已装吨/cursor | L+4..9×30000t | VERIFIED | cursor按已分配物料顺序；源预留不是FIFO | 同函数，ALP:20844 |
| 块大小/块相位/最后已知块/grade | L+10×500t；11原值；12非零×60−1；13原值 | VERIFIED摘要 | 不公开完整矿块数组/已知块字典 | 同函数，ALP:20850 |
| 铲容量/占用/装载数/在途数/桶吨/单铲时间 | L+14..16原值；17×9；18×30t；19分钟原值 | VERIFIED | 服务均值可计算，实际随机抽样不能恢复 | 同函数，ALP:20855 |
| 装载queue/seize/service | L+20..46，每组9个ID槽 | VERIFIED成员与暴露顺序 | service按truckId排序，不是完工顺序 | 同函数，ALP:20861 |
| 卸载站可用/接矿/并发/占用/服务数 | D+0,1标志；2..4×3 | VERIFIED | 等容量车可以已占用resource，occupied≠dumping | DumpSite.appendDispatchObservation，ALP:17777 |
| 缓冲B/预约Q/剩余空间/容量 | D+5..8×500t | VERIFIED | B是FIFO；Q是卸载预约；P0只算B的一份余料 | 同函数，ALP:17799 |
| rate/pending锁/pending车 | D+9×2500t/h；10标志；11 ID | VERIFIED | pending微状态属于P1，不能重复预约/入FIFO | 同函数，ALP:17803 |
| 卸载queue/seize/capacityWait/service | D+12..47，每组9个ID槽 | VERIFIED | P1要恢复先seize后容量等待、并行完成次序 | 同函数，ALP:17806 |
| 路段起终点、长度、限速、关闭 | R,R+1非零×9−1；+2×10000m；+3×10m/s；+4标志 | VERIFIED当前路网 | 后续交通、转段事件及隐藏速度仍需近似 | Main.collectPhysicalObservation，ALP:8159 |

**UNAVAILABLE（当前单次1519维）**：精确默认/分站RNG状态、预抽样服务完成时刻、未揭露矿块真实grade、隐藏自由速度factor、完整历史批次ID及其原始整车吨位、完整引擎同刻事件排程。不得通过ALP内部日志或未来标签把这些量变成P0输入。原FIFO double[2]也不保留原批次累计已破碎份额；不过P0只需余量，不需要原始吨位。

**APPROXIMATION REQUIRED**：P1–P3需要的装卸条件剩余时间、运输ETA及未来入FIFO次序、未揭露grade的条件估计。P0不使用这些近似。不能因有未公开随机变量就直接宣布整个原观测非Markov。

## 3. FIFO及观测更新时间的源码结论

1. `Main.buildObservation`在启用physical时调用 `buildPhysicalObservation`（ALP:3377）。后者先 `advanceCrusherTo(time(SECOND))`，再 `advanceCompletedGradeWindows`，随后collect并逐值强转float放入protobuf（ALP:8079–8095）。因此决策观测不是“上一次0.2秒tick遗留库存”。collect还要求 `crusherClockSec≈min(now,28800)`，误差不得超过1e-7s，否则抛错（ALP:8118）。
2. `crusherFifo`是 `ArrayDeque<double[]>`，批次为 `[剩余吨位,grade]`（ALP:16942）。`advanceCrusherTo`从 `peekFirst`处理，扣 `batch[0]`及B，耗尽后removeFirst；没有另外一个需要相加的破碎在制批次。**正在破碎批次＝当前队首余量**（ALP:17591–17624）。
3. 矿石在卸载完成时才进入FIFO：`completeUnloading → receiveCrusherBatch`；receive先积分旧料到当前时刻，然后Q减载荷，`addLast`新批、B加载荷（ALP:17463–17524）。新批不能补算过去产量。并行卸载按实际完成事件顺序入FIFO，不按到站ETA、truckId或service槽排序。
4. 出料积分按固定窗边界分段，先更新crusherClock后关窗（ALP:17565–17626）；前三窗由advance关闭，第四窗由finish关闭（ALP:7169–7235）。班末先积分到28800，关第4窗，再生成terminal观测，故terminal必须index=4、elapsed=1、remaining=0。
5. `evCrusherTick`周期0.2s（ALP:17252–17294），但建观测、卸载入料等调用也会推进积分；P0从同步后的观测时刻继续，不另加0.2秒延迟。`collectPhysicalObservation`本身只读业务状态，不能绕过build同步后直接拿旧库存。
6. FIFO公开槽按队列迭代顺序填充；无效槽尾部补0，超过16个槽直接抛错，绝不截断；并检查sum(FIFO)=B（ALP:17829–17850）。Python恢复全部16槽并交叉检查B，能发现遗漏批次引起的质量不一致；一条已被错误截断且B也被同步篡改的向量，单凭1519维无法识别其来源造假。

当前P0是固定速率流体积分。ALP内部使用1e-9t循环/移除阈值，Python保留所有正尾量以维持守恒；不宣称亚1e-9t级别逐位一致。跨窗归属精度还受float32时刻/吨位/grade舍入影响；这是明确的数值近似，不是车辆机理近似。

## 4. P0实现及输出契约

入口：`python/window_projection.py:199` 的 `project_fifo_only(raw)`。只读取原1519维、只使用带来源固定参数；不访问ALP运行进程、RPC时间、奖励标签、随机模型或预测未来状态。不修改传入数组。`decode_fifo`可独立用于诊断；预测入口始终开启FIFO/B质量检查。

输出 `Projection.features` 为float32六维，顺序严格：

```text
[Q_current/5000, M_current/5000, valid_current,
 Q_next/5000,    M_next/5000,    valid_next]
```

Q/M只包含观测时刻之后，当前FIFO**剩余物料**的贡献。当前已产吨/金属、卸载预约、车上矿石、未完成装载任务均不计入，不会把bufferTons再加第二份。grade直接为质量分数，金属吨按每批实际贡献吨×grade累计，不能先平均整批grade后切窗。

内部计算未来至班末四窗的贡献数组和最终未处理余量，是为了守恒与调试；agent特征仍只有当前/下一窗6维，既不输出全班最终产量，也不包括P1–P3承诺物料。

| 情形 | 特征语义 |
|---|---|
| 有效活动窗、FIFO空 | `[0,0,1,0,0,1]`（若下一窗存在）；零贡献是有效预测 |
| 第4窗活动、下一窗不存在 | 当前valid=1，尾部`[0,0,0]` |
| 28800秒terminal、index=4 | 六维0；双无效代表无未来考核窗，余料仍在诊断字段保留 |
| 数据错位、非有限值、无效rate、非法FIFO、质量不一致 | 明确ValueError/AssertionError，不返回全0掩盖失败 |

5000t是固定归一化参考，Q/M都除5000，不裁剪。当前物理缓冲500t使正常P0值通常小于0.1；实现仍不将其硬编码成上限。测试中另用超出本场景的6000t合成负载确认无裁剪，该例不代表当前ALP可容纳6000t。

### 数值校验与时间解码

- 交叉验证0/1/3三个时钟的float32半ULP误差区间是否相交，再选择误差最小的时刻候选；windowIndex仍严格取观测值，不用时间去“修复”滞后index。窗口下界/上界、terminal/time/index也联查。1e-9s是double算术容差，记录在参数文件。
- 这使 `t=28799.99999s`、elapsed已舍入到1但remaining仍正的合法末窗观测仍能产生极小正贡献，不会提前置terminal。三时钟冗余提高精度，并非增加1519维之外的信息。`observation_time_error_seconds`记录选择时钟的保守误差；正常窗口时刻的最坏半ULP上界约0.43ms。
- B与槽吨位的容差为ALP已有1e-5t，加B和每个槽各自float32半ULP×500。没有用零reward推断容量或rate，也没有为质量差异默默补料。
- 诊断返回初始FIFO吨/金属、班末余吨/余金属、每窗增量；断言 `ΣQ+余吨=初始吨`、`ΣM+余金属=初始金属`。数值断言容差2e-6t、相对1e-8属于实现数值选择，已明确登记；测试还采用更严格绝对误差。

纯函数使用示例（无需PPO或Gym训练）：

```python
from python.observation_contract import validate_observation
from python.window_projection import project_fifo_only

raw = validate_observation("dispatch.physical.v3", received_obs_values)
projection = project_fifo_only(raw)
z = projection.features  # shape (6,), raw仍是1519维
```

已有Gym wrapper仅随之更新dev contract到v2，避免同为1525维却加载旧语义模型；未修改train/evaluate入口。正式PPO接入不在本轮验收范围。

## 5. 验证结果与证据边界

在Conda `anylogic-env` 下执行，关闭pyc/pytest cache写入：

```bash
PYTHONDONTWRITEBYTECODE=1 /home/jinx/miniconda3/envs/anylogic-env/bin/python -B -m pytest -q -p no:cacheprovider test/test_window_projection.py test/test_masked_policy.py test/test_evaluate.py test/test_reward_v1.py
```

结果：**152 passed**，包括P0的57项用例。覆盖空FIFO、0..3各活动窗、全部窗边前后/精确边界、部分处理队首、顺序改变导致金属归属变化、两窗切分、班末截止与残余、terminal余料、16槽、槽溢出引起质量不一致、孔洞/非零无效槽、非法grade/吨/rate、NaN/Inf/float32溢出、错误time/index/terminal、三时钟冲突、原始数组不变、历史产出与预约/在途不双计、固定尺度且不裁剪。

独立参考算法把每批物料转成处理时间区间，再与固定四窗做交集，与生产实现按窗口逐批扣吨的算法不同；以固定seed20261022生成300个随机状态，核对Q/M及守恒。protobuf序列化回环还验证原始通信仍为1519维，预测器独立输出6维。来源测试核对本次ALP/schema哈希和Reward V1.0；不在预测器运行时强制读取本地ALP。

Mask/评估相关回归未改变普通PPO机制；少量既有Mask回归使用合成临时环境执行PPO更新，不是正式训练。**NOT VERIFIED**：真实AnyLogic快照/连续运行的P0核验；本轮不将上述结果表述成动态仿真对账通过。

## 6. ALP审计信息与下一步核验

**实现P0无需补充ALP字段或改动物理流程**。现有同步守卫、16槽FIFO和rate均足够。本轮未编辑ALP。运行时仍以RPC完整配置、schema及通信一致性检查为准，不要求每次上传或审核ALP。

如后续明确安排一次schema诊断，现有Main变量 `obsDryRun`（ID1792577948784，ALP:1712）当前初值已经是 `true`；`obsCheckDecision`输出首个完整schema CSV，另输出前3次和每50次维度/ego/Mask摘要（ALP:8179–8205），不会输出未来真实信息或全部观测值。本轮不额外开启高频记录。

如需关闭现有schema诊断，用户可在 **Main → Variables → obsDryRun → Initial value** 手动从 `true` 改为 `false`；理由是减少诊断日志，影响仅为不再输出该CSV/周期摘要，RPC配置/schema_id/1519维校验不应关闭。验证应确认DECISION/END仍通过通信校验；后续需要一次schema对账时可显式恢复true并重新编译，核对输出后再关闭。此项是可选人工操作，本轮不执行。

真实P0对账应另行授权采集少量原始1519快照并记录episode/sequence身份。预测输入仍仅raw；RPC double时刻、ALP内部crusherClock、原批次追踪只作核验标签，不参与预测。优先选择空FIFO、近窗边和近班末快照；比较同一已存在FIFO集合后续破碎份额，不能把后来卸入物料的总产出当成P0误差。固定rate/FIFO顺序下，新入料排在其后，不改变旧FIFO贡献；如将来引入速率变化/停机，需要单独版本与新验证。
