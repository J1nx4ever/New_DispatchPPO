anylogic-env 复验记录（2026-10-21）

动作掩码阶段更新：普通PPO掩码Policy及训练入口已实现，最新全量测试84项通过，证据为masked_policy_tests.xml。详见[动作掩码实现与联调步骤](masked_policy_validation.md)。ALP及PPO核心保持不变，尚未启动掩码Policy真实仿真或正式训练。以下记录为此前阶段历史。

最新复验：用户修正ALP后，当前静态审计通过，deterministicCheck=false。新增不训练通信检查入口后，anylogic-env下全部61项测试通过（0失败、0跳过），最新JUnit为anylogic_env_tests.xml。当前ALP SHA256为9115584458893131c665b71a7b6ffadcaa85285d0e5b3506cb4f92a101cde13f，本次代理未修改它；PPO核心SHA256仍保持不变。下一步手动操作见[单班次通信检查](anylogic_smoke_check.md)。以下53通过、1失败及旧ALP摘要保留为此前复验历史，当前拼写问题已解决。

本次使用 `/home/jinx/miniconda3/envs/anylogic-env/bin/python`（Python 3.10.19）。未编辑项目ALP，未编辑PPO核心，未启动正式训练或加载旧模型。

Python审计器现按RL_Training当前模式解析参数：自由参数模式只读取FreeformParamValue，范围模式只读取固定RangeVariationParamValue；缺省表达式回退Main默认值。数值覆盖必须匹配Reward Contract，物理观测必须实际启用，deterministicCheck必须是true/false，policy必须是3；不执行任意Java表达式，不猜测表达式的值。

当前Main.usePhysicalObservation默认false，但RL_Training自由参数覆盖true，这是合法的配置。旧审计器对此产生的关闭误报已修复。新增8个测试覆盖覆盖优先级、非法布尔、固定/范围模式、奖励参数覆盖和非有限数值。

验证命令：

```bash
PYTHONPATH=/tmp/new_dispatchppo_test_deps /home/jinx/miniconda3/envs/anylogic-env/bin/python -m pytest -q test --junitxml=docs/anylogic_env_tests.xml
```

结果：**53通过，1失败，0跳过**。失败为test_alp_and_artifacts对当前项目ALP配置的校验；原因是RL_Training.deterministicCheck仍为`fasle`。该失败保留，没有跳过或改变断言。临时ALP副本中使用正确布尔值的回归测试通过；临时副本不会回写原文件。真实本机gRPC回环、模块导入和合成PPO测试均通过。gRPC测试需要本机临时socket执行权限。

pytest 8.4.2及其依赖仅安装在`/tmp/new_dispatchppo_test_deps`，没有升级或修改Conda环境。临时目录清除后需重新准备测试依赖。requirements.txt已改为本次实际使用的anylogic-env版本；此前DRL环境清单保存到phase1_requirements_drl.txt。未执行整套requirements安装。

用户手动操作：打开AnyLogic中当前工作区的DRL-PPO.alp，选择RL_Training，在自由参数表找到deterministicCheck，将`fasle`改为`false`（如需确定性校验则设`true`），保存。它只影响随机性校验配置，不改变奖励公式或运输业务。保存后先编译，确认不再存在fasle未定义错误，再运行：

```bash
/home/jinx/miniconda3/envs/anylogic-env/bin/python -m python.alp_audit
PYTHONPATH=/tmp/new_dispatchppo_test_deps /home/jinx/miniconda3/envs/anylogic-env/bin/python -m pytest -q test
```

成功标准为ALP审计通过、全部测试通过。真实AnyLogic资源加载、运行时schema、奖励轨迹、班末事件顺序仍待真实仿真验证。之后应进行schema输出核对及动作掩码Policy实现；本次未进入该阶段。

本次前后PPO核心SHA256均为：

`8e4cfa31c622f5e33756e304eea3f7526547db72ae93f7d9f00808845d61ef96`

项目ALP本次前后SHA256均为：

`85c1d38a726acffccb9659c510199b9b07518192f1ba98c43b7cb9de5bb63ed5`

此前phase1_audit_report.md和phase1_tests.xml保留为DRL环境的历史证据；本次环境状态以本记录及anylogic_env_tests.xml为准。
