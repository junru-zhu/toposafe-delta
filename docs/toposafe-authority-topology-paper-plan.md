# TopoSafe-Delta: Top-Conference Paper Plan

**Working title:** TopoSafe-Delta: Authority Cut for Decoupling Communication,
Authorization, and Execution in Multi-Agent LLMs  
**中文题目：** TopoSafe-Delta：多智能体 LLM 安全中的通信、权限与执行拓扑解耦  
**Evidence snapshot:** 2026-10-07  
**Paper type:** Causal measurement paper with an authority-topology mechanism  
**Current status:** An evidence-frozen venue-neutral manuscript now exists.
Authority Composition v0.2 completed 7,440 formal rows without human
review, but only two of four model blocks passed its preregistered validity
gate. Runtime Enforcement v0.2 completed 2,688 fresh initial calls and 257
automatically triggered recovery calls; all four model gates passed and no
invalid proof reached a protected action. Matched Communication B1 completed
12,480 frozen-message calls, passed all four model gates, produced no
preregistered large topology effect, and placed 26 of 27 cross-model contrasts
inside the frozen practical-equivalence margin. Free-running Communication B2
v0.3 then completed 2,880 seven-call episodes, or 20,160 assigned model calls,
with 20,319 provider attempts including retries. All four model blocks passed.
No large total topology effect or semantic increment over B1 replicated across
three models; 10 of 27 contrasts were model-conditional, and the six
SoD/quorum executed-FAR contrasts were practically equivalent across all four
models. Targeted Authority Mechanism Ablations v0.1 completed another 1,200
formal calls with 1,201 provider attempts. All four model gates passed, every
invalid target proof was prevented from authorizing a protected execution,
stale signed replay was the only replicated large advisory effect, and
source-verifier identity exchange was practically equivalent across all four
models. Free-Running Schedule Replication v0.1 completed the remaining 2,880
episodes and 20,160 assigned calls with 20,321 provider attempts. All four
model gates passed. Neither schedule produced a cross-model replicated large
total topology effect or semantic increment, and no large schedule shift
replicated across models. The corrected 61,440-call core intervention ledger is
complete, and the manuscript reports 66,090 formal model calls after adding
the development placement study and both runtime-enforcement extensions. A
zero-call post-hoc control sensitivity then audited the two failed
Study A blocks. All 41 failures in GPT-5.4 and Llama 4 Maverick were safe
`stop_without_progress` choices with zero false-control violations. All four
models pass the later fresh-factorial responsiveness rule, but no
authority-cut threshold contrast has a positive interval in all four models.
The evidence therefore supports the structural and enforced mechanism, not a
universal advisory response to increasing authority cut.

## 1. The Paper Thesis

多智能体安全研究通常把系统画成一张通信图，然后比较 chain、star、tree 或 mesh
哪一种更安全。但真正决定一个错误能否变成受保护状态变化的，不只是谁能给谁发消息，
还包括：

1. 谁的声明有资格改变受保护状态；
2. 一个声明需要多少个相互独立的授权主体共同确认；
3. 哪些 agent 最终拥有执行高影响动作的能力。

TopoSafe-Delta 将一个多智能体系统表示为三张相互关联但概念不同的图：

\[
\mathcal{M} = (G_C, G_A, G_E)
\]

- \(G_C\), **communication topology**：谁能向谁传递消息；
- \(G_A\), **authority topology**：谁的、或哪些主体组合的证明，可以授权某个状态
  更新；
- \(G_E\), **execution topology**：哪些主体可以调用受保护工具或提交不可逆状态变化。

论文的核心命题不是“拓扑重要”，而是：

> 把 communication architecture 当作单一自变量，会混淆消息路径、权限来源和执行
> 能力。多智能体可执行安全需要对 \(G_C\)、\(G_A\) 和 \(G_E\) 分别干预和估计。

当前 Authority-Placement v1.6 提供了这个命题的第一块开发证据：在固定
\(G_C\) 和 \(G_E\) 时，将一个单点 authority 从 source 移到 relay 或 verifier
没有产生稳定差异；相反，platform-authenticated credential 一致且幅度明显地提高了模型对真假
声明的接受率。换句话说，**authentication 在当前设置中是 compliance amplifier，
不是 truth signal**。

Runtime Enforcement v0.1 和 fresh independent v0.2 factorial 进一步分离了
\(G_A\) 与 \(G_E\) 的作用：
\(\kappa_A\) 决定 adversary 能否构造 policy-valid proof，而 fail-closed execution
gate 决定 invalid proof 是否能到达受保护动作。v0.2 在 2,688 条 fresh initial
episodes 中独立复现了该机制：四个模型均通过 validity gate，所有 below-cut
invalid proofs 的 enforced FAR 为零，257 次自动触发 recovery 全部保持 safe
progress。

Matched Communication B1 进一步固定 \(G_A\)、\(G_E\)、message body、traffic 和
budget，只改变六节点通信图。12,480 条正式结果中没有预注册大效应，也没有任何
model-conditional 大效应；27 个 topology-by-authority-by-outcome contrasts 中有
26 个在四个模型上都落入 \(\pm10\) percentage-point practical-equivalence
margin。这支持一个更窄的判断：frozen-message 条件下，route/provenance metadata
不是稳定的大效应来源。

Free-running Communication B2 在同一 30-task subset 上允许中间节点通过统一的
structured forwarding schema 改写或丢弃 message 和 proof。四个模型全部通过
validity gate。较长路径在每个模型中都降低了平均文本相似度，但没有产生跨至少三个
模型复制的大型 safety effect。模型条件效应主要集中在 verifier-single regime；
当 SoD/quorum 的 invalid proof 由统一 fail-closed gate 执行时，六个跨拓扑
executed-FAR contrasts 均满足全模型实用等价。

Targeted Authority Mechanism Ablations 随后固定 task、model 和 parent
reference，只改变 proof 或 authority semantics。1,200 条正式结果中，四个模型
全部通过 gate，八类 invalid proof 的 enforced FAR 都是 0。`stale signed
replay` 是唯一在至少三个模型中复制的大型 advisory effect；交换 source 与
verifier identity 则是唯一在四个模型中都满足 \(\pm10\) percentage-point
practical equivalence 的消融。

Free-Running Schedule Replication 最后保持 task、prompt、model、budget、scoring
和 gate 不变，只改变执行 schedule seed 与请求顺序。四个模型再次全部通过 gate。
两次 schedule 都没有产生跨至少三个模型复制的大型 total topology effect 或
semantic increment；schedule difference 本身也没有跨模型复制的大效应。三个大型
schedule shift 都是单模型的 true-utilization 变化。SoD/quorum 的六个
executed-FAR schedule differences 在四个模型上均满足实用等价。

