# Reward V1.0与基础评估迁移

本轮实施规范（2026-10-22）。单一配置文件为 `python/reward_v1_configuration.json`，新契约ID为 `dispatch-reward-v1.0`。沿用审计中V4业务参数，关闭动作级引导及班末累计品位奖励。历史V4审计与结果保留，不能用其模型续训/评估后标成V1.0。

## 冻结参数

| 参数 | 值/口径 |
|---|---|
| 品位目标/合规区间 | 0.27 / [0.26,0.28]，质量分数 |
| 班次/窗口 | 28800s / 7200s，共4窗 |
| 矿石计划 | 班末真实已破碎16000t；2h参考计划4000t，无独立窗口产量奖励 |
| 废石计划 | 班末实际完成卸载交付4000t |
| 等待项 | `−clip(Δ累计装卸等待vehicle-seconds/(9×200s),0,1)`；先合并等待，再裁剪，沿用原统计边界 |
| 每窗品位项 | `clip(1−clip(abs(0.27−grade)/0.01,0,3),−1,1)`；权重1，grade=该窗实际破碎金属/吨；空窗grade=0、违规 |
| 班末矿石缺口 | `−4×max(0,1−Qcrushed/16000)` |
| 班末废石缺口 | `−4×max(0,1−Qdelivered/4000)` |
| gradeAction | 开关false，权重0，所有动作均为0，含WASTE |
| 班末累计grade项 | 权重0；原始grade诊断仍保留，绝不加入奖励 |
| 闲置惩罚 | 不新增电铲idle或卡车idle奖励 |
| 物理及观测 | 9车、Ore卸载3位、Waste2位、500t缓冲、2500t/h破碎；raw1519维与Mask19–22不变 |

总reward仍通过原字段传输：`wait+grade_2h+production+waste`。为保持wire兼容，`grade_action/grade_shift`字段保留但必须严格0；Python不在接收后偷偷扣除旧奖励。所有参数由RPC显式传入并逐项匹配，不从零奖励猜测参数。配置文件中不再使用的prior=20000t、action_delta_clip=0.1仍登记并校验；它们在开关false及权重0时不参与奖励。

PPO保持普通算法、Actor/Critic各[128,128]、rollout128、batch32、10epochs、gamma0.995、lambda0.95、Adam、learning rate默认3e-4、entropy默认0.01。实验预算与PPO/AnyLogic种子逐次写入manifest；两组必须使用相同超参/预算/holdout seed集。当前20-run场景的AnyLogic种子为202610160011..202610160030，run_index=1..20；可选择其他明确配对预算与seed清单。冻结文件的物理参数是场景来源记录，RPC奖励配置握手不证明所有隐藏物理参数已自动核验。

## AnyLogic手动修改

用户已选择由自己手动修改ALP；本轮不直接编辑该文件。

当前 `.alp` 尚保留旧V4参数，Python升级后会拒绝它，不能据此开始训练。无需改动函数体、事件、观测或协议，仅在AnyLogic项目树的 **Main → Variables** 修改以下3项：

| 对象/变量 | 精确ID及原始源码位置 | 修改前 | 修改后 | 理由/影响 |
|---|---|---|---|---|
| `wGradeShift` | ID1790406210939，`anylogic/DRL-PPO.alp:1294`，Initial value | `6` | `0` | 关闭班末累计品位奖励；窗口品位照常结算 |
| `wGradeAction` | ID1790420834697，`:1456`，Initial value | `0.15` | `0.0` | 动作级奖励权重清零，与开关双重关闭 |
| `rewardContractId` | ID1791513434850，`:1561`，Initial value | `"dispatch-reward-physical-v4"` | `"dispatch-reward-v1.0"` | 区分新旧奖励/模型/结果，防止混用 |

核对并保持：

| Main变量/参数 | ID | 冻结值 |
|---|---|---|
| numTrucks | 1776757906246 | 9 |
| targetGrade | 1776757930264 | 0.27 |
| gradeLowerBound / gradeUpperBound | 1792411741383 / 1792411753002 | 0.26 / 0.28 |
| targetOreTonsShift / targetOreTons2h | 1790406183820 / 1790406174953 | 16000 / 4000 |
| targetWasteTonsShift | 1792411783408 | 4000 |
| waitRefSeconds / wWait | 1790406162748 / 1790420807463 | 200 / 1 |
| wGrade2h / wProduction | 1790406195665 / 1790406219972 | 1 / 4 |
| enableGradeActionReward / wWasteShortfall | 1792626220025 / 1792626243111 | false / 4 |

