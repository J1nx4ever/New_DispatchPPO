# V1.0审计附录：1519维字段逐项清单

日期：2026-10-22。配套[主审计报告](research_v1_audit.md)。本附录为报告数据，不改写schema或训练文件。

对当前磁盘ALP进行内存静态展开，1519项index/name/formula/source与schema一致。下面公式来自已逐项比对的schema；one-hot、路由、FIFO及truck-slot表达式包含展开器的等价简写，不是逐字Java源码。静态展开器对部分字段使用预定义模板；关键FIFO、速率、时间、车辆及资源缩放另人工核对了对应ALP函数。kind为Python验证规则，不能等同于真实运行范围。全部字段仅在当前源版本上为VERIFIED（静态），运行版本一致性仍为NOT VERIFIED。

ALP定位列是实际函数定义起始行；结合字段名可在该函数内定位writer调用。乘数及可重建性、缺失信息、近似详见主报告B矩阵。

| 索引 | 字段 | 物理语义 | ALP函数定位 | 生成/归一化公式 | Python kind |
|---|---|---|---|---|---|
| 0 | `global.shiftElapsed` | 班次已用时间 | [Main.collectPhysicalObservation:L8096](../anylogic/DRL-PPO.alp#L8096) | <code>Math.min(now,rlShiftSeconds)/28800.0</code> | unit |
| 1 | `global.shiftRemaining` | 班次剩余时间 | [Main.collectPhysicalObservation:L8096](../anylogic/DRL-PPO.alp#L8096) | <code>Math.max(0.0,rlShiftSeconds-now)/28800.0</code> | unit |
| 2 | `global.windowIndex` | 当前窗口序号（末窗关闭后为4） | [Main.collectPhysicalObservation:L8096](../anylogic/DRL-PPO.alp#L8096) | <code>currentWindowIndex/4.0</code> | unit |
| 3 | `global.windowRemaining` | 当前窗口剩余时间 | [Main.collectPhysicalObservation:L8096](../anylogic/DRL-PPO.alp#L8096) | <code>Math.max(0.0,end-now)/7200.0</code> | unit |
| 4 | `global.windowTons` | 当前窗口已破碎矿量 | [Main.collectPhysicalObservation:L8096](../anylogic/DRL-PPO.alp#L8096) | <code>windowOreTons/5000.0</code> | scaled |
| 5 | `global.windowMetal` | 当前窗口已破碎金属量 | [Main.collectPhysicalObservation:L8096](../anylogic/DRL-PPO.alp#L8096) | <code>windowMetalTons/5000.0</code> | scaled |
| 6 | `global.noSupply` | 当前窗口无已破碎供料标志 | [Main.collectPhysicalObservation:L8096](../anylogic/DRL-PPO.alp#L8096) | <code>windowOreTons<=0?1:0</code> | binary |
| 7 | `global.shiftOre` | 班次累计已破碎矿量 | [Main.collectPhysicalObservation:L8096](../anylogic/DRL-PPO.alp#L8096) | <code>crusherOreTons/20000.0</code> | scaled |
| 8 | `global.shiftMetal` | 班次累计已破碎金属量 | [Main.collectPhysicalObservation:L8096](../anylogic/DRL-PPO.alp#L8096) | <code>crusherMetalTons/20000.0</code> | scaled |
| 9 | `global.wasteDelivered` | 累计已交付废石量 | [Main.collectPhysicalObservation:L8096](../anylogic/DRL-PPO.alp#L8096) | <code>totalWasteMoved/4000.0</code> | scaled |
| 10 | `global.wasteShortfall` | 废石目标缺口 | [Main.collectPhysicalObservation:L8096](../anylogic/DRL-PPO.alp#L8096) | <code>Math.max(0.0,targetWasteTonsShift-totalWasteMoved)/4000.0</code> | scaled |
| 11 | `global.oreTarget` | 班次矿量目标 | [Main.collectPhysicalObservation:L8096](../anylogic/DRL-PPO.alp#L8096) | <code>targetOreTonsShift/20000.0</code> | scaled |
| 12 | `global.wasteTarget` | 班次废石目标 | [Main.collectPhysicalObservation:L8096](../anylogic/DRL-PPO.alp#L8096) | <code>targetWasteTonsShift/4000.0</code> | scaled |
| 13 | `global.gradeLower` | 品位下界 | [Main.collectPhysicalObservation:L8096](../anylogic/DRL-PPO.alp#L8096) | <code>gradeLowerBound</code> | unit |
| 14 | `global.gradeUpper` | 品位上界 | [Main.collectPhysicalObservation:L8096](../anylogic/DRL-PPO.alp#L8096) | <code>gradeUpperBound</code> | unit |
| 15 | `global.gradeTarget` | 目标品位 | [Main.collectPhysicalObservation:L8096](../anylogic/DRL-PPO.alp#L8096) | <code>targetGrade</code> | unit |
| 16 | `global.deterministic` | 确定性校验开关 | [Main.collectPhysicalObservation:L8096](../anylogic/DRL-PPO.alp#L8096) | <code>deterministicCheck?1:0</code> | binary |
| 17 | `global.terminal` | 达到班末截止标志 | [Main.collectPhysicalObservation:L8096](../anylogic/DRL-PPO.alp#L8096) | <code>terminal?1:0</code> | binary |
| 18 | `global.speedTickPhase` | 速度更新周期相位 | [Main.collectPhysicalObservation:L8096](../anylogic/DRL-PPO.alp#L8096) | <code>(now-Math.floor(now/speedDtSec)*speedDtSec)/speedDtSec</code> | unit |
| 19 | `actionMask.0` | 装载点可派车标志：非终止且可预留吨数>1e-6 | [Main.collectPhysicalObservation:L8096](../anylogic/DRL-PPO.alp#L8096) | <code>!terminal && getLoadSiteById(i).getAvailableTons()>1e-6 ? 1 : 0</code> | binary |
| 20 | `actionMask.1` | 装载点可派车标志：非终止且可预留吨数>1e-6 | [Main.collectPhysicalObservation:L8096](../anylogic/DRL-PPO.alp#L8096) | <code>!terminal && getLoadSiteById(i).getAvailableTons()>1e-6 ? 1 : 0</code> | binary |
| 21 | `actionMask.2` | 装载点可派车标志：非终止且可预留吨数>1e-6 | [Main.collectPhysicalObservation:L8096](../anylogic/DRL-PPO.alp#L8096) | <code>!terminal && getLoadSiteById(i).getAvailableTons()>1e-6 ? 1 : 0</code> | binary |
| 22 | `actionMask.3` | 装载点可派车标志：非终止且可预留吨数>1e-6 | [Main.collectPhysicalObservation:L8096](../anylogic/DRL-PPO.alp#L8096) | <code>!terminal && getLoadSiteById(i).getAvailableTons()>1e-6 ? 1 : 0</code> | binary |
| 23 | `actionTons.0` | 此次派车可预留载荷吨数 | [Main.collectPhysicalObservation:L8096](../anylogic/DRL-PPO.alp#L8096) | <code>!terminal ? min(ego.capacity,getLoadSiteById(i).getAvailableTons())/193.0 : 0</code> | unit |
| 24 | `actionTons.1` | 此次派车可预留载荷吨数 | [Main.collectPhysicalObservation:L8096](../anylogic/DRL-PPO.alp#L8096) | <code>!terminal ? min(ego.capacity,getLoadSiteById(i).getAvailableTons())/193.0 : 0</code> | unit |
| 25 | `actionTons.2` | 此次派车可预留载荷吨数 | [Main.collectPhysicalObservation:L8096](../anylogic/DRL-PPO.alp#L8096) | <code>!terminal ? min(ego.capacity,getLoadSiteById(i).getAvailableTons())/193.0 : 0</code> | unit |
| 26 | `actionTons.3` | 此次派车可预留载荷吨数 | [Main.collectPhysicalObservation:L8096](../anylogic/DRL-PPO.alp#L8096) | <code>!terminal ? min(ego.capacity,getLoadSiteById(i).getAvailableTons())/193.0 : 0</code> | unit |
| 27 | `truck.0.ego` | 当前需要派车的车辆标志 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>decision?1:0</code> | binary |
| 28 | `truck.0.type.0` | 车型类别0/1/2 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(truckType, 0)</code> | binary |
| 29 | `truck.0.type.1` | 车型类别0/1/2 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(truckType, 1)</code> | binary |
| 30 | `truck.0.type.2` | 车型类别0/1/2 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(truckType, 2)</code> | binary |
| 31 | `truck.0.phase.0` | 执行阶段类别0..11（详见审计报告） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(phase, 0)</code> | binary |
| 32 | `truck.0.phase.1` | 执行阶段类别0..11（详见审计报告） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(phase, 1)</code> | binary |
| 33 | `truck.0.phase.2` | 执行阶段类别0..11（详见审计报告） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(phase, 2)</code> | binary |
| 34 | `truck.0.phase.3` | 执行阶段类别0..11（详见审计报告） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(phase, 3)</code> | binary |
| 35 | `truck.0.phase.4` | 执行阶段类别0..11（详见审计报告） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(phase, 4)</code> | binary |
| 36 | `truck.0.phase.5` | 执行阶段类别0..11（详见审计报告） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(phase, 5)</code> | binary |
| 37 | `truck.0.phase.6` | 执行阶段类别0..11（详见审计报告） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(phase, 6)</code> | binary |
| 38 | `truck.0.phase.7` | 执行阶段类别0..11（详见审计报告） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(phase, 7)</code> | binary |
| 39 | `truck.0.phase.8` | 执行阶段类别0..11（详见审计报告） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(phase, 8)</code> | binary |
| 40 | `truck.0.phase.9` | 执行阶段类别0..11（详见审计报告） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(phase, 9)</code> | binary |
| 41 | `truck.0.phase.10` | 执行阶段类别0..11（详见审计报告） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(phase, 10)</code> | binary |
| 42 | `truck.0.phase.11` | 执行阶段类别0..11（详见审计报告） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(phase, 11)</code> | binary |
| 43 | `truck.0.capacity` | 车辆载重能力或卸载点服务并发容量（依据公式） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>capacity/193.0</code> | scaled |
| 44 | `truck.0.loaded` | 有载标志 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>isLoaded?1:0</code> | binary |
| 45 | `truck.0.ore` | 载荷或已预留装载物是否为矿石 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>isLoaded?(payloadIsOre?1:0):(plannedPayloadTons>0 && targetShovel!=null && targetShovel.isOre?1:0)</code> | binary |
| 46 | `truck.0.payloadTons` | 已装载物料吨数 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>payloadTons/193.0</code> | scaled |
| 47 | `truck.0.reservedLoadTons` | 已预留未完成装载吨数 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>plannedPayloadTons/193.0</code> | scaled |
| 48 | `truck.0.gradeKnown` | 已装载物料品位已知标志 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>isLoaded?1:0</code> | binary |
| 49 | `truck.0.payloadGrade` | 已装载物料品位，空载为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>isLoaded?payloadGrade:0.0</code> | unit |
| 50 | `truck.0.loadingGradeMean` | 正在装载物料的可观测品位估计均值 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>gs[0]</code> | unit |
| 51 | `truck.0.loadingGradeStd` | 正在装载物料的可观测品位估计标准差 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>gs[1]</code> | unit |
| 52 | `truck.0.loadingGradeInferred` | 正在装载物料品位是否全部可推知 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>gs[2]</code> | binary |
| 53 | `truck.0.loadTarget.0` | 装载目标one-hot（决策车辆清空） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(!decision && plannedPayloadTons>0 && targetShovel!=null?targetShovel.siteId:-1, 0)</code> | binary |
| 54 | `truck.0.loadTarget.1` | 装载目标one-hot（决策车辆清空） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(!decision && plannedPayloadTons>0 && targetShovel!=null?targetShovel.siteId:-1, 1)</code> | binary |
| 55 | `truck.0.loadTarget.2` | 装载目标one-hot（决策车辆清空） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(!decision && plannedPayloadTons>0 && targetShovel!=null?targetShovel.siteId:-1, 2)</code> | binary |
| 56 | `truck.0.loadTarget.3` | 装载目标one-hot（决策车辆清空） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(!decision && plannedPayloadTons>0 && targetShovel!=null?targetShovel.siteId:-1, 3)</code> | binary |
| 57 | `truck.0.dumpTarget.0` | 卸载目标one-hot（矿石0/废石1） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(isLoaded?(payloadIsOre?0:1):-1, 0)</code> | binary |
| 58 | `truck.0.dumpTarget.1` | 卸载目标one-hot（矿石0/废石1） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(isLoaded?(payloadIsOre?0:1):-1, 1)</code> | binary |
| 59 | `truck.0.node.0` | 当前道路节点one-hot | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(main.obsNodeIndex(currentNode), 0)</code> | binary |
| 60 | `truck.0.node.1` | 当前道路节点one-hot | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(main.obsNodeIndex(currentNode), 1)</code> | binary |
| 61 | `truck.0.node.2` | 当前道路节点one-hot | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(main.obsNodeIndex(currentNode), 2)</code> | binary |
| 62 | `truck.0.node.3` | 当前道路节点one-hot | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(main.obsNodeIndex(currentNode), 3)</code> | binary |
| 63 | `truck.0.node.4` | 当前道路节点one-hot | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(main.obsNodeIndex(currentNode), 4)</code> | binary |
| 64 | `truck.0.node.5` | 当前道路节点one-hot | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(main.obsNodeIndex(currentNode), 5)</code> | binary |
| 65 | `truck.0.node.6` | 当前道路节点one-hot | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(main.obsNodeIndex(currentNode), 6)</code> | binary |
| 66 | `truck.0.node.7` | 当前道路节点one-hot | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(main.obsNodeIndex(currentNode), 7)</code> | binary |
| 67 | `truck.0.node.8` | 当前道路节点one-hot | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(main.obsNodeIndex(currentNode), 8)</code> | binary |
| 68 | `truck.0.xM` | 车辆X坐标（米） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>main.toLengthUnits(getX(),METER)/10000.0</code> | scaled |
| 69 | `truck.0.yM` | 车辆Y坐标（米） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>main.toLengthUnits(getY(),METER)/10000.0</code> | scaled |
| 70 | `truck.0.speed` | 速度（米/秒） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>getSpeed()/10.0</code> | scaled |
| 71 | `truck.0.acceleration` | 动态加速度（米/秒平方） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>dynamicAccel/3.0</code> | scaled |
| 72 | `truck.0.segment.0` | 当前有向路段one-hot（决策车辆不编码运动段） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(seg, 0)</code> | binary |
| 73 | `truck.0.segment.1` | 当前有向路段one-hot（决策车辆不编码运动段） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(seg, 1)</code> | binary |
| 74 | `truck.0.segment.2` | 当前有向路段one-hot（决策车辆不编码运动段） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(seg, 2)</code> | binary |
| 75 | `truck.0.segment.3` | 当前有向路段one-hot（决策车辆不编码运动段） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(seg, 3)</code> | binary |
| 76 | `truck.0.segment.4` | 当前有向路段one-hot（决策车辆不编码运动段） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(seg, 4)</code> | binary |
| 77 | `truck.0.segment.5` | 当前有向路段one-hot（决策车辆不编码运动段） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(seg, 5)</code> | binary |
| 78 | `truck.0.segment.6` | 当前有向路段one-hot（决策车辆不编码运动段） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(seg, 6)</code> | binary |
| 79 | `truck.0.segment.7` | 当前有向路段one-hot（决策车辆不编码运动段） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(seg, 7)</code> | binary |
| 80 | `truck.0.segment.8` | 当前有向路段one-hot（决策车辆不编码运动段） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(seg, 8)</code> | binary |
| 81 | `truck.0.segment.9` | 当前有向路段one-hot（决策车辆不编码运动段） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(seg, 9)</code> | binary |
| 82 | `truck.0.segment.10` | 当前有向路段one-hot（决策车辆不编码运动段） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(seg, 10)</code> | binary |
| 83 | `truck.0.segment.11` | 当前有向路段one-hot（决策车辆不编码运动段） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(seg, 11)</code> | binary |
| 84 | `truck.0.segment.12` | 当前有向路段one-hot（决策车辆不编码运动段） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(seg, 12)</code> | binary |
| 85 | `truck.0.segment.13` | 当前有向路段one-hot（决策车辆不编码运动段） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(seg, 13)</code> | binary |
| 86 | `truck.0.segment.14` | 当前有向路段one-hot（决策车辆不编码运动段） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(seg, 14)</code> | binary |
| 87 | `truck.0.segment.15` | 当前有向路段one-hot（决策车辆不编码运动段） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(seg, 15)</code> | binary |
| 88 | `truck.0.segmentRemaining` | 当前路段剩余距离（米） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>remaining/10000.0</code> | scaled |
| 89 | `truck.0.routeRemaining` | 当前路线剩余距离（米） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>totalRemaining/10000.0</code> | scaled |
| 90 | `truck.0.routeOrder.0` | 对应路段在剩余路线的次序，未经过为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>routeOrder[0] = (j-currentSegmentIndex+1.0)/16.0 or 0</code> | unit |
| 91 | `truck.0.routeOrder.1` | 对应路段在剩余路线的次序，未经过为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>routeOrder[1] = (j-currentSegmentIndex+1.0)/16.0 or 0</code> | unit |
| 92 | `truck.0.routeOrder.2` | 对应路段在剩余路线的次序，未经过为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>routeOrder[2] = (j-currentSegmentIndex+1.0)/16.0 or 0</code> | unit |
| 93 | `truck.0.routeOrder.3` | 对应路段在剩余路线的次序，未经过为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>routeOrder[3] = (j-currentSegmentIndex+1.0)/16.0 or 0</code> | unit |
| 94 | `truck.0.routeOrder.4` | 对应路段在剩余路线的次序，未经过为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>routeOrder[4] = (j-currentSegmentIndex+1.0)/16.0 or 0</code> | unit |
| 95 | `truck.0.routeOrder.5` | 对应路段在剩余路线的次序，未经过为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>routeOrder[5] = (j-currentSegmentIndex+1.0)/16.0 or 0</code> | unit |
| 96 | `truck.0.routeOrder.6` | 对应路段在剩余路线的次序，未经过为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>routeOrder[6] = (j-currentSegmentIndex+1.0)/16.0 or 0</code> | unit |
| 97 | `truck.0.routeOrder.7` | 对应路段在剩余路线的次序，未经过为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>routeOrder[7] = (j-currentSegmentIndex+1.0)/16.0 or 0</code> | unit |
| 98 | `truck.0.routeOrder.8` | 对应路段在剩余路线的次序，未经过为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>routeOrder[8] = (j-currentSegmentIndex+1.0)/16.0 or 0</code> | unit |
| 99 | `truck.0.routeOrder.9` | 对应路段在剩余路线的次序，未经过为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>routeOrder[9] = (j-currentSegmentIndex+1.0)/16.0 or 0</code> | unit |
| 100 | `truck.0.routeOrder.10` | 对应路段在剩余路线的次序，未经过为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>routeOrder[10] = (j-currentSegmentIndex+1.0)/16.0 or 0</code> | unit |
| 101 | `truck.0.routeOrder.11` | 对应路段在剩余路线的次序，未经过为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>routeOrder[11] = (j-currentSegmentIndex+1.0)/16.0 or 0</code> | unit |
| 102 | `truck.0.routeOrder.12` | 对应路段在剩余路线的次序，未经过为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>routeOrder[12] = (j-currentSegmentIndex+1.0)/16.0 or 0</code> | unit |
| 103 | `truck.0.routeOrder.13` | 对应路段在剩余路线的次序，未经过为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>routeOrder[13] = (j-currentSegmentIndex+1.0)/16.0 or 0</code> | unit |
| 104 | `truck.0.routeOrder.14` | 对应路段在剩余路线的次序，未经过为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>routeOrder[14] = (j-currentSegmentIndex+1.0)/16.0 or 0</code> | unit |
| 105 | `truck.0.routeOrder.15` | 对应路段在剩余路线的次序，未经过为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>routeOrder[15] = (j-currentSegmentIndex+1.0)/16.0 or 0</code> | unit |
| 106 | `truck.0.laneRank` | 当前路段车辆进入顺序排位 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>seg>=0?(ahead+1.0)/9.0:0.0</code> | unit |
| 107 | `truck.0.initialDispatched` | 是否完成首次派车 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>initialDispatchDone?1:0</code> | binary |
| 108 | `truck.0.initialPredecessor` | 首次派车前驱车辆ID编码，无前驱为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>initialPredecessor==null?0:(initialPredecessor.truckId+1.0)/9.0</code> | unit |
| 109 | `truck.0.loadWaitAge` | 等待装载资源已用时间 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>isWaitingForLoadResource?Math.max(0.0,now-60.0*queueEnterTime)/28800.0:0.0</code> | unit |
| 110 | `truck.0.dumpWaitAge` | 等待卸载资源已用时间 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>isWaitingForDumpResource?Math.max(0.0,now-60.0*dumpQueueEnterTime)/28800.0:0.0</code> | unit |
| 111 | `truck.0.loadAge` | 当前装载服务已用时间 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>loading?Math.max(0.0,now-60.0*loadStartTime)/600.0:0.0</code> | scaled |
| 112 | `truck.0.loadMean` | 当前载荷平均装载时间（分钟） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>loading?targetShovel.obsMeanLoadMinutes(plannedPayloadTons)/10.0:0.0</code> | scaled |
| 113 | `truck.0.loadMaterialStart` | 当前装载在物料序列中的起始吨位 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>loading?obsLoadMaterialStart/30000.0:0.0</code> | scaled |
| 114 | `truck.0.dumpAge` | 当前卸载服务已用时间 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>dumping?Math.max(0.0,now-60.0*dumpServiceStartTime)/600.0:0.0</code> | scaled |
| 115 | `truck.0.dumpMean` | 当前车辆平均卸载时间（分钟） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>dumping?main.getDumpSiteById(targetDumpSiteId).obsMeanDumpMinutes(this)/10.0:0.0</code> | scaled |
| 116 | `truck.0.freeSamples` | 自由行驶速度估计样本数 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>obsFreeCount/1000.0</code> | scaled |
| 117 | `truck.0.freeRatioMean` | 可观测自由流速度比样本均值 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>obsFreeCount>0?obsFreeMean:0.0</code> | scaled |
| 118 | `truck.0.freeRatioStd` | 可观测自由流速度比样本标准差 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>obsFreeCount>1?Math.sqrt(Math.max(0.0,obsFreeM2/(obsFreeCount-1))):0.0</code> | scaled |
| 119 | `truck.0.motion.0.valid` | 槽位或历史样本是否有效 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:1</code> | binary |
| 120 | `truck.0.motion.0.age` | 运动历史样本距当前时刻秒数 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:Math.max(0.0,now-h[0])/28800.0</code> | unit |
| 121 | `truck.0.motion.0.speed` | 速度（米/秒） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[1]/10.0</code> | scaled |
| 122 | `truck.0.motion.0.acceleration` | 动态加速度（米/秒平方） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[2]/3.0</code> | scaled |
| 123 | `truck.0.motion.0.hasFront` | 历史样本是否存在前车 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[3]</code> | binary |
| 124 | `truck.0.motion.0.frontGap` | 历史前车间距（米） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[4]/10000.0</code> | scaled |
| 125 | `truck.0.motion.0.frontSpeed` | 历史前车速度（米/秒） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[5]/10.0</code> | scaled |
| 126 | `truck.0.motion.1.valid` | 槽位或历史样本是否有效 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:1</code> | binary |
| 127 | `truck.0.motion.1.age` | 运动历史样本距当前时刻秒数 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:Math.max(0.0,now-h[0])/28800.0</code> | unit |
| 128 | `truck.0.motion.1.speed` | 速度（米/秒） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[1]/10.0</code> | scaled |
| 129 | `truck.0.motion.1.acceleration` | 动态加速度（米/秒平方） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[2]/3.0</code> | scaled |
| 130 | `truck.0.motion.1.hasFront` | 历史样本是否存在前车 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[3]</code> | binary |
| 131 | `truck.0.motion.1.frontGap` | 历史前车间距（米） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[4]/10000.0</code> | scaled |
| 132 | `truck.0.motion.1.frontSpeed` | 历史前车速度（米/秒） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[5]/10.0</code> | scaled |
| 133 | `truck.0.motion.2.valid` | 槽位或历史样本是否有效 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:1</code> | binary |
| 134 | `truck.0.motion.2.age` | 运动历史样本距当前时刻秒数 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:Math.max(0.0,now-h[0])/28800.0</code> | unit |
| 135 | `truck.0.motion.2.speed` | 速度（米/秒） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[1]/10.0</code> | scaled |
| 136 | `truck.0.motion.2.acceleration` | 动态加速度（米/秒平方） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[2]/3.0</code> | scaled |
| 137 | `truck.0.motion.2.hasFront` | 历史样本是否存在前车 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[3]</code> | binary |
| 138 | `truck.0.motion.2.frontGap` | 历史前车间距（米） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[4]/10000.0</code> | scaled |
| 139 | `truck.0.motion.2.frontSpeed` | 历史前车速度（米/秒） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[5]/10.0</code> | scaled |
| 140 | `truck.0.motion.3.valid` | 槽位或历史样本是否有效 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:1</code> | binary |
| 141 | `truck.0.motion.3.age` | 运动历史样本距当前时刻秒数 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:Math.max(0.0,now-h[0])/28800.0</code> | unit |
| 142 | `truck.0.motion.3.speed` | 速度（米/秒） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[1]/10.0</code> | scaled |
| 143 | `truck.0.motion.3.acceleration` | 动态加速度（米/秒平方） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[2]/3.0</code> | scaled |
| 144 | `truck.0.motion.3.hasFront` | 历史样本是否存在前车 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[3]</code> | binary |
| 145 | `truck.0.motion.3.frontGap` | 历史前车间距（米） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[4]/10000.0</code> | scaled |
| 146 | `truck.0.motion.3.frontSpeed` | 历史前车速度（米/秒） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[5]/10.0</code> | scaled |
| 147 | `truck.1.ego` | 当前需要派车的车辆标志 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>decision?1:0</code> | binary |
| 148 | `truck.1.type.0` | 车型类别0/1/2 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(truckType, 0)</code> | binary |
| 149 | `truck.1.type.1` | 车型类别0/1/2 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(truckType, 1)</code> | binary |
| 150 | `truck.1.type.2` | 车型类别0/1/2 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(truckType, 2)</code> | binary |
| 151 | `truck.1.phase.0` | 执行阶段类别0..11（详见审计报告） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(phase, 0)</code> | binary |
| 152 | `truck.1.phase.1` | 执行阶段类别0..11（详见审计报告） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(phase, 1)</code> | binary |
| 153 | `truck.1.phase.2` | 执行阶段类别0..11（详见审计报告） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(phase, 2)</code> | binary |
| 154 | `truck.1.phase.3` | 执行阶段类别0..11（详见审计报告） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(phase, 3)</code> | binary |
| 155 | `truck.1.phase.4` | 执行阶段类别0..11（详见审计报告） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(phase, 4)</code> | binary |
| 156 | `truck.1.phase.5` | 执行阶段类别0..11（详见审计报告） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(phase, 5)</code> | binary |
| 157 | `truck.1.phase.6` | 执行阶段类别0..11（详见审计报告） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(phase, 6)</code> | binary |
| 158 | `truck.1.phase.7` | 执行阶段类别0..11（详见审计报告） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(phase, 7)</code> | binary |
| 159 | `truck.1.phase.8` | 执行阶段类别0..11（详见审计报告） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(phase, 8)</code> | binary |
| 160 | `truck.1.phase.9` | 执行阶段类别0..11（详见审计报告） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(phase, 9)</code> | binary |
| 161 | `truck.1.phase.10` | 执行阶段类别0..11（详见审计报告） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(phase, 10)</code> | binary |
| 162 | `truck.1.phase.11` | 执行阶段类别0..11（详见审计报告） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(phase, 11)</code> | binary |
| 163 | `truck.1.capacity` | 车辆载重能力或卸载点服务并发容量（依据公式） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>capacity/193.0</code> | scaled |
| 164 | `truck.1.loaded` | 有载标志 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>isLoaded?1:0</code> | binary |
| 165 | `truck.1.ore` | 载荷或已预留装载物是否为矿石 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>isLoaded?(payloadIsOre?1:0):(plannedPayloadTons>0 && targetShovel!=null && targetShovel.isOre?1:0)</code> | binary |
| 166 | `truck.1.payloadTons` | 已装载物料吨数 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>payloadTons/193.0</code> | scaled |
| 167 | `truck.1.reservedLoadTons` | 已预留未完成装载吨数 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>plannedPayloadTons/193.0</code> | scaled |
| 168 | `truck.1.gradeKnown` | 已装载物料品位已知标志 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>isLoaded?1:0</code> | binary |
| 169 | `truck.1.payloadGrade` | 已装载物料品位，空载为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>isLoaded?payloadGrade:0.0</code> | unit |
| 170 | `truck.1.loadingGradeMean` | 正在装载物料的可观测品位估计均值 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>gs[0]</code> | unit |
| 171 | `truck.1.loadingGradeStd` | 正在装载物料的可观测品位估计标准差 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>gs[1]</code> | unit |
| 172 | `truck.1.loadingGradeInferred` | 正在装载物料品位是否全部可推知 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>gs[2]</code> | binary |
| 173 | `truck.1.loadTarget.0` | 装载目标one-hot（决策车辆清空） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(!decision && plannedPayloadTons>0 && targetShovel!=null?targetShovel.siteId:-1, 0)</code> | binary |
| 174 | `truck.1.loadTarget.1` | 装载目标one-hot（决策车辆清空） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(!decision && plannedPayloadTons>0 && targetShovel!=null?targetShovel.siteId:-1, 1)</code> | binary |
| 175 | `truck.1.loadTarget.2` | 装载目标one-hot（决策车辆清空） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(!decision && plannedPayloadTons>0 && targetShovel!=null?targetShovel.siteId:-1, 2)</code> | binary |
| 176 | `truck.1.loadTarget.3` | 装载目标one-hot（决策车辆清空） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(!decision && plannedPayloadTons>0 && targetShovel!=null?targetShovel.siteId:-1, 3)</code> | binary |
| 177 | `truck.1.dumpTarget.0` | 卸载目标one-hot（矿石0/废石1） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(isLoaded?(payloadIsOre?0:1):-1, 0)</code> | binary |
| 178 | `truck.1.dumpTarget.1` | 卸载目标one-hot（矿石0/废石1） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(isLoaded?(payloadIsOre?0:1):-1, 1)</code> | binary |
| 179 | `truck.1.node.0` | 当前道路节点one-hot | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(main.obsNodeIndex(currentNode), 0)</code> | binary |
| 180 | `truck.1.node.1` | 当前道路节点one-hot | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(main.obsNodeIndex(currentNode), 1)</code> | binary |
| 181 | `truck.1.node.2` | 当前道路节点one-hot | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(main.obsNodeIndex(currentNode), 2)</code> | binary |
| 182 | `truck.1.node.3` | 当前道路节点one-hot | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(main.obsNodeIndex(currentNode), 3)</code> | binary |
| 183 | `truck.1.node.4` | 当前道路节点one-hot | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(main.obsNodeIndex(currentNode), 4)</code> | binary |
| 184 | `truck.1.node.5` | 当前道路节点one-hot | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(main.obsNodeIndex(currentNode), 5)</code> | binary |
| 185 | `truck.1.node.6` | 当前道路节点one-hot | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(main.obsNodeIndex(currentNode), 6)</code> | binary |
| 186 | `truck.1.node.7` | 当前道路节点one-hot | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(main.obsNodeIndex(currentNode), 7)</code> | binary |
| 187 | `truck.1.node.8` | 当前道路节点one-hot | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(main.obsNodeIndex(currentNode), 8)</code> | binary |
| 188 | `truck.1.xM` | 车辆X坐标（米） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>main.toLengthUnits(getX(),METER)/10000.0</code> | scaled |
| 189 | `truck.1.yM` | 车辆Y坐标（米） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>main.toLengthUnits(getY(),METER)/10000.0</code> | scaled |
| 190 | `truck.1.speed` | 速度（米/秒） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>getSpeed()/10.0</code> | scaled |
| 191 | `truck.1.acceleration` | 动态加速度（米/秒平方） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>dynamicAccel/3.0</code> | scaled |
| 192 | `truck.1.segment.0` | 当前有向路段one-hot（决策车辆不编码运动段） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(seg, 0)</code> | binary |
| 193 | `truck.1.segment.1` | 当前有向路段one-hot（决策车辆不编码运动段） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(seg, 1)</code> | binary |
| 194 | `truck.1.segment.2` | 当前有向路段one-hot（决策车辆不编码运动段） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(seg, 2)</code> | binary |
| 195 | `truck.1.segment.3` | 当前有向路段one-hot（决策车辆不编码运动段） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(seg, 3)</code> | binary |
| 196 | `truck.1.segment.4` | 当前有向路段one-hot（决策车辆不编码运动段） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(seg, 4)</code> | binary |
| 197 | `truck.1.segment.5` | 当前有向路段one-hot（决策车辆不编码运动段） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(seg, 5)</code> | binary |
| 198 | `truck.1.segment.6` | 当前有向路段one-hot（决策车辆不编码运动段） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(seg, 6)</code> | binary |
| 199 | `truck.1.segment.7` | 当前有向路段one-hot（决策车辆不编码运动段） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(seg, 7)</code> | binary |
| 200 | `truck.1.segment.8` | 当前有向路段one-hot（决策车辆不编码运动段） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(seg, 8)</code> | binary |
| 201 | `truck.1.segment.9` | 当前有向路段one-hot（决策车辆不编码运动段） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(seg, 9)</code> | binary |
| 202 | `truck.1.segment.10` | 当前有向路段one-hot（决策车辆不编码运动段） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(seg, 10)</code> | binary |
| 203 | `truck.1.segment.11` | 当前有向路段one-hot（决策车辆不编码运动段） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(seg, 11)</code> | binary |
| 204 | `truck.1.segment.12` | 当前有向路段one-hot（决策车辆不编码运动段） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(seg, 12)</code> | binary |
| 205 | `truck.1.segment.13` | 当前有向路段one-hot（决策车辆不编码运动段） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(seg, 13)</code> | binary |
| 206 | `truck.1.segment.14` | 当前有向路段one-hot（决策车辆不编码运动段） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(seg, 14)</code> | binary |
| 207 | `truck.1.segment.15` | 当前有向路段one-hot（决策车辆不编码运动段） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(seg, 15)</code> | binary |
| 208 | `truck.1.segmentRemaining` | 当前路段剩余距离（米） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>remaining/10000.0</code> | scaled |
| 209 | `truck.1.routeRemaining` | 当前路线剩余距离（米） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>totalRemaining/10000.0</code> | scaled |
| 210 | `truck.1.routeOrder.0` | 对应路段在剩余路线的次序，未经过为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>routeOrder[0] = (j-currentSegmentIndex+1.0)/16.0 or 0</code> | unit |
| 211 | `truck.1.routeOrder.1` | 对应路段在剩余路线的次序，未经过为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>routeOrder[1] = (j-currentSegmentIndex+1.0)/16.0 or 0</code> | unit |
| 212 | `truck.1.routeOrder.2` | 对应路段在剩余路线的次序，未经过为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>routeOrder[2] = (j-currentSegmentIndex+1.0)/16.0 or 0</code> | unit |
| 213 | `truck.1.routeOrder.3` | 对应路段在剩余路线的次序，未经过为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>routeOrder[3] = (j-currentSegmentIndex+1.0)/16.0 or 0</code> | unit |
| 214 | `truck.1.routeOrder.4` | 对应路段在剩余路线的次序，未经过为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>routeOrder[4] = (j-currentSegmentIndex+1.0)/16.0 or 0</code> | unit |
| 215 | `truck.1.routeOrder.5` | 对应路段在剩余路线的次序，未经过为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>routeOrder[5] = (j-currentSegmentIndex+1.0)/16.0 or 0</code> | unit |
| 216 | `truck.1.routeOrder.6` | 对应路段在剩余路线的次序，未经过为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>routeOrder[6] = (j-currentSegmentIndex+1.0)/16.0 or 0</code> | unit |
| 217 | `truck.1.routeOrder.7` | 对应路段在剩余路线的次序，未经过为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>routeOrder[7] = (j-currentSegmentIndex+1.0)/16.0 or 0</code> | unit |
| 218 | `truck.1.routeOrder.8` | 对应路段在剩余路线的次序，未经过为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>routeOrder[8] = (j-currentSegmentIndex+1.0)/16.0 or 0</code> | unit |
| 219 | `truck.1.routeOrder.9` | 对应路段在剩余路线的次序，未经过为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>routeOrder[9] = (j-currentSegmentIndex+1.0)/16.0 or 0</code> | unit |
| 220 | `truck.1.routeOrder.10` | 对应路段在剩余路线的次序，未经过为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>routeOrder[10] = (j-currentSegmentIndex+1.0)/16.0 or 0</code> | unit |
| 221 | `truck.1.routeOrder.11` | 对应路段在剩余路线的次序，未经过为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>routeOrder[11] = (j-currentSegmentIndex+1.0)/16.0 or 0</code> | unit |
| 222 | `truck.1.routeOrder.12` | 对应路段在剩余路线的次序，未经过为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>routeOrder[12] = (j-currentSegmentIndex+1.0)/16.0 or 0</code> | unit |
| 223 | `truck.1.routeOrder.13` | 对应路段在剩余路线的次序，未经过为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>routeOrder[13] = (j-currentSegmentIndex+1.0)/16.0 or 0</code> | unit |
| 224 | `truck.1.routeOrder.14` | 对应路段在剩余路线的次序，未经过为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>routeOrder[14] = (j-currentSegmentIndex+1.0)/16.0 or 0</code> | unit |
| 225 | `truck.1.routeOrder.15` | 对应路段在剩余路线的次序，未经过为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>routeOrder[15] = (j-currentSegmentIndex+1.0)/16.0 or 0</code> | unit |
| 226 | `truck.1.laneRank` | 当前路段车辆进入顺序排位 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>seg>=0?(ahead+1.0)/9.0:0.0</code> | unit |
| 227 | `truck.1.initialDispatched` | 是否完成首次派车 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>initialDispatchDone?1:0</code> | binary |
| 228 | `truck.1.initialPredecessor` | 首次派车前驱车辆ID编码，无前驱为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>initialPredecessor==null?0:(initialPredecessor.truckId+1.0)/9.0</code> | unit |
| 229 | `truck.1.loadWaitAge` | 等待装载资源已用时间 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>isWaitingForLoadResource?Math.max(0.0,now-60.0*queueEnterTime)/28800.0:0.0</code> | unit |
| 230 | `truck.1.dumpWaitAge` | 等待卸载资源已用时间 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>isWaitingForDumpResource?Math.max(0.0,now-60.0*dumpQueueEnterTime)/28800.0:0.0</code> | unit |
| 231 | `truck.1.loadAge` | 当前装载服务已用时间 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>loading?Math.max(0.0,now-60.0*loadStartTime)/600.0:0.0</code> | scaled |
| 232 | `truck.1.loadMean` | 当前载荷平均装载时间（分钟） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>loading?targetShovel.obsMeanLoadMinutes(plannedPayloadTons)/10.0:0.0</code> | scaled |
| 233 | `truck.1.loadMaterialStart` | 当前装载在物料序列中的起始吨位 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>loading?obsLoadMaterialStart/30000.0:0.0</code> | scaled |
| 234 | `truck.1.dumpAge` | 当前卸载服务已用时间 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>dumping?Math.max(0.0,now-60.0*dumpServiceStartTime)/600.0:0.0</code> | scaled |
| 235 | `truck.1.dumpMean` | 当前车辆平均卸载时间（分钟） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>dumping?main.getDumpSiteById(targetDumpSiteId).obsMeanDumpMinutes(this)/10.0:0.0</code> | scaled |
| 236 | `truck.1.freeSamples` | 自由行驶速度估计样本数 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>obsFreeCount/1000.0</code> | scaled |
| 237 | `truck.1.freeRatioMean` | 可观测自由流速度比样本均值 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>obsFreeCount>0?obsFreeMean:0.0</code> | scaled |
| 238 | `truck.1.freeRatioStd` | 可观测自由流速度比样本标准差 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>obsFreeCount>1?Math.sqrt(Math.max(0.0,obsFreeM2/(obsFreeCount-1))):0.0</code> | scaled |
| 239 | `truck.1.motion.0.valid` | 槽位或历史样本是否有效 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:1</code> | binary |
| 240 | `truck.1.motion.0.age` | 运动历史样本距当前时刻秒数 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:Math.max(0.0,now-h[0])/28800.0</code> | unit |
| 241 | `truck.1.motion.0.speed` | 速度（米/秒） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[1]/10.0</code> | scaled |
| 242 | `truck.1.motion.0.acceleration` | 动态加速度（米/秒平方） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[2]/3.0</code> | scaled |
| 243 | `truck.1.motion.0.hasFront` | 历史样本是否存在前车 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[3]</code> | binary |
| 244 | `truck.1.motion.0.frontGap` | 历史前车间距（米） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[4]/10000.0</code> | scaled |
| 245 | `truck.1.motion.0.frontSpeed` | 历史前车速度（米/秒） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[5]/10.0</code> | scaled |
| 246 | `truck.1.motion.1.valid` | 槽位或历史样本是否有效 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:1</code> | binary |
| 247 | `truck.1.motion.1.age` | 运动历史样本距当前时刻秒数 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:Math.max(0.0,now-h[0])/28800.0</code> | unit |
| 248 | `truck.1.motion.1.speed` | 速度（米/秒） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[1]/10.0</code> | scaled |
| 249 | `truck.1.motion.1.acceleration` | 动态加速度（米/秒平方） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[2]/3.0</code> | scaled |
| 250 | `truck.1.motion.1.hasFront` | 历史样本是否存在前车 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[3]</code> | binary |
| 251 | `truck.1.motion.1.frontGap` | 历史前车间距（米） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[4]/10000.0</code> | scaled |
| 252 | `truck.1.motion.1.frontSpeed` | 历史前车速度（米/秒） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[5]/10.0</code> | scaled |
| 253 | `truck.1.motion.2.valid` | 槽位或历史样本是否有效 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:1</code> | binary |
| 254 | `truck.1.motion.2.age` | 运动历史样本距当前时刻秒数 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:Math.max(0.0,now-h[0])/28800.0</code> | unit |
| 255 | `truck.1.motion.2.speed` | 速度（米/秒） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[1]/10.0</code> | scaled |
| 256 | `truck.1.motion.2.acceleration` | 动态加速度（米/秒平方） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[2]/3.0</code> | scaled |
| 257 | `truck.1.motion.2.hasFront` | 历史样本是否存在前车 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[3]</code> | binary |
| 258 | `truck.1.motion.2.frontGap` | 历史前车间距（米） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[4]/10000.0</code> | scaled |
| 259 | `truck.1.motion.2.frontSpeed` | 历史前车速度（米/秒） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[5]/10.0</code> | scaled |
| 260 | `truck.1.motion.3.valid` | 槽位或历史样本是否有效 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:1</code> | binary |
| 261 | `truck.1.motion.3.age` | 运动历史样本距当前时刻秒数 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:Math.max(0.0,now-h[0])/28800.0</code> | unit |
| 262 | `truck.1.motion.3.speed` | 速度（米/秒） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[1]/10.0</code> | scaled |
| 263 | `truck.1.motion.3.acceleration` | 动态加速度（米/秒平方） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[2]/3.0</code> | scaled |
| 264 | `truck.1.motion.3.hasFront` | 历史样本是否存在前车 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[3]</code> | binary |
| 265 | `truck.1.motion.3.frontGap` | 历史前车间距（米） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[4]/10000.0</code> | scaled |
| 266 | `truck.1.motion.3.frontSpeed` | 历史前车速度（米/秒） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[5]/10.0</code> | scaled |
| 267 | `truck.2.ego` | 当前需要派车的车辆标志 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>decision?1:0</code> | binary |
| 268 | `truck.2.type.0` | 车型类别0/1/2 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(truckType, 0)</code> | binary |
| 269 | `truck.2.type.1` | 车型类别0/1/2 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(truckType, 1)</code> | binary |
| 270 | `truck.2.type.2` | 车型类别0/1/2 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(truckType, 2)</code> | binary |
| 271 | `truck.2.phase.0` | 执行阶段类别0..11（详见审计报告） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(phase, 0)</code> | binary |
| 272 | `truck.2.phase.1` | 执行阶段类别0..11（详见审计报告） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(phase, 1)</code> | binary |
| 273 | `truck.2.phase.2` | 执行阶段类别0..11（详见审计报告） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(phase, 2)</code> | binary |
| 274 | `truck.2.phase.3` | 执行阶段类别0..11（详见审计报告） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(phase, 3)</code> | binary |
| 275 | `truck.2.phase.4` | 执行阶段类别0..11（详见审计报告） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(phase, 4)</code> | binary |
| 276 | `truck.2.phase.5` | 执行阶段类别0..11（详见审计报告） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(phase, 5)</code> | binary |
| 277 | `truck.2.phase.6` | 执行阶段类别0..11（详见审计报告） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(phase, 6)</code> | binary |
| 278 | `truck.2.phase.7` | 执行阶段类别0..11（详见审计报告） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(phase, 7)</code> | binary |
| 279 | `truck.2.phase.8` | 执行阶段类别0..11（详见审计报告） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(phase, 8)</code> | binary |
| 280 | `truck.2.phase.9` | 执行阶段类别0..11（详见审计报告） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(phase, 9)</code> | binary |
| 281 | `truck.2.phase.10` | 执行阶段类别0..11（详见审计报告） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(phase, 10)</code> | binary |
| 282 | `truck.2.phase.11` | 执行阶段类别0..11（详见审计报告） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(phase, 11)</code> | binary |
| 283 | `truck.2.capacity` | 车辆载重能力或卸载点服务并发容量（依据公式） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>capacity/193.0</code> | scaled |
| 284 | `truck.2.loaded` | 有载标志 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>isLoaded?1:0</code> | binary |
| 285 | `truck.2.ore` | 载荷或已预留装载物是否为矿石 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>isLoaded?(payloadIsOre?1:0):(plannedPayloadTons>0 && targetShovel!=null && targetShovel.isOre?1:0)</code> | binary |
| 286 | `truck.2.payloadTons` | 已装载物料吨数 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>payloadTons/193.0</code> | scaled |
| 287 | `truck.2.reservedLoadTons` | 已预留未完成装载吨数 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>plannedPayloadTons/193.0</code> | scaled |
| 288 | `truck.2.gradeKnown` | 已装载物料品位已知标志 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>isLoaded?1:0</code> | binary |
| 289 | `truck.2.payloadGrade` | 已装载物料品位，空载为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>isLoaded?payloadGrade:0.0</code> | unit |
| 290 | `truck.2.loadingGradeMean` | 正在装载物料的可观测品位估计均值 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>gs[0]</code> | unit |
| 291 | `truck.2.loadingGradeStd` | 正在装载物料的可观测品位估计标准差 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>gs[1]</code> | unit |
| 292 | `truck.2.loadingGradeInferred` | 正在装载物料品位是否全部可推知 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>gs[2]</code> | binary |
| 293 | `truck.2.loadTarget.0` | 装载目标one-hot（决策车辆清空） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(!decision && plannedPayloadTons>0 && targetShovel!=null?targetShovel.siteId:-1, 0)</code> | binary |
| 294 | `truck.2.loadTarget.1` | 装载目标one-hot（决策车辆清空） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(!decision && plannedPayloadTons>0 && targetShovel!=null?targetShovel.siteId:-1, 1)</code> | binary |
| 295 | `truck.2.loadTarget.2` | 装载目标one-hot（决策车辆清空） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(!decision && plannedPayloadTons>0 && targetShovel!=null?targetShovel.siteId:-1, 2)</code> | binary |
| 296 | `truck.2.loadTarget.3` | 装载目标one-hot（决策车辆清空） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(!decision && plannedPayloadTons>0 && targetShovel!=null?targetShovel.siteId:-1, 3)</code> | binary |
| 297 | `truck.2.dumpTarget.0` | 卸载目标one-hot（矿石0/废石1） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(isLoaded?(payloadIsOre?0:1):-1, 0)</code> | binary |
| 298 | `truck.2.dumpTarget.1` | 卸载目标one-hot（矿石0/废石1） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(isLoaded?(payloadIsOre?0:1):-1, 1)</code> | binary |
| 299 | `truck.2.node.0` | 当前道路节点one-hot | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(main.obsNodeIndex(currentNode), 0)</code> | binary |
| 300 | `truck.2.node.1` | 当前道路节点one-hot | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(main.obsNodeIndex(currentNode), 1)</code> | binary |
| 301 | `truck.2.node.2` | 当前道路节点one-hot | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(main.obsNodeIndex(currentNode), 2)</code> | binary |
| 302 | `truck.2.node.3` | 当前道路节点one-hot | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(main.obsNodeIndex(currentNode), 3)</code> | binary |
| 303 | `truck.2.node.4` | 当前道路节点one-hot | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(main.obsNodeIndex(currentNode), 4)</code> | binary |
| 304 | `truck.2.node.5` | 当前道路节点one-hot | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(main.obsNodeIndex(currentNode), 5)</code> | binary |
| 305 | `truck.2.node.6` | 当前道路节点one-hot | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(main.obsNodeIndex(currentNode), 6)</code> | binary |
| 306 | `truck.2.node.7` | 当前道路节点one-hot | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(main.obsNodeIndex(currentNode), 7)</code> | binary |
| 307 | `truck.2.node.8` | 当前道路节点one-hot | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(main.obsNodeIndex(currentNode), 8)</code> | binary |
| 308 | `truck.2.xM` | 车辆X坐标（米） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>main.toLengthUnits(getX(),METER)/10000.0</code> | scaled |
| 309 | `truck.2.yM` | 车辆Y坐标（米） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>main.toLengthUnits(getY(),METER)/10000.0</code> | scaled |
| 310 | `truck.2.speed` | 速度（米/秒） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>getSpeed()/10.0</code> | scaled |
| 311 | `truck.2.acceleration` | 动态加速度（米/秒平方） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>dynamicAccel/3.0</code> | scaled |
| 312 | `truck.2.segment.0` | 当前有向路段one-hot（决策车辆不编码运动段） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(seg, 0)</code> | binary |
| 313 | `truck.2.segment.1` | 当前有向路段one-hot（决策车辆不编码运动段） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(seg, 1)</code> | binary |
| 314 | `truck.2.segment.2` | 当前有向路段one-hot（决策车辆不编码运动段） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(seg, 2)</code> | binary |
| 315 | `truck.2.segment.3` | 当前有向路段one-hot（决策车辆不编码运动段） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(seg, 3)</code> | binary |
| 316 | `truck.2.segment.4` | 当前有向路段one-hot（决策车辆不编码运动段） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(seg, 4)</code> | binary |
| 317 | `truck.2.segment.5` | 当前有向路段one-hot（决策车辆不编码运动段） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(seg, 5)</code> | binary |
| 318 | `truck.2.segment.6` | 当前有向路段one-hot（决策车辆不编码运动段） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(seg, 6)</code> | binary |
| 319 | `truck.2.segment.7` | 当前有向路段one-hot（决策车辆不编码运动段） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(seg, 7)</code> | binary |
| 320 | `truck.2.segment.8` | 当前有向路段one-hot（决策车辆不编码运动段） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(seg, 8)</code> | binary |
| 321 | `truck.2.segment.9` | 当前有向路段one-hot（决策车辆不编码运动段） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(seg, 9)</code> | binary |
| 322 | `truck.2.segment.10` | 当前有向路段one-hot（决策车辆不编码运动段） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(seg, 10)</code> | binary |
| 323 | `truck.2.segment.11` | 当前有向路段one-hot（决策车辆不编码运动段） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(seg, 11)</code> | binary |
| 324 | `truck.2.segment.12` | 当前有向路段one-hot（决策车辆不编码运动段） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(seg, 12)</code> | binary |
| 325 | `truck.2.segment.13` | 当前有向路段one-hot（决策车辆不编码运动段） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(seg, 13)</code> | binary |
| 326 | `truck.2.segment.14` | 当前有向路段one-hot（决策车辆不编码运动段） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(seg, 14)</code> | binary |
| 327 | `truck.2.segment.15` | 当前有向路段one-hot（决策车辆不编码运动段） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(seg, 15)</code> | binary |
| 328 | `truck.2.segmentRemaining` | 当前路段剩余距离（米） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>remaining/10000.0</code> | scaled |
| 329 | `truck.2.routeRemaining` | 当前路线剩余距离（米） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>totalRemaining/10000.0</code> | scaled |
| 330 | `truck.2.routeOrder.0` | 对应路段在剩余路线的次序，未经过为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>routeOrder[0] = (j-currentSegmentIndex+1.0)/16.0 or 0</code> | unit |
| 331 | `truck.2.routeOrder.1` | 对应路段在剩余路线的次序，未经过为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>routeOrder[1] = (j-currentSegmentIndex+1.0)/16.0 or 0</code> | unit |
| 332 | `truck.2.routeOrder.2` | 对应路段在剩余路线的次序，未经过为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>routeOrder[2] = (j-currentSegmentIndex+1.0)/16.0 or 0</code> | unit |
| 333 | `truck.2.routeOrder.3` | 对应路段在剩余路线的次序，未经过为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>routeOrder[3] = (j-currentSegmentIndex+1.0)/16.0 or 0</code> | unit |
| 334 | `truck.2.routeOrder.4` | 对应路段在剩余路线的次序，未经过为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>routeOrder[4] = (j-currentSegmentIndex+1.0)/16.0 or 0</code> | unit |
| 335 | `truck.2.routeOrder.5` | 对应路段在剩余路线的次序，未经过为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>routeOrder[5] = (j-currentSegmentIndex+1.0)/16.0 or 0</code> | unit |
| 336 | `truck.2.routeOrder.6` | 对应路段在剩余路线的次序，未经过为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>routeOrder[6] = (j-currentSegmentIndex+1.0)/16.0 or 0</code> | unit |
| 337 | `truck.2.routeOrder.7` | 对应路段在剩余路线的次序，未经过为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>routeOrder[7] = (j-currentSegmentIndex+1.0)/16.0 or 0</code> | unit |
| 338 | `truck.2.routeOrder.8` | 对应路段在剩余路线的次序，未经过为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>routeOrder[8] = (j-currentSegmentIndex+1.0)/16.0 or 0</code> | unit |
| 339 | `truck.2.routeOrder.9` | 对应路段在剩余路线的次序，未经过为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>routeOrder[9] = (j-currentSegmentIndex+1.0)/16.0 or 0</code> | unit |
| 340 | `truck.2.routeOrder.10` | 对应路段在剩余路线的次序，未经过为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>routeOrder[10] = (j-currentSegmentIndex+1.0)/16.0 or 0</code> | unit |
| 341 | `truck.2.routeOrder.11` | 对应路段在剩余路线的次序，未经过为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>routeOrder[11] = (j-currentSegmentIndex+1.0)/16.0 or 0</code> | unit |
| 342 | `truck.2.routeOrder.12` | 对应路段在剩余路线的次序，未经过为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>routeOrder[12] = (j-currentSegmentIndex+1.0)/16.0 or 0</code> | unit |
| 343 | `truck.2.routeOrder.13` | 对应路段在剩余路线的次序，未经过为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>routeOrder[13] = (j-currentSegmentIndex+1.0)/16.0 or 0</code> | unit |
| 344 | `truck.2.routeOrder.14` | 对应路段在剩余路线的次序，未经过为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>routeOrder[14] = (j-currentSegmentIndex+1.0)/16.0 or 0</code> | unit |
| 345 | `truck.2.routeOrder.15` | 对应路段在剩余路线的次序，未经过为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>routeOrder[15] = (j-currentSegmentIndex+1.0)/16.0 or 0</code> | unit |
| 346 | `truck.2.laneRank` | 当前路段车辆进入顺序排位 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>seg>=0?(ahead+1.0)/9.0:0.0</code> | unit |
| 347 | `truck.2.initialDispatched` | 是否完成首次派车 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>initialDispatchDone?1:0</code> | binary |
| 348 | `truck.2.initialPredecessor` | 首次派车前驱车辆ID编码，无前驱为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>initialPredecessor==null?0:(initialPredecessor.truckId+1.0)/9.0</code> | unit |
| 349 | `truck.2.loadWaitAge` | 等待装载资源已用时间 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>isWaitingForLoadResource?Math.max(0.0,now-60.0*queueEnterTime)/28800.0:0.0</code> | unit |
| 350 | `truck.2.dumpWaitAge` | 等待卸载资源已用时间 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>isWaitingForDumpResource?Math.max(0.0,now-60.0*dumpQueueEnterTime)/28800.0:0.0</code> | unit |
| 351 | `truck.2.loadAge` | 当前装载服务已用时间 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>loading?Math.max(0.0,now-60.0*loadStartTime)/600.0:0.0</code> | scaled |
| 352 | `truck.2.loadMean` | 当前载荷平均装载时间（分钟） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>loading?targetShovel.obsMeanLoadMinutes(plannedPayloadTons)/10.0:0.0</code> | scaled |
| 353 | `truck.2.loadMaterialStart` | 当前装载在物料序列中的起始吨位 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>loading?obsLoadMaterialStart/30000.0:0.0</code> | scaled |
| 354 | `truck.2.dumpAge` | 当前卸载服务已用时间 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>dumping?Math.max(0.0,now-60.0*dumpServiceStartTime)/600.0:0.0</code> | scaled |
| 355 | `truck.2.dumpMean` | 当前车辆平均卸载时间（分钟） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>dumping?main.getDumpSiteById(targetDumpSiteId).obsMeanDumpMinutes(this)/10.0:0.0</code> | scaled |
| 356 | `truck.2.freeSamples` | 自由行驶速度估计样本数 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>obsFreeCount/1000.0</code> | scaled |
| 357 | `truck.2.freeRatioMean` | 可观测自由流速度比样本均值 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>obsFreeCount>0?obsFreeMean:0.0</code> | scaled |
| 358 | `truck.2.freeRatioStd` | 可观测自由流速度比样本标准差 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>obsFreeCount>1?Math.sqrt(Math.max(0.0,obsFreeM2/(obsFreeCount-1))):0.0</code> | scaled |
| 359 | `truck.2.motion.0.valid` | 槽位或历史样本是否有效 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:1</code> | binary |
| 360 | `truck.2.motion.0.age` | 运动历史样本距当前时刻秒数 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:Math.max(0.0,now-h[0])/28800.0</code> | unit |
| 361 | `truck.2.motion.0.speed` | 速度（米/秒） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[1]/10.0</code> | scaled |
| 362 | `truck.2.motion.0.acceleration` | 动态加速度（米/秒平方） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[2]/3.0</code> | scaled |
| 363 | `truck.2.motion.0.hasFront` | 历史样本是否存在前车 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[3]</code> | binary |
| 364 | `truck.2.motion.0.frontGap` | 历史前车间距（米） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[4]/10000.0</code> | scaled |
| 365 | `truck.2.motion.0.frontSpeed` | 历史前车速度（米/秒） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[5]/10.0</code> | scaled |
| 366 | `truck.2.motion.1.valid` | 槽位或历史样本是否有效 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:1</code> | binary |
| 367 | `truck.2.motion.1.age` | 运动历史样本距当前时刻秒数 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:Math.max(0.0,now-h[0])/28800.0</code> | unit |
| 368 | `truck.2.motion.1.speed` | 速度（米/秒） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[1]/10.0</code> | scaled |
| 369 | `truck.2.motion.1.acceleration` | 动态加速度（米/秒平方） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[2]/3.0</code> | scaled |
| 370 | `truck.2.motion.1.hasFront` | 历史样本是否存在前车 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[3]</code> | binary |
| 371 | `truck.2.motion.1.frontGap` | 历史前车间距（米） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[4]/10000.0</code> | scaled |
| 372 | `truck.2.motion.1.frontSpeed` | 历史前车速度（米/秒） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[5]/10.0</code> | scaled |
| 373 | `truck.2.motion.2.valid` | 槽位或历史样本是否有效 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:1</code> | binary |
| 374 | `truck.2.motion.2.age` | 运动历史样本距当前时刻秒数 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:Math.max(0.0,now-h[0])/28800.0</code> | unit |
| 375 | `truck.2.motion.2.speed` | 速度（米/秒） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[1]/10.0</code> | scaled |
| 376 | `truck.2.motion.2.acceleration` | 动态加速度（米/秒平方） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[2]/3.0</code> | scaled |
| 377 | `truck.2.motion.2.hasFront` | 历史样本是否存在前车 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[3]</code> | binary |
| 378 | `truck.2.motion.2.frontGap` | 历史前车间距（米） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[4]/10000.0</code> | scaled |
| 379 | `truck.2.motion.2.frontSpeed` | 历史前车速度（米/秒） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[5]/10.0</code> | scaled |
| 380 | `truck.2.motion.3.valid` | 槽位或历史样本是否有效 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:1</code> | binary |
| 381 | `truck.2.motion.3.age` | 运动历史样本距当前时刻秒数 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:Math.max(0.0,now-h[0])/28800.0</code> | unit |
| 382 | `truck.2.motion.3.speed` | 速度（米/秒） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[1]/10.0</code> | scaled |
| 383 | `truck.2.motion.3.acceleration` | 动态加速度（米/秒平方） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[2]/3.0</code> | scaled |
| 384 | `truck.2.motion.3.hasFront` | 历史样本是否存在前车 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[3]</code> | binary |
| 385 | `truck.2.motion.3.frontGap` | 历史前车间距（米） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[4]/10000.0</code> | scaled |
| 386 | `truck.2.motion.3.frontSpeed` | 历史前车速度（米/秒） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[5]/10.0</code> | scaled |
| 387 | `truck.3.ego` | 当前需要派车的车辆标志 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>decision?1:0</code> | binary |
| 388 | `truck.3.type.0` | 车型类别0/1/2 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(truckType, 0)</code> | binary |
| 389 | `truck.3.type.1` | 车型类别0/1/2 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(truckType, 1)</code> | binary |
| 390 | `truck.3.type.2` | 车型类别0/1/2 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(truckType, 2)</code> | binary |
| 391 | `truck.3.phase.0` | 执行阶段类别0..11（详见审计报告） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(phase, 0)</code> | binary |
| 392 | `truck.3.phase.1` | 执行阶段类别0..11（详见审计报告） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(phase, 1)</code> | binary |
| 393 | `truck.3.phase.2` | 执行阶段类别0..11（详见审计报告） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(phase, 2)</code> | binary |
| 394 | `truck.3.phase.3` | 执行阶段类别0..11（详见审计报告） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(phase, 3)</code> | binary |
| 395 | `truck.3.phase.4` | 执行阶段类别0..11（详见审计报告） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(phase, 4)</code> | binary |
| 396 | `truck.3.phase.5` | 执行阶段类别0..11（详见审计报告） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(phase, 5)</code> | binary |
| 397 | `truck.3.phase.6` | 执行阶段类别0..11（详见审计报告） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(phase, 6)</code> | binary |
| 398 | `truck.3.phase.7` | 执行阶段类别0..11（详见审计报告） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(phase, 7)</code> | binary |
| 399 | `truck.3.phase.8` | 执行阶段类别0..11（详见审计报告） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(phase, 8)</code> | binary |
| 400 | `truck.3.phase.9` | 执行阶段类别0..11（详见审计报告） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(phase, 9)</code> | binary |
| 401 | `truck.3.phase.10` | 执行阶段类别0..11（详见审计报告） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(phase, 10)</code> | binary |
| 402 | `truck.3.phase.11` | 执行阶段类别0..11（详见审计报告） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(phase, 11)</code> | binary |
| 403 | `truck.3.capacity` | 车辆载重能力或卸载点服务并发容量（依据公式） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>capacity/193.0</code> | scaled |
| 404 | `truck.3.loaded` | 有载标志 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>isLoaded?1:0</code> | binary |
| 405 | `truck.3.ore` | 载荷或已预留装载物是否为矿石 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>isLoaded?(payloadIsOre?1:0):(plannedPayloadTons>0 && targetShovel!=null && targetShovel.isOre?1:0)</code> | binary |
| 406 | `truck.3.payloadTons` | 已装载物料吨数 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>payloadTons/193.0</code> | scaled |
| 407 | `truck.3.reservedLoadTons` | 已预留未完成装载吨数 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>plannedPayloadTons/193.0</code> | scaled |
| 408 | `truck.3.gradeKnown` | 已装载物料品位已知标志 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>isLoaded?1:0</code> | binary |
| 409 | `truck.3.payloadGrade` | 已装载物料品位，空载为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>isLoaded?payloadGrade:0.0</code> | unit |
| 410 | `truck.3.loadingGradeMean` | 正在装载物料的可观测品位估计均值 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>gs[0]</code> | unit |
| 411 | `truck.3.loadingGradeStd` | 正在装载物料的可观测品位估计标准差 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>gs[1]</code> | unit |
| 412 | `truck.3.loadingGradeInferred` | 正在装载物料品位是否全部可推知 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>gs[2]</code> | binary |
| 413 | `truck.3.loadTarget.0` | 装载目标one-hot（决策车辆清空） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(!decision && plannedPayloadTons>0 && targetShovel!=null?targetShovel.siteId:-1, 0)</code> | binary |
| 414 | `truck.3.loadTarget.1` | 装载目标one-hot（决策车辆清空） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(!decision && plannedPayloadTons>0 && targetShovel!=null?targetShovel.siteId:-1, 1)</code> | binary |
| 415 | `truck.3.loadTarget.2` | 装载目标one-hot（决策车辆清空） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(!decision && plannedPayloadTons>0 && targetShovel!=null?targetShovel.siteId:-1, 2)</code> | binary |
| 416 | `truck.3.loadTarget.3` | 装载目标one-hot（决策车辆清空） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(!decision && plannedPayloadTons>0 && targetShovel!=null?targetShovel.siteId:-1, 3)</code> | binary |
| 417 | `truck.3.dumpTarget.0` | 卸载目标one-hot（矿石0/废石1） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(isLoaded?(payloadIsOre?0:1):-1, 0)</code> | binary |
| 418 | `truck.3.dumpTarget.1` | 卸载目标one-hot（矿石0/废石1） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(isLoaded?(payloadIsOre?0:1):-1, 1)</code> | binary |
| 419 | `truck.3.node.0` | 当前道路节点one-hot | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(main.obsNodeIndex(currentNode), 0)</code> | binary |
| 420 | `truck.3.node.1` | 当前道路节点one-hot | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(main.obsNodeIndex(currentNode), 1)</code> | binary |
| 421 | `truck.3.node.2` | 当前道路节点one-hot | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(main.obsNodeIndex(currentNode), 2)</code> | binary |
| 422 | `truck.3.node.3` | 当前道路节点one-hot | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(main.obsNodeIndex(currentNode), 3)</code> | binary |
| 423 | `truck.3.node.4` | 当前道路节点one-hot | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(main.obsNodeIndex(currentNode), 4)</code> | binary |
| 424 | `truck.3.node.5` | 当前道路节点one-hot | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(main.obsNodeIndex(currentNode), 5)</code> | binary |
| 425 | `truck.3.node.6` | 当前道路节点one-hot | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(main.obsNodeIndex(currentNode), 6)</code> | binary |
| 426 | `truck.3.node.7` | 当前道路节点one-hot | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(main.obsNodeIndex(currentNode), 7)</code> | binary |
| 427 | `truck.3.node.8` | 当前道路节点one-hot | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(main.obsNodeIndex(currentNode), 8)</code> | binary |
| 428 | `truck.3.xM` | 车辆X坐标（米） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>main.toLengthUnits(getX(),METER)/10000.0</code> | scaled |
| 429 | `truck.3.yM` | 车辆Y坐标（米） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>main.toLengthUnits(getY(),METER)/10000.0</code> | scaled |
| 430 | `truck.3.speed` | 速度（米/秒） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>getSpeed()/10.0</code> | scaled |
| 431 | `truck.3.acceleration` | 动态加速度（米/秒平方） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>dynamicAccel/3.0</code> | scaled |
| 432 | `truck.3.segment.0` | 当前有向路段one-hot（决策车辆不编码运动段） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(seg, 0)</code> | binary |
| 433 | `truck.3.segment.1` | 当前有向路段one-hot（决策车辆不编码运动段） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(seg, 1)</code> | binary |
| 434 | `truck.3.segment.2` | 当前有向路段one-hot（决策车辆不编码运动段） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(seg, 2)</code> | binary |
| 435 | `truck.3.segment.3` | 当前有向路段one-hot（决策车辆不编码运动段） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(seg, 3)</code> | binary |
| 436 | `truck.3.segment.4` | 当前有向路段one-hot（决策车辆不编码运动段） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(seg, 4)</code> | binary |
| 437 | `truck.3.segment.5` | 当前有向路段one-hot（决策车辆不编码运动段） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(seg, 5)</code> | binary |
| 438 | `truck.3.segment.6` | 当前有向路段one-hot（决策车辆不编码运动段） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(seg, 6)</code> | binary |
| 439 | `truck.3.segment.7` | 当前有向路段one-hot（决策车辆不编码运动段） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(seg, 7)</code> | binary |
| 440 | `truck.3.segment.8` | 当前有向路段one-hot（决策车辆不编码运动段） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(seg, 8)</code> | binary |
| 441 | `truck.3.segment.9` | 当前有向路段one-hot（决策车辆不编码运动段） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(seg, 9)</code> | binary |
| 442 | `truck.3.segment.10` | 当前有向路段one-hot（决策车辆不编码运动段） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(seg, 10)</code> | binary |
| 443 | `truck.3.segment.11` | 当前有向路段one-hot（决策车辆不编码运动段） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(seg, 11)</code> | binary |
| 444 | `truck.3.segment.12` | 当前有向路段one-hot（决策车辆不编码运动段） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(seg, 12)</code> | binary |
| 445 | `truck.3.segment.13` | 当前有向路段one-hot（决策车辆不编码运动段） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(seg, 13)</code> | binary |
| 446 | `truck.3.segment.14` | 当前有向路段one-hot（决策车辆不编码运动段） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(seg, 14)</code> | binary |
| 447 | `truck.3.segment.15` | 当前有向路段one-hot（决策车辆不编码运动段） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(seg, 15)</code> | binary |
| 448 | `truck.3.segmentRemaining` | 当前路段剩余距离（米） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>remaining/10000.0</code> | scaled |
| 449 | `truck.3.routeRemaining` | 当前路线剩余距离（米） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>totalRemaining/10000.0</code> | scaled |
| 450 | `truck.3.routeOrder.0` | 对应路段在剩余路线的次序，未经过为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>routeOrder[0] = (j-currentSegmentIndex+1.0)/16.0 or 0</code> | unit |
| 451 | `truck.3.routeOrder.1` | 对应路段在剩余路线的次序，未经过为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>routeOrder[1] = (j-currentSegmentIndex+1.0)/16.0 or 0</code> | unit |
| 452 | `truck.3.routeOrder.2` | 对应路段在剩余路线的次序，未经过为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>routeOrder[2] = (j-currentSegmentIndex+1.0)/16.0 or 0</code> | unit |
| 453 | `truck.3.routeOrder.3` | 对应路段在剩余路线的次序，未经过为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>routeOrder[3] = (j-currentSegmentIndex+1.0)/16.0 or 0</code> | unit |
| 454 | `truck.3.routeOrder.4` | 对应路段在剩余路线的次序，未经过为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>routeOrder[4] = (j-currentSegmentIndex+1.0)/16.0 or 0</code> | unit |
| 455 | `truck.3.routeOrder.5` | 对应路段在剩余路线的次序，未经过为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>routeOrder[5] = (j-currentSegmentIndex+1.0)/16.0 or 0</code> | unit |
| 456 | `truck.3.routeOrder.6` | 对应路段在剩余路线的次序，未经过为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>routeOrder[6] = (j-currentSegmentIndex+1.0)/16.0 or 0</code> | unit |
| 457 | `truck.3.routeOrder.7` | 对应路段在剩余路线的次序，未经过为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>routeOrder[7] = (j-currentSegmentIndex+1.0)/16.0 or 0</code> | unit |
| 458 | `truck.3.routeOrder.8` | 对应路段在剩余路线的次序，未经过为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>routeOrder[8] = (j-currentSegmentIndex+1.0)/16.0 or 0</code> | unit |
| 459 | `truck.3.routeOrder.9` | 对应路段在剩余路线的次序，未经过为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>routeOrder[9] = (j-currentSegmentIndex+1.0)/16.0 or 0</code> | unit |
| 460 | `truck.3.routeOrder.10` | 对应路段在剩余路线的次序，未经过为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>routeOrder[10] = (j-currentSegmentIndex+1.0)/16.0 or 0</code> | unit |
| 461 | `truck.3.routeOrder.11` | 对应路段在剩余路线的次序，未经过为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>routeOrder[11] = (j-currentSegmentIndex+1.0)/16.0 or 0</code> | unit |
| 462 | `truck.3.routeOrder.12` | 对应路段在剩余路线的次序，未经过为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>routeOrder[12] = (j-currentSegmentIndex+1.0)/16.0 or 0</code> | unit |
| 463 | `truck.3.routeOrder.13` | 对应路段在剩余路线的次序，未经过为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>routeOrder[13] = (j-currentSegmentIndex+1.0)/16.0 or 0</code> | unit |
| 464 | `truck.3.routeOrder.14` | 对应路段在剩余路线的次序，未经过为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>routeOrder[14] = (j-currentSegmentIndex+1.0)/16.0 or 0</code> | unit |
| 465 | `truck.3.routeOrder.15` | 对应路段在剩余路线的次序，未经过为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>routeOrder[15] = (j-currentSegmentIndex+1.0)/16.0 or 0</code> | unit |
| 466 | `truck.3.laneRank` | 当前路段车辆进入顺序排位 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>seg>=0?(ahead+1.0)/9.0:0.0</code> | unit |
| 467 | `truck.3.initialDispatched` | 是否完成首次派车 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>initialDispatchDone?1:0</code> | binary |
| 468 | `truck.3.initialPredecessor` | 首次派车前驱车辆ID编码，无前驱为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>initialPredecessor==null?0:(initialPredecessor.truckId+1.0)/9.0</code> | unit |
| 469 | `truck.3.loadWaitAge` | 等待装载资源已用时间 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>isWaitingForLoadResource?Math.max(0.0,now-60.0*queueEnterTime)/28800.0:0.0</code> | unit |
| 470 | `truck.3.dumpWaitAge` | 等待卸载资源已用时间 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>isWaitingForDumpResource?Math.max(0.0,now-60.0*dumpQueueEnterTime)/28800.0:0.0</code> | unit |
| 471 | `truck.3.loadAge` | 当前装载服务已用时间 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>loading?Math.max(0.0,now-60.0*loadStartTime)/600.0:0.0</code> | scaled |
| 472 | `truck.3.loadMean` | 当前载荷平均装载时间（分钟） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>loading?targetShovel.obsMeanLoadMinutes(plannedPayloadTons)/10.0:0.0</code> | scaled |
| 473 | `truck.3.loadMaterialStart` | 当前装载在物料序列中的起始吨位 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>loading?obsLoadMaterialStart/30000.0:0.0</code> | scaled |
| 474 | `truck.3.dumpAge` | 当前卸载服务已用时间 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>dumping?Math.max(0.0,now-60.0*dumpServiceStartTime)/600.0:0.0</code> | scaled |
| 475 | `truck.3.dumpMean` | 当前车辆平均卸载时间（分钟） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>dumping?main.getDumpSiteById(targetDumpSiteId).obsMeanDumpMinutes(this)/10.0:0.0</code> | scaled |
| 476 | `truck.3.freeSamples` | 自由行驶速度估计样本数 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>obsFreeCount/1000.0</code> | scaled |
| 477 | `truck.3.freeRatioMean` | 可观测自由流速度比样本均值 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>obsFreeCount>0?obsFreeMean:0.0</code> | scaled |
| 478 | `truck.3.freeRatioStd` | 可观测自由流速度比样本标准差 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>obsFreeCount>1?Math.sqrt(Math.max(0.0,obsFreeM2/(obsFreeCount-1))):0.0</code> | scaled |
| 479 | `truck.3.motion.0.valid` | 槽位或历史样本是否有效 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:1</code> | binary |
| 480 | `truck.3.motion.0.age` | 运动历史样本距当前时刻秒数 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:Math.max(0.0,now-h[0])/28800.0</code> | unit |
| 481 | `truck.3.motion.0.speed` | 速度（米/秒） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[1]/10.0</code> | scaled |
| 482 | `truck.3.motion.0.acceleration` | 动态加速度（米/秒平方） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[2]/3.0</code> | scaled |
| 483 | `truck.3.motion.0.hasFront` | 历史样本是否存在前车 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[3]</code> | binary |
| 484 | `truck.3.motion.0.frontGap` | 历史前车间距（米） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[4]/10000.0</code> | scaled |
| 485 | `truck.3.motion.0.frontSpeed` | 历史前车速度（米/秒） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[5]/10.0</code> | scaled |
| 486 | `truck.3.motion.1.valid` | 槽位或历史样本是否有效 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:1</code> | binary |
| 487 | `truck.3.motion.1.age` | 运动历史样本距当前时刻秒数 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:Math.max(0.0,now-h[0])/28800.0</code> | unit |
| 488 | `truck.3.motion.1.speed` | 速度（米/秒） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[1]/10.0</code> | scaled |
| 489 | `truck.3.motion.1.acceleration` | 动态加速度（米/秒平方） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[2]/3.0</code> | scaled |
| 490 | `truck.3.motion.1.hasFront` | 历史样本是否存在前车 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[3]</code> | binary |
| 491 | `truck.3.motion.1.frontGap` | 历史前车间距（米） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[4]/10000.0</code> | scaled |
| 492 | `truck.3.motion.1.frontSpeed` | 历史前车速度（米/秒） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[5]/10.0</code> | scaled |
| 493 | `truck.3.motion.2.valid` | 槽位或历史样本是否有效 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:1</code> | binary |
| 494 | `truck.3.motion.2.age` | 运动历史样本距当前时刻秒数 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:Math.max(0.0,now-h[0])/28800.0</code> | unit |
| 495 | `truck.3.motion.2.speed` | 速度（米/秒） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[1]/10.0</code> | scaled |
| 496 | `truck.3.motion.2.acceleration` | 动态加速度（米/秒平方） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[2]/3.0</code> | scaled |
| 497 | `truck.3.motion.2.hasFront` | 历史样本是否存在前车 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[3]</code> | binary |
| 498 | `truck.3.motion.2.frontGap` | 历史前车间距（米） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[4]/10000.0</code> | scaled |
| 499 | `truck.3.motion.2.frontSpeed` | 历史前车速度（米/秒） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[5]/10.0</code> | scaled |
| 500 | `truck.3.motion.3.valid` | 槽位或历史样本是否有效 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:1</code> | binary |
| 501 | `truck.3.motion.3.age` | 运动历史样本距当前时刻秒数 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:Math.max(0.0,now-h[0])/28800.0</code> | unit |
| 502 | `truck.3.motion.3.speed` | 速度（米/秒） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[1]/10.0</code> | scaled |
| 503 | `truck.3.motion.3.acceleration` | 动态加速度（米/秒平方） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[2]/3.0</code> | scaled |
| 504 | `truck.3.motion.3.hasFront` | 历史样本是否存在前车 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[3]</code> | binary |
| 505 | `truck.3.motion.3.frontGap` | 历史前车间距（米） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[4]/10000.0</code> | scaled |
| 506 | `truck.3.motion.3.frontSpeed` | 历史前车速度（米/秒） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[5]/10.0</code> | scaled |
| 507 | `truck.4.ego` | 当前需要派车的车辆标志 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>decision?1:0</code> | binary |
| 508 | `truck.4.type.0` | 车型类别0/1/2 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(truckType, 0)</code> | binary |
| 509 | `truck.4.type.1` | 车型类别0/1/2 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(truckType, 1)</code> | binary |
| 510 | `truck.4.type.2` | 车型类别0/1/2 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(truckType, 2)</code> | binary |
| 511 | `truck.4.phase.0` | 执行阶段类别0..11（详见审计报告） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(phase, 0)</code> | binary |
| 512 | `truck.4.phase.1` | 执行阶段类别0..11（详见审计报告） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(phase, 1)</code> | binary |
| 513 | `truck.4.phase.2` | 执行阶段类别0..11（详见审计报告） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(phase, 2)</code> | binary |
| 514 | `truck.4.phase.3` | 执行阶段类别0..11（详见审计报告） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(phase, 3)</code> | binary |
| 515 | `truck.4.phase.4` | 执行阶段类别0..11（详见审计报告） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(phase, 4)</code> | binary |
| 516 | `truck.4.phase.5` | 执行阶段类别0..11（详见审计报告） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(phase, 5)</code> | binary |
| 517 | `truck.4.phase.6` | 执行阶段类别0..11（详见审计报告） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(phase, 6)</code> | binary |
| 518 | `truck.4.phase.7` | 执行阶段类别0..11（详见审计报告） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(phase, 7)</code> | binary |
| 519 | `truck.4.phase.8` | 执行阶段类别0..11（详见审计报告） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(phase, 8)</code> | binary |
| 520 | `truck.4.phase.9` | 执行阶段类别0..11（详见审计报告） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(phase, 9)</code> | binary |
| 521 | `truck.4.phase.10` | 执行阶段类别0..11（详见审计报告） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(phase, 10)</code> | binary |
| 522 | `truck.4.phase.11` | 执行阶段类别0..11（详见审计报告） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(phase, 11)</code> | binary |
| 523 | `truck.4.capacity` | 车辆载重能力或卸载点服务并发容量（依据公式） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>capacity/193.0</code> | scaled |
| 524 | `truck.4.loaded` | 有载标志 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>isLoaded?1:0</code> | binary |
| 525 | `truck.4.ore` | 载荷或已预留装载物是否为矿石 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>isLoaded?(payloadIsOre?1:0):(plannedPayloadTons>0 && targetShovel!=null && targetShovel.isOre?1:0)</code> | binary |
| 526 | `truck.4.payloadTons` | 已装载物料吨数 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>payloadTons/193.0</code> | scaled |
| 527 | `truck.4.reservedLoadTons` | 已预留未完成装载吨数 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>plannedPayloadTons/193.0</code> | scaled |
| 528 | `truck.4.gradeKnown` | 已装载物料品位已知标志 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>isLoaded?1:0</code> | binary |
| 529 | `truck.4.payloadGrade` | 已装载物料品位，空载为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>isLoaded?payloadGrade:0.0</code> | unit |
| 530 | `truck.4.loadingGradeMean` | 正在装载物料的可观测品位估计均值 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>gs[0]</code> | unit |
| 531 | `truck.4.loadingGradeStd` | 正在装载物料的可观测品位估计标准差 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>gs[1]</code> | unit |
| 532 | `truck.4.loadingGradeInferred` | 正在装载物料品位是否全部可推知 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>gs[2]</code> | binary |
| 533 | `truck.4.loadTarget.0` | 装载目标one-hot（决策车辆清空） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(!decision && plannedPayloadTons>0 && targetShovel!=null?targetShovel.siteId:-1, 0)</code> | binary |
| 534 | `truck.4.loadTarget.1` | 装载目标one-hot（决策车辆清空） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(!decision && plannedPayloadTons>0 && targetShovel!=null?targetShovel.siteId:-1, 1)</code> | binary |
| 535 | `truck.4.loadTarget.2` | 装载目标one-hot（决策车辆清空） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(!decision && plannedPayloadTons>0 && targetShovel!=null?targetShovel.siteId:-1, 2)</code> | binary |
| 536 | `truck.4.loadTarget.3` | 装载目标one-hot（决策车辆清空） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(!decision && plannedPayloadTons>0 && targetShovel!=null?targetShovel.siteId:-1, 3)</code> | binary |
| 537 | `truck.4.dumpTarget.0` | 卸载目标one-hot（矿石0/废石1） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(isLoaded?(payloadIsOre?0:1):-1, 0)</code> | binary |
| 538 | `truck.4.dumpTarget.1` | 卸载目标one-hot（矿石0/废石1） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(isLoaded?(payloadIsOre?0:1):-1, 1)</code> | binary |
| 539 | `truck.4.node.0` | 当前道路节点one-hot | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(main.obsNodeIndex(currentNode), 0)</code> | binary |
| 540 | `truck.4.node.1` | 当前道路节点one-hot | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(main.obsNodeIndex(currentNode), 1)</code> | binary |
| 541 | `truck.4.node.2` | 当前道路节点one-hot | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(main.obsNodeIndex(currentNode), 2)</code> | binary |
| 542 | `truck.4.node.3` | 当前道路节点one-hot | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(main.obsNodeIndex(currentNode), 3)</code> | binary |
| 543 | `truck.4.node.4` | 当前道路节点one-hot | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(main.obsNodeIndex(currentNode), 4)</code> | binary |
| 544 | `truck.4.node.5` | 当前道路节点one-hot | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(main.obsNodeIndex(currentNode), 5)</code> | binary |
| 545 | `truck.4.node.6` | 当前道路节点one-hot | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(main.obsNodeIndex(currentNode), 6)</code> | binary |
| 546 | `truck.4.node.7` | 当前道路节点one-hot | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(main.obsNodeIndex(currentNode), 7)</code> | binary |
| 547 | `truck.4.node.8` | 当前道路节点one-hot | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(main.obsNodeIndex(currentNode), 8)</code> | binary |
| 548 | `truck.4.xM` | 车辆X坐标（米） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>main.toLengthUnits(getX(),METER)/10000.0</code> | scaled |
| 549 | `truck.4.yM` | 车辆Y坐标（米） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>main.toLengthUnits(getY(),METER)/10000.0</code> | scaled |
| 550 | `truck.4.speed` | 速度（米/秒） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>getSpeed()/10.0</code> | scaled |
| 551 | `truck.4.acceleration` | 动态加速度（米/秒平方） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>dynamicAccel/3.0</code> | scaled |
| 552 | `truck.4.segment.0` | 当前有向路段one-hot（决策车辆不编码运动段） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(seg, 0)</code> | binary |
| 553 | `truck.4.segment.1` | 当前有向路段one-hot（决策车辆不编码运动段） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(seg, 1)</code> | binary |
| 554 | `truck.4.segment.2` | 当前有向路段one-hot（决策车辆不编码运动段） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(seg, 2)</code> | binary |
| 555 | `truck.4.segment.3` | 当前有向路段one-hot（决策车辆不编码运动段） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(seg, 3)</code> | binary |
| 556 | `truck.4.segment.4` | 当前有向路段one-hot（决策车辆不编码运动段） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(seg, 4)</code> | binary |
| 557 | `truck.4.segment.5` | 当前有向路段one-hot（决策车辆不编码运动段） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(seg, 5)</code> | binary |
| 558 | `truck.4.segment.6` | 当前有向路段one-hot（决策车辆不编码运动段） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(seg, 6)</code> | binary |
| 559 | `truck.4.segment.7` | 当前有向路段one-hot（决策车辆不编码运动段） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(seg, 7)</code> | binary |
| 560 | `truck.4.segment.8` | 当前有向路段one-hot（决策车辆不编码运动段） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(seg, 8)</code> | binary |
| 561 | `truck.4.segment.9` | 当前有向路段one-hot（决策车辆不编码运动段） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(seg, 9)</code> | binary |
| 562 | `truck.4.segment.10` | 当前有向路段one-hot（决策车辆不编码运动段） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(seg, 10)</code> | binary |
| 563 | `truck.4.segment.11` | 当前有向路段one-hot（决策车辆不编码运动段） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(seg, 11)</code> | binary |
| 564 | `truck.4.segment.12` | 当前有向路段one-hot（决策车辆不编码运动段） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(seg, 12)</code> | binary |
| 565 | `truck.4.segment.13` | 当前有向路段one-hot（决策车辆不编码运动段） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(seg, 13)</code> | binary |
| 566 | `truck.4.segment.14` | 当前有向路段one-hot（决策车辆不编码运动段） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(seg, 14)</code> | binary |
| 567 | `truck.4.segment.15` | 当前有向路段one-hot（决策车辆不编码运动段） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(seg, 15)</code> | binary |
| 568 | `truck.4.segmentRemaining` | 当前路段剩余距离（米） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>remaining/10000.0</code> | scaled |
| 569 | `truck.4.routeRemaining` | 当前路线剩余距离（米） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>totalRemaining/10000.0</code> | scaled |
| 570 | `truck.4.routeOrder.0` | 对应路段在剩余路线的次序，未经过为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>routeOrder[0] = (j-currentSegmentIndex+1.0)/16.0 or 0</code> | unit |
| 571 | `truck.4.routeOrder.1` | 对应路段在剩余路线的次序，未经过为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>routeOrder[1] = (j-currentSegmentIndex+1.0)/16.0 or 0</code> | unit |
| 572 | `truck.4.routeOrder.2` | 对应路段在剩余路线的次序，未经过为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>routeOrder[2] = (j-currentSegmentIndex+1.0)/16.0 or 0</code> | unit |
| 573 | `truck.4.routeOrder.3` | 对应路段在剩余路线的次序，未经过为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>routeOrder[3] = (j-currentSegmentIndex+1.0)/16.0 or 0</code> | unit |
| 574 | `truck.4.routeOrder.4` | 对应路段在剩余路线的次序，未经过为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>routeOrder[4] = (j-currentSegmentIndex+1.0)/16.0 or 0</code> | unit |
| 575 | `truck.4.routeOrder.5` | 对应路段在剩余路线的次序，未经过为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>routeOrder[5] = (j-currentSegmentIndex+1.0)/16.0 or 0</code> | unit |
| 576 | `truck.4.routeOrder.6` | 对应路段在剩余路线的次序，未经过为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>routeOrder[6] = (j-currentSegmentIndex+1.0)/16.0 or 0</code> | unit |
| 577 | `truck.4.routeOrder.7` | 对应路段在剩余路线的次序，未经过为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>routeOrder[7] = (j-currentSegmentIndex+1.0)/16.0 or 0</code> | unit |
| 578 | `truck.4.routeOrder.8` | 对应路段在剩余路线的次序，未经过为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>routeOrder[8] = (j-currentSegmentIndex+1.0)/16.0 or 0</code> | unit |
| 579 | `truck.4.routeOrder.9` | 对应路段在剩余路线的次序，未经过为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>routeOrder[9] = (j-currentSegmentIndex+1.0)/16.0 or 0</code> | unit |
| 580 | `truck.4.routeOrder.10` | 对应路段在剩余路线的次序，未经过为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>routeOrder[10] = (j-currentSegmentIndex+1.0)/16.0 or 0</code> | unit |
| 581 | `truck.4.routeOrder.11` | 对应路段在剩余路线的次序，未经过为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>routeOrder[11] = (j-currentSegmentIndex+1.0)/16.0 or 0</code> | unit |
| 582 | `truck.4.routeOrder.12` | 对应路段在剩余路线的次序，未经过为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>routeOrder[12] = (j-currentSegmentIndex+1.0)/16.0 or 0</code> | unit |
| 583 | `truck.4.routeOrder.13` | 对应路段在剩余路线的次序，未经过为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>routeOrder[13] = (j-currentSegmentIndex+1.0)/16.0 or 0</code> | unit |
| 584 | `truck.4.routeOrder.14` | 对应路段在剩余路线的次序，未经过为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>routeOrder[14] = (j-currentSegmentIndex+1.0)/16.0 or 0</code> | unit |
| 585 | `truck.4.routeOrder.15` | 对应路段在剩余路线的次序，未经过为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>routeOrder[15] = (j-currentSegmentIndex+1.0)/16.0 or 0</code> | unit |
| 586 | `truck.4.laneRank` | 当前路段车辆进入顺序排位 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>seg>=0?(ahead+1.0)/9.0:0.0</code> | unit |
| 587 | `truck.4.initialDispatched` | 是否完成首次派车 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>initialDispatchDone?1:0</code> | binary |
| 588 | `truck.4.initialPredecessor` | 首次派车前驱车辆ID编码，无前驱为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>initialPredecessor==null?0:(initialPredecessor.truckId+1.0)/9.0</code> | unit |
| 589 | `truck.4.loadWaitAge` | 等待装载资源已用时间 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>isWaitingForLoadResource?Math.max(0.0,now-60.0*queueEnterTime)/28800.0:0.0</code> | unit |
| 590 | `truck.4.dumpWaitAge` | 等待卸载资源已用时间 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>isWaitingForDumpResource?Math.max(0.0,now-60.0*dumpQueueEnterTime)/28800.0:0.0</code> | unit |
| 591 | `truck.4.loadAge` | 当前装载服务已用时间 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>loading?Math.max(0.0,now-60.0*loadStartTime)/600.0:0.0</code> | scaled |
| 592 | `truck.4.loadMean` | 当前载荷平均装载时间（分钟） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>loading?targetShovel.obsMeanLoadMinutes(plannedPayloadTons)/10.0:0.0</code> | scaled |
| 593 | `truck.4.loadMaterialStart` | 当前装载在物料序列中的起始吨位 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>loading?obsLoadMaterialStart/30000.0:0.0</code> | scaled |
| 594 | `truck.4.dumpAge` | 当前卸载服务已用时间 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>dumping?Math.max(0.0,now-60.0*dumpServiceStartTime)/600.0:0.0</code> | scaled |
| 595 | `truck.4.dumpMean` | 当前车辆平均卸载时间（分钟） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>dumping?main.getDumpSiteById(targetDumpSiteId).obsMeanDumpMinutes(this)/10.0:0.0</code> | scaled |
| 596 | `truck.4.freeSamples` | 自由行驶速度估计样本数 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>obsFreeCount/1000.0</code> | scaled |
| 597 | `truck.4.freeRatioMean` | 可观测自由流速度比样本均值 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>obsFreeCount>0?obsFreeMean:0.0</code> | scaled |
| 598 | `truck.4.freeRatioStd` | 可观测自由流速度比样本标准差 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>obsFreeCount>1?Math.sqrt(Math.max(0.0,obsFreeM2/(obsFreeCount-1))):0.0</code> | scaled |
| 599 | `truck.4.motion.0.valid` | 槽位或历史样本是否有效 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:1</code> | binary |
| 600 | `truck.4.motion.0.age` | 运动历史样本距当前时刻秒数 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:Math.max(0.0,now-h[0])/28800.0</code> | unit |
| 601 | `truck.4.motion.0.speed` | 速度（米/秒） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[1]/10.0</code> | scaled |
| 602 | `truck.4.motion.0.acceleration` | 动态加速度（米/秒平方） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[2]/3.0</code> | scaled |
| 603 | `truck.4.motion.0.hasFront` | 历史样本是否存在前车 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[3]</code> | binary |
| 604 | `truck.4.motion.0.frontGap` | 历史前车间距（米） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[4]/10000.0</code> | scaled |
| 605 | `truck.4.motion.0.frontSpeed` | 历史前车速度（米/秒） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[5]/10.0</code> | scaled |
| 606 | `truck.4.motion.1.valid` | 槽位或历史样本是否有效 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:1</code> | binary |
| 607 | `truck.4.motion.1.age` | 运动历史样本距当前时刻秒数 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:Math.max(0.0,now-h[0])/28800.0</code> | unit |
| 608 | `truck.4.motion.1.speed` | 速度（米/秒） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[1]/10.0</code> | scaled |
| 609 | `truck.4.motion.1.acceleration` | 动态加速度（米/秒平方） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[2]/3.0</code> | scaled |
| 610 | `truck.4.motion.1.hasFront` | 历史样本是否存在前车 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[3]</code> | binary |
| 611 | `truck.4.motion.1.frontGap` | 历史前车间距（米） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[4]/10000.0</code> | scaled |
| 612 | `truck.4.motion.1.frontSpeed` | 历史前车速度（米/秒） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[5]/10.0</code> | scaled |
| 613 | `truck.4.motion.2.valid` | 槽位或历史样本是否有效 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:1</code> | binary |
| 614 | `truck.4.motion.2.age` | 运动历史样本距当前时刻秒数 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:Math.max(0.0,now-h[0])/28800.0</code> | unit |
| 615 | `truck.4.motion.2.speed` | 速度（米/秒） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[1]/10.0</code> | scaled |
| 616 | `truck.4.motion.2.acceleration` | 动态加速度（米/秒平方） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[2]/3.0</code> | scaled |
| 617 | `truck.4.motion.2.hasFront` | 历史样本是否存在前车 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[3]</code> | binary |
| 618 | `truck.4.motion.2.frontGap` | 历史前车间距（米） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[4]/10000.0</code> | scaled |
| 619 | `truck.4.motion.2.frontSpeed` | 历史前车速度（米/秒） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[5]/10.0</code> | scaled |
| 620 | `truck.4.motion.3.valid` | 槽位或历史样本是否有效 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:1</code> | binary |
| 621 | `truck.4.motion.3.age` | 运动历史样本距当前时刻秒数 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:Math.max(0.0,now-h[0])/28800.0</code> | unit |
| 622 | `truck.4.motion.3.speed` | 速度（米/秒） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[1]/10.0</code> | scaled |
| 623 | `truck.4.motion.3.acceleration` | 动态加速度（米/秒平方） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[2]/3.0</code> | scaled |
| 624 | `truck.4.motion.3.hasFront` | 历史样本是否存在前车 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[3]</code> | binary |
| 625 | `truck.4.motion.3.frontGap` | 历史前车间距（米） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[4]/10000.0</code> | scaled |
| 626 | `truck.4.motion.3.frontSpeed` | 历史前车速度（米/秒） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[5]/10.0</code> | scaled |
| 627 | `truck.5.ego` | 当前需要派车的车辆标志 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>decision?1:0</code> | binary |
| 628 | `truck.5.type.0` | 车型类别0/1/2 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(truckType, 0)</code> | binary |
| 629 | `truck.5.type.1` | 车型类别0/1/2 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(truckType, 1)</code> | binary |
| 630 | `truck.5.type.2` | 车型类别0/1/2 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(truckType, 2)</code> | binary |
| 631 | `truck.5.phase.0` | 执行阶段类别0..11（详见审计报告） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(phase, 0)</code> | binary |
| 632 | `truck.5.phase.1` | 执行阶段类别0..11（详见审计报告） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(phase, 1)</code> | binary |
| 633 | `truck.5.phase.2` | 执行阶段类别0..11（详见审计报告） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(phase, 2)</code> | binary |
| 634 | `truck.5.phase.3` | 执行阶段类别0..11（详见审计报告） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(phase, 3)</code> | binary |
| 635 | `truck.5.phase.4` | 执行阶段类别0..11（详见审计报告） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(phase, 4)</code> | binary |
| 636 | `truck.5.phase.5` | 执行阶段类别0..11（详见审计报告） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(phase, 5)</code> | binary |
| 637 | `truck.5.phase.6` | 执行阶段类别0..11（详见审计报告） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(phase, 6)</code> | binary |
| 638 | `truck.5.phase.7` | 执行阶段类别0..11（详见审计报告） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(phase, 7)</code> | binary |
| 639 | `truck.5.phase.8` | 执行阶段类别0..11（详见审计报告） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(phase, 8)</code> | binary |
| 640 | `truck.5.phase.9` | 执行阶段类别0..11（详见审计报告） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(phase, 9)</code> | binary |
| 641 | `truck.5.phase.10` | 执行阶段类别0..11（详见审计报告） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(phase, 10)</code> | binary |
| 642 | `truck.5.phase.11` | 执行阶段类别0..11（详见审计报告） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(phase, 11)</code> | binary |
| 643 | `truck.5.capacity` | 车辆载重能力或卸载点服务并发容量（依据公式） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>capacity/193.0</code> | scaled |
| 644 | `truck.5.loaded` | 有载标志 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>isLoaded?1:0</code> | binary |
| 645 | `truck.5.ore` | 载荷或已预留装载物是否为矿石 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>isLoaded?(payloadIsOre?1:0):(plannedPayloadTons>0 && targetShovel!=null && targetShovel.isOre?1:0)</code> | binary |
| 646 | `truck.5.payloadTons` | 已装载物料吨数 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>payloadTons/193.0</code> | scaled |
| 647 | `truck.5.reservedLoadTons` | 已预留未完成装载吨数 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>plannedPayloadTons/193.0</code> | scaled |
| 648 | `truck.5.gradeKnown` | 已装载物料品位已知标志 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>isLoaded?1:0</code> | binary |
| 649 | `truck.5.payloadGrade` | 已装载物料品位，空载为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>isLoaded?payloadGrade:0.0</code> | unit |
| 650 | `truck.5.loadingGradeMean` | 正在装载物料的可观测品位估计均值 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>gs[0]</code> | unit |
| 651 | `truck.5.loadingGradeStd` | 正在装载物料的可观测品位估计标准差 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>gs[1]</code> | unit |
| 652 | `truck.5.loadingGradeInferred` | 正在装载物料品位是否全部可推知 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>gs[2]</code> | binary |
| 653 | `truck.5.loadTarget.0` | 装载目标one-hot（决策车辆清空） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(!decision && plannedPayloadTons>0 && targetShovel!=null?targetShovel.siteId:-1, 0)</code> | binary |
| 654 | `truck.5.loadTarget.1` | 装载目标one-hot（决策车辆清空） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(!decision && plannedPayloadTons>0 && targetShovel!=null?targetShovel.siteId:-1, 1)</code> | binary |
| 655 | `truck.5.loadTarget.2` | 装载目标one-hot（决策车辆清空） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(!decision && plannedPayloadTons>0 && targetShovel!=null?targetShovel.siteId:-1, 2)</code> | binary |
| 656 | `truck.5.loadTarget.3` | 装载目标one-hot（决策车辆清空） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(!decision && plannedPayloadTons>0 && targetShovel!=null?targetShovel.siteId:-1, 3)</code> | binary |
| 657 | `truck.5.dumpTarget.0` | 卸载目标one-hot（矿石0/废石1） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(isLoaded?(payloadIsOre?0:1):-1, 0)</code> | binary |
| 658 | `truck.5.dumpTarget.1` | 卸载目标one-hot（矿石0/废石1） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(isLoaded?(payloadIsOre?0:1):-1, 1)</code> | binary |
| 659 | `truck.5.node.0` | 当前道路节点one-hot | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(main.obsNodeIndex(currentNode), 0)</code> | binary |
| 660 | `truck.5.node.1` | 当前道路节点one-hot | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(main.obsNodeIndex(currentNode), 1)</code> | binary |
| 661 | `truck.5.node.2` | 当前道路节点one-hot | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(main.obsNodeIndex(currentNode), 2)</code> | binary |
| 662 | `truck.5.node.3` | 当前道路节点one-hot | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(main.obsNodeIndex(currentNode), 3)</code> | binary |
| 663 | `truck.5.node.4` | 当前道路节点one-hot | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(main.obsNodeIndex(currentNode), 4)</code> | binary |
| 664 | `truck.5.node.5` | 当前道路节点one-hot | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(main.obsNodeIndex(currentNode), 5)</code> | binary |
| 665 | `truck.5.node.6` | 当前道路节点one-hot | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(main.obsNodeIndex(currentNode), 6)</code> | binary |
| 666 | `truck.5.node.7` | 当前道路节点one-hot | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(main.obsNodeIndex(currentNode), 7)</code> | binary |
| 667 | `truck.5.node.8` | 当前道路节点one-hot | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(main.obsNodeIndex(currentNode), 8)</code> | binary |
| 668 | `truck.5.xM` | 车辆X坐标（米） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>main.toLengthUnits(getX(),METER)/10000.0</code> | scaled |
| 669 | `truck.5.yM` | 车辆Y坐标（米） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>main.toLengthUnits(getY(),METER)/10000.0</code> | scaled |
| 670 | `truck.5.speed` | 速度（米/秒） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>getSpeed()/10.0</code> | scaled |
| 671 | `truck.5.acceleration` | 动态加速度（米/秒平方） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>dynamicAccel/3.0</code> | scaled |
| 672 | `truck.5.segment.0` | 当前有向路段one-hot（决策车辆不编码运动段） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(seg, 0)</code> | binary |
| 673 | `truck.5.segment.1` | 当前有向路段one-hot（决策车辆不编码运动段） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(seg, 1)</code> | binary |
| 674 | `truck.5.segment.2` | 当前有向路段one-hot（决策车辆不编码运动段） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(seg, 2)</code> | binary |
| 675 | `truck.5.segment.3` | 当前有向路段one-hot（决策车辆不编码运动段） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(seg, 3)</code> | binary |
| 676 | `truck.5.segment.4` | 当前有向路段one-hot（决策车辆不编码运动段） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(seg, 4)</code> | binary |
| 677 | `truck.5.segment.5` | 当前有向路段one-hot（决策车辆不编码运动段） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(seg, 5)</code> | binary |
| 678 | `truck.5.segment.6` | 当前有向路段one-hot（决策车辆不编码运动段） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(seg, 6)</code> | binary |
| 679 | `truck.5.segment.7` | 当前有向路段one-hot（决策车辆不编码运动段） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(seg, 7)</code> | binary |
| 680 | `truck.5.segment.8` | 当前有向路段one-hot（决策车辆不编码运动段） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(seg, 8)</code> | binary |
| 681 | `truck.5.segment.9` | 当前有向路段one-hot（决策车辆不编码运动段） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(seg, 9)</code> | binary |
| 682 | `truck.5.segment.10` | 当前有向路段one-hot（决策车辆不编码运动段） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(seg, 10)</code> | binary |
| 683 | `truck.5.segment.11` | 当前有向路段one-hot（决策车辆不编码运动段） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(seg, 11)</code> | binary |
| 684 | `truck.5.segment.12` | 当前有向路段one-hot（决策车辆不编码运动段） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(seg, 12)</code> | binary |
| 685 | `truck.5.segment.13` | 当前有向路段one-hot（决策车辆不编码运动段） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(seg, 13)</code> | binary |
| 686 | `truck.5.segment.14` | 当前有向路段one-hot（决策车辆不编码运动段） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(seg, 14)</code> | binary |
| 687 | `truck.5.segment.15` | 当前有向路段one-hot（决策车辆不编码运动段） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(seg, 15)</code> | binary |
| 688 | `truck.5.segmentRemaining` | 当前路段剩余距离（米） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>remaining/10000.0</code> | scaled |
| 689 | `truck.5.routeRemaining` | 当前路线剩余距离（米） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>totalRemaining/10000.0</code> | scaled |
| 690 | `truck.5.routeOrder.0` | 对应路段在剩余路线的次序，未经过为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>routeOrder[0] = (j-currentSegmentIndex+1.0)/16.0 or 0</code> | unit |
| 691 | `truck.5.routeOrder.1` | 对应路段在剩余路线的次序，未经过为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>routeOrder[1] = (j-currentSegmentIndex+1.0)/16.0 or 0</code> | unit |
| 692 | `truck.5.routeOrder.2` | 对应路段在剩余路线的次序，未经过为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>routeOrder[2] = (j-currentSegmentIndex+1.0)/16.0 or 0</code> | unit |
| 693 | `truck.5.routeOrder.3` | 对应路段在剩余路线的次序，未经过为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>routeOrder[3] = (j-currentSegmentIndex+1.0)/16.0 or 0</code> | unit |
| 694 | `truck.5.routeOrder.4` | 对应路段在剩余路线的次序，未经过为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>routeOrder[4] = (j-currentSegmentIndex+1.0)/16.0 or 0</code> | unit |
| 695 | `truck.5.routeOrder.5` | 对应路段在剩余路线的次序，未经过为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>routeOrder[5] = (j-currentSegmentIndex+1.0)/16.0 or 0</code> | unit |
| 696 | `truck.5.routeOrder.6` | 对应路段在剩余路线的次序，未经过为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>routeOrder[6] = (j-currentSegmentIndex+1.0)/16.0 or 0</code> | unit |
| 697 | `truck.5.routeOrder.7` | 对应路段在剩余路线的次序，未经过为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>routeOrder[7] = (j-currentSegmentIndex+1.0)/16.0 or 0</code> | unit |
| 698 | `truck.5.routeOrder.8` | 对应路段在剩余路线的次序，未经过为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>routeOrder[8] = (j-currentSegmentIndex+1.0)/16.0 or 0</code> | unit |
| 699 | `truck.5.routeOrder.9` | 对应路段在剩余路线的次序，未经过为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>routeOrder[9] = (j-currentSegmentIndex+1.0)/16.0 or 0</code> | unit |
| 700 | `truck.5.routeOrder.10` | 对应路段在剩余路线的次序，未经过为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>routeOrder[10] = (j-currentSegmentIndex+1.0)/16.0 or 0</code> | unit |
| 701 | `truck.5.routeOrder.11` | 对应路段在剩余路线的次序，未经过为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>routeOrder[11] = (j-currentSegmentIndex+1.0)/16.0 or 0</code> | unit |
| 702 | `truck.5.routeOrder.12` | 对应路段在剩余路线的次序，未经过为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>routeOrder[12] = (j-currentSegmentIndex+1.0)/16.0 or 0</code> | unit |
| 703 | `truck.5.routeOrder.13` | 对应路段在剩余路线的次序，未经过为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>routeOrder[13] = (j-currentSegmentIndex+1.0)/16.0 or 0</code> | unit |
| 704 | `truck.5.routeOrder.14` | 对应路段在剩余路线的次序，未经过为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>routeOrder[14] = (j-currentSegmentIndex+1.0)/16.0 or 0</code> | unit |
| 705 | `truck.5.routeOrder.15` | 对应路段在剩余路线的次序，未经过为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>routeOrder[15] = (j-currentSegmentIndex+1.0)/16.0 or 0</code> | unit |
| 706 | `truck.5.laneRank` | 当前路段车辆进入顺序排位 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>seg>=0?(ahead+1.0)/9.0:0.0</code> | unit |
| 707 | `truck.5.initialDispatched` | 是否完成首次派车 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>initialDispatchDone?1:0</code> | binary |
| 708 | `truck.5.initialPredecessor` | 首次派车前驱车辆ID编码，无前驱为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>initialPredecessor==null?0:(initialPredecessor.truckId+1.0)/9.0</code> | unit |
| 709 | `truck.5.loadWaitAge` | 等待装载资源已用时间 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>isWaitingForLoadResource?Math.max(0.0,now-60.0*queueEnterTime)/28800.0:0.0</code> | unit |
| 710 | `truck.5.dumpWaitAge` | 等待卸载资源已用时间 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>isWaitingForDumpResource?Math.max(0.0,now-60.0*dumpQueueEnterTime)/28800.0:0.0</code> | unit |
| 711 | `truck.5.loadAge` | 当前装载服务已用时间 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>loading?Math.max(0.0,now-60.0*loadStartTime)/600.0:0.0</code> | scaled |
| 712 | `truck.5.loadMean` | 当前载荷平均装载时间（分钟） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>loading?targetShovel.obsMeanLoadMinutes(plannedPayloadTons)/10.0:0.0</code> | scaled |
| 713 | `truck.5.loadMaterialStart` | 当前装载在物料序列中的起始吨位 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>loading?obsLoadMaterialStart/30000.0:0.0</code> | scaled |
| 714 | `truck.5.dumpAge` | 当前卸载服务已用时间 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>dumping?Math.max(0.0,now-60.0*dumpServiceStartTime)/600.0:0.0</code> | scaled |
| 715 | `truck.5.dumpMean` | 当前车辆平均卸载时间（分钟） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>dumping?main.getDumpSiteById(targetDumpSiteId).obsMeanDumpMinutes(this)/10.0:0.0</code> | scaled |
| 716 | `truck.5.freeSamples` | 自由行驶速度估计样本数 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>obsFreeCount/1000.0</code> | scaled |
| 717 | `truck.5.freeRatioMean` | 可观测自由流速度比样本均值 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>obsFreeCount>0?obsFreeMean:0.0</code> | scaled |
| 718 | `truck.5.freeRatioStd` | 可观测自由流速度比样本标准差 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>obsFreeCount>1?Math.sqrt(Math.max(0.0,obsFreeM2/(obsFreeCount-1))):0.0</code> | scaled |
| 719 | `truck.5.motion.0.valid` | 槽位或历史样本是否有效 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:1</code> | binary |
| 720 | `truck.5.motion.0.age` | 运动历史样本距当前时刻秒数 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:Math.max(0.0,now-h[0])/28800.0</code> | unit |
| 721 | `truck.5.motion.0.speed` | 速度（米/秒） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[1]/10.0</code> | scaled |
| 722 | `truck.5.motion.0.acceleration` | 动态加速度（米/秒平方） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[2]/3.0</code> | scaled |
| 723 | `truck.5.motion.0.hasFront` | 历史样本是否存在前车 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[3]</code> | binary |
| 724 | `truck.5.motion.0.frontGap` | 历史前车间距（米） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[4]/10000.0</code> | scaled |
| 725 | `truck.5.motion.0.frontSpeed` | 历史前车速度（米/秒） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[5]/10.0</code> | scaled |
| 726 | `truck.5.motion.1.valid` | 槽位或历史样本是否有效 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:1</code> | binary |
| 727 | `truck.5.motion.1.age` | 运动历史样本距当前时刻秒数 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:Math.max(0.0,now-h[0])/28800.0</code> | unit |
| 728 | `truck.5.motion.1.speed` | 速度（米/秒） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[1]/10.0</code> | scaled |
| 729 | `truck.5.motion.1.acceleration` | 动态加速度（米/秒平方） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[2]/3.0</code> | scaled |
| 730 | `truck.5.motion.1.hasFront` | 历史样本是否存在前车 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[3]</code> | binary |
| 731 | `truck.5.motion.1.frontGap` | 历史前车间距（米） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[4]/10000.0</code> | scaled |
| 732 | `truck.5.motion.1.frontSpeed` | 历史前车速度（米/秒） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[5]/10.0</code> | scaled |
| 733 | `truck.5.motion.2.valid` | 槽位或历史样本是否有效 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:1</code> | binary |
| 734 | `truck.5.motion.2.age` | 运动历史样本距当前时刻秒数 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:Math.max(0.0,now-h[0])/28800.0</code> | unit |
| 735 | `truck.5.motion.2.speed` | 速度（米/秒） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[1]/10.0</code> | scaled |
| 736 | `truck.5.motion.2.acceleration` | 动态加速度（米/秒平方） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[2]/3.0</code> | scaled |
| 737 | `truck.5.motion.2.hasFront` | 历史样本是否存在前车 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[3]</code> | binary |
| 738 | `truck.5.motion.2.frontGap` | 历史前车间距（米） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[4]/10000.0</code> | scaled |
| 739 | `truck.5.motion.2.frontSpeed` | 历史前车速度（米/秒） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[5]/10.0</code> | scaled |
| 740 | `truck.5.motion.3.valid` | 槽位或历史样本是否有效 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:1</code> | binary |
| 741 | `truck.5.motion.3.age` | 运动历史样本距当前时刻秒数 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:Math.max(0.0,now-h[0])/28800.0</code> | unit |
| 742 | `truck.5.motion.3.speed` | 速度（米/秒） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[1]/10.0</code> | scaled |
| 743 | `truck.5.motion.3.acceleration` | 动态加速度（米/秒平方） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[2]/3.0</code> | scaled |
| 744 | `truck.5.motion.3.hasFront` | 历史样本是否存在前车 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[3]</code> | binary |
| 745 | `truck.5.motion.3.frontGap` | 历史前车间距（米） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[4]/10000.0</code> | scaled |
| 746 | `truck.5.motion.3.frontSpeed` | 历史前车速度（米/秒） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[5]/10.0</code> | scaled |
| 747 | `truck.6.ego` | 当前需要派车的车辆标志 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>decision?1:0</code> | binary |
| 748 | `truck.6.type.0` | 车型类别0/1/2 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(truckType, 0)</code> | binary |
| 749 | `truck.6.type.1` | 车型类别0/1/2 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(truckType, 1)</code> | binary |
| 750 | `truck.6.type.2` | 车型类别0/1/2 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(truckType, 2)</code> | binary |
| 751 | `truck.6.phase.0` | 执行阶段类别0..11（详见审计报告） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(phase, 0)</code> | binary |
| 752 | `truck.6.phase.1` | 执行阶段类别0..11（详见审计报告） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(phase, 1)</code> | binary |
| 753 | `truck.6.phase.2` | 执行阶段类别0..11（详见审计报告） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(phase, 2)</code> | binary |
| 754 | `truck.6.phase.3` | 执行阶段类别0..11（详见审计报告） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(phase, 3)</code> | binary |
| 755 | `truck.6.phase.4` | 执行阶段类别0..11（详见审计报告） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(phase, 4)</code> | binary |
| 756 | `truck.6.phase.5` | 执行阶段类别0..11（详见审计报告） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(phase, 5)</code> | binary |
| 757 | `truck.6.phase.6` | 执行阶段类别0..11（详见审计报告） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(phase, 6)</code> | binary |
| 758 | `truck.6.phase.7` | 执行阶段类别0..11（详见审计报告） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(phase, 7)</code> | binary |
| 759 | `truck.6.phase.8` | 执行阶段类别0..11（详见审计报告） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(phase, 8)</code> | binary |
| 760 | `truck.6.phase.9` | 执行阶段类别0..11（详见审计报告） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(phase, 9)</code> | binary |
| 761 | `truck.6.phase.10` | 执行阶段类别0..11（详见审计报告） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(phase, 10)</code> | binary |
| 762 | `truck.6.phase.11` | 执行阶段类别0..11（详见审计报告） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(phase, 11)</code> | binary |
| 763 | `truck.6.capacity` | 车辆载重能力或卸载点服务并发容量（依据公式） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>capacity/193.0</code> | scaled |
| 764 | `truck.6.loaded` | 有载标志 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>isLoaded?1:0</code> | binary |
| 765 | `truck.6.ore` | 载荷或已预留装载物是否为矿石 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>isLoaded?(payloadIsOre?1:0):(plannedPayloadTons>0 && targetShovel!=null && targetShovel.isOre?1:0)</code> | binary |
| 766 | `truck.6.payloadTons` | 已装载物料吨数 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>payloadTons/193.0</code> | scaled |
| 767 | `truck.6.reservedLoadTons` | 已预留未完成装载吨数 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>plannedPayloadTons/193.0</code> | scaled |
| 768 | `truck.6.gradeKnown` | 已装载物料品位已知标志 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>isLoaded?1:0</code> | binary |
| 769 | `truck.6.payloadGrade` | 已装载物料品位，空载为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>isLoaded?payloadGrade:0.0</code> | unit |
| 770 | `truck.6.loadingGradeMean` | 正在装载物料的可观测品位估计均值 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>gs[0]</code> | unit |
| 771 | `truck.6.loadingGradeStd` | 正在装载物料的可观测品位估计标准差 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>gs[1]</code> | unit |
| 772 | `truck.6.loadingGradeInferred` | 正在装载物料品位是否全部可推知 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>gs[2]</code> | binary |
| 773 | `truck.6.loadTarget.0` | 装载目标one-hot（决策车辆清空） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(!decision && plannedPayloadTons>0 && targetShovel!=null?targetShovel.siteId:-1, 0)</code> | binary |
| 774 | `truck.6.loadTarget.1` | 装载目标one-hot（决策车辆清空） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(!decision && plannedPayloadTons>0 && targetShovel!=null?targetShovel.siteId:-1, 1)</code> | binary |
| 775 | `truck.6.loadTarget.2` | 装载目标one-hot（决策车辆清空） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(!decision && plannedPayloadTons>0 && targetShovel!=null?targetShovel.siteId:-1, 2)</code> | binary |
| 776 | `truck.6.loadTarget.3` | 装载目标one-hot（决策车辆清空） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(!decision && plannedPayloadTons>0 && targetShovel!=null?targetShovel.siteId:-1, 3)</code> | binary |
| 777 | `truck.6.dumpTarget.0` | 卸载目标one-hot（矿石0/废石1） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(isLoaded?(payloadIsOre?0:1):-1, 0)</code> | binary |
| 778 | `truck.6.dumpTarget.1` | 卸载目标one-hot（矿石0/废石1） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(isLoaded?(payloadIsOre?0:1):-1, 1)</code> | binary |
| 779 | `truck.6.node.0` | 当前道路节点one-hot | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(main.obsNodeIndex(currentNode), 0)</code> | binary |
| 780 | `truck.6.node.1` | 当前道路节点one-hot | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(main.obsNodeIndex(currentNode), 1)</code> | binary |
| 781 | `truck.6.node.2` | 当前道路节点one-hot | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(main.obsNodeIndex(currentNode), 2)</code> | binary |
| 782 | `truck.6.node.3` | 当前道路节点one-hot | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(main.obsNodeIndex(currentNode), 3)</code> | binary |
| 783 | `truck.6.node.4` | 当前道路节点one-hot | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(main.obsNodeIndex(currentNode), 4)</code> | binary |
| 784 | `truck.6.node.5` | 当前道路节点one-hot | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(main.obsNodeIndex(currentNode), 5)</code> | binary |
| 785 | `truck.6.node.6` | 当前道路节点one-hot | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(main.obsNodeIndex(currentNode), 6)</code> | binary |
| 786 | `truck.6.node.7` | 当前道路节点one-hot | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(main.obsNodeIndex(currentNode), 7)</code> | binary |
| 787 | `truck.6.node.8` | 当前道路节点one-hot | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(main.obsNodeIndex(currentNode), 8)</code> | binary |
| 788 | `truck.6.xM` | 车辆X坐标（米） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>main.toLengthUnits(getX(),METER)/10000.0</code> | scaled |
| 789 | `truck.6.yM` | 车辆Y坐标（米） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>main.toLengthUnits(getY(),METER)/10000.0</code> | scaled |
| 790 | `truck.6.speed` | 速度（米/秒） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>getSpeed()/10.0</code> | scaled |
| 791 | `truck.6.acceleration` | 动态加速度（米/秒平方） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>dynamicAccel/3.0</code> | scaled |
| 792 | `truck.6.segment.0` | 当前有向路段one-hot（决策车辆不编码运动段） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(seg, 0)</code> | binary |
| 793 | `truck.6.segment.1` | 当前有向路段one-hot（决策车辆不编码运动段） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(seg, 1)</code> | binary |
| 794 | `truck.6.segment.2` | 当前有向路段one-hot（决策车辆不编码运动段） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(seg, 2)</code> | binary |
| 795 | `truck.6.segment.3` | 当前有向路段one-hot（决策车辆不编码运动段） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(seg, 3)</code> | binary |
| 796 | `truck.6.segment.4` | 当前有向路段one-hot（决策车辆不编码运动段） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(seg, 4)</code> | binary |
| 797 | `truck.6.segment.5` | 当前有向路段one-hot（决策车辆不编码运动段） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(seg, 5)</code> | binary |
| 798 | `truck.6.segment.6` | 当前有向路段one-hot（决策车辆不编码运动段） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(seg, 6)</code> | binary |
| 799 | `truck.6.segment.7` | 当前有向路段one-hot（决策车辆不编码运动段） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(seg, 7)</code> | binary |
| 800 | `truck.6.segment.8` | 当前有向路段one-hot（决策车辆不编码运动段） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(seg, 8)</code> | binary |
| 801 | `truck.6.segment.9` | 当前有向路段one-hot（决策车辆不编码运动段） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(seg, 9)</code> | binary |
| 802 | `truck.6.segment.10` | 当前有向路段one-hot（决策车辆不编码运动段） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(seg, 10)</code> | binary |
| 803 | `truck.6.segment.11` | 当前有向路段one-hot（决策车辆不编码运动段） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(seg, 11)</code> | binary |
| 804 | `truck.6.segment.12` | 当前有向路段one-hot（决策车辆不编码运动段） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(seg, 12)</code> | binary |
| 805 | `truck.6.segment.13` | 当前有向路段one-hot（决策车辆不编码运动段） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(seg, 13)</code> | binary |
| 806 | `truck.6.segment.14` | 当前有向路段one-hot（决策车辆不编码运动段） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(seg, 14)</code> | binary |
| 807 | `truck.6.segment.15` | 当前有向路段one-hot（决策车辆不编码运动段） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(seg, 15)</code> | binary |
| 808 | `truck.6.segmentRemaining` | 当前路段剩余距离（米） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>remaining/10000.0</code> | scaled |
| 809 | `truck.6.routeRemaining` | 当前路线剩余距离（米） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>totalRemaining/10000.0</code> | scaled |
| 810 | `truck.6.routeOrder.0` | 对应路段在剩余路线的次序，未经过为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>routeOrder[0] = (j-currentSegmentIndex+1.0)/16.0 or 0</code> | unit |
| 811 | `truck.6.routeOrder.1` | 对应路段在剩余路线的次序，未经过为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>routeOrder[1] = (j-currentSegmentIndex+1.0)/16.0 or 0</code> | unit |
| 812 | `truck.6.routeOrder.2` | 对应路段在剩余路线的次序，未经过为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>routeOrder[2] = (j-currentSegmentIndex+1.0)/16.0 or 0</code> | unit |
| 813 | `truck.6.routeOrder.3` | 对应路段在剩余路线的次序，未经过为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>routeOrder[3] = (j-currentSegmentIndex+1.0)/16.0 or 0</code> | unit |
| 814 | `truck.6.routeOrder.4` | 对应路段在剩余路线的次序，未经过为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>routeOrder[4] = (j-currentSegmentIndex+1.0)/16.0 or 0</code> | unit |
| 815 | `truck.6.routeOrder.5` | 对应路段在剩余路线的次序，未经过为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>routeOrder[5] = (j-currentSegmentIndex+1.0)/16.0 or 0</code> | unit |
| 816 | `truck.6.routeOrder.6` | 对应路段在剩余路线的次序，未经过为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>routeOrder[6] = (j-currentSegmentIndex+1.0)/16.0 or 0</code> | unit |
| 817 | `truck.6.routeOrder.7` | 对应路段在剩余路线的次序，未经过为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>routeOrder[7] = (j-currentSegmentIndex+1.0)/16.0 or 0</code> | unit |
| 818 | `truck.6.routeOrder.8` | 对应路段在剩余路线的次序，未经过为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>routeOrder[8] = (j-currentSegmentIndex+1.0)/16.0 or 0</code> | unit |
| 819 | `truck.6.routeOrder.9` | 对应路段在剩余路线的次序，未经过为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>routeOrder[9] = (j-currentSegmentIndex+1.0)/16.0 or 0</code> | unit |
| 820 | `truck.6.routeOrder.10` | 对应路段在剩余路线的次序，未经过为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>routeOrder[10] = (j-currentSegmentIndex+1.0)/16.0 or 0</code> | unit |
| 821 | `truck.6.routeOrder.11` | 对应路段在剩余路线的次序，未经过为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>routeOrder[11] = (j-currentSegmentIndex+1.0)/16.0 or 0</code> | unit |
| 822 | `truck.6.routeOrder.12` | 对应路段在剩余路线的次序，未经过为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>routeOrder[12] = (j-currentSegmentIndex+1.0)/16.0 or 0</code> | unit |
| 823 | `truck.6.routeOrder.13` | 对应路段在剩余路线的次序，未经过为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>routeOrder[13] = (j-currentSegmentIndex+1.0)/16.0 or 0</code> | unit |
| 824 | `truck.6.routeOrder.14` | 对应路段在剩余路线的次序，未经过为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>routeOrder[14] = (j-currentSegmentIndex+1.0)/16.0 or 0</code> | unit |
| 825 | `truck.6.routeOrder.15` | 对应路段在剩余路线的次序，未经过为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>routeOrder[15] = (j-currentSegmentIndex+1.0)/16.0 or 0</code> | unit |
| 826 | `truck.6.laneRank` | 当前路段车辆进入顺序排位 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>seg>=0?(ahead+1.0)/9.0:0.0</code> | unit |
| 827 | `truck.6.initialDispatched` | 是否完成首次派车 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>initialDispatchDone?1:0</code> | binary |
| 828 | `truck.6.initialPredecessor` | 首次派车前驱车辆ID编码，无前驱为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>initialPredecessor==null?0:(initialPredecessor.truckId+1.0)/9.0</code> | unit |
| 829 | `truck.6.loadWaitAge` | 等待装载资源已用时间 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>isWaitingForLoadResource?Math.max(0.0,now-60.0*queueEnterTime)/28800.0:0.0</code> | unit |
| 830 | `truck.6.dumpWaitAge` | 等待卸载资源已用时间 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>isWaitingForDumpResource?Math.max(0.0,now-60.0*dumpQueueEnterTime)/28800.0:0.0</code> | unit |
| 831 | `truck.6.loadAge` | 当前装载服务已用时间 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>loading?Math.max(0.0,now-60.0*loadStartTime)/600.0:0.0</code> | scaled |
| 832 | `truck.6.loadMean` | 当前载荷平均装载时间（分钟） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>loading?targetShovel.obsMeanLoadMinutes(plannedPayloadTons)/10.0:0.0</code> | scaled |
| 833 | `truck.6.loadMaterialStart` | 当前装载在物料序列中的起始吨位 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>loading?obsLoadMaterialStart/30000.0:0.0</code> | scaled |
| 834 | `truck.6.dumpAge` | 当前卸载服务已用时间 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>dumping?Math.max(0.0,now-60.0*dumpServiceStartTime)/600.0:0.0</code> | scaled |
| 835 | `truck.6.dumpMean` | 当前车辆平均卸载时间（分钟） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>dumping?main.getDumpSiteById(targetDumpSiteId).obsMeanDumpMinutes(this)/10.0:0.0</code> | scaled |
| 836 | `truck.6.freeSamples` | 自由行驶速度估计样本数 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>obsFreeCount/1000.0</code> | scaled |
| 837 | `truck.6.freeRatioMean` | 可观测自由流速度比样本均值 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>obsFreeCount>0?obsFreeMean:0.0</code> | scaled |
| 838 | `truck.6.freeRatioStd` | 可观测自由流速度比样本标准差 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>obsFreeCount>1?Math.sqrt(Math.max(0.0,obsFreeM2/(obsFreeCount-1))):0.0</code> | scaled |
| 839 | `truck.6.motion.0.valid` | 槽位或历史样本是否有效 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:1</code> | binary |
| 840 | `truck.6.motion.0.age` | 运动历史样本距当前时刻秒数 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:Math.max(0.0,now-h[0])/28800.0</code> | unit |
| 841 | `truck.6.motion.0.speed` | 速度（米/秒） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[1]/10.0</code> | scaled |
| 842 | `truck.6.motion.0.acceleration` | 动态加速度（米/秒平方） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[2]/3.0</code> | scaled |
| 843 | `truck.6.motion.0.hasFront` | 历史样本是否存在前车 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[3]</code> | binary |
| 844 | `truck.6.motion.0.frontGap` | 历史前车间距（米） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[4]/10000.0</code> | scaled |
| 845 | `truck.6.motion.0.frontSpeed` | 历史前车速度（米/秒） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[5]/10.0</code> | scaled |
| 846 | `truck.6.motion.1.valid` | 槽位或历史样本是否有效 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:1</code> | binary |
| 847 | `truck.6.motion.1.age` | 运动历史样本距当前时刻秒数 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:Math.max(0.0,now-h[0])/28800.0</code> | unit |
| 848 | `truck.6.motion.1.speed` | 速度（米/秒） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[1]/10.0</code> | scaled |
| 849 | `truck.6.motion.1.acceleration` | 动态加速度（米/秒平方） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[2]/3.0</code> | scaled |
| 850 | `truck.6.motion.1.hasFront` | 历史样本是否存在前车 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[3]</code> | binary |
| 851 | `truck.6.motion.1.frontGap` | 历史前车间距（米） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[4]/10000.0</code> | scaled |
| 852 | `truck.6.motion.1.frontSpeed` | 历史前车速度（米/秒） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[5]/10.0</code> | scaled |
| 853 | `truck.6.motion.2.valid` | 槽位或历史样本是否有效 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:1</code> | binary |
| 854 | `truck.6.motion.2.age` | 运动历史样本距当前时刻秒数 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:Math.max(0.0,now-h[0])/28800.0</code> | unit |
| 855 | `truck.6.motion.2.speed` | 速度（米/秒） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[1]/10.0</code> | scaled |
| 856 | `truck.6.motion.2.acceleration` | 动态加速度（米/秒平方） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[2]/3.0</code> | scaled |
| 857 | `truck.6.motion.2.hasFront` | 历史样本是否存在前车 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[3]</code> | binary |
| 858 | `truck.6.motion.2.frontGap` | 历史前车间距（米） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[4]/10000.0</code> | scaled |
| 859 | `truck.6.motion.2.frontSpeed` | 历史前车速度（米/秒） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[5]/10.0</code> | scaled |
| 860 | `truck.6.motion.3.valid` | 槽位或历史样本是否有效 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:1</code> | binary |
| 861 | `truck.6.motion.3.age` | 运动历史样本距当前时刻秒数 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:Math.max(0.0,now-h[0])/28800.0</code> | unit |
| 862 | `truck.6.motion.3.speed` | 速度（米/秒） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[1]/10.0</code> | scaled |
| 863 | `truck.6.motion.3.acceleration` | 动态加速度（米/秒平方） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[2]/3.0</code> | scaled |
| 864 | `truck.6.motion.3.hasFront` | 历史样本是否存在前车 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[3]</code> | binary |
| 865 | `truck.6.motion.3.frontGap` | 历史前车间距（米） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[4]/10000.0</code> | scaled |
| 866 | `truck.6.motion.3.frontSpeed` | 历史前车速度（米/秒） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[5]/10.0</code> | scaled |
| 867 | `truck.7.ego` | 当前需要派车的车辆标志 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>decision?1:0</code> | binary |
| 868 | `truck.7.type.0` | 车型类别0/1/2 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(truckType, 0)</code> | binary |
| 869 | `truck.7.type.1` | 车型类别0/1/2 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(truckType, 1)</code> | binary |
| 870 | `truck.7.type.2` | 车型类别0/1/2 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(truckType, 2)</code> | binary |
| 871 | `truck.7.phase.0` | 执行阶段类别0..11（详见审计报告） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(phase, 0)</code> | binary |
| 872 | `truck.7.phase.1` | 执行阶段类别0..11（详见审计报告） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(phase, 1)</code> | binary |
| 873 | `truck.7.phase.2` | 执行阶段类别0..11（详见审计报告） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(phase, 2)</code> | binary |
| 874 | `truck.7.phase.3` | 执行阶段类别0..11（详见审计报告） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(phase, 3)</code> | binary |
| 875 | `truck.7.phase.4` | 执行阶段类别0..11（详见审计报告） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(phase, 4)</code> | binary |
| 876 | `truck.7.phase.5` | 执行阶段类别0..11（详见审计报告） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(phase, 5)</code> | binary |
| 877 | `truck.7.phase.6` | 执行阶段类别0..11（详见审计报告） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(phase, 6)</code> | binary |
| 878 | `truck.7.phase.7` | 执行阶段类别0..11（详见审计报告） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(phase, 7)</code> | binary |
| 879 | `truck.7.phase.8` | 执行阶段类别0..11（详见审计报告） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(phase, 8)</code> | binary |
| 880 | `truck.7.phase.9` | 执行阶段类别0..11（详见审计报告） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(phase, 9)</code> | binary |
| 881 | `truck.7.phase.10` | 执行阶段类别0..11（详见审计报告） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(phase, 10)</code> | binary |
| 882 | `truck.7.phase.11` | 执行阶段类别0..11（详见审计报告） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(phase, 11)</code> | binary |
| 883 | `truck.7.capacity` | 车辆载重能力或卸载点服务并发容量（依据公式） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>capacity/193.0</code> | scaled |
| 884 | `truck.7.loaded` | 有载标志 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>isLoaded?1:0</code> | binary |
| 885 | `truck.7.ore` | 载荷或已预留装载物是否为矿石 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>isLoaded?(payloadIsOre?1:0):(plannedPayloadTons>0 && targetShovel!=null && targetShovel.isOre?1:0)</code> | binary |
| 886 | `truck.7.payloadTons` | 已装载物料吨数 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>payloadTons/193.0</code> | scaled |
| 887 | `truck.7.reservedLoadTons` | 已预留未完成装载吨数 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>plannedPayloadTons/193.0</code> | scaled |
| 888 | `truck.7.gradeKnown` | 已装载物料品位已知标志 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>isLoaded?1:0</code> | binary |
| 889 | `truck.7.payloadGrade` | 已装载物料品位，空载为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>isLoaded?payloadGrade:0.0</code> | unit |
| 890 | `truck.7.loadingGradeMean` | 正在装载物料的可观测品位估计均值 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>gs[0]</code> | unit |
| 891 | `truck.7.loadingGradeStd` | 正在装载物料的可观测品位估计标准差 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>gs[1]</code> | unit |
| 892 | `truck.7.loadingGradeInferred` | 正在装载物料品位是否全部可推知 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>gs[2]</code> | binary |
| 893 | `truck.7.loadTarget.0` | 装载目标one-hot（决策车辆清空） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(!decision && plannedPayloadTons>0 && targetShovel!=null?targetShovel.siteId:-1, 0)</code> | binary |
| 894 | `truck.7.loadTarget.1` | 装载目标one-hot（决策车辆清空） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(!decision && plannedPayloadTons>0 && targetShovel!=null?targetShovel.siteId:-1, 1)</code> | binary |
| 895 | `truck.7.loadTarget.2` | 装载目标one-hot（决策车辆清空） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(!decision && plannedPayloadTons>0 && targetShovel!=null?targetShovel.siteId:-1, 2)</code> | binary |
| 896 | `truck.7.loadTarget.3` | 装载目标one-hot（决策车辆清空） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(!decision && plannedPayloadTons>0 && targetShovel!=null?targetShovel.siteId:-1, 3)</code> | binary |
| 897 | `truck.7.dumpTarget.0` | 卸载目标one-hot（矿石0/废石1） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(isLoaded?(payloadIsOre?0:1):-1, 0)</code> | binary |
| 898 | `truck.7.dumpTarget.1` | 卸载目标one-hot（矿石0/废石1） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(isLoaded?(payloadIsOre?0:1):-1, 1)</code> | binary |
| 899 | `truck.7.node.0` | 当前道路节点one-hot | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(main.obsNodeIndex(currentNode), 0)</code> | binary |
| 900 | `truck.7.node.1` | 当前道路节点one-hot | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(main.obsNodeIndex(currentNode), 1)</code> | binary |
| 901 | `truck.7.node.2` | 当前道路节点one-hot | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(main.obsNodeIndex(currentNode), 2)</code> | binary |
| 902 | `truck.7.node.3` | 当前道路节点one-hot | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(main.obsNodeIndex(currentNode), 3)</code> | binary |
| 903 | `truck.7.node.4` | 当前道路节点one-hot | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(main.obsNodeIndex(currentNode), 4)</code> | binary |
| 904 | `truck.7.node.5` | 当前道路节点one-hot | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(main.obsNodeIndex(currentNode), 5)</code> | binary |
| 905 | `truck.7.node.6` | 当前道路节点one-hot | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(main.obsNodeIndex(currentNode), 6)</code> | binary |
| 906 | `truck.7.node.7` | 当前道路节点one-hot | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(main.obsNodeIndex(currentNode), 7)</code> | binary |
| 907 | `truck.7.node.8` | 当前道路节点one-hot | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(main.obsNodeIndex(currentNode), 8)</code> | binary |
| 908 | `truck.7.xM` | 车辆X坐标（米） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>main.toLengthUnits(getX(),METER)/10000.0</code> | scaled |
| 909 | `truck.7.yM` | 车辆Y坐标（米） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>main.toLengthUnits(getY(),METER)/10000.0</code> | scaled |
| 910 | `truck.7.speed` | 速度（米/秒） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>getSpeed()/10.0</code> | scaled |
| 911 | `truck.7.acceleration` | 动态加速度（米/秒平方） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>dynamicAccel/3.0</code> | scaled |
| 912 | `truck.7.segment.0` | 当前有向路段one-hot（决策车辆不编码运动段） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(seg, 0)</code> | binary |
| 913 | `truck.7.segment.1` | 当前有向路段one-hot（决策车辆不编码运动段） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(seg, 1)</code> | binary |
| 914 | `truck.7.segment.2` | 当前有向路段one-hot（决策车辆不编码运动段） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(seg, 2)</code> | binary |
| 915 | `truck.7.segment.3` | 当前有向路段one-hot（决策车辆不编码运动段） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(seg, 3)</code> | binary |
| 916 | `truck.7.segment.4` | 当前有向路段one-hot（决策车辆不编码运动段） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(seg, 4)</code> | binary |
| 917 | `truck.7.segment.5` | 当前有向路段one-hot（决策车辆不编码运动段） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(seg, 5)</code> | binary |
| 918 | `truck.7.segment.6` | 当前有向路段one-hot（决策车辆不编码运动段） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(seg, 6)</code> | binary |
| 919 | `truck.7.segment.7` | 当前有向路段one-hot（决策车辆不编码运动段） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(seg, 7)</code> | binary |
| 920 | `truck.7.segment.8` | 当前有向路段one-hot（决策车辆不编码运动段） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(seg, 8)</code> | binary |
| 921 | `truck.7.segment.9` | 当前有向路段one-hot（决策车辆不编码运动段） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(seg, 9)</code> | binary |
| 922 | `truck.7.segment.10` | 当前有向路段one-hot（决策车辆不编码运动段） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(seg, 10)</code> | binary |
| 923 | `truck.7.segment.11` | 当前有向路段one-hot（决策车辆不编码运动段） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(seg, 11)</code> | binary |
| 924 | `truck.7.segment.12` | 当前有向路段one-hot（决策车辆不编码运动段） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(seg, 12)</code> | binary |
| 925 | `truck.7.segment.13` | 当前有向路段one-hot（决策车辆不编码运动段） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(seg, 13)</code> | binary |
| 926 | `truck.7.segment.14` | 当前有向路段one-hot（决策车辆不编码运动段） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(seg, 14)</code> | binary |
| 927 | `truck.7.segment.15` | 当前有向路段one-hot（决策车辆不编码运动段） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(seg, 15)</code> | binary |
| 928 | `truck.7.segmentRemaining` | 当前路段剩余距离（米） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>remaining/10000.0</code> | scaled |
| 929 | `truck.7.routeRemaining` | 当前路线剩余距离（米） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>totalRemaining/10000.0</code> | scaled |
| 930 | `truck.7.routeOrder.0` | 对应路段在剩余路线的次序，未经过为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>routeOrder[0] = (j-currentSegmentIndex+1.0)/16.0 or 0</code> | unit |
| 931 | `truck.7.routeOrder.1` | 对应路段在剩余路线的次序，未经过为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>routeOrder[1] = (j-currentSegmentIndex+1.0)/16.0 or 0</code> | unit |
| 932 | `truck.7.routeOrder.2` | 对应路段在剩余路线的次序，未经过为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>routeOrder[2] = (j-currentSegmentIndex+1.0)/16.0 or 0</code> | unit |
| 933 | `truck.7.routeOrder.3` | 对应路段在剩余路线的次序，未经过为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>routeOrder[3] = (j-currentSegmentIndex+1.0)/16.0 or 0</code> | unit |
| 934 | `truck.7.routeOrder.4` | 对应路段在剩余路线的次序，未经过为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>routeOrder[4] = (j-currentSegmentIndex+1.0)/16.0 or 0</code> | unit |
| 935 | `truck.7.routeOrder.5` | 对应路段在剩余路线的次序，未经过为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>routeOrder[5] = (j-currentSegmentIndex+1.0)/16.0 or 0</code> | unit |
| 936 | `truck.7.routeOrder.6` | 对应路段在剩余路线的次序，未经过为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>routeOrder[6] = (j-currentSegmentIndex+1.0)/16.0 or 0</code> | unit |
| 937 | `truck.7.routeOrder.7` | 对应路段在剩余路线的次序，未经过为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>routeOrder[7] = (j-currentSegmentIndex+1.0)/16.0 or 0</code> | unit |
| 938 | `truck.7.routeOrder.8` | 对应路段在剩余路线的次序，未经过为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>routeOrder[8] = (j-currentSegmentIndex+1.0)/16.0 or 0</code> | unit |
| 939 | `truck.7.routeOrder.9` | 对应路段在剩余路线的次序，未经过为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>routeOrder[9] = (j-currentSegmentIndex+1.0)/16.0 or 0</code> | unit |
| 940 | `truck.7.routeOrder.10` | 对应路段在剩余路线的次序，未经过为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>routeOrder[10] = (j-currentSegmentIndex+1.0)/16.0 or 0</code> | unit |
| 941 | `truck.7.routeOrder.11` | 对应路段在剩余路线的次序，未经过为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>routeOrder[11] = (j-currentSegmentIndex+1.0)/16.0 or 0</code> | unit |
| 942 | `truck.7.routeOrder.12` | 对应路段在剩余路线的次序，未经过为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>routeOrder[12] = (j-currentSegmentIndex+1.0)/16.0 or 0</code> | unit |
| 943 | `truck.7.routeOrder.13` | 对应路段在剩余路线的次序，未经过为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>routeOrder[13] = (j-currentSegmentIndex+1.0)/16.0 or 0</code> | unit |
| 944 | `truck.7.routeOrder.14` | 对应路段在剩余路线的次序，未经过为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>routeOrder[14] = (j-currentSegmentIndex+1.0)/16.0 or 0</code> | unit |
| 945 | `truck.7.routeOrder.15` | 对应路段在剩余路线的次序，未经过为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>routeOrder[15] = (j-currentSegmentIndex+1.0)/16.0 or 0</code> | unit |
| 946 | `truck.7.laneRank` | 当前路段车辆进入顺序排位 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>seg>=0?(ahead+1.0)/9.0:0.0</code> | unit |
| 947 | `truck.7.initialDispatched` | 是否完成首次派车 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>initialDispatchDone?1:0</code> | binary |
| 948 | `truck.7.initialPredecessor` | 首次派车前驱车辆ID编码，无前驱为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>initialPredecessor==null?0:(initialPredecessor.truckId+1.0)/9.0</code> | unit |
| 949 | `truck.7.loadWaitAge` | 等待装载资源已用时间 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>isWaitingForLoadResource?Math.max(0.0,now-60.0*queueEnterTime)/28800.0:0.0</code> | unit |
| 950 | `truck.7.dumpWaitAge` | 等待卸载资源已用时间 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>isWaitingForDumpResource?Math.max(0.0,now-60.0*dumpQueueEnterTime)/28800.0:0.0</code> | unit |
| 951 | `truck.7.loadAge` | 当前装载服务已用时间 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>loading?Math.max(0.0,now-60.0*loadStartTime)/600.0:0.0</code> | scaled |
| 952 | `truck.7.loadMean` | 当前载荷平均装载时间（分钟） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>loading?targetShovel.obsMeanLoadMinutes(plannedPayloadTons)/10.0:0.0</code> | scaled |
| 953 | `truck.7.loadMaterialStart` | 当前装载在物料序列中的起始吨位 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>loading?obsLoadMaterialStart/30000.0:0.0</code> | scaled |
| 954 | `truck.7.dumpAge` | 当前卸载服务已用时间 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>dumping?Math.max(0.0,now-60.0*dumpServiceStartTime)/600.0:0.0</code> | scaled |
| 955 | `truck.7.dumpMean` | 当前车辆平均卸载时间（分钟） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>dumping?main.getDumpSiteById(targetDumpSiteId).obsMeanDumpMinutes(this)/10.0:0.0</code> | scaled |
| 956 | `truck.7.freeSamples` | 自由行驶速度估计样本数 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>obsFreeCount/1000.0</code> | scaled |
| 957 | `truck.7.freeRatioMean` | 可观测自由流速度比样本均值 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>obsFreeCount>0?obsFreeMean:0.0</code> | scaled |
| 958 | `truck.7.freeRatioStd` | 可观测自由流速度比样本标准差 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>obsFreeCount>1?Math.sqrt(Math.max(0.0,obsFreeM2/(obsFreeCount-1))):0.0</code> | scaled |
| 959 | `truck.7.motion.0.valid` | 槽位或历史样本是否有效 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:1</code> | binary |
| 960 | `truck.7.motion.0.age` | 运动历史样本距当前时刻秒数 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:Math.max(0.0,now-h[0])/28800.0</code> | unit |
| 961 | `truck.7.motion.0.speed` | 速度（米/秒） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[1]/10.0</code> | scaled |
| 962 | `truck.7.motion.0.acceleration` | 动态加速度（米/秒平方） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[2]/3.0</code> | scaled |
| 963 | `truck.7.motion.0.hasFront` | 历史样本是否存在前车 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[3]</code> | binary |
| 964 | `truck.7.motion.0.frontGap` | 历史前车间距（米） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[4]/10000.0</code> | scaled |
| 965 | `truck.7.motion.0.frontSpeed` | 历史前车速度（米/秒） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[5]/10.0</code> | scaled |
| 966 | `truck.7.motion.1.valid` | 槽位或历史样本是否有效 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:1</code> | binary |
| 967 | `truck.7.motion.1.age` | 运动历史样本距当前时刻秒数 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:Math.max(0.0,now-h[0])/28800.0</code> | unit |
| 968 | `truck.7.motion.1.speed` | 速度（米/秒） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[1]/10.0</code> | scaled |
| 969 | `truck.7.motion.1.acceleration` | 动态加速度（米/秒平方） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[2]/3.0</code> | scaled |
| 970 | `truck.7.motion.1.hasFront` | 历史样本是否存在前车 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[3]</code> | binary |
| 971 | `truck.7.motion.1.frontGap` | 历史前车间距（米） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[4]/10000.0</code> | scaled |
| 972 | `truck.7.motion.1.frontSpeed` | 历史前车速度（米/秒） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[5]/10.0</code> | scaled |
| 973 | `truck.7.motion.2.valid` | 槽位或历史样本是否有效 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:1</code> | binary |
| 974 | `truck.7.motion.2.age` | 运动历史样本距当前时刻秒数 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:Math.max(0.0,now-h[0])/28800.0</code> | unit |
| 975 | `truck.7.motion.2.speed` | 速度（米/秒） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[1]/10.0</code> | scaled |
| 976 | `truck.7.motion.2.acceleration` | 动态加速度（米/秒平方） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[2]/3.0</code> | scaled |
| 977 | `truck.7.motion.2.hasFront` | 历史样本是否存在前车 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[3]</code> | binary |
| 978 | `truck.7.motion.2.frontGap` | 历史前车间距（米） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[4]/10000.0</code> | scaled |
| 979 | `truck.7.motion.2.frontSpeed` | 历史前车速度（米/秒） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[5]/10.0</code> | scaled |
| 980 | `truck.7.motion.3.valid` | 槽位或历史样本是否有效 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:1</code> | binary |
| 981 | `truck.7.motion.3.age` | 运动历史样本距当前时刻秒数 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:Math.max(0.0,now-h[0])/28800.0</code> | unit |
| 982 | `truck.7.motion.3.speed` | 速度（米/秒） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[1]/10.0</code> | scaled |
| 983 | `truck.7.motion.3.acceleration` | 动态加速度（米/秒平方） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[2]/3.0</code> | scaled |
| 984 | `truck.7.motion.3.hasFront` | 历史样本是否存在前车 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[3]</code> | binary |
| 985 | `truck.7.motion.3.frontGap` | 历史前车间距（米） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[4]/10000.0</code> | scaled |
| 986 | `truck.7.motion.3.frontSpeed` | 历史前车速度（米/秒） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[5]/10.0</code> | scaled |
| 987 | `truck.8.ego` | 当前需要派车的车辆标志 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>decision?1:0</code> | binary |
| 988 | `truck.8.type.0` | 车型类别0/1/2 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(truckType, 0)</code> | binary |
| 989 | `truck.8.type.1` | 车型类别0/1/2 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(truckType, 1)</code> | binary |
| 990 | `truck.8.type.2` | 车型类别0/1/2 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(truckType, 2)</code> | binary |
| 991 | `truck.8.phase.0` | 执行阶段类别0..11（详见审计报告） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(phase, 0)</code> | binary |
| 992 | `truck.8.phase.1` | 执行阶段类别0..11（详见审计报告） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(phase, 1)</code> | binary |
| 993 | `truck.8.phase.2` | 执行阶段类别0..11（详见审计报告） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(phase, 2)</code> | binary |
| 994 | `truck.8.phase.3` | 执行阶段类别0..11（详见审计报告） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(phase, 3)</code> | binary |
| 995 | `truck.8.phase.4` | 执行阶段类别0..11（详见审计报告） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(phase, 4)</code> | binary |
| 996 | `truck.8.phase.5` | 执行阶段类别0..11（详见审计报告） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(phase, 5)</code> | binary |
| 997 | `truck.8.phase.6` | 执行阶段类别0..11（详见审计报告） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(phase, 6)</code> | binary |
| 998 | `truck.8.phase.7` | 执行阶段类别0..11（详见审计报告） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(phase, 7)</code> | binary |
| 999 | `truck.8.phase.8` | 执行阶段类别0..11（详见审计报告） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(phase, 8)</code> | binary |
| 1000 | `truck.8.phase.9` | 执行阶段类别0..11（详见审计报告） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(phase, 9)</code> | binary |
| 1001 | `truck.8.phase.10` | 执行阶段类别0..11（详见审计报告） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(phase, 10)</code> | binary |
| 1002 | `truck.8.phase.11` | 执行阶段类别0..11（详见审计报告） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(phase, 11)</code> | binary |
| 1003 | `truck.8.capacity` | 车辆载重能力或卸载点服务并发容量（依据公式） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>capacity/193.0</code> | scaled |
| 1004 | `truck.8.loaded` | 有载标志 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>isLoaded?1:0</code> | binary |
| 1005 | `truck.8.ore` | 载荷或已预留装载物是否为矿石 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>isLoaded?(payloadIsOre?1:0):(plannedPayloadTons>0 && targetShovel!=null && targetShovel.isOre?1:0)</code> | binary |
| 1006 | `truck.8.payloadTons` | 已装载物料吨数 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>payloadTons/193.0</code> | scaled |
| 1007 | `truck.8.reservedLoadTons` | 已预留未完成装载吨数 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>plannedPayloadTons/193.0</code> | scaled |
| 1008 | `truck.8.gradeKnown` | 已装载物料品位已知标志 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>isLoaded?1:0</code> | binary |
| 1009 | `truck.8.payloadGrade` | 已装载物料品位，空载为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>isLoaded?payloadGrade:0.0</code> | unit |
| 1010 | `truck.8.loadingGradeMean` | 正在装载物料的可观测品位估计均值 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>gs[0]</code> | unit |
| 1011 | `truck.8.loadingGradeStd` | 正在装载物料的可观测品位估计标准差 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>gs[1]</code> | unit |
| 1012 | `truck.8.loadingGradeInferred` | 正在装载物料品位是否全部可推知 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>gs[2]</code> | binary |
| 1013 | `truck.8.loadTarget.0` | 装载目标one-hot（决策车辆清空） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(!decision && plannedPayloadTons>0 && targetShovel!=null?targetShovel.siteId:-1, 0)</code> | binary |
| 1014 | `truck.8.loadTarget.1` | 装载目标one-hot（决策车辆清空） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(!decision && plannedPayloadTons>0 && targetShovel!=null?targetShovel.siteId:-1, 1)</code> | binary |
| 1015 | `truck.8.loadTarget.2` | 装载目标one-hot（决策车辆清空） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(!decision && plannedPayloadTons>0 && targetShovel!=null?targetShovel.siteId:-1, 2)</code> | binary |
| 1016 | `truck.8.loadTarget.3` | 装载目标one-hot（决策车辆清空） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(!decision && plannedPayloadTons>0 && targetShovel!=null?targetShovel.siteId:-1, 3)</code> | binary |
| 1017 | `truck.8.dumpTarget.0` | 卸载目标one-hot（矿石0/废石1） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(isLoaded?(payloadIsOre?0:1):-1, 0)</code> | binary |
| 1018 | `truck.8.dumpTarget.1` | 卸载目标one-hot（矿石0/废石1） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(isLoaded?(payloadIsOre?0:1):-1, 1)</code> | binary |
| 1019 | `truck.8.node.0` | 当前道路节点one-hot | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(main.obsNodeIndex(currentNode), 0)</code> | binary |
| 1020 | `truck.8.node.1` | 当前道路节点one-hot | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(main.obsNodeIndex(currentNode), 1)</code> | binary |
| 1021 | `truck.8.node.2` | 当前道路节点one-hot | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(main.obsNodeIndex(currentNode), 2)</code> | binary |
| 1022 | `truck.8.node.3` | 当前道路节点one-hot | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(main.obsNodeIndex(currentNode), 3)</code> | binary |
| 1023 | `truck.8.node.4` | 当前道路节点one-hot | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(main.obsNodeIndex(currentNode), 4)</code> | binary |
| 1024 | `truck.8.node.5` | 当前道路节点one-hot | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(main.obsNodeIndex(currentNode), 5)</code> | binary |
| 1025 | `truck.8.node.6` | 当前道路节点one-hot | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(main.obsNodeIndex(currentNode), 6)</code> | binary |
| 1026 | `truck.8.node.7` | 当前道路节点one-hot | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(main.obsNodeIndex(currentNode), 7)</code> | binary |
| 1027 | `truck.8.node.8` | 当前道路节点one-hot | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(main.obsNodeIndex(currentNode), 8)</code> | binary |
| 1028 | `truck.8.xM` | 车辆X坐标（米） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>main.toLengthUnits(getX(),METER)/10000.0</code> | scaled |
| 1029 | `truck.8.yM` | 车辆Y坐标（米） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>main.toLengthUnits(getY(),METER)/10000.0</code> | scaled |
| 1030 | `truck.8.speed` | 速度（米/秒） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>getSpeed()/10.0</code> | scaled |
| 1031 | `truck.8.acceleration` | 动态加速度（米/秒平方） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>dynamicAccel/3.0</code> | scaled |
| 1032 | `truck.8.segment.0` | 当前有向路段one-hot（决策车辆不编码运动段） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(seg, 0)</code> | binary |
| 1033 | `truck.8.segment.1` | 当前有向路段one-hot（决策车辆不编码运动段） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(seg, 1)</code> | binary |
| 1034 | `truck.8.segment.2` | 当前有向路段one-hot（决策车辆不编码运动段） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(seg, 2)</code> | binary |
| 1035 | `truck.8.segment.3` | 当前有向路段one-hot（决策车辆不编码运动段） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(seg, 3)</code> | binary |
| 1036 | `truck.8.segment.4` | 当前有向路段one-hot（决策车辆不编码运动段） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(seg, 4)</code> | binary |
| 1037 | `truck.8.segment.5` | 当前有向路段one-hot（决策车辆不编码运动段） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(seg, 5)</code> | binary |
| 1038 | `truck.8.segment.6` | 当前有向路段one-hot（决策车辆不编码运动段） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(seg, 6)</code> | binary |
| 1039 | `truck.8.segment.7` | 当前有向路段one-hot（决策车辆不编码运动段） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(seg, 7)</code> | binary |
| 1040 | `truck.8.segment.8` | 当前有向路段one-hot（决策车辆不编码运动段） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(seg, 8)</code> | binary |
| 1041 | `truck.8.segment.9` | 当前有向路段one-hot（决策车辆不编码运动段） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(seg, 9)</code> | binary |
| 1042 | `truck.8.segment.10` | 当前有向路段one-hot（决策车辆不编码运动段） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(seg, 10)</code> | binary |
| 1043 | `truck.8.segment.11` | 当前有向路段one-hot（决策车辆不编码运动段） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(seg, 11)</code> | binary |
| 1044 | `truck.8.segment.12` | 当前有向路段one-hot（决策车辆不编码运动段） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(seg, 12)</code> | binary |
| 1045 | `truck.8.segment.13` | 当前有向路段one-hot（决策车辆不编码运动段） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(seg, 13)</code> | binary |
| 1046 | `truck.8.segment.14` | 当前有向路段one-hot（决策车辆不编码运动段） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(seg, 14)</code> | binary |
| 1047 | `truck.8.segment.15` | 当前有向路段one-hot（决策车辆不编码运动段） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>oneHot(seg, 15)</code> | binary |
| 1048 | `truck.8.segmentRemaining` | 当前路段剩余距离（米） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>remaining/10000.0</code> | scaled |
| 1049 | `truck.8.routeRemaining` | 当前路线剩余距离（米） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>totalRemaining/10000.0</code> | scaled |
| 1050 | `truck.8.routeOrder.0` | 对应路段在剩余路线的次序，未经过为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>routeOrder[0] = (j-currentSegmentIndex+1.0)/16.0 or 0</code> | unit |
| 1051 | `truck.8.routeOrder.1` | 对应路段在剩余路线的次序，未经过为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>routeOrder[1] = (j-currentSegmentIndex+1.0)/16.0 or 0</code> | unit |
| 1052 | `truck.8.routeOrder.2` | 对应路段在剩余路线的次序，未经过为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>routeOrder[2] = (j-currentSegmentIndex+1.0)/16.0 or 0</code> | unit |
| 1053 | `truck.8.routeOrder.3` | 对应路段在剩余路线的次序，未经过为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>routeOrder[3] = (j-currentSegmentIndex+1.0)/16.0 or 0</code> | unit |
| 1054 | `truck.8.routeOrder.4` | 对应路段在剩余路线的次序，未经过为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>routeOrder[4] = (j-currentSegmentIndex+1.0)/16.0 or 0</code> | unit |
| 1055 | `truck.8.routeOrder.5` | 对应路段在剩余路线的次序，未经过为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>routeOrder[5] = (j-currentSegmentIndex+1.0)/16.0 or 0</code> | unit |
| 1056 | `truck.8.routeOrder.6` | 对应路段在剩余路线的次序，未经过为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>routeOrder[6] = (j-currentSegmentIndex+1.0)/16.0 or 0</code> | unit |
| 1057 | `truck.8.routeOrder.7` | 对应路段在剩余路线的次序，未经过为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>routeOrder[7] = (j-currentSegmentIndex+1.0)/16.0 or 0</code> | unit |
| 1058 | `truck.8.routeOrder.8` | 对应路段在剩余路线的次序，未经过为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>routeOrder[8] = (j-currentSegmentIndex+1.0)/16.0 or 0</code> | unit |
| 1059 | `truck.8.routeOrder.9` | 对应路段在剩余路线的次序，未经过为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>routeOrder[9] = (j-currentSegmentIndex+1.0)/16.0 or 0</code> | unit |
| 1060 | `truck.8.routeOrder.10` | 对应路段在剩余路线的次序，未经过为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>routeOrder[10] = (j-currentSegmentIndex+1.0)/16.0 or 0</code> | unit |
| 1061 | `truck.8.routeOrder.11` | 对应路段在剩余路线的次序，未经过为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>routeOrder[11] = (j-currentSegmentIndex+1.0)/16.0 or 0</code> | unit |
| 1062 | `truck.8.routeOrder.12` | 对应路段在剩余路线的次序，未经过为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>routeOrder[12] = (j-currentSegmentIndex+1.0)/16.0 or 0</code> | unit |
| 1063 | `truck.8.routeOrder.13` | 对应路段在剩余路线的次序，未经过为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>routeOrder[13] = (j-currentSegmentIndex+1.0)/16.0 or 0</code> | unit |
| 1064 | `truck.8.routeOrder.14` | 对应路段在剩余路线的次序，未经过为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>routeOrder[14] = (j-currentSegmentIndex+1.0)/16.0 or 0</code> | unit |
| 1065 | `truck.8.routeOrder.15` | 对应路段在剩余路线的次序，未经过为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>routeOrder[15] = (j-currentSegmentIndex+1.0)/16.0 or 0</code> | unit |
| 1066 | `truck.8.laneRank` | 当前路段车辆进入顺序排位 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>seg>=0?(ahead+1.0)/9.0:0.0</code> | unit |
| 1067 | `truck.8.initialDispatched` | 是否完成首次派车 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>initialDispatchDone?1:0</code> | binary |
| 1068 | `truck.8.initialPredecessor` | 首次派车前驱车辆ID编码，无前驱为0 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>initialPredecessor==null?0:(initialPredecessor.truckId+1.0)/9.0</code> | unit |
| 1069 | `truck.8.loadWaitAge` | 等待装载资源已用时间 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>isWaitingForLoadResource?Math.max(0.0,now-60.0*queueEnterTime)/28800.0:0.0</code> | unit |
| 1070 | `truck.8.dumpWaitAge` | 等待卸载资源已用时间 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>isWaitingForDumpResource?Math.max(0.0,now-60.0*dumpQueueEnterTime)/28800.0:0.0</code> | unit |
| 1071 | `truck.8.loadAge` | 当前装载服务已用时间 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>loading?Math.max(0.0,now-60.0*loadStartTime)/600.0:0.0</code> | scaled |
| 1072 | `truck.8.loadMean` | 当前载荷平均装载时间（分钟） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>loading?targetShovel.obsMeanLoadMinutes(plannedPayloadTons)/10.0:0.0</code> | scaled |
| 1073 | `truck.8.loadMaterialStart` | 当前装载在物料序列中的起始吨位 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>loading?obsLoadMaterialStart/30000.0:0.0</code> | scaled |
| 1074 | `truck.8.dumpAge` | 当前卸载服务已用时间 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>dumping?Math.max(0.0,now-60.0*dumpServiceStartTime)/600.0:0.0</code> | scaled |
| 1075 | `truck.8.dumpMean` | 当前车辆平均卸载时间（分钟） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>dumping?main.getDumpSiteById(targetDumpSiteId).obsMeanDumpMinutes(this)/10.0:0.0</code> | scaled |
| 1076 | `truck.8.freeSamples` | 自由行驶速度估计样本数 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>obsFreeCount/1000.0</code> | scaled |
| 1077 | `truck.8.freeRatioMean` | 可观测自由流速度比样本均值 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>obsFreeCount>0?obsFreeMean:0.0</code> | scaled |
| 1078 | `truck.8.freeRatioStd` | 可观测自由流速度比样本标准差 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>obsFreeCount>1?Math.sqrt(Math.max(0.0,obsFreeM2/(obsFreeCount-1))):0.0</code> | scaled |
| 1079 | `truck.8.motion.0.valid` | 槽位或历史样本是否有效 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:1</code> | binary |
| 1080 | `truck.8.motion.0.age` | 运动历史样本距当前时刻秒数 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:Math.max(0.0,now-h[0])/28800.0</code> | unit |
| 1081 | `truck.8.motion.0.speed` | 速度（米/秒） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[1]/10.0</code> | scaled |
| 1082 | `truck.8.motion.0.acceleration` | 动态加速度（米/秒平方） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[2]/3.0</code> | scaled |
| 1083 | `truck.8.motion.0.hasFront` | 历史样本是否存在前车 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[3]</code> | binary |
| 1084 | `truck.8.motion.0.frontGap` | 历史前车间距（米） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[4]/10000.0</code> | scaled |
| 1085 | `truck.8.motion.0.frontSpeed` | 历史前车速度（米/秒） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[5]/10.0</code> | scaled |
| 1086 | `truck.8.motion.1.valid` | 槽位或历史样本是否有效 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:1</code> | binary |
| 1087 | `truck.8.motion.1.age` | 运动历史样本距当前时刻秒数 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:Math.max(0.0,now-h[0])/28800.0</code> | unit |
| 1088 | `truck.8.motion.1.speed` | 速度（米/秒） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[1]/10.0</code> | scaled |
| 1089 | `truck.8.motion.1.acceleration` | 动态加速度（米/秒平方） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[2]/3.0</code> | scaled |
| 1090 | `truck.8.motion.1.hasFront` | 历史样本是否存在前车 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[3]</code> | binary |
| 1091 | `truck.8.motion.1.frontGap` | 历史前车间距（米） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[4]/10000.0</code> | scaled |
| 1092 | `truck.8.motion.1.frontSpeed` | 历史前车速度（米/秒） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[5]/10.0</code> | scaled |
| 1093 | `truck.8.motion.2.valid` | 槽位或历史样本是否有效 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:1</code> | binary |
| 1094 | `truck.8.motion.2.age` | 运动历史样本距当前时刻秒数 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:Math.max(0.0,now-h[0])/28800.0</code> | unit |
| 1095 | `truck.8.motion.2.speed` | 速度（米/秒） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[1]/10.0</code> | scaled |
| 1096 | `truck.8.motion.2.acceleration` | 动态加速度（米/秒平方） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[2]/3.0</code> | scaled |
| 1097 | `truck.8.motion.2.hasFront` | 历史样本是否存在前车 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[3]</code> | binary |
| 1098 | `truck.8.motion.2.frontGap` | 历史前车间距（米） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[4]/10000.0</code> | scaled |
| 1099 | `truck.8.motion.2.frontSpeed` | 历史前车速度（米/秒） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[5]/10.0</code> | scaled |
| 1100 | `truck.8.motion.3.valid` | 槽位或历史样本是否有效 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:1</code> | binary |
| 1101 | `truck.8.motion.3.age` | 运动历史样本距当前时刻秒数 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:Math.max(0.0,now-h[0])/28800.0</code> | unit |
| 1102 | `truck.8.motion.3.speed` | 速度（米/秒） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[1]/10.0</code> | scaled |
| 1103 | `truck.8.motion.3.acceleration` | 动态加速度（米/秒平方） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[2]/3.0</code> | scaled |
| 1104 | `truck.8.motion.3.hasFront` | 历史样本是否存在前车 | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[3]</code> | binary |
| 1105 | `truck.8.motion.3.frontGap` | 历史前车间距（米） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[4]/10000.0</code> | scaled |
| 1106 | `truck.8.motion.3.frontSpeed` | 历史前车速度（米/秒） | [Truck.appendDispatchObservation:L15568](../anylogic/DRL-PPO.alp#L15568) | <code>h==null?0:h[5]/10.0</code> | scaled |
| 1107 | `load.0.available` | 站点可用标志（与有剩余可预留物料分别表达） | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>available?1:0</code> | binary |
| 1108 | `load.0.isOre` | 装载物是否为矿石 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>isOre?1:0</code> | binary |
| 1109 | `load.0.meanGrade` | 装载点名义品位 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>grade</code> | unit |
| 1110 | `load.0.gradeHalfRange` | 随机块品位半区间，确定性模式为0 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>main.deterministicCheck?0:gradeHalfRange</code> | unit |
| 1111 | `load.0.initialTons` | 初始矿量储备 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>initialReserveTons/30000.0</code> | scaled |
| 1112 | `load.0.remainingTons` | 剩余矿量（含预留未装完量） | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>remainingTons/30000.0</code> | scaled |
| 1113 | `load.0.reservedTons` | 预留吨数（装载点预留装载量/卸载点预留缓冲量） | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>reservedTons/30000.0</code> | scaled |
| 1114 | `load.0.availableTons` | 可继续预留的矿量 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>getAvailableTons()/30000.0</code> | scaled |
| 1115 | `load.0.producedTons` | 已完成装载吨数 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>producedTons/30000.0</code> | scaled |
| 1116 | `load.0.allocationCursor` | 物料预留分配游标吨位 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>extractionCursorTons/30000.0</code> | scaled |
| 1117 | `load.0.blockTons` | 品位块吨数 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>gradeBlockTons/500.0</code> | scaled |
| 1118 | `load.0.cursorFraction` | 分配游标在当前品位块内的相位 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>inBlock/gradeBlockTons</code> | unit |
| 1119 | `load.0.lastKnownBlock` | 最后已推知品位块索引编码，未知为0 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>obsLastKnownBlock<0?0:(obsLastKnownBlock+1.0)/60.0</code> | scaled |
| 1120 | `load.0.lastKnownGrade` | 最后已推知块品位，未知为0 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>obsLastKnownBlock<0?0:obsLastKnownGrade</code> | unit |
| 1121 | `load.0.shovelCapacity` | 装载点铲装服务容量 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>shovelCapacity</code> | scaled |
| 1122 | `load.0.shovelBusy` | 铲装资源占用数 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>shovelResource.busy()</code> | binary |
| 1123 | `load.0.loadingCount` | 正在装载服务车辆数 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>numInService</code> | binary |
| 1124 | `load.0.incomingCount` | 在途装载车辆数 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>incomingTrucks/9.0</code> | unit |
| 1125 | `load.0.bucketTons` | 单铲有效吨数，上限30吨 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>Math.min(30.0,bucket*density*0.90)/30.0</code> | unit |
| 1126 | `load.0.singleServeMin` | 单铲服务时间（分钟） | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>singleServeTime</code> | scaled |
| 1127 | `load.0.queue.0` | 排队车辆ID槽，顺序来自AnyLogic队列 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1128 | `load.0.queue.1` | 排队车辆ID槽，顺序来自AnyLogic队列 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1129 | `load.0.queue.2` | 排队车辆ID槽，顺序来自AnyLogic队列 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1130 | `load.0.queue.3` | 排队车辆ID槽，顺序来自AnyLogic队列 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1131 | `load.0.queue.4` | 排队车辆ID槽，顺序来自AnyLogic队列 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1132 | `load.0.queue.5` | 排队车辆ID槽，顺序来自AnyLogic队列 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1133 | `load.0.queue.6` | 排队车辆ID槽，顺序来自AnyLogic队列 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1134 | `load.0.queue.7` | 排队车辆ID槽，顺序来自AnyLogic队列 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1135 | `load.0.queue.8` | 排队车辆ID槽，顺序来自AnyLogic队列 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1136 | `load.0.seize.0` | 资源申请等待车辆ID槽 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1137 | `load.0.seize.1` | 资源申请等待车辆ID槽 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1138 | `load.0.seize.2` | 资源申请等待车辆ID槽 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1139 | `load.0.seize.3` | 资源申请等待车辆ID槽 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1140 | `load.0.seize.4` | 资源申请等待车辆ID槽 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1141 | `load.0.seize.5` | 资源申请等待车辆ID槽 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1142 | `load.0.seize.6` | 资源申请等待车辆ID槽 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1143 | `load.0.seize.7` | 资源申请等待车辆ID槽 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1144 | `load.0.seize.8` | 资源申请等待车辆ID槽 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1145 | `load.0.service.0` | 服务中车辆ID槽，按truckId排序 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1146 | `load.0.service.1` | 服务中车辆ID槽，按truckId排序 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1147 | `load.0.service.2` | 服务中车辆ID槽，按truckId排序 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1148 | `load.0.service.3` | 服务中车辆ID槽，按truckId排序 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1149 | `load.0.service.4` | 服务中车辆ID槽，按truckId排序 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1150 | `load.0.service.5` | 服务中车辆ID槽，按truckId排序 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1151 | `load.0.service.6` | 服务中车辆ID槽，按truckId排序 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1152 | `load.0.service.7` | 服务中车辆ID槽，按truckId排序 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1153 | `load.0.service.8` | 服务中车辆ID槽，按truckId排序 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1154 | `load.1.available` | 站点可用标志（与有剩余可预留物料分别表达） | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>available?1:0</code> | binary |
| 1155 | `load.1.isOre` | 装载物是否为矿石 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>isOre?1:0</code> | binary |
| 1156 | `load.1.meanGrade` | 装载点名义品位 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>grade</code> | unit |
| 1157 | `load.1.gradeHalfRange` | 随机块品位半区间，确定性模式为0 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>main.deterministicCheck?0:gradeHalfRange</code> | unit |
| 1158 | `load.1.initialTons` | 初始矿量储备 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>initialReserveTons/30000.0</code> | scaled |
| 1159 | `load.1.remainingTons` | 剩余矿量（含预留未装完量） | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>remainingTons/30000.0</code> | scaled |
| 1160 | `load.1.reservedTons` | 预留吨数（装载点预留装载量/卸载点预留缓冲量） | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>reservedTons/30000.0</code> | scaled |
| 1161 | `load.1.availableTons` | 可继续预留的矿量 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>getAvailableTons()/30000.0</code> | scaled |
| 1162 | `load.1.producedTons` | 已完成装载吨数 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>producedTons/30000.0</code> | scaled |
| 1163 | `load.1.allocationCursor` | 物料预留分配游标吨位 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>extractionCursorTons/30000.0</code> | scaled |
| 1164 | `load.1.blockTons` | 品位块吨数 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>gradeBlockTons/500.0</code> | scaled |
| 1165 | `load.1.cursorFraction` | 分配游标在当前品位块内的相位 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>inBlock/gradeBlockTons</code> | unit |
| 1166 | `load.1.lastKnownBlock` | 最后已推知品位块索引编码，未知为0 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>obsLastKnownBlock<0?0:(obsLastKnownBlock+1.0)/60.0</code> | scaled |
| 1167 | `load.1.lastKnownGrade` | 最后已推知块品位，未知为0 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>obsLastKnownBlock<0?0:obsLastKnownGrade</code> | unit |
| 1168 | `load.1.shovelCapacity` | 装载点铲装服务容量 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>shovelCapacity</code> | scaled |
| 1169 | `load.1.shovelBusy` | 铲装资源占用数 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>shovelResource.busy()</code> | binary |
| 1170 | `load.1.loadingCount` | 正在装载服务车辆数 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>numInService</code> | binary |
| 1171 | `load.1.incomingCount` | 在途装载车辆数 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>incomingTrucks/9.0</code> | unit |
| 1172 | `load.1.bucketTons` | 单铲有效吨数，上限30吨 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>Math.min(30.0,bucket*density*0.90)/30.0</code> | unit |
| 1173 | `load.1.singleServeMin` | 单铲服务时间（分钟） | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>singleServeTime</code> | scaled |
| 1174 | `load.1.queue.0` | 排队车辆ID槽，顺序来自AnyLogic队列 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1175 | `load.1.queue.1` | 排队车辆ID槽，顺序来自AnyLogic队列 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1176 | `load.1.queue.2` | 排队车辆ID槽，顺序来自AnyLogic队列 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1177 | `load.1.queue.3` | 排队车辆ID槽，顺序来自AnyLogic队列 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1178 | `load.1.queue.4` | 排队车辆ID槽，顺序来自AnyLogic队列 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1179 | `load.1.queue.5` | 排队车辆ID槽，顺序来自AnyLogic队列 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1180 | `load.1.queue.6` | 排队车辆ID槽，顺序来自AnyLogic队列 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1181 | `load.1.queue.7` | 排队车辆ID槽，顺序来自AnyLogic队列 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1182 | `load.1.queue.8` | 排队车辆ID槽，顺序来自AnyLogic队列 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1183 | `load.1.seize.0` | 资源申请等待车辆ID槽 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1184 | `load.1.seize.1` | 资源申请等待车辆ID槽 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1185 | `load.1.seize.2` | 资源申请等待车辆ID槽 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1186 | `load.1.seize.3` | 资源申请等待车辆ID槽 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1187 | `load.1.seize.4` | 资源申请等待车辆ID槽 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1188 | `load.1.seize.5` | 资源申请等待车辆ID槽 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1189 | `load.1.seize.6` | 资源申请等待车辆ID槽 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1190 | `load.1.seize.7` | 资源申请等待车辆ID槽 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1191 | `load.1.seize.8` | 资源申请等待车辆ID槽 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1192 | `load.1.service.0` | 服务中车辆ID槽，按truckId排序 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1193 | `load.1.service.1` | 服务中车辆ID槽，按truckId排序 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1194 | `load.1.service.2` | 服务中车辆ID槽，按truckId排序 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1195 | `load.1.service.3` | 服务中车辆ID槽，按truckId排序 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1196 | `load.1.service.4` | 服务中车辆ID槽，按truckId排序 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1197 | `load.1.service.5` | 服务中车辆ID槽，按truckId排序 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1198 | `load.1.service.6` | 服务中车辆ID槽，按truckId排序 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1199 | `load.1.service.7` | 服务中车辆ID槽，按truckId排序 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1200 | `load.1.service.8` | 服务中车辆ID槽，按truckId排序 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1201 | `load.2.available` | 站点可用标志（与有剩余可预留物料分别表达） | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>available?1:0</code> | binary |
| 1202 | `load.2.isOre` | 装载物是否为矿石 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>isOre?1:0</code> | binary |
| 1203 | `load.2.meanGrade` | 装载点名义品位 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>grade</code> | unit |
| 1204 | `load.2.gradeHalfRange` | 随机块品位半区间，确定性模式为0 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>main.deterministicCheck?0:gradeHalfRange</code> | unit |
| 1205 | `load.2.initialTons` | 初始矿量储备 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>initialReserveTons/30000.0</code> | scaled |
| 1206 | `load.2.remainingTons` | 剩余矿量（含预留未装完量） | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>remainingTons/30000.0</code> | scaled |
| 1207 | `load.2.reservedTons` | 预留吨数（装载点预留装载量/卸载点预留缓冲量） | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>reservedTons/30000.0</code> | scaled |
| 1208 | `load.2.availableTons` | 可继续预留的矿量 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>getAvailableTons()/30000.0</code> | scaled |
| 1209 | `load.2.producedTons` | 已完成装载吨数 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>producedTons/30000.0</code> | scaled |
| 1210 | `load.2.allocationCursor` | 物料预留分配游标吨位 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>extractionCursorTons/30000.0</code> | scaled |
| 1211 | `load.2.blockTons` | 品位块吨数 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>gradeBlockTons/500.0</code> | scaled |
| 1212 | `load.2.cursorFraction` | 分配游标在当前品位块内的相位 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>inBlock/gradeBlockTons</code> | unit |
| 1213 | `load.2.lastKnownBlock` | 最后已推知品位块索引编码，未知为0 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>obsLastKnownBlock<0?0:(obsLastKnownBlock+1.0)/60.0</code> | scaled |
| 1214 | `load.2.lastKnownGrade` | 最后已推知块品位，未知为0 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>obsLastKnownBlock<0?0:obsLastKnownGrade</code> | unit |
| 1215 | `load.2.shovelCapacity` | 装载点铲装服务容量 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>shovelCapacity</code> | scaled |
| 1216 | `load.2.shovelBusy` | 铲装资源占用数 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>shovelResource.busy()</code> | binary |
| 1217 | `load.2.loadingCount` | 正在装载服务车辆数 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>numInService</code> | binary |
| 1218 | `load.2.incomingCount` | 在途装载车辆数 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>incomingTrucks/9.0</code> | unit |
| 1219 | `load.2.bucketTons` | 单铲有效吨数，上限30吨 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>Math.min(30.0,bucket*density*0.90)/30.0</code> | unit |
| 1220 | `load.2.singleServeMin` | 单铲服务时间（分钟） | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>singleServeTime</code> | scaled |
| 1221 | `load.2.queue.0` | 排队车辆ID槽，顺序来自AnyLogic队列 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1222 | `load.2.queue.1` | 排队车辆ID槽，顺序来自AnyLogic队列 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1223 | `load.2.queue.2` | 排队车辆ID槽，顺序来自AnyLogic队列 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1224 | `load.2.queue.3` | 排队车辆ID槽，顺序来自AnyLogic队列 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1225 | `load.2.queue.4` | 排队车辆ID槽，顺序来自AnyLogic队列 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1226 | `load.2.queue.5` | 排队车辆ID槽，顺序来自AnyLogic队列 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1227 | `load.2.queue.6` | 排队车辆ID槽，顺序来自AnyLogic队列 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1228 | `load.2.queue.7` | 排队车辆ID槽，顺序来自AnyLogic队列 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1229 | `load.2.queue.8` | 排队车辆ID槽，顺序来自AnyLogic队列 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1230 | `load.2.seize.0` | 资源申请等待车辆ID槽 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1231 | `load.2.seize.1` | 资源申请等待车辆ID槽 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1232 | `load.2.seize.2` | 资源申请等待车辆ID槽 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1233 | `load.2.seize.3` | 资源申请等待车辆ID槽 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1234 | `load.2.seize.4` | 资源申请等待车辆ID槽 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1235 | `load.2.seize.5` | 资源申请等待车辆ID槽 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1236 | `load.2.seize.6` | 资源申请等待车辆ID槽 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1237 | `load.2.seize.7` | 资源申请等待车辆ID槽 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1238 | `load.2.seize.8` | 资源申请等待车辆ID槽 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1239 | `load.2.service.0` | 服务中车辆ID槽，按truckId排序 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1240 | `load.2.service.1` | 服务中车辆ID槽，按truckId排序 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1241 | `load.2.service.2` | 服务中车辆ID槽，按truckId排序 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1242 | `load.2.service.3` | 服务中车辆ID槽，按truckId排序 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1243 | `load.2.service.4` | 服务中车辆ID槽，按truckId排序 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1244 | `load.2.service.5` | 服务中车辆ID槽，按truckId排序 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1245 | `load.2.service.6` | 服务中车辆ID槽，按truckId排序 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1246 | `load.2.service.7` | 服务中车辆ID槽，按truckId排序 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1247 | `load.2.service.8` | 服务中车辆ID槽，按truckId排序 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1248 | `load.3.available` | 站点可用标志（与有剩余可预留物料分别表达） | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>available?1:0</code> | binary |
| 1249 | `load.3.isOre` | 装载物是否为矿石 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>isOre?1:0</code> | binary |
| 1250 | `load.3.meanGrade` | 装载点名义品位 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>grade</code> | unit |
| 1251 | `load.3.gradeHalfRange` | 随机块品位半区间，确定性模式为0 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>main.deterministicCheck?0:gradeHalfRange</code> | unit |
| 1252 | `load.3.initialTons` | 初始矿量储备 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>initialReserveTons/30000.0</code> | scaled |
| 1253 | `load.3.remainingTons` | 剩余矿量（含预留未装完量） | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>remainingTons/30000.0</code> | scaled |
| 1254 | `load.3.reservedTons` | 预留吨数（装载点预留装载量/卸载点预留缓冲量） | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>reservedTons/30000.0</code> | scaled |
| 1255 | `load.3.availableTons` | 可继续预留的矿量 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>getAvailableTons()/30000.0</code> | scaled |
| 1256 | `load.3.producedTons` | 已完成装载吨数 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>producedTons/30000.0</code> | scaled |
| 1257 | `load.3.allocationCursor` | 物料预留分配游标吨位 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>extractionCursorTons/30000.0</code> | scaled |
| 1258 | `load.3.blockTons` | 品位块吨数 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>gradeBlockTons/500.0</code> | scaled |
| 1259 | `load.3.cursorFraction` | 分配游标在当前品位块内的相位 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>inBlock/gradeBlockTons</code> | unit |
| 1260 | `load.3.lastKnownBlock` | 最后已推知品位块索引编码，未知为0 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>obsLastKnownBlock<0?0:(obsLastKnownBlock+1.0)/60.0</code> | scaled |
| 1261 | `load.3.lastKnownGrade` | 最后已推知块品位，未知为0 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>obsLastKnownBlock<0?0:obsLastKnownGrade</code> | unit |
| 1262 | `load.3.shovelCapacity` | 装载点铲装服务容量 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>shovelCapacity</code> | scaled |
| 1263 | `load.3.shovelBusy` | 铲装资源占用数 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>shovelResource.busy()</code> | binary |
| 1264 | `load.3.loadingCount` | 正在装载服务车辆数 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>numInService</code> | binary |
| 1265 | `load.3.incomingCount` | 在途装载车辆数 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>incomingTrucks/9.0</code> | unit |
| 1266 | `load.3.bucketTons` | 单铲有效吨数，上限30吨 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>Math.min(30.0,bucket*density*0.90)/30.0</code> | unit |
| 1267 | `load.3.singleServeMin` | 单铲服务时间（分钟） | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>singleServeTime</code> | scaled |
| 1268 | `load.3.queue.0` | 排队车辆ID槽，顺序来自AnyLogic队列 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1269 | `load.3.queue.1` | 排队车辆ID槽，顺序来自AnyLogic队列 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1270 | `load.3.queue.2` | 排队车辆ID槽，顺序来自AnyLogic队列 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1271 | `load.3.queue.3` | 排队车辆ID槽，顺序来自AnyLogic队列 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1272 | `load.3.queue.4` | 排队车辆ID槽，顺序来自AnyLogic队列 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1273 | `load.3.queue.5` | 排队车辆ID槽，顺序来自AnyLogic队列 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1274 | `load.3.queue.6` | 排队车辆ID槽，顺序来自AnyLogic队列 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1275 | `load.3.queue.7` | 排队车辆ID槽，顺序来自AnyLogic队列 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1276 | `load.3.queue.8` | 排队车辆ID槽，顺序来自AnyLogic队列 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1277 | `load.3.seize.0` | 资源申请等待车辆ID槽 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1278 | `load.3.seize.1` | 资源申请等待车辆ID槽 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1279 | `load.3.seize.2` | 资源申请等待车辆ID槽 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1280 | `load.3.seize.3` | 资源申请等待车辆ID槽 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1281 | `load.3.seize.4` | 资源申请等待车辆ID槽 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1282 | `load.3.seize.5` | 资源申请等待车辆ID槽 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1283 | `load.3.seize.6` | 资源申请等待车辆ID槽 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1284 | `load.3.seize.7` | 资源申请等待车辆ID槽 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1285 | `load.3.seize.8` | 资源申请等待车辆ID槽 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1286 | `load.3.service.0` | 服务中车辆ID槽，按truckId排序 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1287 | `load.3.service.1` | 服务中车辆ID槽，按truckId排序 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1288 | `load.3.service.2` | 服务中车辆ID槽，按truckId排序 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1289 | `load.3.service.3` | 服务中车辆ID槽，按truckId排序 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1290 | `load.3.service.4` | 服务中车辆ID槽，按truckId排序 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1291 | `load.3.service.5` | 服务中车辆ID槽，按truckId排序 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1292 | `load.3.service.6` | 服务中车辆ID槽，按truckId排序 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1293 | `load.3.service.7` | 服务中车辆ID槽，按truckId排序 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1294 | `load.3.service.8` | 服务中车辆ID槽，按truckId排序 | [LoadSite.appendDispatchObservation:L20825](../anylogic/DRL-PPO.alp#L20825) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1295 | `dump.0.available` | 站点可用标志（与有剩余可预留物料分别表达） | [DumpSite.appendDispatchObservation:L17773](../anylogic/DRL-PPO.alp#L17773) | <code>available?1:0</code> | binary |
| 1296 | `dump.0.acceptsOre` | 卸载点接收矿石标志 | [DumpSite.appendDispatchObservation:L17773](../anylogic/DRL-PPO.alp#L17773) | <code>acceptsOre?1:0</code> | binary |
| 1297 | `dump.0.capacity` | 车辆载重能力或卸载点服务并发容量（依据公式） | [DumpSite.appendDispatchObservation:L17773](../anylogic/DRL-PPO.alp#L17773) | <code>serviceCapacity/3.0</code> | scaled |
| 1298 | `dump.0.occupied` | 已占用卸载资源数 | [DumpSite.appendDispatchObservation:L17773](../anylogic/DRL-PPO.alp#L17773) | <code>dumpResource.busy()/3.0</code> | scaled |
| 1299 | `dump.0.dumping` | 当前卸载服务车辆数 | [DumpSite.appendDispatchObservation:L17773](../anylogic/DRL-PPO.alp#L17773) | <code>numInDumpService/3.0</code> | scaled |
| 1300 | `dump.0.bufferTons` | 破碎缓冲库存吨数 | [DumpSite.appendDispatchObservation:L17773](../anylogic/DRL-PPO.alp#L17773) | <code>acceptsOre?crusherStoredTons/500.0:0.0</code> | scaled |
| 1301 | `dump.0.reservedTons` | 预留吨数（装载点预留装载量/卸载点预留缓冲量） | [DumpSite.appendDispatchObservation:L17773](../anylogic/DRL-PPO.alp#L17773) | <code>acceptsOre?crusherReservedTons/500.0:0.0</code> | scaled |
| 1302 | `dump.0.freeBufferTons` | 破碎缓冲可用吨数（扣除库存与预留） | [DumpSite.appendDispatchObservation:L17773](../anylogic/DRL-PPO.alp#L17773) | <code>acceptsOre?(crusherBufferCapacityTons-crusherStoredTons-crusherReservedTons)/500.0:0.0</code> | scaled |
| 1303 | `dump.0.bufferCapacity` | 破碎缓冲容量吨数 | [DumpSite.appendDispatchObservation:L17773](../anylogic/DRL-PPO.alp#L17773) | <code>acceptsOre?crusherBufferCapacityTons/500.0:0.0</code> | scaled |
| 1304 | `dump.0.crusherRate` | 破碎能力吨/小时 | [DumpSite.appendDispatchObservation:L17773](../anylogic/DRL-PPO.alp#L17773) | <code>acceptsOre?crusherRateTph/2500.0:0.0</code> | scaled |
| 1305 | `dump.0.admissionPending` | 卸载准入待处理标志 | [DumpSite.appendDispatchObservation:L17773](../anylogic/DRL-PPO.alp#L17773) | <code>dumpAdmissionPending?1:0</code> | binary |
| 1306 | `dump.0.admissionTruck` | 待准入车辆ID编码 | [DumpSite.appendDispatchObservation:L17773](../anylogic/DRL-PPO.alp#L17773) | <code>obsAdmissionTruck==null?0:(obsAdmissionTruck.truckId+1.0)/9.0</code> | unit |
| 1307 | `dump.0.queue.0` | 排队车辆ID槽，顺序来自AnyLogic队列 | [DumpSite.appendDispatchObservation:L17773](../anylogic/DRL-PPO.alp#L17773) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1308 | `dump.0.queue.1` | 排队车辆ID槽，顺序来自AnyLogic队列 | [DumpSite.appendDispatchObservation:L17773](../anylogic/DRL-PPO.alp#L17773) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1309 | `dump.0.queue.2` | 排队车辆ID槽，顺序来自AnyLogic队列 | [DumpSite.appendDispatchObservation:L17773](../anylogic/DRL-PPO.alp#L17773) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1310 | `dump.0.queue.3` | 排队车辆ID槽，顺序来自AnyLogic队列 | [DumpSite.appendDispatchObservation:L17773](../anylogic/DRL-PPO.alp#L17773) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1311 | `dump.0.queue.4` | 排队车辆ID槽，顺序来自AnyLogic队列 | [DumpSite.appendDispatchObservation:L17773](../anylogic/DRL-PPO.alp#L17773) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1312 | `dump.0.queue.5` | 排队车辆ID槽，顺序来自AnyLogic队列 | [DumpSite.appendDispatchObservation:L17773](../anylogic/DRL-PPO.alp#L17773) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1313 | `dump.0.queue.6` | 排队车辆ID槽，顺序来自AnyLogic队列 | [DumpSite.appendDispatchObservation:L17773](../anylogic/DRL-PPO.alp#L17773) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1314 | `dump.0.queue.7` | 排队车辆ID槽，顺序来自AnyLogic队列 | [DumpSite.appendDispatchObservation:L17773](../anylogic/DRL-PPO.alp#L17773) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1315 | `dump.0.queue.8` | 排队车辆ID槽，顺序来自AnyLogic队列 | [DumpSite.appendDispatchObservation:L17773](../anylogic/DRL-PPO.alp#L17773) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1316 | `dump.0.seize.0` | 资源申请等待车辆ID槽 | [DumpSite.appendDispatchObservation:L17773](../anylogic/DRL-PPO.alp#L17773) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1317 | `dump.0.seize.1` | 资源申请等待车辆ID槽 | [DumpSite.appendDispatchObservation:L17773](../anylogic/DRL-PPO.alp#L17773) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1318 | `dump.0.seize.2` | 资源申请等待车辆ID槽 | [DumpSite.appendDispatchObservation:L17773](../anylogic/DRL-PPO.alp#L17773) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1319 | `dump.0.seize.3` | 资源申请等待车辆ID槽 | [DumpSite.appendDispatchObservation:L17773](../anylogic/DRL-PPO.alp#L17773) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1320 | `dump.0.seize.4` | 资源申请等待车辆ID槽 | [DumpSite.appendDispatchObservation:L17773](../anylogic/DRL-PPO.alp#L17773) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1321 | `dump.0.seize.5` | 资源申请等待车辆ID槽 | [DumpSite.appendDispatchObservation:L17773](../anylogic/DRL-PPO.alp#L17773) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1322 | `dump.0.seize.6` | 资源申请等待车辆ID槽 | [DumpSite.appendDispatchObservation:L17773](../anylogic/DRL-PPO.alp#L17773) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1323 | `dump.0.seize.7` | 资源申请等待车辆ID槽 | [DumpSite.appendDispatchObservation:L17773](../anylogic/DRL-PPO.alp#L17773) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1324 | `dump.0.seize.8` | 资源申请等待车辆ID槽 | [DumpSite.appendDispatchObservation:L17773](../anylogic/DRL-PPO.alp#L17773) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1325 | `dump.0.capacityWait.0` | 等待缓冲容量车辆ID槽 | [DumpSite.appendDispatchObservation:L17773](../anylogic/DRL-PPO.alp#L17773) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1326 | `dump.0.capacityWait.1` | 等待缓冲容量车辆ID槽 | [DumpSite.appendDispatchObservation:L17773](../anylogic/DRL-PPO.alp#L17773) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1327 | `dump.0.capacityWait.2` | 等待缓冲容量车辆ID槽 | [DumpSite.appendDispatchObservation:L17773](../anylogic/DRL-PPO.alp#L17773) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1328 | `dump.0.capacityWait.3` | 等待缓冲容量车辆ID槽 | [DumpSite.appendDispatchObservation:L17773](../anylogic/DRL-PPO.alp#L17773) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1329 | `dump.0.capacityWait.4` | 等待缓冲容量车辆ID槽 | [DumpSite.appendDispatchObservation:L17773](../anylogic/DRL-PPO.alp#L17773) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1330 | `dump.0.capacityWait.5` | 等待缓冲容量车辆ID槽 | [DumpSite.appendDispatchObservation:L17773](../anylogic/DRL-PPO.alp#L17773) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1331 | `dump.0.capacityWait.6` | 等待缓冲容量车辆ID槽 | [DumpSite.appendDispatchObservation:L17773](../anylogic/DRL-PPO.alp#L17773) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1332 | `dump.0.capacityWait.7` | 等待缓冲容量车辆ID槽 | [DumpSite.appendDispatchObservation:L17773](../anylogic/DRL-PPO.alp#L17773) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1333 | `dump.0.capacityWait.8` | 等待缓冲容量车辆ID槽 | [DumpSite.appendDispatchObservation:L17773](../anylogic/DRL-PPO.alp#L17773) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1334 | `dump.0.service.0` | 服务中车辆ID槽，按truckId排序 | [DumpSite.appendDispatchObservation:L17773](../anylogic/DRL-PPO.alp#L17773) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1335 | `dump.0.service.1` | 服务中车辆ID槽，按truckId排序 | [DumpSite.appendDispatchObservation:L17773](../anylogic/DRL-PPO.alp#L17773) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1336 | `dump.0.service.2` | 服务中车辆ID槽，按truckId排序 | [DumpSite.appendDispatchObservation:L17773](../anylogic/DRL-PPO.alp#L17773) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1337 | `dump.0.service.3` | 服务中车辆ID槽，按truckId排序 | [DumpSite.appendDispatchObservation:L17773](../anylogic/DRL-PPO.alp#L17773) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1338 | `dump.0.service.4` | 服务中车辆ID槽，按truckId排序 | [DumpSite.appendDispatchObservation:L17773](../anylogic/DRL-PPO.alp#L17773) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1339 | `dump.0.service.5` | 服务中车辆ID槽，按truckId排序 | [DumpSite.appendDispatchObservation:L17773](../anylogic/DRL-PPO.alp#L17773) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1340 | `dump.0.service.6` | 服务中车辆ID槽，按truckId排序 | [DumpSite.appendDispatchObservation:L17773](../anylogic/DRL-PPO.alp#L17773) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1341 | `dump.0.service.7` | 服务中车辆ID槽，按truckId排序 | [DumpSite.appendDispatchObservation:L17773](../anylogic/DRL-PPO.alp#L17773) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1342 | `dump.0.service.8` | 服务中车辆ID槽，按truckId排序 | [DumpSite.appendDispatchObservation:L17773](../anylogic/DRL-PPO.alp#L17773) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1343 | `dump.1.available` | 站点可用标志（与有剩余可预留物料分别表达） | [DumpSite.appendDispatchObservation:L17773](../anylogic/DRL-PPO.alp#L17773) | <code>available?1:0</code> | binary |
| 1344 | `dump.1.acceptsOre` | 卸载点接收矿石标志 | [DumpSite.appendDispatchObservation:L17773](../anylogic/DRL-PPO.alp#L17773) | <code>acceptsOre?1:0</code> | binary |
| 1345 | `dump.1.capacity` | 车辆载重能力或卸载点服务并发容量（依据公式） | [DumpSite.appendDispatchObservation:L17773](../anylogic/DRL-PPO.alp#L17773) | <code>serviceCapacity/3.0</code> | scaled |
| 1346 | `dump.1.occupied` | 已占用卸载资源数 | [DumpSite.appendDispatchObservation:L17773](../anylogic/DRL-PPO.alp#L17773) | <code>dumpResource.busy()/3.0</code> | scaled |
| 1347 | `dump.1.dumping` | 当前卸载服务车辆数 | [DumpSite.appendDispatchObservation:L17773](../anylogic/DRL-PPO.alp#L17773) | <code>numInDumpService/3.0</code> | scaled |
| 1348 | `dump.1.bufferTons` | 破碎缓冲库存吨数 | [DumpSite.appendDispatchObservation:L17773](../anylogic/DRL-PPO.alp#L17773) | <code>acceptsOre?crusherStoredTons/500.0:0.0</code> | scaled |
| 1349 | `dump.1.reservedTons` | 预留吨数（装载点预留装载量/卸载点预留缓冲量） | [DumpSite.appendDispatchObservation:L17773](../anylogic/DRL-PPO.alp#L17773) | <code>acceptsOre?crusherReservedTons/500.0:0.0</code> | scaled |
| 1350 | `dump.1.freeBufferTons` | 破碎缓冲可用吨数（扣除库存与预留） | [DumpSite.appendDispatchObservation:L17773](../anylogic/DRL-PPO.alp#L17773) | <code>acceptsOre?(crusherBufferCapacityTons-crusherStoredTons-crusherReservedTons)/500.0:0.0</code> | scaled |
| 1351 | `dump.1.bufferCapacity` | 破碎缓冲容量吨数 | [DumpSite.appendDispatchObservation:L17773](../anylogic/DRL-PPO.alp#L17773) | <code>acceptsOre?crusherBufferCapacityTons/500.0:0.0</code> | scaled |
| 1352 | `dump.1.crusherRate` | 破碎能力吨/小时 | [DumpSite.appendDispatchObservation:L17773](../anylogic/DRL-PPO.alp#L17773) | <code>acceptsOre?crusherRateTph/2500.0:0.0</code> | scaled |
| 1353 | `dump.1.admissionPending` | 卸载准入待处理标志 | [DumpSite.appendDispatchObservation:L17773](../anylogic/DRL-PPO.alp#L17773) | <code>dumpAdmissionPending?1:0</code> | binary |
| 1354 | `dump.1.admissionTruck` | 待准入车辆ID编码 | [DumpSite.appendDispatchObservation:L17773](../anylogic/DRL-PPO.alp#L17773) | <code>obsAdmissionTruck==null?0:(obsAdmissionTruck.truckId+1.0)/9.0</code> | unit |
| 1355 | `dump.1.queue.0` | 排队车辆ID槽，顺序来自AnyLogic队列 | [DumpSite.appendDispatchObservation:L17773](../anylogic/DRL-PPO.alp#L17773) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1356 | `dump.1.queue.1` | 排队车辆ID槽，顺序来自AnyLogic队列 | [DumpSite.appendDispatchObservation:L17773](../anylogic/DRL-PPO.alp#L17773) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1357 | `dump.1.queue.2` | 排队车辆ID槽，顺序来自AnyLogic队列 | [DumpSite.appendDispatchObservation:L17773](../anylogic/DRL-PPO.alp#L17773) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1358 | `dump.1.queue.3` | 排队车辆ID槽，顺序来自AnyLogic队列 | [DumpSite.appendDispatchObservation:L17773](../anylogic/DRL-PPO.alp#L17773) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1359 | `dump.1.queue.4` | 排队车辆ID槽，顺序来自AnyLogic队列 | [DumpSite.appendDispatchObservation:L17773](../anylogic/DRL-PPO.alp#L17773) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1360 | `dump.1.queue.5` | 排队车辆ID槽，顺序来自AnyLogic队列 | [DumpSite.appendDispatchObservation:L17773](../anylogic/DRL-PPO.alp#L17773) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1361 | `dump.1.queue.6` | 排队车辆ID槽，顺序来自AnyLogic队列 | [DumpSite.appendDispatchObservation:L17773](../anylogic/DRL-PPO.alp#L17773) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1362 | `dump.1.queue.7` | 排队车辆ID槽，顺序来自AnyLogic队列 | [DumpSite.appendDispatchObservation:L17773](../anylogic/DRL-PPO.alp#L17773) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1363 | `dump.1.queue.8` | 排队车辆ID槽，顺序来自AnyLogic队列 | [DumpSite.appendDispatchObservation:L17773](../anylogic/DRL-PPO.alp#L17773) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1364 | `dump.1.seize.0` | 资源申请等待车辆ID槽 | [DumpSite.appendDispatchObservation:L17773](../anylogic/DRL-PPO.alp#L17773) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1365 | `dump.1.seize.1` | 资源申请等待车辆ID槽 | [DumpSite.appendDispatchObservation:L17773](../anylogic/DRL-PPO.alp#L17773) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1366 | `dump.1.seize.2` | 资源申请等待车辆ID槽 | [DumpSite.appendDispatchObservation:L17773](../anylogic/DRL-PPO.alp#L17773) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1367 | `dump.1.seize.3` | 资源申请等待车辆ID槽 | [DumpSite.appendDispatchObservation:L17773](../anylogic/DRL-PPO.alp#L17773) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1368 | `dump.1.seize.4` | 资源申请等待车辆ID槽 | [DumpSite.appendDispatchObservation:L17773](../anylogic/DRL-PPO.alp#L17773) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1369 | `dump.1.seize.5` | 资源申请等待车辆ID槽 | [DumpSite.appendDispatchObservation:L17773](../anylogic/DRL-PPO.alp#L17773) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1370 | `dump.1.seize.6` | 资源申请等待车辆ID槽 | [DumpSite.appendDispatchObservation:L17773](../anylogic/DRL-PPO.alp#L17773) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1371 | `dump.1.seize.7` | 资源申请等待车辆ID槽 | [DumpSite.appendDispatchObservation:L17773](../anylogic/DRL-PPO.alp#L17773) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1372 | `dump.1.seize.8` | 资源申请等待车辆ID槽 | [DumpSite.appendDispatchObservation:L17773](../anylogic/DRL-PPO.alp#L17773) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1373 | `dump.1.capacityWait.0` | 等待缓冲容量车辆ID槽 | [DumpSite.appendDispatchObservation:L17773](../anylogic/DRL-PPO.alp#L17773) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1374 | `dump.1.capacityWait.1` | 等待缓冲容量车辆ID槽 | [DumpSite.appendDispatchObservation:L17773](../anylogic/DRL-PPO.alp#L17773) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1375 | `dump.1.capacityWait.2` | 等待缓冲容量车辆ID槽 | [DumpSite.appendDispatchObservation:L17773](../anylogic/DRL-PPO.alp#L17773) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1376 | `dump.1.capacityWait.3` | 等待缓冲容量车辆ID槽 | [DumpSite.appendDispatchObservation:L17773](../anylogic/DRL-PPO.alp#L17773) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1377 | `dump.1.capacityWait.4` | 等待缓冲容量车辆ID槽 | [DumpSite.appendDispatchObservation:L17773](../anylogic/DRL-PPO.alp#L17773) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1378 | `dump.1.capacityWait.5` | 等待缓冲容量车辆ID槽 | [DumpSite.appendDispatchObservation:L17773](../anylogic/DRL-PPO.alp#L17773) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1379 | `dump.1.capacityWait.6` | 等待缓冲容量车辆ID槽 | [DumpSite.appendDispatchObservation:L17773](../anylogic/DRL-PPO.alp#L17773) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1380 | `dump.1.capacityWait.7` | 等待缓冲容量车辆ID槽 | [DumpSite.appendDispatchObservation:L17773](../anylogic/DRL-PPO.alp#L17773) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1381 | `dump.1.capacityWait.8` | 等待缓冲容量车辆ID槽 | [DumpSite.appendDispatchObservation:L17773](../anylogic/DRL-PPO.alp#L17773) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1382 | `dump.1.service.0` | 服务中车辆ID槽，按truckId排序 | [DumpSite.appendDispatchObservation:L17773](../anylogic/DRL-PPO.alp#L17773) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1383 | `dump.1.service.1` | 服务中车辆ID槽，按truckId排序 | [DumpSite.appendDispatchObservation:L17773](../anylogic/DRL-PPO.alp#L17773) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1384 | `dump.1.service.2` | 服务中车辆ID槽，按truckId排序 | [DumpSite.appendDispatchObservation:L17773](../anylogic/DRL-PPO.alp#L17773) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1385 | `dump.1.service.3` | 服务中车辆ID槽，按truckId排序 | [DumpSite.appendDispatchObservation:L17773](../anylogic/DRL-PPO.alp#L17773) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1386 | `dump.1.service.4` | 服务中车辆ID槽，按truckId排序 | [DumpSite.appendDispatchObservation:L17773](../anylogic/DRL-PPO.alp#L17773) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1387 | `dump.1.service.5` | 服务中车辆ID槽，按truckId排序 | [DumpSite.appendDispatchObservation:L17773](../anylogic/DRL-PPO.alp#L17773) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1388 | `dump.1.service.6` | 服务中车辆ID槽，按truckId排序 | [DumpSite.appendDispatchObservation:L17773](../anylogic/DRL-PPO.alp#L17773) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1389 | `dump.1.service.7` | 服务中车辆ID槽，按truckId排序 | [DumpSite.appendDispatchObservation:L17773](../anylogic/DRL-PPO.alp#L17773) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1390 | `dump.1.service.8` | 服务中车辆ID槽，按truckId排序 | [DumpSite.appendDispatchObservation:L17773](../anylogic/DRL-PPO.alp#L17773) | <code>i<list.size() ? (list.get(i).truckId+1.0)/9.0 : 0.0</code> | truck_slot |
| 1391 | `fifo.0.valid` | 槽位或历史样本是否有效 | [DumpSite.appendCrusherFifoObservation:L17812](../anylogic/DRL-PPO.alp#L17812) | <code>batch present ? 1 : 0</code> | binary |
| 1392 | `fifo.0.tons` | FIFO物料批次剩余吨数 | [DumpSite.appendCrusherFifoObservation:L17812](../anylogic/DRL-PPO.alp#L17812) | <code>batch present ? b[0]/500.0 : 0</code> | scaled |
| 1393 | `fifo.0.grade` | FIFO物料批次品位 | [DumpSite.appendCrusherFifoObservation:L17812](../anylogic/DRL-PPO.alp#L17812) | <code>batch present ? b[1] : 0</code> | unit |
| 1394 | `fifo.1.valid` | 槽位或历史样本是否有效 | [DumpSite.appendCrusherFifoObservation:L17812](../anylogic/DRL-PPO.alp#L17812) | <code>batch present ? 1 : 0</code> | binary |
| 1395 | `fifo.1.tons` | FIFO物料批次剩余吨数 | [DumpSite.appendCrusherFifoObservation:L17812](../anylogic/DRL-PPO.alp#L17812) | <code>batch present ? b[0]/500.0 : 0</code> | scaled |
| 1396 | `fifo.1.grade` | FIFO物料批次品位 | [DumpSite.appendCrusherFifoObservation:L17812](../anylogic/DRL-PPO.alp#L17812) | <code>batch present ? b[1] : 0</code> | unit |
| 1397 | `fifo.2.valid` | 槽位或历史样本是否有效 | [DumpSite.appendCrusherFifoObservation:L17812](../anylogic/DRL-PPO.alp#L17812) | <code>batch present ? 1 : 0</code> | binary |
| 1398 | `fifo.2.tons` | FIFO物料批次剩余吨数 | [DumpSite.appendCrusherFifoObservation:L17812](../anylogic/DRL-PPO.alp#L17812) | <code>batch present ? b[0]/500.0 : 0</code> | scaled |
| 1399 | `fifo.2.grade` | FIFO物料批次品位 | [DumpSite.appendCrusherFifoObservation:L17812](../anylogic/DRL-PPO.alp#L17812) | <code>batch present ? b[1] : 0</code> | unit |
| 1400 | `fifo.3.valid` | 槽位或历史样本是否有效 | [DumpSite.appendCrusherFifoObservation:L17812](../anylogic/DRL-PPO.alp#L17812) | <code>batch present ? 1 : 0</code> | binary |
| 1401 | `fifo.3.tons` | FIFO物料批次剩余吨数 | [DumpSite.appendCrusherFifoObservation:L17812](../anylogic/DRL-PPO.alp#L17812) | <code>batch present ? b[0]/500.0 : 0</code> | scaled |
| 1402 | `fifo.3.grade` | FIFO物料批次品位 | [DumpSite.appendCrusherFifoObservation:L17812](../anylogic/DRL-PPO.alp#L17812) | <code>batch present ? b[1] : 0</code> | unit |
| 1403 | `fifo.4.valid` | 槽位或历史样本是否有效 | [DumpSite.appendCrusherFifoObservation:L17812](../anylogic/DRL-PPO.alp#L17812) | <code>batch present ? 1 : 0</code> | binary |
| 1404 | `fifo.4.tons` | FIFO物料批次剩余吨数 | [DumpSite.appendCrusherFifoObservation:L17812](../anylogic/DRL-PPO.alp#L17812) | <code>batch present ? b[0]/500.0 : 0</code> | scaled |
| 1405 | `fifo.4.grade` | FIFO物料批次品位 | [DumpSite.appendCrusherFifoObservation:L17812](../anylogic/DRL-PPO.alp#L17812) | <code>batch present ? b[1] : 0</code> | unit |
| 1406 | `fifo.5.valid` | 槽位或历史样本是否有效 | [DumpSite.appendCrusherFifoObservation:L17812](../anylogic/DRL-PPO.alp#L17812) | <code>batch present ? 1 : 0</code> | binary |
| 1407 | `fifo.5.tons` | FIFO物料批次剩余吨数 | [DumpSite.appendCrusherFifoObservation:L17812](../anylogic/DRL-PPO.alp#L17812) | <code>batch present ? b[0]/500.0 : 0</code> | scaled |
| 1408 | `fifo.5.grade` | FIFO物料批次品位 | [DumpSite.appendCrusherFifoObservation:L17812](../anylogic/DRL-PPO.alp#L17812) | <code>batch present ? b[1] : 0</code> | unit |
| 1409 | `fifo.6.valid` | 槽位或历史样本是否有效 | [DumpSite.appendCrusherFifoObservation:L17812](../anylogic/DRL-PPO.alp#L17812) | <code>batch present ? 1 : 0</code> | binary |
| 1410 | `fifo.6.tons` | FIFO物料批次剩余吨数 | [DumpSite.appendCrusherFifoObservation:L17812](../anylogic/DRL-PPO.alp#L17812) | <code>batch present ? b[0]/500.0 : 0</code> | scaled |
| 1411 | `fifo.6.grade` | FIFO物料批次品位 | [DumpSite.appendCrusherFifoObservation:L17812](../anylogic/DRL-PPO.alp#L17812) | <code>batch present ? b[1] : 0</code> | unit |
| 1412 | `fifo.7.valid` | 槽位或历史样本是否有效 | [DumpSite.appendCrusherFifoObservation:L17812](../anylogic/DRL-PPO.alp#L17812) | <code>batch present ? 1 : 0</code> | binary |
| 1413 | `fifo.7.tons` | FIFO物料批次剩余吨数 | [DumpSite.appendCrusherFifoObservation:L17812](../anylogic/DRL-PPO.alp#L17812) | <code>batch present ? b[0]/500.0 : 0</code> | scaled |
| 1414 | `fifo.7.grade` | FIFO物料批次品位 | [DumpSite.appendCrusherFifoObservation:L17812](../anylogic/DRL-PPO.alp#L17812) | <code>batch present ? b[1] : 0</code> | unit |
| 1415 | `fifo.8.valid` | 槽位或历史样本是否有效 | [DumpSite.appendCrusherFifoObservation:L17812](../anylogic/DRL-PPO.alp#L17812) | <code>batch present ? 1 : 0</code> | binary |
| 1416 | `fifo.8.tons` | FIFO物料批次剩余吨数 | [DumpSite.appendCrusherFifoObservation:L17812](../anylogic/DRL-PPO.alp#L17812) | <code>batch present ? b[0]/500.0 : 0</code> | scaled |
| 1417 | `fifo.8.grade` | FIFO物料批次品位 | [DumpSite.appendCrusherFifoObservation:L17812](../anylogic/DRL-PPO.alp#L17812) | <code>batch present ? b[1] : 0</code> | unit |
| 1418 | `fifo.9.valid` | 槽位或历史样本是否有效 | [DumpSite.appendCrusherFifoObservation:L17812](../anylogic/DRL-PPO.alp#L17812) | <code>batch present ? 1 : 0</code> | binary |
| 1419 | `fifo.9.tons` | FIFO物料批次剩余吨数 | [DumpSite.appendCrusherFifoObservation:L17812](../anylogic/DRL-PPO.alp#L17812) | <code>batch present ? b[0]/500.0 : 0</code> | scaled |
| 1420 | `fifo.9.grade` | FIFO物料批次品位 | [DumpSite.appendCrusherFifoObservation:L17812](../anylogic/DRL-PPO.alp#L17812) | <code>batch present ? b[1] : 0</code> | unit |
| 1421 | `fifo.10.valid` | 槽位或历史样本是否有效 | [DumpSite.appendCrusherFifoObservation:L17812](../anylogic/DRL-PPO.alp#L17812) | <code>batch present ? 1 : 0</code> | binary |
| 1422 | `fifo.10.tons` | FIFO物料批次剩余吨数 | [DumpSite.appendCrusherFifoObservation:L17812](../anylogic/DRL-PPO.alp#L17812) | <code>batch present ? b[0]/500.0 : 0</code> | scaled |
| 1423 | `fifo.10.grade` | FIFO物料批次品位 | [DumpSite.appendCrusherFifoObservation:L17812](../anylogic/DRL-PPO.alp#L17812) | <code>batch present ? b[1] : 0</code> | unit |
| 1424 | `fifo.11.valid` | 槽位或历史样本是否有效 | [DumpSite.appendCrusherFifoObservation:L17812](../anylogic/DRL-PPO.alp#L17812) | <code>batch present ? 1 : 0</code> | binary |
| 1425 | `fifo.11.tons` | FIFO物料批次剩余吨数 | [DumpSite.appendCrusherFifoObservation:L17812](../anylogic/DRL-PPO.alp#L17812) | <code>batch present ? b[0]/500.0 : 0</code> | scaled |
| 1426 | `fifo.11.grade` | FIFO物料批次品位 | [DumpSite.appendCrusherFifoObservation:L17812](../anylogic/DRL-PPO.alp#L17812) | <code>batch present ? b[1] : 0</code> | unit |
| 1427 | `fifo.12.valid` | 槽位或历史样本是否有效 | [DumpSite.appendCrusherFifoObservation:L17812](../anylogic/DRL-PPO.alp#L17812) | <code>batch present ? 1 : 0</code> | binary |
| 1428 | `fifo.12.tons` | FIFO物料批次剩余吨数 | [DumpSite.appendCrusherFifoObservation:L17812](../anylogic/DRL-PPO.alp#L17812) | <code>batch present ? b[0]/500.0 : 0</code> | scaled |
| 1429 | `fifo.12.grade` | FIFO物料批次品位 | [DumpSite.appendCrusherFifoObservation:L17812](../anylogic/DRL-PPO.alp#L17812) | <code>batch present ? b[1] : 0</code> | unit |
| 1430 | `fifo.13.valid` | 槽位或历史样本是否有效 | [DumpSite.appendCrusherFifoObservation:L17812](../anylogic/DRL-PPO.alp#L17812) | <code>batch present ? 1 : 0</code> | binary |
| 1431 | `fifo.13.tons` | FIFO物料批次剩余吨数 | [DumpSite.appendCrusherFifoObservation:L17812](../anylogic/DRL-PPO.alp#L17812) | <code>batch present ? b[0]/500.0 : 0</code> | scaled |
| 1432 | `fifo.13.grade` | FIFO物料批次品位 | [DumpSite.appendCrusherFifoObservation:L17812](../anylogic/DRL-PPO.alp#L17812) | <code>batch present ? b[1] : 0</code> | unit |
| 1433 | `fifo.14.valid` | 槽位或历史样本是否有效 | [DumpSite.appendCrusherFifoObservation:L17812](../anylogic/DRL-PPO.alp#L17812) | <code>batch present ? 1 : 0</code> | binary |
| 1434 | `fifo.14.tons` | FIFO物料批次剩余吨数 | [DumpSite.appendCrusherFifoObservation:L17812](../anylogic/DRL-PPO.alp#L17812) | <code>batch present ? b[0]/500.0 : 0</code> | scaled |
| 1435 | `fifo.14.grade` | FIFO物料批次品位 | [DumpSite.appendCrusherFifoObservation:L17812](../anylogic/DRL-PPO.alp#L17812) | <code>batch present ? b[1] : 0</code> | unit |
| 1436 | `fifo.15.valid` | 槽位或历史样本是否有效 | [DumpSite.appendCrusherFifoObservation:L17812](../anylogic/DRL-PPO.alp#L17812) | <code>batch present ? 1 : 0</code> | binary |
| 1437 | `fifo.15.tons` | FIFO物料批次剩余吨数 | [DumpSite.appendCrusherFifoObservation:L17812](../anylogic/DRL-PPO.alp#L17812) | <code>batch present ? b[0]/500.0 : 0</code> | scaled |
| 1438 | `fifo.15.grade` | FIFO物料批次品位 | [DumpSite.appendCrusherFifoObservation:L17812](../anylogic/DRL-PPO.alp#L17812) | <code>batch present ? b[1] : 0</code> | unit |
| 1439 | `road.0.from` | 有向路段起点节点索引编码 | [Main.collectPhysicalObservation:L8096](../anylogic/DRL-PPO.alp#L8096) | <code>(obsNodeIndex(s.from)+1.0)/9.0</code> | unit |
| 1440 | `road.0.to` | 有向路段终点节点索引编码 | [Main.collectPhysicalObservation:L8096](../anylogic/DRL-PPO.alp#L8096) | <code>(obsNodeIndex(s.to)+1.0)/9.0</code> | unit |
| 1441 | `road.0.length` | 有向路段长度（米） | [Main.collectPhysicalObservation:L8096](../anylogic/DRL-PPO.alp#L8096) | <code>s.length/10000.0</code> | scaled |
| 1442 | `road.0.limit` | 道路限速（米/秒） | [Main.collectPhysicalObservation:L8096](../anylogic/DRL-PPO.alp#L8096) | <code>s.speedLimit/10.0</code> | scaled |
| 1443 | `road.0.closed` | 道路关闭标志 | [Main.collectPhysicalObservation:L8096](../anylogic/DRL-PPO.alp#L8096) | <code>s.closed?1:0</code> | binary |
| 1444 | `road.1.from` | 有向路段起点节点索引编码 | [Main.collectPhysicalObservation:L8096](../anylogic/DRL-PPO.alp#L8096) | <code>(obsNodeIndex(s.from)+1.0)/9.0</code> | unit |
| 1445 | `road.1.to` | 有向路段终点节点索引编码 | [Main.collectPhysicalObservation:L8096](../anylogic/DRL-PPO.alp#L8096) | <code>(obsNodeIndex(s.to)+1.0)/9.0</code> | unit |
| 1446 | `road.1.length` | 有向路段长度（米） | [Main.collectPhysicalObservation:L8096](../anylogic/DRL-PPO.alp#L8096) | <code>s.length/10000.0</code> | scaled |
| 1447 | `road.1.limit` | 道路限速（米/秒） | [Main.collectPhysicalObservation:L8096](../anylogic/DRL-PPO.alp#L8096) | <code>s.speedLimit/10.0</code> | scaled |
| 1448 | `road.1.closed` | 道路关闭标志 | [Main.collectPhysicalObservation:L8096](../anylogic/DRL-PPO.alp#L8096) | <code>s.closed?1:0</code> | binary |
| 1449 | `road.2.from` | 有向路段起点节点索引编码 | [Main.collectPhysicalObservation:L8096](../anylogic/DRL-PPO.alp#L8096) | <code>(obsNodeIndex(s.from)+1.0)/9.0</code> | unit |
| 1450 | `road.2.to` | 有向路段终点节点索引编码 | [Main.collectPhysicalObservation:L8096](../anylogic/DRL-PPO.alp#L8096) | <code>(obsNodeIndex(s.to)+1.0)/9.0</code> | unit |
| 1451 | `road.2.length` | 有向路段长度（米） | [Main.collectPhysicalObservation:L8096](../anylogic/DRL-PPO.alp#L8096) | <code>s.length/10000.0</code> | scaled |
| 1452 | `road.2.limit` | 道路限速（米/秒） | [Main.collectPhysicalObservation:L8096](../anylogic/DRL-PPO.alp#L8096) | <code>s.speedLimit/10.0</code> | scaled |
| 1453 | `road.2.closed` | 道路关闭标志 | [Main.collectPhysicalObservation:L8096](../anylogic/DRL-PPO.alp#L8096) | <code>s.closed?1:0</code> | binary |
| 1454 | `road.3.from` | 有向路段起点节点索引编码 | [Main.collectPhysicalObservation:L8096](../anylogic/DRL-PPO.alp#L8096) | <code>(obsNodeIndex(s.from)+1.0)/9.0</code> | unit |
| 1455 | `road.3.to` | 有向路段终点节点索引编码 | [Main.collectPhysicalObservation:L8096](../anylogic/DRL-PPO.alp#L8096) | <code>(obsNodeIndex(s.to)+1.0)/9.0</code> | unit |
| 1456 | `road.3.length` | 有向路段长度（米） | [Main.collectPhysicalObservation:L8096](../anylogic/DRL-PPO.alp#L8096) | <code>s.length/10000.0</code> | scaled |
| 1457 | `road.3.limit` | 道路限速（米/秒） | [Main.collectPhysicalObservation:L8096](../anylogic/DRL-PPO.alp#L8096) | <code>s.speedLimit/10.0</code> | scaled |
| 1458 | `road.3.closed` | 道路关闭标志 | [Main.collectPhysicalObservation:L8096](../anylogic/DRL-PPO.alp#L8096) | <code>s.closed?1:0</code> | binary |
| 1459 | `road.4.from` | 有向路段起点节点索引编码 | [Main.collectPhysicalObservation:L8096](../anylogic/DRL-PPO.alp#L8096) | <code>(obsNodeIndex(s.from)+1.0)/9.0</code> | unit |
| 1460 | `road.4.to` | 有向路段终点节点索引编码 | [Main.collectPhysicalObservation:L8096](../anylogic/DRL-PPO.alp#L8096) | <code>(obsNodeIndex(s.to)+1.0)/9.0</code> | unit |
| 1461 | `road.4.length` | 有向路段长度（米） | [Main.collectPhysicalObservation:L8096](../anylogic/DRL-PPO.alp#L8096) | <code>s.length/10000.0</code> | scaled |
| 1462 | `road.4.limit` | 道路限速（米/秒） | [Main.collectPhysicalObservation:L8096](../anylogic/DRL-PPO.alp#L8096) | <code>s.speedLimit/10.0</code> | scaled |
| 1463 | `road.4.closed` | 道路关闭标志 | [Main.collectPhysicalObservation:L8096](../anylogic/DRL-PPO.alp#L8096) | <code>s.closed?1:0</code> | binary |
| 1464 | `road.5.from` | 有向路段起点节点索引编码 | [Main.collectPhysicalObservation:L8096](../anylogic/DRL-PPO.alp#L8096) | <code>(obsNodeIndex(s.from)+1.0)/9.0</code> | unit |
| 1465 | `road.5.to` | 有向路段终点节点索引编码 | [Main.collectPhysicalObservation:L8096](../anylogic/DRL-PPO.alp#L8096) | <code>(obsNodeIndex(s.to)+1.0)/9.0</code> | unit |
| 1466 | `road.5.length` | 有向路段长度（米） | [Main.collectPhysicalObservation:L8096](../anylogic/DRL-PPO.alp#L8096) | <code>s.length/10000.0</code> | scaled |
| 1467 | `road.5.limit` | 道路限速（米/秒） | [Main.collectPhysicalObservation:L8096](../anylogic/DRL-PPO.alp#L8096) | <code>s.speedLimit/10.0</code> | scaled |
| 1468 | `road.5.closed` | 道路关闭标志 | [Main.collectPhysicalObservation:L8096](../anylogic/DRL-PPO.alp#L8096) | <code>s.closed?1:0</code> | binary |
| 1469 | `road.6.from` | 有向路段起点节点索引编码 | [Main.collectPhysicalObservation:L8096](../anylogic/DRL-PPO.alp#L8096) | <code>(obsNodeIndex(s.from)+1.0)/9.0</code> | unit |
| 1470 | `road.6.to` | 有向路段终点节点索引编码 | [Main.collectPhysicalObservation:L8096](../anylogic/DRL-PPO.alp#L8096) | <code>(obsNodeIndex(s.to)+1.0)/9.0</code> | unit |
| 1471 | `road.6.length` | 有向路段长度（米） | [Main.collectPhysicalObservation:L8096](../anylogic/DRL-PPO.alp#L8096) | <code>s.length/10000.0</code> | scaled |
| 1472 | `road.6.limit` | 道路限速（米/秒） | [Main.collectPhysicalObservation:L8096](../anylogic/DRL-PPO.alp#L8096) | <code>s.speedLimit/10.0</code> | scaled |
| 1473 | `road.6.closed` | 道路关闭标志 | [Main.collectPhysicalObservation:L8096](../anylogic/DRL-PPO.alp#L8096) | <code>s.closed?1:0</code> | binary |
| 1474 | `road.7.from` | 有向路段起点节点索引编码 | [Main.collectPhysicalObservation:L8096](../anylogic/DRL-PPO.alp#L8096) | <code>(obsNodeIndex(s.from)+1.0)/9.0</code> | unit |
| 1475 | `road.7.to` | 有向路段终点节点索引编码 | [Main.collectPhysicalObservation:L8096](../anylogic/DRL-PPO.alp#L8096) | <code>(obsNodeIndex(s.to)+1.0)/9.0</code> | unit |
| 1476 | `road.7.length` | 有向路段长度（米） | [Main.collectPhysicalObservation:L8096](../anylogic/DRL-PPO.alp#L8096) | <code>s.length/10000.0</code> | scaled |
| 1477 | `road.7.limit` | 道路限速（米/秒） | [Main.collectPhysicalObservation:L8096](../anylogic/DRL-PPO.alp#L8096) | <code>s.speedLimit/10.0</code> | scaled |
| 1478 | `road.7.closed` | 道路关闭标志 | [Main.collectPhysicalObservation:L8096](../anylogic/DRL-PPO.alp#L8096) | <code>s.closed?1:0</code> | binary |
| 1479 | `road.8.from` | 有向路段起点节点索引编码 | [Main.collectPhysicalObservation:L8096](../anylogic/DRL-PPO.alp#L8096) | <code>(obsNodeIndex(s.from)+1.0)/9.0</code> | unit |
| 1480 | `road.8.to` | 有向路段终点节点索引编码 | [Main.collectPhysicalObservation:L8096](../anylogic/DRL-PPO.alp#L8096) | <code>(obsNodeIndex(s.to)+1.0)/9.0</code> | unit |
| 1481 | `road.8.length` | 有向路段长度（米） | [Main.collectPhysicalObservation:L8096](../anylogic/DRL-PPO.alp#L8096) | <code>s.length/10000.0</code> | scaled |
| 1482 | `road.8.limit` | 道路限速（米/秒） | [Main.collectPhysicalObservation:L8096](../anylogic/DRL-PPO.alp#L8096) | <code>s.speedLimit/10.0</code> | scaled |
| 1483 | `road.8.closed` | 道路关闭标志 | [Main.collectPhysicalObservation:L8096](../anylogic/DRL-PPO.alp#L8096) | <code>s.closed?1:0</code> | binary |
| 1484 | `road.9.from` | 有向路段起点节点索引编码 | [Main.collectPhysicalObservation:L8096](../anylogic/DRL-PPO.alp#L8096) | <code>(obsNodeIndex(s.from)+1.0)/9.0</code> | unit |
| 1485 | `road.9.to` | 有向路段终点节点索引编码 | [Main.collectPhysicalObservation:L8096](../anylogic/DRL-PPO.alp#L8096) | <code>(obsNodeIndex(s.to)+1.0)/9.0</code> | unit |
| 1486 | `road.9.length` | 有向路段长度（米） | [Main.collectPhysicalObservation:L8096](../anylogic/DRL-PPO.alp#L8096) | <code>s.length/10000.0</code> | scaled |
| 1487 | `road.9.limit` | 道路限速（米/秒） | [Main.collectPhysicalObservation:L8096](../anylogic/DRL-PPO.alp#L8096) | <code>s.speedLimit/10.0</code> | scaled |
| 1488 | `road.9.closed` | 道路关闭标志 | [Main.collectPhysicalObservation:L8096](../anylogic/DRL-PPO.alp#L8096) | <code>s.closed?1:0</code> | binary |
| 1489 | `road.10.from` | 有向路段起点节点索引编码 | [Main.collectPhysicalObservation:L8096](../anylogic/DRL-PPO.alp#L8096) | <code>(obsNodeIndex(s.from)+1.0)/9.0</code> | unit |
| 1490 | `road.10.to` | 有向路段终点节点索引编码 | [Main.collectPhysicalObservation:L8096](../anylogic/DRL-PPO.alp#L8096) | <code>(obsNodeIndex(s.to)+1.0)/9.0</code> | unit |
| 1491 | `road.10.length` | 有向路段长度（米） | [Main.collectPhysicalObservation:L8096](../anylogic/DRL-PPO.alp#L8096) | <code>s.length/10000.0</code> | scaled |
| 1492 | `road.10.limit` | 道路限速（米/秒） | [Main.collectPhysicalObservation:L8096](../anylogic/DRL-PPO.alp#L8096) | <code>s.speedLimit/10.0</code> | scaled |
| 1493 | `road.10.closed` | 道路关闭标志 | [Main.collectPhysicalObservation:L8096](../anylogic/DRL-PPO.alp#L8096) | <code>s.closed?1:0</code> | binary |
| 1494 | `road.11.from` | 有向路段起点节点索引编码 | [Main.collectPhysicalObservation:L8096](../anylogic/DRL-PPO.alp#L8096) | <code>(obsNodeIndex(s.from)+1.0)/9.0</code> | unit |
| 1495 | `road.11.to` | 有向路段终点节点索引编码 | [Main.collectPhysicalObservation:L8096](../anylogic/DRL-PPO.alp#L8096) | <code>(obsNodeIndex(s.to)+1.0)/9.0</code> | unit |
| 1496 | `road.11.length` | 有向路段长度（米） | [Main.collectPhysicalObservation:L8096](../anylogic/DRL-PPO.alp#L8096) | <code>s.length/10000.0</code> | scaled |
| 1497 | `road.11.limit` | 道路限速（米/秒） | [Main.collectPhysicalObservation:L8096](../anylogic/DRL-PPO.alp#L8096) | <code>s.speedLimit/10.0</code> | scaled |
| 1498 | `road.11.closed` | 道路关闭标志 | [Main.collectPhysicalObservation:L8096](../anylogic/DRL-PPO.alp#L8096) | <code>s.closed?1:0</code> | binary |
| 1499 | `road.12.from` | 有向路段起点节点索引编码 | [Main.collectPhysicalObservation:L8096](../anylogic/DRL-PPO.alp#L8096) | <code>(obsNodeIndex(s.from)+1.0)/9.0</code> | unit |
| 1500 | `road.12.to` | 有向路段终点节点索引编码 | [Main.collectPhysicalObservation:L8096](../anylogic/DRL-PPO.alp#L8096) | <code>(obsNodeIndex(s.to)+1.0)/9.0</code> | unit |
| 1501 | `road.12.length` | 有向路段长度（米） | [Main.collectPhysicalObservation:L8096](../anylogic/DRL-PPO.alp#L8096) | <code>s.length/10000.0</code> | scaled |
| 1502 | `road.12.limit` | 道路限速（米/秒） | [Main.collectPhysicalObservation:L8096](../anylogic/DRL-PPO.alp#L8096) | <code>s.speedLimit/10.0</code> | scaled |
| 1503 | `road.12.closed` | 道路关闭标志 | [Main.collectPhysicalObservation:L8096](../anylogic/DRL-PPO.alp#L8096) | <code>s.closed?1:0</code> | binary |
| 1504 | `road.13.from` | 有向路段起点节点索引编码 | [Main.collectPhysicalObservation:L8096](../anylogic/DRL-PPO.alp#L8096) | <code>(obsNodeIndex(s.from)+1.0)/9.0</code> | unit |
| 1505 | `road.13.to` | 有向路段终点节点索引编码 | [Main.collectPhysicalObservation:L8096](../anylogic/DRL-PPO.alp#L8096) | <code>(obsNodeIndex(s.to)+1.0)/9.0</code> | unit |
| 1506 | `road.13.length` | 有向路段长度（米） | [Main.collectPhysicalObservation:L8096](../anylogic/DRL-PPO.alp#L8096) | <code>s.length/10000.0</code> | scaled |
| 1507 | `road.13.limit` | 道路限速（米/秒） | [Main.collectPhysicalObservation:L8096](../anylogic/DRL-PPO.alp#L8096) | <code>s.speedLimit/10.0</code> | scaled |
| 1508 | `road.13.closed` | 道路关闭标志 | [Main.collectPhysicalObservation:L8096](../anylogic/DRL-PPO.alp#L8096) | <code>s.closed?1:0</code> | binary |
| 1509 | `road.14.from` | 有向路段起点节点索引编码 | [Main.collectPhysicalObservation:L8096](../anylogic/DRL-PPO.alp#L8096) | <code>(obsNodeIndex(s.from)+1.0)/9.0</code> | unit |
| 1510 | `road.14.to` | 有向路段终点节点索引编码 | [Main.collectPhysicalObservation:L8096](../anylogic/DRL-PPO.alp#L8096) | <code>(obsNodeIndex(s.to)+1.0)/9.0</code> | unit |
| 1511 | `road.14.length` | 有向路段长度（米） | [Main.collectPhysicalObservation:L8096](../anylogic/DRL-PPO.alp#L8096) | <code>s.length/10000.0</code> | scaled |
| 1512 | `road.14.limit` | 道路限速（米/秒） | [Main.collectPhysicalObservation:L8096](../anylogic/DRL-PPO.alp#L8096) | <code>s.speedLimit/10.0</code> | scaled |
| 1513 | `road.14.closed` | 道路关闭标志 | [Main.collectPhysicalObservation:L8096](../anylogic/DRL-PPO.alp#L8096) | <code>s.closed?1:0</code> | binary |
| 1514 | `road.15.from` | 有向路段起点节点索引编码 | [Main.collectPhysicalObservation:L8096](../anylogic/DRL-PPO.alp#L8096) | <code>(obsNodeIndex(s.from)+1.0)/9.0</code> | unit |
| 1515 | `road.15.to` | 有向路段终点节点索引编码 | [Main.collectPhysicalObservation:L8096](../anylogic/DRL-PPO.alp#L8096) | <code>(obsNodeIndex(s.to)+1.0)/9.0</code> | unit |
| 1516 | `road.15.length` | 有向路段长度（米） | [Main.collectPhysicalObservation:L8096](../anylogic/DRL-PPO.alp#L8096) | <code>s.length/10000.0</code> | scaled |
| 1517 | `road.15.limit` | 道路限速（米/秒） | [Main.collectPhysicalObservation:L8096](../anylogic/DRL-PPO.alp#L8096) | <code>s.speedLimit/10.0</code> | scaled |
| 1518 | `road.15.closed` | 道路关闭标志 | [Main.collectPhysicalObservation:L8096](../anylogic/DRL-PPO.alp#L8096) | <code>s.closed?1:0</code> | binary |
