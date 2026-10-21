# yun-agent-governance

**Tools rot. Governance doesn't.**
How one AI assistant went from *relying on good intentions* to *relying on machines* — in three months.

一个 AI 助手怎么在三个月内，从「靠自觉」改成「靠机器」。
工具会过时，治理机制不会。

---

## EN

### What this is
The de-identified, open-sourceable core of a **file-based personal AI assistant** (codename *Kai*) that helps a first-year CS student with coursework. Over three months the assistant kept failing in unglamorous ways — quoting stale numbers, trusting its own summaries, reporting roadmaps as facts — and kept getting caught by its user. This repo is what those catches turned into: not bigger prompts, but **mechanisms** — scripts, ledgers, gates and ceremonies that keep working when nobody is watching.

It is positioned as an **AI engineering governance** artifact: evidence of designing, instrumenting and operating guardrails around a long-running autonomous agent. Not a security tooling repo.

### The story in one paragraph
Phase 1 was *good intentions*: instructions like "always double-check numbers" lived in the system prompt, and worked exactly as well as willpower usually does. Phase 2 was *facilities*: tools were built to check things — and then rarely invoked. Phase 3 — the three months this repo documents — was *machines*: every repeated failure was converted into something that cannot forget: a postmortem log whose entries must hook to a mechanism, a held-out behavioral eval that must pass before any rule change ships, two git repositories where the pre-change state is committed instead of `.bak`-ed, a supply-chain scanner, and weekly automations that audit what the assistant would rather not look at. The user went from full-time QA to reading one line each Sunday: *"N new lessons, hook rate X%"*.

### What's inside
| Path | What it is |
|---|---|
| `eval/runeval.py` | Held-out self-eval runner: 9 automatic behavioral checks + a 5-item manual checklist. Exit code = number of failures. Run after every non-trivial rule change; regression means fix or revert. |
| `tools/supply_chain_check.py` | Supply-chain hygiene for agent gear: pinned MCP versions, skill-count red line, auto-upgrade pattern scan. Report-only, but every check prints — silent pass is a bug. |
| `docs/failure-modes.md` | 25 real failures, each abstracted: what happened, root cause, lesson, a self-check question, and the mechanism it hooks to. |
| `docs/governance-playbook.md` | 14 transferable mechanisms (state-before-claims, no-silent-pass, closed-loop postmortems, held-out eval gate, …). The actual product of this repo. |
| `examples/runeval.config.example.json` | Example config wiring the eval runner to an assistant's files. |

### Quickstart
```bash
# 1. point the eval runner at your own assistant home
cp examples/runeval.config.example.json my.config.json   # edit paths
python eval/runeval.py my.config.json                    # exit 0 = all green
python eval/runeval.py --list my.config.json             # the manual checklist

# 2. audit your agent gear
python tools/supply_chain_check.py \
  --mcp ~/.your-assistant/mcp.json \
  --skills-dir ~/.your-assistant/skills \
  --tools-dir ./your-tools
```

### Design principles
1. **Willpower is not a control.** Every rule that matters exists twice: once as prose, once as something that runs.
2. **Silent pass is the enemy.** Zero results, missing files, expired sessions must print loudly or not run at all.
3. **Postmortems hook or they don't ship.** A lesson without a mechanism attached is a story.
4. **Regressions revert.** The eval suite outranks the roadmap.
5. **The human audits the auditor.** Every claim ships with its evidence trail.

### Ideas & references (all public)
- Evaluator-gated improvement (GEPA, DSPy) — *your own eval set as the reward.*
- "The Postmortem That Changed Nothing", latini.dev (2026) — *"We did not fail to write the document. We failed to change the system."*
- Checkmarx / NHI / AI Governance MCP incident reviews (2026) — supply-chain incidents and the rug-pull pattern.
- arXiv 2608.05810 — unvetted skill accumulation degrades performance (motivates the skill red line).
- arXiv 2603.29231 — long-horizon agent reliability: failure grows superlinearly with task length (motivates the long-task protocol).
- Agent Skills open standard (agentskills.io; SEP-2640, 2026-09) — portable skill packaging; "read ≠ activate" approval model.

### Disclaimer
Personal data was scrubbed before publication: no real names, school, courses, budgets, career details or coursework content. All cases in `docs/failure-modes.md` are abstracted from real incidents. Verified state at publication: two git repos, 15 commits (9 + 6); 25 postmortem entries; 9 automatic eval cases + 5 behavior checks.

### License
MIT (see `LICENSE`).

---

## ZH

### 这是什么
一个**基于文件的常驻 AI 助手**（代号 *Kai*）的脱敏开源核心：它服务一名计算机系大一学生。三个月里它反复栽在不体面的错误上——引用过期的数字、相信自己造的汇总、把路线图当成实况——而每一次都是用户亲手抓出来的。本仓库就是这些"被抓"沉淀下来的东西：**不是更大的提示词，而是机制**——脚本、台账、闸门和流程，在没人盯着的时候照样运转。

它的定位是 **AI 工程治理**作品：围绕一个长期运行的自治 agent 设计、埋点、运转护栏的过程证据，不是网安工具仓库。

### 一段话故事
第一阶段靠**自觉**：「数字必须复查」这类指示躺在系统提示词里，效果跟意志力通常的效果一样。第二阶段靠**设施**：造了检查工具——然后很少被调用。第三阶段——本仓库记录的三个月——靠**机器**：每重复犯一次错，就把它改造成不会忘的东西：教训清单里每条必须挂到至少一个机制、改了规则必须先过 held-out 自评否则回滚、两个 git 仓库存"改前态"而不是 `.bak` 副本、供应链扫描器、每周自动审它不想看的地方。用户从全职质检，变成周日读一行：「本周新增 N 条、挂钩率 X%」。

### 目录内容
见上表（EN 部分）。核心产出是 `docs/governance-playbook.md`——14 条可迁移机制。

### 快速开始
命令见上（EN 部分）。一句话：把 `runeval.py` 指向你自己的助手目录，把扫描器指向你的装备目录。

### 设计原则
1. **自觉不是控制。** 每条重要的规则存在两遍：一遍是文字，一遍是能跑的东西。
2. **静默通过是敌人。** 零结果、缺文件、会话失效，要么大声打印，要么别跑。
3. **复盘不挂钩就不入库。** 没有机制承接的教训只是故事。
4. **退步就回滚。** 自评集的优先级高于路线图。
5. **人来审计审计者。** 每个结论都带着证据链交付。

### 许可
MIT。