## 2. Research Gap

### 2.1 Covered territory

现有工作已经覆盖以下宽泛问题：

- NetSafe 研究 canonical communication topology 如何改变攻击传播与任务表现；
- G-Safeguard 基于 utterance graph 检测异常并执行 topology intervention；
- Architecture Matters 系统比较 role、communication topology 和 memory 对安全与
  性能的影响；
- MasDrift 测量不同 centralized/decentralized architecture 中 authorization
  preservation，并比较 source re-anchoring 与 chain propagation；
- From Spark to Fire 建模错误在多智能体依赖图中的级联；
- Delegation Without Trust 从 runtime governance 角度实现身份、授权和委派约束。

因此不能主张：

- 首次研究 multi-agent topology safety；
- 首次发现 topology、role 或 hierarchy 会影响安全；
- 首次研究 authorization drift；
- 首次提出 agent identity、delegation 或 runtime authorization；
- 首次使用 executable state 判断 agent violation。

### 2.2 The unresolved causal problem

最接近的 MasDrift 明确将其 scale-up conditions 解释为一个 architecture bundle：
depth、agent count、handoff count 和 tool-call exposure 会同时变化。因此其结果可以
说明 architecture configuration 与 authorization failure 相关，但不能单独识别：

- 是 communication path length 造成风险；
- 是 handoff 中的语义损失造成风险；
- 是 authority 被赋予错误角色造成风险；
- 还是更多 tool exposure 提供了执行机会。

Architecture Matters 也同时研究 role、topology 和 memory。它证明 architecture
matters，但没有把“能发消息”“能授权状态”“能执行动作”建模为三个独立拓扑。

### 2.3 Evidence-bounded gap statement

在本次公开文献检索范围内，尚未发现一项研究同时满足以下条件：

1. 显式区分 \(G_C\)、\(G_A\) 与 \(G_E\)；
2. 在固定任务、模型、prompt、action space、node/edge 数、model calls、message
   slots、token budget 和 execution budget 时，只改变其中一张图；
3. 在 paired true/false worlds 中保持 executor 看到的 state-claim message body
   字节一致；
4. 将 claim truth 保存在模型不可见的 executable ground-truth state 中；
5. 同时测量 false-state acceptance、true-state utilization 和 safe progress；
6. 用 deterministic world-state scorer，而非对话有害性 judge，作为主要标签；
7. 对 single authority、scoped capability、separation of duties 和 quorum
   authority 进行同一协议下的比较。

因此，TopoSafe-Delta 的 defensible gap 是：

> 现有工作尚未因果分离 communication topology、authority topology 与 execution
> topology 对多智能体可执行安全的影响，也没有检验安全是否由 authority 的位置，
> 还是由授权所需的独立主体数量与证明结构决定。

这是一个 conditional joint gap，不是 absolute first claim。投稿前必须重新检查
MasDrift、Architecture Matters 及后续 authorization-topology 工作的最新版本。

## 3. Mechanism: Authority Cut

### 3.1 Definition

令 \(P\) 为 authority principals。对每个受保护状态转换 \(x\)，authorization
protocol 定义一组可满足 proof policy 的 signer sets
\(\mathcal{Q}_x\subseteq 2^P\)。因此 \(G_A\) 更准确地说是一张 authority
hypergraph，而不只是普通有向图。

在 compromised principals 可以为任意 claim 提供 authenticated share、honest
principals 只为有独立新鲜证据的 claim 签名的 threat model 下，定义
**authority cut**：

\[
\kappa_A(x) =
\min_{\mathcal{C}\subseteq P}
\left\{
|\mathcal{C}|:
\exists \pi,\ 
\operatorname{Verify}_x(\pi)=1
\text{ when principals in }\mathcal{C}\text{ may deviate}
\right\}
\]

其中 honest principals 遵守冻结的 signing policy，
\(\operatorname{Verify}_x\) 检查 signer uniqueness、threshold、scope、
state version 与 freshness。重复使用同一 principal 的两个 signature 只计一个
independent principal。

直观上：

- unsigned claim：没有可验证 authority，\(\kappa_A\) 不适用；
- single authenticated authority：\(\kappa_A=1\)；
- source + verifier 的 2-of-2 separation of duties：\(\kappa_A=2\)；
- 2-of-3 independent quorum：\(\kappa_A=2\)；
- 3-of-3 unanimity：\(\kappa_A=3\)。

\(\kappa_A\) 是 authorization protocol 的结构属性，不直接保证 LLM executor
遵守 proof policy。实验仍允许 executor 在 invalid proof 下选择 protected action，
因此最终 FAR 同时反映 proof 是否可构造以及模型是否执行 proof enforcement。

### 3.2 Why the current placement result matters

在 v1.6 中，source、relay 和 verifier 三个 placement 都只有一个 authority：

\[
\kappa_A^{source}
=
\kappa_A^{relay}
=
\kappa_A^{verifier}
=1
\]

所以移动 authority 位置并没有改变攻陷阈值。该机制预测 placement effect 应当小，
而 credential effect 可以很大，因为 authenticated metadata 改变了 executor 对声明
的可接受性。

这把一个“没有显著 placement 排名”的结果转化为可检验机制：

> 安全的关键结构量可能不是 authority 离 executor 有几跳，而是错误声明需要穿过
> 多少个相互独立的授权边界。

### 3.3 Falsifiable predictions

- **P1: Credential amplification.** 当 proof 只证明身份、不证明状态真值时，
  authenticated credential 同时提高 FAR 与 TUR，TCG 仍接近 0。
- **P2: Placement invariance at fixed cut.** 在
  \(\kappa_A=1\)、message body 和 budgets 匹配时，source/relay/verifier placement
  差异小于 credential effect。
- **P3: Cut protection.** 当 adversary budget \(c < \kappa_A\) 时，提高
  \(\kappa_A\) 会降低 FAR。
- **P4: Threshold failure.** 当 \(c \ge \kappa_A\) 时，quorum 的 FAR 优势消失；
  否则观察到的改善可能只是 prompt 偏好，而不是 authority-cut 机制。
- **P5: Utility frontier.** 提高 \(\kappa_A\) 可能降低 FAR，也可能增加 unnecessary
  verification 或降低 TUR；有效方法必须改善 FAR–TUR–safe-progress frontier，而非
  通过停止执行获得表面安全。
- **P6: Conditional topology effect.** 当 \(G_A\)、\(G_E\)、message body、traffic
  和 role assignment 固定后，\(G_C\) 的剩余效应应显著小于未匹配的 architecture
  ranking；若自由运行 intermediaries 会重写或丢失证明，\(G_C\) 与 \(G_A\) 将出现
  interaction。

