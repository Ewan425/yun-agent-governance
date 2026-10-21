# Governance Playbook: mechanisms that outlive tools

> Distilled from operating a file-based AI assistant for one user over three
> months. Every mechanism here exists because the assistant failed without it
> (see `failure-modes.md`). None of them require any particular product,
> vendor or framework -- that is the point.

## 1. state-before-claims
**Problem**: Status reports built from memory, docs, or proposals that drifted from reality.
**Rule**: Before reporting any "done / pending / installed" list, query live state seconds before reporting: `git log --oneline -3`, `git status --short`, the automation/task registry. Roadmap docs are leads, never facts.
**Wire it**: a standing item in the delivery gate; an eval behavior case.
**Guards against**: failure-modes #1, #2, #14, #15.

## 2. no-silent-pass
**Problem**: Automation printing "0 found -- success" on an expired session; green checklists that never touched outcomes.
**Rule**: Every check must print an explicit result line. Empty results, missing files, and parse failures are *errors to print*, never silent zeros. A tool that cannot validate its own outcome is safer not run.
**Wire it**: standard header/summary in every tool script; parse-failure branches that always print.
**Guards against**: #6, #7, #22.

## 3. count-two-ways
**Problem**: Hand-counted numbers in formal reports ("21" vs actual 20); same-algorithm "rechecks" that repeat the same error.
**Rule**: Any "I counted N" must be recomputable by a script, and any verification must use an independent method from the original count. Reconcile N against "how many there should be" when that total is knowable.
**Wire it**: write the counter first, report its output; keep baselines for anything recurrent.
**Guards against**: #1, #2, #3, #5, #7.

## 4. known-answer-testing
**Problem**: Tools shipped because "it ran", then failing on the first real use.
**Rule**: A new tool's first test is a real case whose answer you already know. A green unknown-answer run is not evidence.
**Wire it**: every new tool ships with at least one fixture case in its README or test file.
**Guards against**: #20, #21, #17.

## 5. two-repo-git
**Problem**: Configuration, memory and tools all mutating without history; ad-hoc `.bak` copies that drift and sneak back in.
**Rule**: Two repositories -- one for identity/memory, one for tools/ledgers. Every change session ends in commits; the pre-change state is *committed*, never copied to side files. Upgrades are governance events.
**Wire it**: `git init` both; a habit (later an eval case) that dirty trees block delivery.
**Guards against**: #25, #8.

## 6. rule-change-ceremony
**Problem**: Edits to the rules themselves -- the highest-leverage, least-guarded change there is.
**Rule**: Five steps, order fixed: snapshot the rule into a ledger (with reason) -> commit the pre-change state -> edit -> verify (eval gate, mirrors, syntax) -> commit the post-change state and log. Then a 7-day outcome review: did the change actually help? If not, delete it.
**Wire it**: a playbook page the assistant re-reads before every rule edit; the ledger doubles as an audit trail.
**Guards against**: #25, #13.

## 7. held-out-eval-gate
**Problem**: "Every check green" while reality silently regressed; rule changes that broke behavior nobody re-tested.
**Rule**: A small suite of behavioral checks (not unit tests -- *behavior*) run after every non-trivial rule change. Regression = fix or revert; the commit message carries the score.
**Wire it**: `eval/runeval.py` + a config describing the assistant's files.
**Guards against**: #5, #8, #15; operationalizes the evaluator-gated idea (GEPA/DSPy) at file-system scale.

## 8. closed-loop-postmortems
**Problem**: Lessons written, read once, forgotten; the same incident recurring 18 months later.
**Rule**: Every postmortem entry must hook to at least one mechanism (rule / eval case / playbook / automation). No hook = not admitted. Hook rate is reviewed on a schedule. Reflection output is wiring work, not prose.
**Wire it**: the `Hooked to` field; an eval case that audits entries past a sequence threshold.
**Guards against**: #9, #23, #24.

## 9. supply-chain-discipline
**Problem**: Third-party gear (MCP servers, skills) installed once and forgotten; the rug-pull pattern -- benign at install, malicious after an update.
**Rule**: Pin versions (never `@latest`); cap unvetted skill count; scan local tools for self-upgrading code; credential-bearing config gets a rotation policy; any behavior change in a dependency is a governance event.
**Wire it**: `tools/supply_chain_check.py` on a schedule.
**Guards against**: an incident class that never made this log *because* the check shipped before the breach.

## 10. automation-vs-proactivity
**Problem**: Scheduled work being redone by hand ("should I run it now?"), or user-facing automations silently deleted as "optimization".
**Rule**: If an automation owns a job, never redo it or ask whether to run it -- it runs itself. The assistant's proactive voice covers only what automation cannot reach. Never remove a user-facing automation unilaterally; that is the user's call.
**Wire it**: an explicit registry of automations, consulted before any "let me do that" impulse.
**Guards against**: #19.

## 11. learner-data-not-willpower
**Problem**: Assuming what a learner knows by asking; motivation-based plans that collapse.
**Rule**: Track gaps in a ledger; probe understanding with a single question instead of asking "do you know X"; every exercise result feeds the ledger, and the ledger -- not vibes -- picks the next topic. Schedule by the human's clock, never by the machine's costs.
**Wire it**: a small `ledger.py add/due/done/report`; quiz-before-teach in the teaching flow.
**Guards against**: #18, #19.

## 12. design-for-refutation
**Problem**: Confident, polished statements the user cannot push back on -- until they do, and everything cracks.
**Rule**: The user is better at catching the assistant's errors than the assistant is. So: cite checkable sources for factual claims, show how numbers were obtained, deliver in forms that can be tried, and state what would prove the claim wrong. Optimize for refutability, not eloquence.
**Wire it**: a standing preflight question -- "did this delivery leave room for the user to disagree?"
**Guards against**: #12, #16, #17, #18.

## 13. long-task-protocol
**Problem**: Long agent sessions forget steps, misroute tools, and rot silently (long-horizon failure grows superlinearly with length).
**Rule**: More than ~7 steps: plan first, execute stepwise. Tool returns enter context as *summaries* (raw output to disk). One task per session; resume by reading files, not by dragging a giant chat history forward.
**Wire it**: split before starting; a summarizer step between tool and context.
**Guards against**: an entire failure category, by avoiding the conditions that breed it.

## 14. mirror-memory
**Problem**: A single memory file drifts, gets truncated in an edit, or loses its anchor phrases -- and nothing notices until behavior degrades.
**Rule**: Keep two byte-identical copies of the master memory file, plus a short list of literal anchor strings that must survive every edit. Drift or missing anchor = alarm at boot, not at behavior time.
**Wire it**: boot-time mirror check + anchor check as eval cases.
**Guards against**: #13, #25.

---

### Meta-rule
Mechanisms are judged by adoption, not by how good they sound. Every mechanism above names what it guards; if a failure recurs anyway, the mechanism gets fixed or deleted -- it does not get a second layer of prose.