在 **RL_Training → Parameters（UseFreeformParameters=true）** 核查同ID参数覆盖，特别是 `enableGradeActionReward=false`。空覆盖沿用Main默认；不要改非激活RangeVariation表后误以为生效。`wGradeShift/wGradeAction/rewardContractId`在当前模型是普通变量，应改Main初值。保持串行、无额外replication，NumberOfRuns与Python预算/seed清单一致。

保存ALP并重新编译。完成后运行可选离线审计：

```bash
/home/jinx/miniconda3/envs/anylogic-env/bin/python -B -m python.alp_audit --alp anylogic/DRL-PPO.alp
```

验证：参数匹配、源码审计通过；RPC首个请求必须含新contract及全部config字段；每个回调flag=0、grade_action=0、grade_shift=0。废石不足时独立waste缺口仍非零；四窗按真实破碎结果产生。磁盘hash/离线审计不证明GUI实际已重新编译运行。

## provenance与评估

新增 `reward_v1_provenance.json` 仅登记本轮独立复核的三处函数差异：两个请求构造函数增加RPC配置map，另一个函数完整序列化配置。保留原始和V4来源记录；未知函数变更、函数删除、观测函数变化继续拒绝。`validate_alp_sources`只验证源码；`validate_alp_contract`同时检查活动实验参数，不能用源码通过冒充V1.0迁移完成。

评估默认不读ALP。先验证checkpoint的V1.0版本、配置与指纹，再等待AnyLogic START配置；核对指纹后才调用predict。首个START仍留给env.reset，后续回调继续逐次验证配置。可显式使用 `--audit-alp --alp-path anylogic/DRL-PPO.alp`；不开该选项不依赖本地ALP。配置缺失、错误schema、旧版本、运行中改参均应明确报错。

四窗摘要跨DECISION/END累积，每窗恰一次且按0..3顺序；验证窗吨/金属与班末产出一致。输出窗口合规率、全班四窗全合规率、矿石/废石各自达标率与生产联合达标率（只指矿废联合，不混入品位）。保留原始回报、Mask分布及等待vehicle-seconds，配置诊断不再被累加成reward分量。

## 本轮边界

未修改受保护PPO核心、P0预测器、原gRPC/schema或物理流程，未启动真实AnyLogic或生产训练。现有历史报告记录的是当时状态，不回写为新版本结果。单元测试使用临时ALP副本演练上述3项迁移；这不等于磁盘/GUI模型已完成修改。

## 验收结果与剩余步骤

2026-10-22使用 `anylogic-env` 执行：

```bash
PYTHONDONTWRITEBYTECODE=1 /home/jinx/miniconda3/envs/anylogic-env/bin/python -B -m pytest -q -p no:cacheprovider test
```

全套198项：沙箱内197通过，1项本地gRPC端口绑定受限；该项 `test/test_contracts.py::test_real_grpc_gym_lifecycle` 在获准沙箱外复跑后通过。合计198项均已通过，无跳过。新增/调整用例包括冻结配置逐项缺失与漂移拒绝、动作和班末grade项严格为0、矿废零/不足/达标/超产缺口、品位上下界和空窗、三项ALP迁移与部分迁移拒绝、未知源码变更/增删函数拒绝、四窗分批回调累积/重复/遗漏/乱序/质量金属守恒、配置指纹校验及真实Bridge的无ALP评估握手。合成PPO收集回归会更新临时模型，评估集成测试明确禁止learn/train；均未创建生产训练结果。

当前磁盘ALP的142个函数通过来源审计；全量V1.0契约审计仍因 `wGradeShift=6` 明确失败，这是等待人工迁移的预期结果，不是provenance失败。临时副本完成3项参数修改后，完整离线契约通过。后续顺序：手动改3项 → 保存并重新编译 → 上述可选离线审计 → 明确启动真实RPC接线验收；本轮没有声称真实运行已通过。

修改前后哈希一致：

- ALP：`330489397cd36f9c02f1cefd44c91eaf2df99fc4bc85e3c9cf6d7cd5ff6f1545`。
- 受保护PPO核心：`8e4cfa31c622f5e33756e304eea3f7526547db72ae93f7d9f00808845d61ef96`。