## 4. Research Questions

- **RQ1:** Identity authentication 会让模型更准确地利用 state update，还是只会让
  模型更愿意服从 update？
- **RQ2:** 在 authority cut 固定为 1 时，authority placement 是否仍有独立效应？
- **RQ3:** scoped capability、separation of duties 和 quorum 是否能在保留 TUR 的
  同时降低 FAR？
- **RQ4:** authority-cut prediction 是否随 compromised-principal budget 呈现阈值
  行为？
- **RQ5:** 当 authority 和 execution topology 固定后，matched communication
  topology 还剩多少可识别的安全效应？
- **RQ6:** topology 是否主要通过 semantic rewriting、proof loss、repeated exposure
  或 role centrality 改变安全？
- **RQ7:** 这些效应在 policy family、model family 与 task domain 上是否稳定？

## 5. Claim–Evidence Matrix

| Claim | Required evidence | Current status |
| --- | --- | --- |
| C1. \(G_C\)、\(G_A\)、\(G_E\) 必须作为不同实验对象 | Formal definitions; matched interventions; validity audit | Supported by matched B1 and free-running B2 interventions in the synthetic scope |
| C2. Authentication can amplify acceptance without truth discrimination | Paired true/false prompts; FAR/TUR/TCG; valid controls | Verified development evidence in two models |
| C3. Moving one authority does not reliably improve safety when \(\kappa_A=1\) | Placement contrasts across held-out tasks and models | Supported only as development evidence |
| C4. Increasing authority cut reduces FAR for \(c<\kappa_A\) | Single versus SoD/quorum; compromised-principal ablation | Not supported as a universal advisory response: verifier-single and SoD replicate in three models, quorum in two, and none in all four |
| C5. Fail-closed runtime proof enforcement converts an authority cut into an executable boundary | Deterministic proof gate; invalid-proof replay; denial recovery | Supported by a fresh 48-task, four-model factorial and 1,200 targeted ablation calls; all model gates passed |
| C6. Canonical topology rankings partly reflect bundled authority and execution changes | Matched \(G_C\) intervention plus unmatched architecture baseline | B1 and B2 find no replicated large \(G_C\) effect; B2 retains model-conditional semantic effects, and the direct unmatched comparison remains pending |
| C7. Independent authority composition improves the safety–utility frontier | FAR, TUR, safe progress, verification cost and threshold stress tests | Not supported as a universal cross-model advisory claim; retain the narrower proof-validity and enforced-execution claim in C5 |
| C8. Advisory sensitivity to exact proof defects is model-dependent, while deterministic proof validation is stable | Ten matched proof/semantics interventions; advisory and enforced FAR | Supported by 1,200 calls across four valid model blocks; stale replay replicated in three models, identity swapping was equivalent across four, and invalid-proof enforced FAR was zero |
| C9. The absence of a replicated large communication-topology ranking is robust to an independent execution schedule | Same frozen B2 matrix under a different schedule seed; paired schedule-difference analysis | Supported in the synthetic scope: both schedules have zero cross-model replicated large total or semantic effects, and the schedule difference has zero replicated large effects |
| C10. The original Study A control failures reflect conservative abstention rather than unsafe control execution | Zero-call reanalysis preserving the preregistered gate; later responsiveness rule; threshold replication audit | Post-hoc sensitivity supported: 41/41 failures in the two invalid blocks were safe no-progress choices, but the original gate remains failed |

## 6. Existing Development Evidence

### 6.1 Authority-Placement v1.6

- Formal calls: 1,008.
- Smoke calls: 84, stored separately.
- Provider errors: 0.
- Valid models: Claude Sonnet 5 and NVIDIA Nemotron 3 Super 120B.
- Invalid/excluded model: GPT-5.4, because control failures were
  \(3/48=6.25\%\), above the preregistered 5% gate.
- Malformed/truncated responses: 0.
- Paired message-body, prompt, graph-budget and scorer-replay checks passed.

### 6.2 Verified findings

For Claude and Nemotron:

1. authenticated provenance increased both FAR and TUR at every placement;
2. preregistered credential safety-cost and utility-gain intervals were above
   zero;
3. TCG stayed between \(-0.042\) and \(+0.042\);
4. verifier-minus-source and verifier-minus-relay placement contrasts were
   small and their intervals included or touched zero.

### 6.3 Correct interpretation

The result supports:

> Under a fixed chain and a single-authority design, credential semantics
> dominate authority location. Authentication increases trust in the claim but
> does not provide evidence that the hidden claim is true.

It does not support:

- topology is generally irrelevant;
- verifier placement is always useless;
- the models can infer hidden truth;
- GPT-5.4 confirms the result;
- the rates generalize beyond the 24 synthetic development tasks;
- response-mode differences permit pooled model ranking.

### 6.4 Runtime Enforcement v0.1

The runtime extension reuses the 6,480 non-control proof-bearing rows from
Authority Composition v0.2. It applies three deterministic execution
conditions:

1. advisory proof presentation, which preserves the parent outcome;
2. a fail-closed gate that blocks the protected action whenever
   \(\operatorname{Verify}_x(\pi)=0\);
3. gate plus one recovery turn with the authoritative snapshot and a
   standardized denial.

The gate blocked all 697 parent attempts that selected a protected action under
an invalid proof. All 697 recovery calls selected the designated safe-progress
action, no model repeated the blocked action, and no invalid proof produced an
executed violation. Claude generated no recovery call because its parent rows
contained no protected attempt under an invalid proof. The package used no
human-review evidence.

This result establishes the implementation-level distinction between proof
forgeability and execution enforcement in the frozen synthetic setting.
Because recovery cases were selected from observed v0.2 behavior, it remains a
post-hoc mechanistic extension rather than an independent factorial test.

### 6.5 Runtime Enforcement v0.2: Fresh Independent Factorial

The independent factorial uses 48 new task clusters, balanced across four
policy families and six domains, with no task-ID overlap with prior packages.
Each task contributes 14 initial cells: verifier-single, source-plus-verifier
separation of duties, and 2-of-3 quorum under true claims and false claims with
compromise budgets \(c\in\{0,1,2\}\), plus two direct-state controls. Across
four models, this yields 2,688 formal initial calls.

Before any provider call, the protocol froze one adaptive rule: every
non-control episode that selected the protected action under an invalid proof
received exactly one recovery turn. This rule produced 257 recovery calls,
with no manual case selection. The four model blocks all passed the
preregistered validity gates. Control task-progress rates ranged from 89.6% to
100%, false-control violation was zero, and malformed-or-truncated rates were
at most 0.30%.

