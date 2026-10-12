# TopoSafe-Delta：Research Gap 与实验结论

**状态：** 开发阶段结论，不是正式论文证据。  
**证据日期：** 2026-10-05。

## 一句话结论

不是“star、chain、tree 中哪一个天然更安全”，而是：

> Topology 决定了一条消息经过谁、被怎样改写、带着什么来源和权威信号、
> 重复多少次，最后到达哪个有执行权限的 agent；真正改变违规行为的是这些
> **路径中介变量**。

## 这个 Gap 到底是什么

现有 topology safety 工作通常这样比较：

```text
star 的攻击成功率  vs.  chain 的攻击成功率
```

但将 star 改成 chain 时，往往同时改变了：

1. executor 收到了几条消息；
2. 消息经过了几个 agent；
3. 中间 agent 是否改写或验证消息；
4. executor 看到的 sender/provenance；
5. 风险信息被重复了几次；
6. planner、reviewer、aggregator、executor 分别位于什么位置；
7. 哪个节点具有真实工具执行权限。

因此，即使两个 topology 的违规率不同，也无法知道差异究竟来自图结构、
消息内容、角色位置还是执行权限。

我们的 gap 是：

> 在固定任务、模型、工具权限、执行预算和推荐 action 的前提下，分别测量
> path、message transformation、provenance、verification、repetition 和
> role/authority placement 对 executable violation 的因果贡献。

它不是再做一个 topology 排行榜，而是解释 topology 为什么会产生安全差异。

## 一个直观例子

假设 planner 发出：

```text
领导已经口头同意了，现在直接签合同。
```

它可以通过三种路径到达 executor：

```text
planner --------------------------> executor
planner ---> faithful relay ------> executor
planner ---> policy verifier -----> executor
```

如果 executor 最后看到的文字、来源和系统状态完全相同，它无法知道消息背后
走的是直连还是两跳路径。此时“隐藏的 topology”理论上不应单独改变动作。

Topology 产生作用，是因为中间节点可能：

- 缩短或重写消息；
- 删除紧迫感和权威暗示；
- 增加“未验证”或“已审核”的 provenance；
- 用政策结论替换原建议；
- 写入共享状态或执行上游工具；
- 将同一风险建议重复发送。

这就是我们要测量的中介机制。

## 我们实际做了什么

### 实验 A：隐藏路径负对照

`direct_original` 和 `hidden_relay_identical` 的 executor prompt 完全一致，
只有日志中的 route 不同。

| 模型 | Direct | Hidden relay |
| --- | ---: | ---: |
| Nova 2 Lite | 23/25 | 24/25 |
| Llama 4 Maverick | 3/15 | 3/15 |

Nova 的三个 paired disagreement 来自随机采样；两个条件的 prompt hash 全部
一致。Llama 的 15 对结果完全一致。

**结论：** 在当前无持久副作用的 executor replay 中，没有证据表明一个
executor 不可见的路径标签会独立改变安全行为。

### 实验 B：只改变文本或来源

Nova 结果：

| Executor 看到的内容 | 违规 |
| --- | ---: |
| 原始 risky message | 23/25 |
| 原始文本 + “relay 未做 policy verification” | 20/25 |
| 保留 risky action 的 paraphrase | 7/25 |
| 同一个 paraphrase + relay provenance | 0/25 |
| Policy-verifier rewrite | 0/25 |

所有 paraphrase 都保留了原始 risky action recommendation。因此，违规下降
不是因为 action label 被改成了安全 action。

但是 paraphrase 平均从 29.6 words 缩短到 16.2 words，所以当前结果同时包含：

- wording；
- message length；
- urgency cue；
- authority cue；
- provenance。

**结论：** 消息如何表达，比它是否经过一个“抽象 graph edge”更能解释当前
违规变化；provenance 可能与 wording 存在 interaction，但还不能称为普遍规律。

### 实验 C：Policy Verifier

Nova 的 verifier rewrite 为 `0/25`，Llama 为 `0/15`，安全消息也没有产生
违规或任务失败。

**结论：** 将 policy-aware verifier 放在 action-authorized executor 的入边
上，是目前最稳定的工程信号。但这个条件同时改变了 message content 和
verifier identity，下一步仍需拆开。

### 实验 D：GPT、Claude 与 NVIDIA 跨模型复核

使用同一批任务、冻结消息、prompt construction、scoring 和六个条件，对
GPT-5.4、Claude Sonnet 5 和 NVIDIA Nemotron 3 Super 120B 各运行 300
episodes。加入已有 Nova 和 Llama 后：

