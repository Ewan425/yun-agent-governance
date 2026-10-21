# Failure Modes: 25 ways a file-based AI assistant actually failed

> A postmortem log from a personal AI assistant (codename "Kai") that helps a
> first-year CS student with coursework. Every entry below caused real harm
> before it was caught -- almost every one was caught by the user, not by the
> assistant. Entries are abstracted: tools, courses and people are generic.
>
> The rule that keeps this list alive: **every entry must hook to at least one
> mechanism** (a rule, an eval case, a playbook, an automation). An unhooked
> lesson is a story, not a fix. Inspired by "The Postmortem That Changed
> Nothing" (latini.dev, 2026): *"We did not fail to write the document. We
> failed to change the system."*
>
> Field guide: **What happened** / **Root cause** / **Lesson** /
> **Self-check** (a question to ask before shipping) / **Hooked to**
> (mechanisms in `governance-playbook.md`).

---

## Chapter 1 -- Numbers and sources

### 1. Reporting numbers from memory
- **What happened**: The assistant quoted exam grading structure ("midterm 30%, final 40%, everything in week 14") from memory. The syllabus said: group project 30% is a *separate* item, and the final sits in week 16, not 14. Partly right, partly fabricated, delivered with full confidence.
- **Root cause**: Memory of a number feels like knowledge. It isn't.
- **Lesson**: Any number with consequences (weights, dates, scores, ranges, thresholds) must be re-read from the original document at answer time. A remembered number is "unverified" until checked.
- **Self-check**: Did I look this number up just now, or am I remembering it? Remembering → go look.
- **Hooked to**: `state-before-claims`, `count-two-ways`.

### 2. Treating a stale index as fact
- **What happened**: A hand-maintained index file said a course had "17 handouts, chapter 4 not started". Reality: 77 handouts, week 14 reached. The assistant quoted the index.
- **Root cause**: The index was self-authored, so it felt trustworthy. It had silently rotted.
- **Lesson**: An index locates files; it is not a source of counts. Before citing any quantity from it, `ls` the directory.
- **Self-check**: Is this count from my last audit, or from right now?
- **Hooked to**: `state-before-claims`, `count-two-ways`.

### 3. "Verifying" with the same algorithm twice
- **What happened**: A baseline count said 77 files; a recount said 77 too -- but both used `ls | wc -l`, which also counted a subdirectory. Real file count: 76. Same algorithm twice is agreement, not verification.
- **Root cause**: Re-running an identical method correlates the errors with it.
- **Lesson**: Cross-checks must be *independent* (e.g., `os.path.isfile` walk vs `ls`), or they prove nothing.
- **Self-check**: Can I state how this number was counted, and would a different method agree?
- **Hooked to**: `count-two-ways`.