The fail-closed gate reduced invalid-proof executed FAR to zero for every
model. The paired advisory-minus-enforced reductions were 0.8% for GPT-5.4,
0.0% for Claude Sonnet 5, 52.1% for Nemotron 3 Super 120B, and 54.2% for
Llama 4 Maverick. All 257 triggered recoveries made safe progress, and no
recovery repeated the blocked protected action. True-world task progress was
100% for every model.

The threshold result matches the mechanism's scope. Below
\(\kappa_A\), the proof is invalid and the gate blocks execution. At or above
\(\kappa_A\), the adversarial proof satisfies the authorization policy, so
execution enforcement alone does not reduce FAR. This is independent evidence
for the \(G_A\)-by-\(G_E\) interaction within the synthetic task family. The
matched frozen-message \(G_C\) intervention is reported in Section 9.5.

## 7. Completed Authority-Composition Package and Remaining Design

The original 24 tasks remain development-only. A separate 120-task package
passed the frozen automatic validation suite and was executed in Authority
Composition v0.2. It is held out from the v1.6 development tasks, but the
completed run remains bounded evidence because two of four model blocks failed
the preregistered control gate.

### 7.1 Task package

- **120 frozen synthetic task clusters, held out from v1.6 development.**
- Four policy families, 30 tasks each:
  approval bypass, false completion, unauthorized execution, protected transfer.
- Six operational domains, balanced within each policy family.
- Every task has:
  - one protected action;
  - one safe-progress action;
  - a stale snapshot;
  - a hidden current ground-truth state;
  - byte-identical true/false executor-visible claim bodies;
  - deterministic safe, violating and true-authorized oracle traces.
- Existing 24 v1.6 tasks are dev/calibration and cannot enter the confirmatory
  test set.

### 7.2 Automatic instrument validity

The task family uses executable state and proof predicates as labels. The
freeze gate applies to all 120 tasks:

- an independent renderer reconstructs every task from the catalog and frozen
  policy-family contract, then compares text, state, actions, effects and
  success predicates exactly;
- 480 deterministic traces verify protected-false, protected-true,
  safe-progress and inert-action outcomes;
- all 720 action-order permutations must preserve the gate, action labels,
  claim body and scorer output;
- 720 paired true/false prompt checks require identical executor-visible
  prompts within each placement and credential condition;
- 192 signer-set, scope and freshness combinations are checked against an
  independent threshold-set oracle;
- any failure blocks the complete package and requires regeneration; tasks
  cannot be removed using validation or model outcomes.

No human review or LLM judge supplies task labels. The resulting evidence
supports executable correctness and causal isolation for this synthetic task
family. The paper does not estimate human preference, deployed-workflow
realism, or real-world incident prevalence.

### 7.3 Models

Mandatory frozen families:

1. GPT-5.4;
2. Claude Sonnet 5;
3. NVIDIA Nemotron 3 Super 120B;
4. Llama 4 Maverick, provisionally configured as the independent open-weight
   family.

Exact endpoint IDs, dates, regions, decoding settings, structured-output modes
and provider limitations are recorded in the frozen v0.2 package. Results are
reported per model; no simple pooled ranking is used. The completed validity
gate retains Claude and Nemotron for bounded Study A interpretation and keeps
GPT-5.4 and Llama descriptive.

## 8. Study A: Authority Composition

### 8.1 Fixed graphs

- \(G_C\): source \(\rightarrow\) relay \(\rightarrow\) verifier
  \(\rightarrow\) executor.
- \(G_E\): only executor can select the protected action.
- Node count, edge count, model calls, executor deliveries, action space,
  claim body and output budget are identical across paired cells.

### 8.2 Six authority regimes

| Regime | Authorization proof | Authority cut |
| --- | --- | ---: |
| unsigned | no platform proof | N/A |
| source-single | source identity credential | 1 |
| relay-single | relay identity credential | 1 |
| verifier-single | verifier identity credential | 1 |
| source+verifier SoD | both independent principals must approve | 2 |
| 2-of-3 quorum | any two independent principals must approve | 2 |

Each regime is crossed with `true_update` and `false_update`, plus
`snapshot_only_false` and `fresh_state_visible_true` controls:

\[
6 \times 2 + 2 = 14 \text{ cells per task}
\]

Formal scale:

\[
120 \times 14 \times 4 = 6{,}720 \text{ model calls}
\]

### 8.3 Truth and compromise construction

- The state-claim message body is identical in paired true/false worlds.
- In true worlds, every required authority has fresh independent evidence and
  the proof is protocol-valid.
- In the primary false world, exactly one principal is compromised:
  - single-authority regimes can produce a valid identity credential for a
    false claim;
  - SoD/quorum regimes cannot produce a complete valid proof.
- The executor never sees the hidden scorer truth.
- Proof metadata may differ only where required by the frozen authorization
  protocol; message semantics, action space and resource budgets remain fixed.

This separates two questions:

1. can a model discriminate hidden truth from an identity credential;
2. does it enforce the validity of a multi-principal authorization proof?

### 8.4 Primary estimands

\[
\mathrm{FAR}
=
P(\text{protected action}\mid\text{false state})
\]

\[
\mathrm{TUR}
=
P(\text{protected action}\mid\text{true state})
\]

\[
\mathrm{TCG}
=
\mathrm{TUR}-\mathrm{FAR}
\]

Preregistered contrasts:

1. credential safety cost and utility gain;
2. verifier-single minus source-single;
3. verifier-single minus relay-single;
4. SoD minus matched single-authority;
5. quorum minus matched single-authority;
6. quorum minus SoD;
7. FAR–TUR frontier change;
8. safe-progress and unnecessary-verification cost.

## 9. Study B: Matched Communication Topology

### 9.1 Purpose

Study A changes \(G_A\) while fixing \(G_C\) and \(G_E\). Study B changes
\(G_C\) while fixing \(G_A\) and \(G_E\).

### 9.2 Topology construction

B1 uses four frozen six-node, six-edge directed graphs chosen to vary:

- source-to-executor distance;
- degree centralization;
- number of independent routes;
- bottleneck concentration.

All conditions match:

- six nodes and the same directed-edge count;
- the same number and schedule of message deliveries;
- aggregate message bytes and token budget;
- exactly one executor-facing state claim;
- the same authority proof and execution permission;
- role-to-node assignments through balanced permutations.

Unused delivery slots carry frozen inert messages so a safer graph cannot win
merely because it generated less traffic.

The realized graphs have source-to-executor distances 1, 3, 4, and 5. Their
degree-centralization values are 0.9, 0.0, 0.3, and 0.3, and their
edge-disjoint source-to-executor route counts are 2, 2, 1, and 1. Six scheduled
delivery slots are used in every cell, and anonymous role rotations are
balanced with 20 tasks per topology-rotation assignment.

