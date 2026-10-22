# 当前迁移说明

Reward V1.0的冻结参数、ALP手动修改位置及评估握手规范见[迁移文档](reward_v1_freeze.md)。训练、通信检查及评估默认均以RPC完整配置为准；评估仅在显式 `--audit-alp --alp-path ...` 时审计本地ALP。以下历史记录中的V4配置可变范围不再适用于V1.0冻结实验。

AnyLogic运行时配置握手：无需重复上传ALP

训练和通信检查默认只使用AnyLogic通过gRPC传来的配置，不读取本地ALP，不运行本地源码审计。修改开关后重启Python服务及对应的AnyLogic实验即可，默认--grade-action auto自动识别组别。保留通信契约和运行一致性检查，它们不是ALP文件审核。

目前ALP已经发送grade_action_enabled，但尚未完整发送废石权重及v4固定数学参数；Python不能从“惩罚为0”推断权重。为完整识别配置，需要在AnyLogic做以下一次性接口补充，之后无需再上传ALP。代理没有编辑ALP。

1. 在Main中新建Function：

- 名称：buildRewardConfigComponents
- 返回值：java.util.Map<String, Double>
- 参数：无
- Body填写以下代码（只填函数体，不再套public/return type函数声明）：

```java
java.util.Map<String, Double> c = new java.util.LinkedHashMap<String, Double>();
c.put("grade_action_enabled", enableGradeActionReward ? 1.0 : 0.0);
c.put("config.waste_shortfall_weight", wWasteShortfall);
c.put("config.target_waste_tons_shift", targetWasteTonsShift);
c.put("config.num_trucks", (double) trucks.size());
c.put("config.target_grade", targetGrade);
c.put("config.grade_lower", gradeLowerBound);
c.put("config.grade_upper", gradeUpperBound);
c.put("config.wait_ref_seconds", waitRefSeconds);
c.put("config.target_ore_tons_2h", targetOreTons2h);
c.put("config.target_ore_tons_shift", targetOreTonsShift);
c.put("config.w_wait", wWait);
c.put("config.w_grade_2h", wGrade2h);
c.put("config.w_grade_shift", wGradeShift);
c.put("config.w_production", wProduction);
c.put("config.w_grade_action", wGradeAction);
c.put("config.grade_prior_tons", gradePriorTons);
c.put("config.grade_action_delta_clip", gradeActionDeltaClip);
return c;
```

2. 在Main.selectNextLoadSiteAI中找到构造DispatchRequest的builder链，在末尾.build()之前添加：

```java
.putAllRewardComponents(buildRewardConfigComponents())
```

例如末尾变成：

```java
.setRewardContractId(rewardContractId)
.putAllRewardComponents(buildRewardConfigComponents())
.build();
```

3. 在Main.finishEpisodeAndNotify中，同样找到DispatchRequest的builder链，在.build()前添加相同的一行。原来的wait/grade_action/waste及其他诊断字段全部保留。

这三处修改只把实际配置放进既有reward_components map，不改变Reward公式、参数值、观测维度、动作或运输业务，不需要改proto或重新构建协议JAR。config.*和grade_action_enabled都是诊断元数据，不计入总奖励。已有grade_action_enabled键即使重复写入同一值也不改变其含义。

4. 保存并编译模型。首个EPISODE_START及后续请求都会带完整配置。Python收到首个合法START后锁定配置，再创建对应on/off目录并初始化Policy；该START仍由原Gym reset消费，没有多reset、虚构transition或丢样本。后续请求的配置改变会报错，避免在同一训练运行中混入不同目标。

5. 日常使用同一个命令，不必每次执行alp_audit，也不必传--alp-path：

```bash
conda run --no-capture-output -n anylogic-env python -m python.train --episodes 20 --anylogic-seed-manifest docs/rl_training_seed_manifest.json --seed 123
```

看到“waiting for AnyLogic EPISODE_START configuration”后，手动启动AnyLogic。运行次数在AnyLogic中设为20以匹配本次预算；Python不再通过本地ALP核对此设置，而是按请求元数据及--episodes预算验收。请避免让AnyLogic在Python预算结束后继续发起额外运行。

- 开组：仅在AnyLogic设置enableGradeActionReward=true，然后使用同一个Python命令。
- 关组：仅在AnyLogic设置enableGradeActionReward=false，然后使用同一个Python命令。
- 可选--grade-action on/off只是额外防误配；默认auto无需填写。
- 不训练的联调也使用同一握手：python -m python.smoke_dispatch --action-rule masked-untrained --output-dir runs/smoke-runtime-001。
- 详细记录仍默认关闭。manifest保存配置来源anylogic_rpc、完整接收参数、组别和指纹；默认alp_path/alp_sha256为空，不声称验证GUI源文件身份。

当前v4支持从RPC识别开关、废石权重及废石目标。其余配置必须匹配已定义的v4数学契约，数值变化会给出“unsupported v4 runtime parameter”错误，不能默默按旧常量计算；修改奖励数学定义时仍需同步Python数学契约/版本，但不要求上传ALP。缺失参数会给出具体字段名称，不回退读取本地ALP或猜测配置。

本地文件审计仅在确有需要时显式执行：

```bash
conda run -n anylogic-env python -m python.alp_audit --alp /path/to/model.alp
```

或训练时显式选择--audit-alp --alp-path /path/to/model.alp；该可选结果会与运行时配置比较。日常消融不用这些选项。

验证结果：anylogic-env下126项测试通过，包括on/off握手、完整参数识别、缺失/漂移拒绝、无本地ALP的实际masked PPO合成训练启动、首个START保留、关闭服务释放等待RPC，以及全部既有PPO/掩码/gRPC回归。真实AnyLogic新配置字段的传输尚待用户完成一次性接口补充后验证；本次未运行真实训练。