### 4. Copying unverified attribution into code comments
- **What happened**: A script carried the comment "baseline 12 because 2 mp4 files were excluded". An independent audit found zero mp4 files anywhere and no record they were ever counted. The "explanation" was folklore that had hardened into fact -- and *explained* numbers get trusted more than bare ones.
- **Root cause**: A plausible comment was treated as a previously verified conclusion.
- **Lesson**: Every "because" written into code or docs needs a source, or must be labeled unverified. Second-hand explanations (including your own past self's) are not sources.
- **Self-check**: Which file and line is the original evidence for this claim? If none: mark it unverified.
- **Hooked to**: `state-before-claims`.

### 5. A hand-counted N never reconciled
- **What happened**: An audit report stated "21 skills installed". The machine count said 20. The wrong number shipped in a formal report.
- **Root cause**: Counting by hand and stopping there.
- **Lesson**: Any "I counted N" must be recomputable by a script. Write the counter first, then report its output.
- **Self-check**: Is there a script that reproduces this N? If not, build one before reporting.
- **Hooked to**: `count-two-ways`, `held-out-eval-gate`.

## Chapter 2 -- Silent success

### 6. Tool success is not task success
- **What happened**: A campus-LMS downloader printed "1 found, 1 succeeded, 0 failed" and the assistant nearly reported "download complete". Reality: one course alone had 77 files; course files were nested in folder modules the crawler treated as file pages and skipped, so it scraped layer 0 and declared victory. Worse: the login session had long expired, and the tool reported "0 files found -- success" on a dead session.
- **Root cause**: The tool printed its own exit status; nobody checked coverage against a known total.
- **Lesson**: A silent pass is worse than a loud error. An automation that can't validate its own outcome would be safer not running.
- **Self-check**: Is this "success" a verified count, or the script's say-so? If counts can't be reconciled, treat it as failure.
- **Hooked to**: `no-silent-pass`, `known-answer-testing`.

### 7. Trusting a self-made summary
- **What happened**: A run summary read "74 files, zero failures" and the assistant wrote it into memory as an achievement. Real coverage: 19 of 76. Fifty-seven files missed -- and the summary was never cross-checked against "how many should there be".
- **Root cause**: The assistant manufactured the summary, then believed it. A generated aggregate is not evidence.
- **Lesson**: An aggregation file proves the run finished, nothing more. Its numbers must be reconciled against an independently known total before they enter reports or memory.
- **Self-check**: Do I know the expected total from an independent source? If not, the summary is unverified.
- **Hooked to**: `no-silent-pass`, `count-two-ways`.

### 8. Built is not used
- **What happened**: A trigger log of 644 invocations showed four "fixed and in use" guardrail tools had been called 0, 1, 1 and 1 times. Running one of them once immediately surfaced two courses below their file baselines -- a regression that had lain undetected for two days.
- **Root cause**: "Facility exists" was confused with "facility runs". A green checklist substitutes for adoption.
- **Lesson**: Facilities are measured in invocations, not in constructions. If the counter is zero, the "fix" is theoretical.
- **Self-check**: What is the actual call count of the tool I'm claiming to use?
- **Hooked to**: `no-silent-pass`, `held-out-eval-gate`.

### 9. Done but not ticked
- **What happened**: A report's todo list left two items unchecked -- "modify script X" and "run real-data regression" -- although both were complete, with real artifacts on disk. Two rounds later the stale list would have misled even the assistant itself.
- **Root cause**: "Doing the work" and "updating the list" were treated as separate, optional steps.
- **Lesson**: Misinformation isn't only exaggeration; it is also lag. An action counts as done only when the code changed *and* the checklist was ticked.
- **Self-check**: Did I close out every list item this change was tracked under?
- **Hooked to**: `closed-loop-postmortems`.

## Chapter 3 -- Speak only after checking

### 10. A missing file is not a missing obligation
- **What happened**: No submission folder existed for a weekly exercise, so the assistant escalated: "0 submitted -- red alert." Reality: the exercise was in-class only (never submitted), and one "missing" item was a screenshot a classmate had shared. Three confident conclusions, all wrong, from one directory listing.
- **Root cause**: Filesystem state was equated with the user's obligations.
- **Lesson**: Before reporting something as "missing", establish that it was owed at all. State is not obligation.
- **Self-check**: Is this item actually submittable/gradable? If unconfirmed, the word "missing" is banned.
- **Hooked to**: `state-before-claims`.

### 11. Teaching from your own knowledge, not their syllabus
- **What happened**: Building a study aid on two's complement, the assistant covered binary only. The lecturer's own week-3 slides carried the hex variant (sign by leading digit, complement tables) as examinable material. The assistant knew plenty -- just not what would be tested.
- **Root cause**: Internal knowledge was treated as the curriculum.
- **Lesson**: The user's course materials are the ground truth for what gets taught. Grep the actual slides before deciding scope.
- **Self-check**: Does this content appear in *their* materials? Check before teaching.
- **Hooked to**: `state-before-claims`.

### 12. "Didn't do" is not "decided not to"
- **What happened**: A status report declared an activity "stalled at zero output". The user had simply rejected that tool as unsuitable -- a decision, recorded in context, which the assistant misread as a problem.
- **Root cause**: Absence of activity was assumed to mean absence of intent.
- **Lesson**: "Not doing X" and "choosing not to do X" are different states. A decision is not a defect and must not be reported as one.
- **Self-check**: Did the user decline this? If yes, it is off the report.
- **Hooked to**: `design-for-refutation`.

### 13. Stale environment facts driving wrong conclusions
- **What happened**: Memory claimed "shell PATH broken", "no Unicode path support", "glob unreliable on these paths". All three were re-tested and found false -- but the assistant had been routing around phantom breakage, choosing worse tools for weeks.
- **Root cause**: Technical memories were never re-validated; they expired silently.
- **Lesson**: A stale technical fact is worse than no fact. Re-test environment claims on a schedule, and date every such claim.
- **Self-check**: When was this environment fact last actually tested?
- **Hooked to**: `state-before-claims`, `mirror-memory`.

### 14. Proposing what already exists
- **What happened**: The assistant proposed "add a VAD pre-filter to the transcription script -- it's one parameter, but I should A/B it first", delivered as a careful warning. The script had carried `vad_filter=True` at line 61 for weeks. Ten seconds of grepping its own code would have prevented the proposal.
- **Root cause**: A search-result insight ("VAD reduces hallucinations") was pattern-matched to "we probably lack this" and spoken aloud.
- **Lesson**: Before proposing "add X" or claiming "can't do Y": grep for X in the codebase first. Reporting on your own implementation is still reporting -- same evidence bar as any other number.
- **Self-check**: Have I checked the current implementation state of the thing I'm about to propose?
- **Hooked to**: `state-before-claims`.

### 15. Reading a proposal document as live state
- **What happened**: In one evening, three status errors: finished git work was reported as "to be done" (sourced from an old proposal); an active weekly automation was reported as "not yet installed, awaiting your call"; a change requiring no restart was bundled into "pick your moment". All three came from consulting proposal text instead of the machine.
- **Root cause**: Roadmap documents feel authoritative; live state requires running commands, so the lazy path won -- three times in one night.
- **Lesson**: Proposals are leads; machine state is fact. Reporting any status list requires fresh `git log` / automation-registry reads first. If you were caught three times in one evening, willpower is demonstrably not the fix.
- **Self-check**: Did I just query live state for every item on this list, seconds ago?
- **Hooked to**: `state-before-claims`, `held-out-eval-gate`.

## Chapter 4 -- Delivery form

### 16. Right content, wrong container
- **What happened**: Two carefully built PDF study sheets for a zero-background learner were judged unusable on arrival. The learner needed plain-language story first, term names second, one concept at a time, and content revealed *after* answering. A static document cannot wait for an answer.
- **Root cause**: More content was offered when the missing thing was a different medium.
- **Lesson**: Delivery form is part of the product. A beginner doesn't need more words; they need feedback timing. Wrong container → zero value, no matter how good the content.
- **Self-check**: Is the recipient a beginner or a reviewer? Beginners get interactive, not static.
- **Hooked to**: `design-for-refutation`.

### 17. Explanation decoupled from the answer
- **What happened**: An interactive quiz hardcoded its explanation as "Correct! You spotted..." -- so a *wrong* answer rendered as "Incorrect. Correct!" on screen. The user asked on the spot: "so which is it?"
- **Root cause**: Explanation text was written once, globally, instead of being bound to each option.
- **Lesson**: Feedback must attach to the option, not the question: `[option text, is_correct, why_this_option_is_right_or_wrong]`.
- **Self-check**: Does any feedback string start with a hardcoded "correct/incorrect"? Then it's wired to the wrong thing.
- **Hooked to**: `known-answer-testing`, `design-for-refutation`.

### 18. Readable artifacts instead of practice
- **What happened**: One evening produced a diagnostic report, two study packs, an index and three interactive widgets -- all read or clicked, zero exercises attempted. Reading has instant feedback; practice doesn't, so both drifted to reading.
- **Root cause**: The assistant optimized for what it could produce, not what the user needed to do.
- **Lesson**: Every batch of readable deliverables must ship with one action only the user can perform. If nothing in the delivery requires their hand, you've given too much.
- **Self-check**: Which step here requires the user to write or speak? None → cut scope.
- **Hooked to**: `design-for-refutation`, `learner-data-not-willpower`.

### 19. Scheduling by the assistant's cost, not the human's clock
- **What happened**: Content generation was scheduled at 23:00, justified as "quota-friendly" -- the assistant's quota. The user could not absorb output at that hour.
- **Root cause**: Optimization targets were chosen from the machine's perspective.
- **Lesson**: Ask about the human's schedule before optimizing your own costs. Their availability is the constraint; your quota is not.
- **Self-check**: Whose constraint is this schedule serving?
- **Hooked to**: `automation-vs-proactivity`.

## Chapter 5 -- Tooling and mechanism governance

### 20. Shipping a tool without a known-answer test
- **What happened**: A monitoring tool was built and run once; it said "nothing new", and that was accepted as validation. Its crawler was silently missing nested content. A single regression case -- "is file X, which we know exists, detected?" -- would have exposed it in five minutes.
- **Root cause**: "It ran" was treated as "it works".
- **Lesson**: A new tool's first test must be a real case whose answer is already known. Passing an unknown-answer run proves nothing.
- **Self-check**: Can I name one real, known-answer case this tool has been tested against?
- **Hooked to**: `known-answer-testing`.

### 21. Building a tool, then never using it
- **What happened**: A PDF-grep tool was built at 01:20. By 01:50 the assistant had written two more raw PDF-parsing snippets by hand -- nine similar code blocks in one night. The tool had never been validated against the real need, so it stayed invisible at the moment of use.
- **Root cause**: No validation loop connected "tool exists" to "task at hand reaches for it".
- **Lesson**: Build the tool, then immediately solve your *current* real task with it. If the last real need didn't use it, the tool isn't finished.
- **Self-check**: Did the most recent real task use this tool? If not, it's vaporware.
- **Hooked to**: `known-answer-testing`.

### 22. Trusting the error message's direction
- **What happened**: Connecting to a local debugging port returned HTTP 502 -- looking exactly like a crashed browser. The real cause: the host application's `http_proxy` was intercepting even `127.0.0.1` traffic.
- **Root cause**: The error's apparent meaning ("target is down") was accepted instead of treating it as a symptom.
- **Lesson**: Proxy pollution is the most common fake-failure source. On 5xx or connection-refused, check `env | grep -i proxy` before blaming your code or the target.
- **Self-check**: Is this error my bug, or is the environment lying to me?
- **Hooked to**: `no-silent-pass`.

### 23. Reflection that audits wording, not outcomes
- **What happened**: The automated nightly reflection ran earnestly and produced a thorough multi-thousand-word log -- all green. It had scanned *phrasing* ("did I use internal jargon", "did I promise without tool traces"), never *outcomes* ("did the downloads actually complete"). Fifty-seven missing files sailed through a fully green review. The pattern had even been noticed in a previous log and left unwired: noticing is not fixing.
- **Root cause**: The mechanism inspected the assistant's speech, which it controls, instead of the world, which it doesn't.
- **Lesson**: Reflection that would stay green in the exact scenario it most needs to catch is theater. Anchor every self-review to an external reconciliation first, phrasing checks second.
- **Self-check**: If I committed the failure this tool exists to catch, would it actually go red?
- **Hooked to**: `closed-loop-postmortems`, `no-silent-pass`.

### 24. Wiring the fix so it cannot drift back
- **What happened**: The outcome of #23 was fixed properly: a reconciliation script now runs *before* any wording audit (order non-negotiable), external-evidence checks lead the delivery gate, and "summary numbers must reconcile against baselines" was written into the automation's prompt instead of left as an oral promise.
- **Root cause**: (This entry records the fix, as a template.) The fix worked because it changed scripts, ordering and prompts -- not because anyone resolved to "be more careful".
- **Lesson**: A fix that lives in a person's attention will evaporate. Move it into code, order and scheduled prompts.
- **Self-check**: Where exactly does this fix live? If the answer is "in my diligence", it isn't fixed.
- **Hooked to**: `closed-loop-postmortems`, `rule-change-ceremony`.

### 25. Process drift: two maps conflict, habit wins
- **What happened**: A manual had replaced ".bak backups" with "git-committed pre-change state" weeks earlier. Under time pressure the assistant made a `.bak` copy anyway -- and only read the manual *after* acting. The outdated instruction still sitting in another file competed with the new one, and the old habit won.
- **Root cause**: Two authoritative documents disagreed; the stale one was never deleted, and the manual wasn't re-read before acting.
- **Lesson**: When two maps conflict, the newer procedure wins -- and the old text gets fixed or removed the moment it is discovered. Read the current manual *before* the act, not after.
- **Self-check**: Does a procedure exist for this action, and which version is current?
- **Hooked to**: `rule-change-ceremony`, `mirror-memory`.

---

## The three-line pre-delivery self-check

Before any delivery, ask:

1. **Numbers**: every consequential number re-checked against its source just now?
2. **Form**: does the recipient's level match the medium (interactive for beginners, not static piles)?
3. **Their hand**: is there one step here that only the user can do? If not, cut scope.

Facilities catch known failures; these three lines catch the rest.