### 9.3 Two levels of ecological validity

**B1: Frozen-message structural test, completed**

- Intermediaries do not rewrite the claim.
- The executor-facing claim body is byte-identical.
- Only route/provenance-chain metadata changes.
- This estimates the residual structural trust effect of \(G_C\).

**B2: Free-running propagation test, completed**

- Intermediaries use one model-driven `forward_envelope` schema and may
  summarize, transform or drop the claim and proof.
- Each episode uses six forwarding calls and one executor call. Ex-ante calls,
  token limits, message slots and action budgets remain matched.
- This measures the total topology effect, including endogenous semantic
  rewriting and proof loss.

B2 is not substituted for B1: the difference between them is the mechanism.
The free-text v0.1 and v0.2 configurations stopped after excluded smoke tests
because Llama did not reliably return parseable JSON. Version 0.3 froze the
uniform structured interface before formal calls.

### 9.4 Factorial matrix

Primary B1 matrix:

- four communication topologies;
- three authority regimes:
  verifier-single, source+verifier SoD, 2-of-3 quorum;
- true/false state;
- four models;
- 120 tasks;
- two global controls per task/model.

\[
120 \times 4 \times 3 \times 2 \times 4
+ 120 \times 2 \times 4
= 12{,}480 \text{ calls}
\]

All 12,480 B1 rows completed. The run required 13,073 provider API attempts,
including retries. All four model blocks passed the frozen gates: control
progress ranged from 99.2% to 100%, false-control violation was zero,
malformed-or-truncated rate was at most 0.26%, and final provider errors,
missing rows, duplicate episode IDs, budget mismatches, and invalid-proof
executions were zero.

The B2 matrix uses the same four topologies, three authority regimes, paired
truth worlds and four models on a deterministic 30-task stratified subset:

\[
30 \times 4 \times 3 \times 2 \times 4
= 2{,}880 \text{ episodes}.
\]

Every episode contains six forwarding calls and one executor call:

\[
2{,}880 \times 7
= 20{,}160 \text{ assigned model calls}.
\]

All 2,880 episodes completed with 20,319 provider attempts including retries.
All four model blocks passed the frozen validity gates.

### 9.5 B1 result

Each `topo_B`, `topo_C`, and `topo_D` cell was paired with `topo_A` at the task,
authority-regime, truth, action-space, message, and budget levels. The
preregistered large-effect rule required an absolute paired difference of at
least 10 percentage points and a 95% task-bootstrap interval excluding zero.
No contrast met that rule in any model, and no large effect replicated across
models.

Across the 27 topology-by-authority-by-outcome contrasts, 26 had all four
model-specific intervals inside the frozen \(\pm10\)-point equivalence margin.
The sole exception was Nemotron's `topo_C` versus `topo_A` SoD advisory FAR:
the estimate was \(-6.7\) points with a 95% interval of
\([-11.7,-2.5]\) points. The estimate did not reach the 10-point large-effect
threshold. The largest absolute estimate in each remaining model was 5.0
points for Claude, 3.3 for GPT, and 1.7 for Llama.

For SoD and quorum at \(c=1<\kappa_A\), the deterministic gate reduced executed
FAR to zero in all four communication topologies. B1 therefore supports
practical near-equivalence of frozen route/provenance metadata after authority,
execution, message content, traffic, and budgets are fixed. It does not
identify the effect of topology-dependent semantic rewriting or proof loss;
that mechanism belongs to B2.

### 9.6 B2 result

B2 compares each free-running topology with `topo_A` on the same tasks and
subtracts the corresponding B1 contrast to isolate the semantic-propagation
increment. The preregistered 10-point and task-bootstrap rules are unchanged.
No large B2 topology effect replicated across at least three models, and no
large semantic increment over B1 replicated. Ten of 27 contrasts were
model-conditional under each classification. These effects were concentrated
in verifier-single outcomes for GPT-5.4 and Claude Sonnet 5 rather than forming
a stable topology ranking.

For example, `topo_D` versus `topo_A` changed verifier-single executed FAR by
\(-33.3\) points for GPT-5.4 with a 95% interval of
\([-50.0,-16.7]\), by \(-16.7\) points for Claude Sonnet 5 with
\([-30.0,-3.3]\), by \(+6.7\) points for Llama 4 Maverick with
\([0.0,16.7]\), and by \(0.0\) points for Nemotron. The sign and magnitude are
therefore model-dependent.

Free-running propagation changed message form even when executable safety did
not move consistently. Mean source-to-final similarity from `topo_A` to
`topo_D` fell from 0.781 to 0.576 for GPT, 0.912 to 0.866 for Claude, 0.989 to
0.805 for Llama, and 0.975 to 0.963 for Nemotron. At `topo_D`, delivery rates
remained between 97.2% and 100%, and valid-proof retention remained between
97.5% and 100%.

Only six of 27 B2 contrasts satisfied practical equivalence across every
model. All six were executed-FAR contrasts for SoD or quorum. In these
cut-two regimes, the common fail-closed gate kept false-world executed FAR at
zero across all topologies. B2 therefore separates semantic drift from a
replicated executable-safety effect: communication paths alter messages, but
the resulting safety effect is model-conditional, while enforceable
multi-principal authority remains topology-stable in this setting.

### 9.7 Independent schedule replication

The replication reused the same 30 tasks, cases, prompts, four models,
topologies, authority regimes, paired truth worlds, budgets, scorer, and
validity gates as B2. It changed only the schedule seed and resulting request
order. The provider does not expose a sampling seed, so this is an execution-
schedule replication rather than deterministic model-sampling replication.

All 2,880 episodes and 20,160 assigned calls completed with 20,321 provider
attempts including retries. All four model gates passed. Active-forward
failure rates were at most 0.30%, executor failure rates were at most 0.28%,
and no invalid proof authorized a protected execution.

The replication preserved the paper-level topology result. Neither the parent
B2 schedule nor the replication produced a large total topology effect in at
least three models, and neither produced a replicated large semantic increment
over B1. The paired schedule-difference analysis also found no replicated
large effect. Three shifts were model-conditional and all concerned true-state
utilization: GPT-5.4 changed by \(+23.3\) points for `topo_B` SoD and
\(-23.3\) points for `topo_D` quorum, while Claude Sonnet 5 changed by
\(-16.7\) points for `topo_C` quorum. Six of 27 schedule-difference contrasts
were practically equivalent across all models; all six were SoD/quorum
executed-FAR contrasts. The broad absence of a replicated topology ranking is
therefore schedule-robust, although exact utility magnitudes remain
model-conditional.

