from __future__ import annotations

import hashlib
import html
import json
import random
import zipfile
from pathlib import Path
from typing import Any

from swarmsafe_delta.pilot import load_tasks


PACKET_VERSION = "toposafe-authority-human-audit-v0.1"
REVIEW_FIELDS = (
    "policy_unambiguous",
    "scenario_and_actions_plausible",
    "no_unencoded_second_violation",
)


def _stable_seed(slot: str, value: str) -> int:
    digest = hashlib.sha256(f"{slot}::{value}".encode("utf-8")).hexdigest()
    return int(digest[:16], 16)


def _ordered_tasks(
    *,
    tasks: list[dict[str, Any]],
    audit_manifest: dict[str, Any],
    reviewer_slot: str,
) -> list[dict[str, Any]]:
    selected_ids = list(audit_manifest["selected_task_ids"])
    task_map = {task["id"]: task for task in tasks}
    missing = sorted(set(selected_ids) - set(task_map))
    if missing:
        raise ValueError(f"Audit manifest references missing tasks: {missing}")
    selected = [task_map[task_id] for task_id in selected_ids]
    random.Random(_stable_seed(reviewer_slot, PACKET_VERSION)).shuffle(selected)
    return selected


def _display_actions(
    task: dict[str, Any],
    *,
    reviewer_slot: str,
) -> list[dict[str, str]]:
    actions = [
        {
            "label": "",
            "description": str(action["description"]),
        }
        for action in task["actions"]
    ]
    random.Random(_stable_seed(reviewer_slot, task["id"])).shuffle(actions)
    for index, action in enumerate(actions):
        action["label"] = f"Option {chr(ord('A') + index)}"
    return actions


def _review_rows(
    *,
    tasks: list[dict[str, Any]],
    audit_manifest: dict[str, Any],
    reviewer_slot: str,
) -> list[dict[str, Any]]:
    rows = []
    for display_index, task in enumerate(
        _ordered_tasks(
            tasks=tasks,
            audit_manifest=audit_manifest,
            reviewer_slot=reviewer_slot,
        ),
        start=1,
    ):
        rows.append(
            {
                "display_id": f"{reviewer_slot}-{display_index:02d}",
                "task_id": task["id"],
                "construction_cluster_id": task["construction_cluster_id"],
                "catalog_item_id": task["catalog_item_id"],
                "policy_family": task["policy_family"],
                "domain": task["domain"],
                "audit_selection_reason": (
                    "covers_catalog_item_and_family_domain_cell"
                ),
                "reviewer_slot": reviewer_slot,
                "user_task": task["user_task"],
                "planner_context": task["planner_context"],
                "policy": task["policy"],
                "actions": _display_actions(
                    task,
                    reviewer_slot=reviewer_slot,
                ),
            }
        )
    return rows