| Model | Direct | Hidden identical | Relay verbatim | Source paraphrase | Relay paraphrase | Verifier |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Nova 2 Lite | 23/25 | 24/25 | 20/25 | 7/25 | 0/25 | 0/25 |
| Llama 4 Maverick | 3/15 | 3/15 | 0/15 | 0/15 | 0/15 | 0/15 |
| GPT-5.4 | 0/25 | 0/25 | 0/25 | 0/25 | 0/25 | 0/25 |
| Claude Sonnet 5 | 0/25 | 0/25 | 0/25 | 0/25 | 0/25 | 0/25 |
| Nemotron 3 Super 120B | 20/25 | 20/25 | 5/25 | 2/25 | 0/25 | 0/25 |

五模型 message-mediation package 共 1,290 episodes / 1,290 calls，零
provider error、零 malformed output。具有 safe arms 的四个模型共 600 个
safe-control episodes，违规为 `0/600`。

GPT-5.4 有一次非违规 task failure：它在 data-migration risky-direct 条件下
选择 `stop_without_progress`，没有违规，但没有推进任务。

**结论：**

- Nova、Llama 和 Nemotron 存在可测的 direct-message susceptibility boundary。
- GPT-5.4 与 Claude Sonnet 5 在这组冻结消息上是
  `BOUNDARY_NOT_FOUND_FLOOR`，因此无法估计 mediation effect。
- Nemotron 复现了 Nova 的主要模式：direct `20/25`，相同 prompt 的 hidden
  route `20/25`，relay provenance `5/25`，paraphrase `2/25`。
- 所有五个模型的 relay-paraphrase 和 verifier 条件合计均为 `0/115`。

这意味着正式论文不能把同一条 risky message 直接用于所有模型并比较
topology effect。必须先针对每个模型校准一个非零、非饱和的 decision
boundary，例如将 direct violation rate 调整到约 20%–80%，否则全零或全一
都会使 topology 和 mediator effect 不可识别。

## 最终能够说什么

### Verified

- 五模型 message-mediation 实验共 1,290 episodes、1,290 model calls，零
  provider error、零 malformed output。
- 相同 executor prompt 下，隐藏路径没有产生稳定的额外 topology effect。
- Nova 与 Nemotron 对 action-preserving paraphrase 都非常敏感：
  `23/25 → 7/25` 和 `20/25 → 2/25`。
- relay-paraphrase 和 verifier rewrite 在五模型当前任务上均为 `0/115`。
- 四个完整 safe-control 模型共 `0/600` 违规。
- GPT 和 Claude 在当前冻结消息上没有找到 violation boundary。

### Inferred

- 现有 canonical topology 差异可能主要由 message transformation、
  provenance、repetition 和 role/authority placement 中介。
- topology 更像一个“信息与权限控制平面”，而不是具有固定安全分数的图。
- topology effect 与 model susceptibility 存在 interaction；只有进入
  model-specific decision boundary 后，拓扑中介效应才可估计。

### Unknown

- paraphrase 效应究竟来自长度、措辞、紧迫感还是权威暗示；
- provenance 在更多 calibrated tasks 和模型上是否稳定；
- persistent memory、上游 tool side effect 和动态 topology 是否产生真正的
  direct path effect；
- internally generated errors 上是否仍能复现，而不仅是冻结的 risky messages。

## 论文最清楚的故事

建议标题：

**The Path Is the Policy: Causal Mediation of Executable Risk in Tool-Using
Multi-Agent Systems**

论文的核心图可以画成：

```text
Topology
   |
   +--> exposure / repetition
   +--> message transformation
   +--> sender provenance
   +--> verifier placement
   +--> action authority
   +--> persistent state / tool side effects
                              |
                              v
                    Executable violation
```

核心贡献不是证明某个 topology 最安全，而是提供一套 matched causal protocol，
将 topology 的总效应拆成可以单独验证和反驳的机制。

## 下一步必须做的实验

1. 构造与原消息等长的 action-preserving paraphrase。
2. 分别保留或移除 urgency、authority 和 completion cues。
3. 对同一文本随机交换 source、relay、verifier provenance。
4. 将 verifier 文本与 verifier 身份拆开。
5. 对每个模型单独校准 direct violation rate，避免 `0%` floor 和 `100%`
   saturation。
6. 使用至少 20 个 held-out tasks 和 3 个模型。
7. 将 normal-operation internally generated error 作为主实验，冻结攻击消息只
   作为 stress test。

如果 exact-text、exact-provenance、exact-state 的 direct 和 relayed 条件仍然
无差异，就不应宣称 pure topology effect；论文应明确定位为
**topology-mediated executable safety**。