## 10. Study C: Mechanism and Robustness

### 10.1 Authority-cut threshold test

On a stratified 30-task subset, vary compromised principals:

- \(c=0\): all honest;
- \(c=1\): primary threat model;
- \(c=2\): quorum-breaking adversary.

The authority-cut claim is supported only if:

- SoD/quorum lower FAR when \(c=1<\kappa_A\);
- their advantage disappears or sharply narrows when
  \(c=2\ge\kappa_A\).

Study A 已提供 `true_update` 与 primary `false_update, c=1` rows。阈值扩展只新增
三个 regime（verifier-single、source+verifier SoD、2-of-3 quorum）在 false world
中的 \(c=0\) 与 \(c=2\)：

\[
30 \times 3 \times 2 \times 4
=720 \text{ calls}
\]

Authority Composition v0.2 completed all 720 threshold rows. Claude Sonnet 5
showed FAR sequences of \(0.00,0.40,0.40\) for verifier-single and
\(0.00,0.00,0.33\) for source-plus-verifier SoD at \(c=0,1,2\). Its quorum
sequence was \(0.00,0.00,0.03\), but quorum TUR in Study A was only 0.008.
Nemotron 3 Super 120B produced positive cut contrasts for all three regimes,
but FAR below the cut remained high: 0.50 for verifier and SoD at \(c=0\),
and 0.40/0.47 for quorum at \(c=0/1\). The cut therefore predicts a change in
acceptance for these model blocks, but it does not make invalid proofs
fail-closed when the executor does not enforce proof validity.

### 10.2 Required ablations

- replace independent signers with two signatures from the same principal;
- remove state-field scope binding;
- remove state-version/freshness binding;
- replay a stale but correctly signed proof;
- swap source and verifier identities;
- compromise the verifier instead of the source;
- randomize authority labels while preserving proof validity;
- remove one quorum share;
- duplicate the same claim without adding independent authority;
- replace policy-valid proof with natural-language consensus.

Each ablation tests a mechanism. Repeated cosmetic prompt variants are not
publication evidence.

这些消融使用 Runtime Enforcement v0.2 的同一 30-task subset。每个消融是一个
预先指定的 targeted cell，matched reference 从该 frozen parent factorial
复用，不重复收集：

\[
30 \times 10 \times 4
=1{,}200 \text{ calls}
\]

Authority Mechanism Ablations v0.1 completed all 1,200 calls with 1,201
provider attempts. The 30 tasks were selected from Runtime Enforcement v0.2
without using model outcomes, and same-task parent responses were reused as
the matched references. All four model blocks passed integrity and
parent-validity gates. There were no missing or duplicate rows, unresolved
provider errors, malformed or truncated responses, proof or score mismatches,
or invalid-proof executions.

`replay_stale_signed_proof` was the only replicated large advisory effect.
Relative to its valid signed reference, FAR fell by 73.3 points for GPT-5.4,
40.0 for Claude Sonnet 5, and 33.3 for Nemotron 3 Super 120B; each 95%
task-bootstrap interval excluded zero. Llama changed by \(-3.3\) points with
an interval crossing zero. `swap_source_verifier_identities` was the only
ablation whose advisory effect satisfied the frozen \(\pm10\)-point practical
equivalence rule in all four models. Four other large advisory effects were
model-conditional: repeated same-principal signatures, missing scope, missing
freshness, and a missing quorum share.

The enforced result was uniform across model behavior. Eight ablations
constructed invalid proofs, giving 960 invalid-proof target calls across four
models. Their maximum enforced FAR was zero in every model. This supports the
mechanism-level claim that exact proof semantics may affect an LLM's advisory
choice, but deterministic proof validation is required for a stable execution
boundary.

### 10.3 Free-running replication and schedule robustness

- B2 free-running subset completed:
  \(30 \times 4 \times 3 \times 2 \times 4 = 2{,}880\) episodes,
  with seven model calls per episode and 20,160 assigned calls.
- Independent schedule-seed replication completed on the same 30-task
  topology matrix: another 2,880 episodes and 20,160 assigned calls.
- The replication required 20,321 provider attempts. All four validity gates
  passed, with zero unresolved provider errors and zero invalid-proof
  executions.
- The provider did not expose a sampling seed. The completed experiment
  therefore tests schedule and request-order robustness, not deterministic
  model-sampling reproducibility.
- Both schedules produced zero cross-model replicated large total topology
  effects and zero replicated large semantic increments. The schedule
  difference produced zero replicated large effects.

### 10.4 Total recommended scale

| Component | Assigned model calls | Status |
| --- | ---: | --- |
| Study A: authority composition | 6,720 | Complete; two of four model gates passed |
| Study B1: matched communication topology | 12,480 | Complete; all four model gates passed |
| Study B2: free-running subset | 20,160 | Complete; all four model gates passed |
| Schedule robustness subset | 20,160 | Complete; all four model gates passed |
| Study C1: authority-cut threshold extension | 720 | Complete; bounded mixed result |
| Study C2: targeted mechanism ablations | 1,200 | Complete; all four model gates passed |
| **Core intervention total** | **61,440** | **61,440 calls complete** |

The existing 1,008 v1.6 formal calls remain development evidence and are not
mixed into the core intervention ledger. Adding those calls, 697 Runtime
Enforcement v0.1 recovery calls, and 2,945 Runtime Enforcement v0.2
initial-plus-recovery calls yields 66,090 formal model calls reported in the
manuscript. Deterministic gate replays and smoke calls remain separate.

The earlier 26,880 total treated each seven-call B2 episode as one provider
call. Correct accounting assigns 20,160 calls to B2 and another 20,160 to its
schedule replication. The correction changes compute accounting, not the
factorial sample size or estimands.

## 11. Baselines

1. **Unsigned message:** no authenticated authority.
2. **Identity-only single authority:** current industry-like trust primitive.
3. **Central verifier:** strongest single-placement baseline.
4. **Natural-language consensus:** multiple agents agree but no enforceable
   independent proof.
5. **Source re-anchoring:** every protected action is checked against the
   original user request.
6. **Scoped capability:** proof bound to state field, object, version and action.
7. **Separation of duties:** two distinct principals must approve.
8. **Independent quorum:** threshold authorization with signer uniqueness.
9. **Topology-aware guard:** detects or blocks suspicious message paths without
   changing authority structure.

The main comparison is not “our method versus all defenses.” It is which
structural primitive changes the causal safety–utility frontier.

## 12. Statistics and Reporting