def render_html(
    *,
    tasks: list[dict[str, Any]],
    audit_manifest: dict[str, Any],
    reviewer_slot: str,
) -> str:
    rows = _review_rows(
        tasks=tasks,
        audit_manifest=audit_manifest,
        reviewer_slot=reviewer_slot,
    )
    payload = json.dumps(
        rows,
        ensure_ascii=False,
        separators=(",", ":"),
    ).replace("</", "<\\/")
    title = f"TopoSafe-Delta Reviewer {reviewer_slot}"
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)}</title>
  <style>
    :root {{
      color-scheme: light;
      --ink: #18212f;
      --muted: #5f6b7a;
      --line: #dce2e8;
      --soft: #f5f7fa;
      --accent: #2458a6;
      --accent-soft: #eaf1fb;
      --danger: #a33535;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background: #ffffff;
      color: var(--ink);
      font: 16px/1.55 -apple-system, BlinkMacSystemFont, "Segoe UI",
        "PingFang SC", "Microsoft YaHei", sans-serif;
    }}
    main {{ width: min(920px, calc(100% - 32px)); margin: 36px auto 80px; }}
    h1 {{ margin: 0 0 8px; font-size: clamp(28px, 4vw, 40px); }}
    h2 {{ margin: 0; font-size: 23px; }}
    p {{ margin: 8px 0; }}
    .intro {{
      padding-bottom: 24px;
      border-bottom: 1px solid var(--line);
    }}
    .intro strong {{ color: var(--accent); }}
    .identity {{
      display: grid;
      grid-template-columns: 170px 1fr;
      gap: 12px;
      align-items: center;
      margin: 24px 0;
    }}
    input[type="text"], textarea {{
      width: 100%;
      border: 1px solid #b9c3cf;
      border-radius: 8px;
      padding: 11px 12px;
      font: inherit;
      background: #fff;
    }}
    input:focus, textarea:focus {{
      outline: 3px solid var(--accent-soft);
      border-color: var(--accent);
    }}
    .progress-wrap {{
      position: sticky;
      top: 0;
      z-index: 3;
      background: rgba(255,255,255,.96);
      padding: 14px 0;
      border-bottom: 1px solid var(--line);
    }}
    .progress-row {{
      display: flex;
      justify-content: space-between;
      gap: 16px;
      margin-bottom: 8px;
      color: var(--muted);
      font-size: 14px;
    }}
    .track {{ height: 8px; border-radius: 99px; background: #e7ebf0; }}
    .bar {{
      width: 0;
      height: 100%;
      border-radius: inherit;
      background: var(--accent);
      transition: width .2s ease;
    }}
    .card {{
      margin: 28px 0;
      padding: 28px;
      border: 1px solid var(--line);
      border-radius: 14px;
      box-shadow: 0 8px 24px rgba(34, 51, 74, .06);
    }}
    .task-number {{
      color: var(--muted);
      font-size: 14px;
      margin-bottom: 4px;
    }}
    .section-label {{
      margin-top: 20px;
      color: var(--muted);
      font-size: 13px;
      font-weight: 700;
      letter-spacing: .04em;
      text-transform: uppercase;
    }}
    .policy {{
      border-left: 4px solid var(--accent);
      background: var(--accent-soft);
      padding: 14px 16px;
      margin-top: 8px;
    }}
    .actions {{ margin: 8px 0 0; padding: 0; list-style: none; }}
    .actions li {{
      display: grid;
      grid-template-columns: 82px 1fr;
      gap: 12px;
      padding: 10px 0;
      border-bottom: 1px solid #edf0f3;
    }}
    .actions li:last-child {{ border-bottom: 0; }}
    .option {{ font-weight: 700; color: var(--accent); }}
    .questions {{
      margin-top: 24px;
      padding-top: 20px;
      border-top: 1px solid var(--line);
    }}
    fieldset {{
      margin: 0 0 18px;
      padding: 0;
      border: 0;
    }}
    legend {{ font-weight: 650; margin-bottom: 9px; }}
    .choices {{ display: flex; gap: 10px; }}
    .choice {{
      display: inline-flex;
      align-items: center;
      gap: 7px;
      min-width: 88px;
      padding: 8px 12px;
      border: 1px solid var(--line);
      border-radius: 8px;
      cursor: pointer;
    }}
    .choice:has(input:checked) {{
      border-color: var(--accent);
      background: var(--accent-soft);
    }}
    textarea {{ min-height: 76px; resize: vertical; }}
    .footer-actions {{
      display: flex;
      flex-wrap: wrap;
      gap: 12px;
      margin-top: 30px;
    }}
    button {{
      border: 0;
      border-radius: 9px;
      padding: 12px 18px;
      font: 650 15px/1.2 inherit;
      cursor: pointer;
    }}
    .primary {{ background: var(--accent); color: #fff; }}
    .secondary {{ background: var(--soft); color: var(--ink); }}
    .message {{ min-height: 24px; margin-top: 12px; color: var(--danger); }}
    .privacy {{
      margin-top: 24px;
      color: var(--muted);
      font-size: 14px;
    }}
    @media (max-width: 640px) {{
      main {{ width: min(100% - 20px, 920px); margin-top: 22px; }}
      .identity {{ grid-template-columns: 1fr; }}
      .card {{ padding: 20px; }}
      .actions li {{ grid-template-columns: 74px 1fr; }}
    }}
  </style>
</head>
<body>
<main>
  <section class="intro">
    <h1>TopoSafe-Delta 任务审核</h1>
    <p>Reviewer {html.escape(reviewer_slot)} · 共 <strong>30</strong> 个任务</p>
    <p>请按任务文字本身判断。不要推测模型表现，也不要与另一位 reviewer 讨论答案。</p>
    <p>每题只需选择 Yes 或 No。全部三项为 Yes 时该任务通过；选择 No 时请写一句原因。</p>
  </section>

  <div class="identity">
    <label for="reviewer-id"><strong>Reviewer ID</strong><br>请填写固定且可追溯的代号</label>
    <input id="reviewer-id" type="text" autocomplete="off"
      placeholder="例如 HUMAN-{html.escape(reviewer_slot)}-202610">
  </div>

  <div class="progress-wrap">
    <div class="progress-row">
      <span id="progress-text">已完成 0 / 30</span>
      <span>进度会自动保存在当前浏览器</span>
    </div>
    <div class="track"><div class="bar" id="progress-bar"></div></div>
  </div>

  <div id="tasks"></div>

  <div class="footer-actions">
    <button class="primary" id="download">完成并下载 CSV</button>
    <button class="secondary" id="clear">清空本地答案</button>
  </div>
  <div class="message" id="message" role="status"></div>
  <p class="privacy">问卷完全离线运行，不会上传内容。请把下载的 CSV 发回研究负责人。</p>
</main>

<script>
const TASKS = {payload};
const REVIEWER_SLOT = {json.dumps(reviewer_slot)};
const STORAGE_KEY = {json.dumps(PACKET_VERSION)} + "::" + REVIEWER_SLOT;
const QUESTIONS = [
  {{
    key: "policy_unambiguous",
    text: "1. 安全规则是否清楚、没有明显歧义？"
  }},
  {{
    key: "scenario_and_actions_plausible",
    text: "2. 这个场景和三个可选操作是否合理、现实？"
  }},
  {{
    key: "no_unencoded_second_violation",
    text: "3. 是否只有这里描述的主要安全问题，没有遗漏另一个重要风险？"
  }}
];

function escapeHtml(value) {{
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}}

function loadState() {{
  try {{
    return JSON.parse(localStorage.getItem(STORAGE_KEY)) || {{
      reviewerId: "",
      answers: {{}}
    }};
  }} catch (_) {{
    return {{ reviewerId: "", answers: {{}} }};
  }}
}}

let state = loadState();
const reviewerInput = document.getElementById("reviewer-id");
reviewerInput.value = state.reviewerId || "";

function saveState() {{
  state.reviewerId = reviewerInput.value.trim();
  localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  updateProgress();
}}

function taskAnswer(taskId) {{
  if (!state.answers[taskId]) {{
    state.answers[taskId] = {{ notes: "" }};
  }}
  return state.answers[taskId];
}}

function render() {{
  const root = document.getElementById("tasks");
  root.innerHTML = TASKS.map((task, index) => {{
    const answer = taskAnswer(task.task_id);
    const actions = task.actions.map(action => `
      <li><span class="option">${{escapeHtml(action.label)}}</span>
      <span>${{escapeHtml(action.description)}}</span></li>`).join("");
    const questions = QUESTIONS.map(question => {{
      const current = answer[question.key] || "";
      return `
        <fieldset>
          <legend>${{escapeHtml(question.text)}}</legend>
          <div class="choices">
            <label class="choice">
              <input type="radio" name="${{task.task_id}}-${{question.key}}"
                data-task="${{task.task_id}}" data-field="${{question.key}}"
                value="yes" ${{current === "yes" ? "checked" : ""}}> Yes
            </label>
            <label class="choice">
              <input type="radio" name="${{task.task_id}}-${{question.key}}"
                data-task="${{task.task_id}}" data-field="${{question.key}}"
                value="no" ${{current === "no" ? "checked" : ""}}> No
            </label>
          </div>
        </fieldset>`;
    }}).join("");
    return `
      <article class="card">
        <div class="task-number">任务 ${{index + 1}} / ${{TASKS.length}}</div>
        <h2>${{escapeHtml(task.user_task)}}</h2>
        <div class="section-label">背景</div>
        <p>${{escapeHtml(task.planner_context)}}</p>
        <div class="section-label">安全规则</div>
        <div class="policy">${{escapeHtml(task.policy)}}</div>
        <div class="section-label">可选操作</div>
        <ul class="actions">${{actions}}</ul>
        <div class="questions">${{questions}}
          <label><strong>备注</strong>（选择 No 时请说明原因）</label>
          <textarea data-task="${{task.task_id}}" data-field="notes"
            placeholder="可留空">${{escapeHtml(answer.notes || "")}}</textarea>
        </div>
      </article>`;
  }}).join("");

  root.querySelectorAll("input[type=radio]").forEach(input => {{
    input.addEventListener("change", event => {{
      const taskId = event.target.dataset.task;
      taskAnswer(taskId)[event.target.dataset.field] = event.target.value;
      saveState();
    }});
  }});
  root.querySelectorAll("textarea").forEach(textarea => {{
    textarea.addEventListener("input", event => {{
      const taskId = event.target.dataset.task;
      taskAnswer(taskId).notes = event.target.value;
      saveState();
    }});
  }});
  updateProgress();
}}

function isComplete(task) {{
  const answer = taskAnswer(task.task_id);
  return QUESTIONS.every(question => ["yes", "no"].includes(answer[question.key]));
}}

function updateProgress() {{
  const completed = TASKS.filter(isComplete).length;
  document.getElementById("progress-text").textContent =
    `已完成 ${{completed}} / ${{TASKS.length}}`;
  document.getElementById("progress-bar").style.width =
    `${{completed / TASKS.length * 100}}%`;
}}

function csvCell(value) {{
  return '"' + String(value ?? "").replaceAll('"', '""') + '"';
}}

function exportCsv() {{
  saveState();
  const message = document.getElementById("message");
  if (!state.reviewerId) {{
    message.textContent = "请先填写 Reviewer ID。";
    reviewerInput.focus();
    return;
  }}
  const incomplete = TASKS.filter(task => !isComplete(task));
  if (incomplete.length) {{
    message.textContent = `还有 ${{incomplete.length}} 个任务没有完成。`;
    return;
  }}
  const missingNotes = TASKS.filter(task => {{
    const answer = taskAnswer(task.task_id);
    const hasNo = QUESTIONS.some(question => answer[question.key] === "no");
    return hasNo && !String(answer.notes || "").trim();
  }});
  if (missingNotes.length) {{
    message.textContent = `有 ${{missingNotes.length}} 个任务选择了 No，但没有填写原因。`;
    return;
  }}
  const headers = [
    "task_id", "construction_cluster_id", "catalog_item_id",
    "policy_family", "domain", "audit_selection_reason", "reviewer_slot",
    "reviewer_id", "review_status", "policy_unambiguous",
    "scenario_and_actions_plausible", "no_unencoded_second_violation",
    "notes"
  ];
  const lines = [headers.map(csvCell).join(",")];
  TASKS.forEach(task => {{
    const answer = taskAnswer(task.task_id);
    const passed = QUESTIONS.every(question => answer[question.key] === "yes");
    const row = {{
      ...task,
      reviewer_id: state.reviewerId,
      review_status: passed ? "pass" : "fail",
      policy_unambiguous: answer.policy_unambiguous,
      scenario_and_actions_plausible: answer.scenario_and_actions_plausible,
      no_unencoded_second_violation: answer.no_unencoded_second_violation,
      notes: answer.notes || ""
    }};
    lines.push(headers.map(header => csvCell(row[header])).join(","));
  }});
  const blob = new Blob(["\\ufeff" + lines.join("\\r\\n")], {{
    type: "text/csv;charset=utf-8"
  }});
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = `TopoSafe-Delta-Reviewer-${{REVIEWER_SLOT}}-completed.csv`;
  link.click();
  URL.revokeObjectURL(link.href);
  message.style.color = "#236a3b";
  message.textContent = "CSV 已下载，请发送给研究负责人。";
}}

reviewerInput.addEventListener("input", saveState);
document.getElementById("download").addEventListener("click", exportCsv);
document.getElementById("clear").addEventListener("click", () => {{
  if (confirm("确定清空当前浏览器中 Reviewer " + REVIEWER_SLOT + " 的全部答案吗？")) {{
    localStorage.removeItem(STORAGE_KEY);
    state = {{ reviewerId: "", answers: {{}} }};
    reviewerInput.value = "";
    render();
    document.getElementById("message").textContent = "";
  }}
}});
render();
</script>
</body>
</html>
"""


def render_readme(reviewer_slot: str) -> str:
    return f"""TopoSafe-Delta Reviewer {reviewer_slot}

1. 双击打开 TopoSafe-Delta-Reviewer-{reviewer_slot}.html。
2. 填写 Reviewer ID。
3. 独立审核 30 个任务，每个任务回答三个 Yes/No 问题。
4. 如果选择 No，请写一句原因。
5. 点击“完成并下载 CSV”。
6. 把下载的 TopoSafe-Delta-Reviewer-{reviewer_slot}-completed.csv 发回研究负责人。

注意：
- 不要与另一位 reviewer 讨论答案。
- 不要根据模型可能如何回答来判断任务。
- 页面完全离线运行，答案只保存在当前浏览器中。
- 请审核页面展示的原始英文任务文字；中文仅用于解释字段。
"""


def build_reviewer_packet(
    *,
    tasks_path: Path,
    audit_manifest_path: Path,
    reviewer_slot: str,
    output_root: Path,
) -> dict[str, Any]:
    reviewer_slot = reviewer_slot.upper()
    if reviewer_slot not in {"A", "B"}:
        raise ValueError("reviewer_slot must be A or B")
    tasks = load_tasks(tasks_path)
    audit_manifest = json.loads(
        audit_manifest_path.read_text(encoding="utf-8")
    )
    reviewer_dir = output_root / f"reviewer_{reviewer_slot}"
    reviewer_dir.mkdir(parents=True, exist_ok=True)
    html_path = (
        reviewer_dir / f"TopoSafe-Delta-Reviewer-{reviewer_slot}.html"
    )
    readme_path = reviewer_dir / "README.txt"
    html_path.write_text(
        render_html(
            tasks=tasks,
            audit_manifest=audit_manifest,
            reviewer_slot=reviewer_slot,
        ),
        encoding="utf-8",
    )
    readme_path.write_text(
        render_readme(reviewer_slot),
        encoding="utf-8",
    )
    zip_path = output_root / f"TopoSafe-Delta-Reviewer-{reviewer_slot}.zip"
    temporary = zip_path.with_suffix(".zip.tmp")
    with zipfile.ZipFile(
        temporary,
        "w",
        compression=zipfile.ZIP_DEFLATED,
    ) as archive:
        archive.write(html_path, arcname=html_path.name)
        archive.write(readme_path, arcname=readme_path.name)
    temporary.replace(zip_path)
    return {
        "packet_version": PACKET_VERSION,
        "reviewer_slot": reviewer_slot,
        "tasks": len(audit_manifest["selected_task_ids"]),
        "html": str(html_path),
        "readme": str(readme_path),
        "zip": str(zip_path),
    }
