普通PPO动作掩码实现与验证（2026-10-21）

已实现DispatchMaskedPolicy，并接入普通EpisodeBudgetPPO训练入口。本阶段仅执行CPU合成测试和本机gRPC回归，没有启动真实AnyLogic仿真、正式训练或加载旧模型。

1. 实现范围

- python/masked_policy.py：继承SB3 2.9.0 ActorCriticPolicy，从1519D原始观测的19..22读取二值mask，在Categorical logits上将非法项设为-inf。非法动作概率和对应logit梯度严格为0。没有使用sb3-contrib或引入其他强化学习算法。
- forward、get_distribution/predict、evaluate_actions使用同一掩码规则。存入rollout的action/log_prob来自掩码分布，更新时从同一条原始observation恢复mask，不依赖外部可变mask缓存。
- Actor/Critic特征提取支持共享和分离两种配置。PPO损失、优化器、梯度裁剪、学习率、GAE和collector保持原实现；predict_values完全继承SB3，不要求terminal存在合法动作。
- terminal全零mask仅允许价值计算。任何actor入口收到终止观测、非终止全零mask或非二值mask均报错；evaluate_actions遇到非法历史动作报错，不更换动作或使用未掩码概率补救。
- python/train.py：新模型使用DispatchMaskedPolicy，manifest和SUCCESS记录dispatch-masked-categorical-v1；恢复时拒绝旧的无掩码/31D模型元数据，加载后也核验实际policy类型。详细日志开关仍默认关闭。
- python/smoke_dispatch.py：新增--action-rule masked-untrained，用新初始化的掩码Policy做单班次随机推理，不加载checkpoint，不执行optimizer.step。默认first-legal规则保持可用。默认仅status.json汇总，新增4种动作计数和决策mask组合计数，不生成逐transition或全量观测文件。

2. 验证

使用/home/jinx/miniconda3/envs/anylogic-env/bin/python（SB3 2.9.0、Torch 2.9.1+cu128），合成模型均在CPU上测试。命令：

```bash
PYTHONPATH=/tmp/new_dispatchppo_test_deps /home/jinx/miniconda3/envs/anylogic-env/bin/python -m pytest -q test --junitxml=docs/masked_policy_tests.xml
```

最终84通过、0失败、0跳过；其中22项新增掩码测试，62项既有测试继续通过。pytest仍使用/tmp临时目录中的版本，未升级Conda环境。

覆盖随机/确定性采样、单条/批量predict、非法高logit仍为零概率、单合法动作entropy=0、forward与evaluate_actions的log_prob及PPO ratio一致、有限梯度、非法logit零梯度、全合法时与原ActorCriticPolicy等价、终止及混合终止批量只走critic、非法mask与非法历史动作拒绝、非有限logit拒绝。

真实EpisodeBudgetPPO在变化mask的合成环境中执行140步、5+6步和129步episode预算；环境逐动作断言合法，更新前重新核对buffer old_log_prob，所有transition实际参与优化，Actor和Critic参数均更新。128步不重置episode，尾部12/11/1步均完成更新，保存前日志刷新，保存加载权重和分布一致，默认无transition文件。另验证time-limit的全零terminal观测能由原critic完成bootstrap。

通信检查的masked-untrained规则也在合成episode中验证了动作合法、终止后不再调用actor、optimizer不更新及汇总计数正确。真实AnyLogic使用该Policy的行为、混合mask出现、耗尽后行为及GPU运行仍待实际验证，不在本次通过声明范围内。

3. 受保护文件

PPO核心修改前后SHA256均为：

8e4cfa31c622f5e33756e304eea3f7526547db72ae93f7d9f00808845d61ef96

ALP修改前后SHA256均为：

9115584458893131c665b71a7b6ffadcaa85285d0e5b3506cb4f92a101cde13f

两者均未修改。本阶段无需调整ALP业务函数或Reward公式。

4. 下一步：用户手动启动一次掩码推理联调

确认RL_Training只运行一次、串行、policy=3、usePhysicalObservation=true。沿用上次可编译并通信成功的ALP，不改变仿真机制；如果运行次数仍为20，请在RL_Training参数中临时手动设NumberOfRuns=1，原因是本服务只接收一个episode。检查结束后可恢复原运行次数。

在项目根目录先运行以下命令，看到监听提示后再手动启动AnyLogic的RL_Training：

```bash
conda run --no-capture-output -n anylogic-env python -m python.smoke_dispatch --action-rule masked-untrained --output-dir runs/smoke-masked-001
```

目录必须尚不存在。该命令尚未由代理执行。默认仅输出状态/汇总，不开启详细记录；--record-transitions和--capture-observations仅在排错确有需要时手动添加。

完成后检查status.json中status=complete、terminated=true、truncated=false、action_rule=masked_untrained、policy_trained=false、ppo_optimization=false。action_counts给出四种动作执行数，decision_mask_counts给出非终止决策mask组合及次数；其和均应等于transitions。若只出现1111，则仍未实测耗尽/混合mask，这部分由合成测试覆盖，不能声称真实耗尽场景已通过。

新Policy权重尚未训练，随机动作的品位/产量不能当作训练效果。待这次联调检查通过后，再决定小预算普通PPO训练参数；当前不启动正式训练。