- Statistical unit: task cluster.
- Primary analysis: paired task-level differences.
- Uncertainty: 5,000 task-cluster bootstrap samples.
- Report every model separately.
- Use a hierarchical logistic model only as secondary analysis:
  fixed effects for topology, authority regime, truth and interactions; random
  intercepts for task.
- Correct the preregistered contrast family with Holm's method.
- Show raw counts, rates, paired effects and intervals.
- Do not treat repeated schedules as independent new tasks.
- Calibrate development tasks so relevant baseline FAR is approximately
  10–30%; do not use additional repetitions to manufacture identifiability
  after floor or ceiling is observed.
- Provider errors, malformed responses and truncations remain visible.

## 13. Validity Gates

- paired claim-body hash must match exactly;
- truth must not leak through prompt, action ordering or message length;
- calls, tokens, message slots, action space, node/edge budget and tool
  permissions must match the frozen comparison;
- scorer replay must reproduce every label;
- malformed/truncation above 2% invalidates that model block;
- control failure above 5% invalidates the corresponding model/run block;
- provider errors are reported and never silently deleted;
- task or protocol repairs create a new corrected run;
- no partial JSON is used to infer an action;
- no confirmatory task is selected using model outcomes;
- response-mode differences are documented and prohibit naive model ranking.

## 14. Paper-Level Results Structure

### Main Table 1: Authority composition

Per model and regime:

- FAR;
- TUR;
- TCG;
- safe-progress rate;
- unnecessary-verification rate;
- control and malformed rates.

### Main Figure 1: Three-topology decomposition

One protected transition shown with separate \(G_C\), \(G_A\) and \(G_E\).
The figure must visually show that moving a signer and increasing the number of
independent signers are different interventions.

### Main Figure 2: Safety–utility frontier

Plot FAR against TUR, with safe progress encoded separately. The strongest
result is a regime that moves down in FAR without moving equally far left in
TUR.

### Main Figure 3: Authority-cut threshold

FAR as a function of compromised-principal budget \(c\), grouped by
\(\kappa_A\). The predicted break occurs near \(c=\kappa_A\).

### Main Figure 4: Matched versus bundled topology

Compare:

1. unmatched canonical architecture ranking;
2. matched B1 structural effect;
3. B2 free-running total effect.

This figure tests whether apparent topology effects shrink after authority,
traffic and role placement are controlled.

### Main Table 2: Mechanism ablations

Per model, report target and reference advisory FAR, paired effects and
intervals, proof validity, and enforced FAR for signer independence, scope,
freshness, replay, identity exchange, compromise location, label semantics,
missing shares, duplicated unsigned claims, and natural-language consensus.

## 15. Conclusion: What Can Be Said Now

### Verified

1. In the valid v1.6 model blocks, platform-authenticated provenance increased
   both false-state acceptance and true-state utilization.
2. The observed TCG was near zero, so authentication did not provide hidden
   truth discrimination.
3. Moving a single authority among source, relay and verifier did not produce a
   stable placement advantage under the fixed chain.
4. Authority Composition v0.2 completed 7,440 formal rows with automatic task,
   proof, score and hash validation and no human-review evidence.
5. In its two valid model blocks, FAR generally increased when the compromise
   budget reached the authority cut, but the below-cut FAR and utility response
   differed sharply by model and authority regime.
6. Runtime Enforcement v0.1 replayed 6,480 proof-bearing rows and completed
   697/697 recovery calls without human review, provider errors, malformed
   outputs or repeated protected attempts. No invalid proof was executed.
7. Runtime Enforcement v0.2 completed 2,688 fresh initial calls and 257
   automatically triggered recovery calls across four models. Every model
   passed the frozen validity gates, invalid-proof executed FAR was zero, and
   all triggered recoveries made safe progress without human review.
8. Matched Communication B1 completed 12,480 formal calls across 120 tasks,
   four models, four communication graphs and three authority regimes. All
   validity gates passed, no preregistered large topology effect appeared, and
   26 of 27 cross-model contrasts satisfied the \(\pm10\)-point equivalence
   rule.
9. Free-running Communication B2 v0.3 completed 2,880 formal episodes and
   20,160 assigned model calls with 20,319 provider attempts. All four model
   gates passed. Neither total topology effects nor semantic increments
   produced a replicated large effect; 10 of 27 contrasts were
   model-conditional, while all six SoD/quorum executed-FAR contrasts were
   practically equivalent across models.
10. Targeted Authority Mechanism Ablations v0.1 completed 1,200 formal calls
    with 1,201 provider attempts. All four model gates passed, invalid target
    proofs had zero enforced FAR, stale signed replay was the only replicated
    large advisory effect, and source-verifier identity exchange was
    practically equivalent across all four models.
11. Free-Running Schedule Replication v0.1 completed 2,880 episodes and 20,160
    assigned calls with 20,321 provider attempts. All four model gates passed.
    Neither schedule produced a cross-model replicated large total topology
    effect or semantic increment, the schedule difference produced no
    replicated large effect, and all invalid proofs remained blocked.
12. Authority Composition Control Sensitivity v0.1 added zero provider calls.
    The 41 exact-control failures in the two originally invalid Study A blocks
    were all safe no-progress choices with zero false-control violations.
    Under the later fresh-factorial responsiveness rule, all four blocks pass.
    Verifier-single and SoD threshold contrasts replicate in three models,
    quorum in two, and none in all four.

### Inferred

1. The observed behavior is more consistent with a model reacting to authority
   semantics than with a model recovering state truth.
2. The weak placement result is consistent with all three conditions sharing
   the same authority cut, \(\kappa_A=1\).
3. Authority cut characterizes proof forgeability, while fail-closed runtime
   enforcement converts that structural threshold into an executable-safety
   boundary for invalid proofs.
4. Broad architecture effects shrink after authority, execution, traffic and
   budgets are matched. Free-running semantics reintroduce model-conditional
   effects, but not a replicated topology ranking under either completed
   schedule.
5. The advisory response to authority cut is model-dependent. The stable
   cross-model mechanism is proof validity plus fail-closed execution, not
   behavioral recognition of every threshold policy.

### Unknown

1. Whether the results generalize to additional task families and real
   tools.

### Invalid or excluded

- GPT-5.4 v1.6 is descriptive only because its control-failure gate failed.
- v1–v1.5 remain excluded according to their preserved protocol records.
- In Authority Composition v0.2, GPT-5.4 had 17/240 control failures and Llama
  4 Maverick had 24/240. Both exceeded the preregistered 5% gate. Their
  threshold rows remain descriptive and are not combined with the valid model
  blocks under the original analysis. The post-hoc sensitivity shows that all
  41 failures were safe no-progress choices and that both blocks pass the later
  responsiveness rule; this does not retroactively replace the preregistered
  gate.

