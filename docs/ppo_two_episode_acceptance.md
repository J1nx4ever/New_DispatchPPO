普通PPO两episode训练验收

用户已授权本次小预算真实训练。本次从新初始化的DispatchMaskedPolicy开始，不加载旧模型。n_steps固定128，batch_size=32、n_epochs=10、gamma=0.995、gae_lambda=0.95，沿用现有Actor/Critic优化及Reward；episode预算为2。默认关闭逐transition、逐请求和rollout快照，仅保留汇总、TensorBoard、episode统计及训练完整性审计。

启动前需要用户手动操作（代理不编辑ALP）：

- 打开当前工作区anylogic/DRL-PPO.alp，选择RL_Training，将NumberOfRuns由20改为2，保存文件。只改变实验运行次数，不改变单班次仿真业务。
- 保持串行AllowParallelEvaluations=false、UseReplication=false、currentDispatchPolicy=3、usePhysicalObservation=true。
- 保持experimentRunIndex=(long) index+1L、experimentSeed=202610160011L+(long) index。对应两行元数据为(1,202610160011)、(2,202610160012)，清单已保存为docs/ppo_acceptance_seed_manifest.json。
- 验证保存后实验运行次数为2、模型编译通过。先保存再启动Python，避免run_manifest记录的是变更前的ALP摘要。

Python启动命令（如由代理启动了同一服务，不要在另一个终端重复执行）：

```bash
conda run --no-capture-output -n anylogic-env python -m python.train --episodes 2 --anylogic-seed-manifest docs/ppo_acceptance_seed_manifest.json --output-dir runs/ppo-acceptance-001 --n-steps 128 --batch-size 32 --seed 123
```

看到Dispatch gRPC listening提示后，在AnyLogic手动启动RL_Training。输出目录必须不存在或为空，重复验收需用新目录。命令不会自动打开AnyLogic。

训练在收到第2个真实终止后收尾：更新不足128步的最后rollout，刷新训练日志，再保存dispatch_ppo.zip。只有整个成功流程完成才会生成SUCCESS.json；不要把模型文件单独存在解释成完整验收通过。

验收检查：

1. SUCCESS.json.completed_episodes=2，run_manifest.status=complete，policy_contract_id=dispatch-masked-categorical-v1；seed元数据符合清单。
2. training_finish.json中collected_transitions=unique_updated_transitions，discarded_transitions=0，last_terminal_transition_updated=true，episode_budget_reached=true，final_logger_flushed=true；最后事件顺序为ppo_update_completed、final_logger_flushed、model_saved。
3. stage_episodes.jsonl恰好2条，episode长度之和等于collected_transitions；实际最后rollout长度与真实transition数对应。若总步数恰好为128的倍数，则本次不覆盖实际尾部，尾部路径仍由合成测试保证。
4. dispatch_ppo.zip摘要等于SUCCESS.json.model_sha256；能加载出DispatchMaskedPolicy，权重有限，预测只选择合法动作。
5. 默认不存在transitions.jsonl和rollout_audit；episode与优化统计继续保留。受保护核心SHA256保持8e4cfa31c622f5e33756e304eea3f7526547db72ae93f7d9f00808845d61ef96。

两episode仅验证真实数据上的训练闭环，不据此判断收敛或生产调度效果。真实耗尽mask若未发生，仍不能声称该真实场景已覆盖。