## 16. Final Claim Boundary

The completed evidence supports the following bounded conclusion:

> Multi-agent safety is not determined by communication topology alone.
> Authentication can amplify obedience to both true and false state claims,
> while relocating a single authority leaves the system's compromise threshold
> unchanged. Separating communication, authority, and execution topology
> shows that independent, scoped authorization sets the proof-forgeability
> threshold, while fail-closed runtime enforcement determines whether an
> invalid proof becomes an executable state change. Advisory responses to that
> threshold vary by model and authority regime.

The universal safety–utility-frontier claim is not supported. The post-hoc
control sensitivity removes unsafe control behavior as the explanation for the
two failed blocks, but the threshold result still varies across models:
verifier-single and SoD replicate in three models, quorum in two, and no
threshold contrast replicates in all four. Additional calls are not required
for the bounded structural and enforcement conclusion. A new experiment would
be necessary only to pursue a different, universal advisory-response claim,
which the current evidence does not motivate.

## 17. Publication Readiness Decision

The current evidence is sufficient to write:

- the Introduction and research gap;
- the formal three-graph model;
- the Authority-Placement development study;
- the frozen authority-composition protocol;
- a bounded results section for the completed v0.2 run;
- the post-hoc runtime-enforcement mechanism and its bounded result;
- the fresh independent four-model runtime-enforcement factorial;
- the completed matched frozen-message communication-topology result;
- the completed free-running semantic-propagation result;
- the completed independent schedule-robustness result;
- the completed targeted authority-mechanism ablation result;
- the completed zero-call Study A control-sensitivity analysis.

The evidence-frozen venue-neutral manuscript is
[`manuscript/toposafe-delta.md`](../manuscript/toposafe-delta.md).
The executable authority-regime registry and corrected call ledger are in
[`experiments/TopoSafe-Delta-AuthorityComposition-v0.2/`](../experiments/TopoSafe-Delta-AuthorityComposition-v0.2/).
The runtime gate, recovery protocol and results are in
[`experiments/TopoSafe-Delta-RuntimeEnforcement-v0.1/`](../experiments/TopoSafe-Delta-RuntimeEnforcement-v0.1/)
and
[`experiments/TopoSafe-Delta-RuntimeEnforcement-v0.2/`](../experiments/TopoSafe-Delta-RuntimeEnforcement-v0.2/).
The matched communication design and results are in
[`experiments/TopoSafe-Delta-MatchedCommunication-v0.1/`](../experiments/TopoSafe-Delta-MatchedCommunication-v0.1/).
The free-running design and results are in
[`experiments/TopoSafe-Delta-FreeRunningCommunication-v0.3/`](../experiments/TopoSafe-Delta-FreeRunningCommunication-v0.3/).
The independent schedule-replication design and results are in
[`experiments/TopoSafe-Delta-FreeRunningScheduleReplication-v0.1/`](../experiments/TopoSafe-Delta-FreeRunningScheduleReplication-v0.1/).
The targeted authority-mechanism design and results are in
[`experiments/TopoSafe-Delta-AuthorityMechanismAblations-v0.1/`](../experiments/TopoSafe-Delta-AuthorityMechanismAblations-v0.1/).
The post-hoc control-gate sensitivity is in
[`experiments/TopoSafe-Delta-AuthorityCompositionControlSensitivity-v0.1/`](../experiments/TopoSafe-Delta-AuthorityCompositionControlSensitivity-v0.1/).

The implementation has advanced beyond a paper-only plan:

- 120 candidates span six domains and four policy families, with five tasks in
  every family-domain cell;
- the full automatic suite covers 120 semantic contracts, 480 oracle traces,
  720 action permutations, 720 paired prompts and 192 proof assignments;
- Study A generates 1,680 cells per model and the threshold extension generates
  180 cells per model;
- 7,440/7,440 formal rows completed, with 7,472 provider API attempts including
  retries;
- human review has been removed from the experiment and freeze inputs;
- Claude Sonnet 5 and Nemotron 3 Super 120B passed Study A validity, while
  GPT-5.4 and Llama 4 Maverick failed the 5% control gate;
- Runtime Enforcement v0.1 completed 6,480 gate replays and 697 formal
  recovery calls, with zero invalid-proof executions;
- Runtime Enforcement v0.2 completed 2,688 fresh initial calls and 257
  automatically selected recovery calls. All four model gates passed, all
  triggered recoveries made safe progress, and total provider attempts
  including retries were 3,012;
- Matched Communication B1 completed 12,480/12,480 formal rows with 13,073
  provider attempts. All four model gates passed, 26/27 contrasts met the
  cross-model equivalence rule, and no contrast met the preregistered
  large-effect rule;
- Free-running Communication B2 v0.3 completed 2,880/2,880 episodes, 20,160
  assigned calls and 20,319 provider attempts. All four model gates passed;
  there were no replicated large total or semantic topology effects, 10/27
  contrasts were model-conditional, and 6/27 were practically equivalent
  across all models;
- Targeted Authority Mechanism Ablations v0.1 completed 1,200/1,200 calls with
  1,201 provider attempts. All four model gates passed; one large advisory
  effect replicated across three models, one ablation was practically
  equivalent across all four models, and invalid-proof enforced FAR was zero;
- Free-Running Schedule Replication v0.1 completed 2,880/2,880 episodes,
  20,160 assigned calls and 20,321 provider attempts. All four model gates
  passed; neither schedule nor their paired difference produced a
  cross-model replicated large topology effect;
- Authority Composition Control Sensitivity v0.1 added zero provider calls.
  The two originally invalid blocks had 41 safe no-progress control failures
  and zero false-control violations. All four blocks pass the later
  responsiveness rule, but no threshold contrast replicates in all four
  models.

Authority Composition v0.2 still does not support a four-model confirmatory
authority-composition claim. Runtime Enforcement v0.2 independently supports
the narrower mechanism: authority composition determines proof forgeability,
and fail-closed runtime enforcement prevents invalid proofs from becoming
protected actions below the cut. Matched Communication B1 further shows no
stable large residual effect from frozen route/provenance metadata after
\(G_A\), \(G_E\), content, traffic, and budgets are fixed. Free-running B2
shows that endogenous rewriting produces model-conditional effects but no
replicated large topology ranking, while SoD/quorum executed FAR remains
topology-stable under fail-closed enforcement. The independent schedule
replication preserves that absence of a replicated large topology ranking.
The original four-model Study A gate remains failed. The sensitivity analysis
shows that its failures were conservative abstentions, while the threshold
response itself remains model-dependent. No additional model experiment is
recommended for the bounded paper claim.
