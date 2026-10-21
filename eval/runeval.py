#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
runeval.py -- held-out self-evaluation runner for a file-based AI assistant.

Why this exists
---------------
An assistant that edits its own rules drifts. The usual failure is not a
crash; it is a quiet regression -- "every check green" while the actual
task was silently wrong. The fix (borrowed from evaluator-gated evolution,
a la GEPA in DSPy): keep a small held-out suite of *behavioral* checks and
re-run it after every non-trivial rule change. A failing suite means:
fix it or revert it -- never push forward.

Two kinds of cases
------------------
Automatic cases (this script prints PASS/FAIL; exit code = number of
failures) plus a behavior checklist (things a script cannot judge; print
with --list and walk through by hand).

Usage
    python runeval.py config.json          # run all automatic cases
    python runeval.py --list config.json   # print the behavior checklist

The config file declares where your assistant lives: memory files, boot
check script, git repos, playbooks, skills dir, ledger script, and the
postmortem log. See examples/runeval.config.example.json.

Discipline
    Any FAIL: fix before committing. The commit message that changed the
    rule must carry the new score. Regression = fix or revert.
"""
import glob
import json
import os
import re
import subprocess
import sys

PY = sys.executable

CASES = []


def case(name):
    def deco(fn):
        CASES.append((name, fn))
        return fn
    return deco


def ok(good, detail=''):
    return ('PASS' if good else 'FAIL', detail)


class Cfg(object):
    """config.json wrapper"""
    def __init__(self, path):
        with open(path, encoding='utf-8') as fh:
            self.d = json.load(fh)

    def get(self, key, default=None):
        return self.d.get(key, default)


CFG = None


def _read(path):
    if path and os.path.exists(path):
        return open(path, encoding='utf-8', errors='replace').read()
    return ''


@case('memory mirror: two copies byte-identical')
def _mirror():
    a, b = CFG.get('memory_a', ''), CFG.get('memory_b', '')
    if not a or not b:
        return ok(False, 'memory_a/memory_b not configured')
    if not (os.path.exists(a) and os.path.exists(b)):
        return ok(False, 'mirror file missing')
    x = open(a, 'rb').read()
    y = open(b, 'rb').read()
    return ok(x == y, '%dB vs %dB' % (len(x), len(y)))


@case('boot gate: startup self-check free of failure markers')
def _gate():
    script = CFG.get('boot_gate_script', '')
    if not script:
        return ok(False, 'boot_gate_script not configured')
    if not os.path.exists(script):
        return ok(False, 'boot script missing')
    markers = CFG.get('failure_markers', ['FAIL'])
    try:
        p = subprocess.run([PY, script], capture_output=True, text=True,
                           timeout=180, encoding='utf-8', errors='replace')
    except Exception as e:  # noqa: BLE001
        return ok(False, 'runner error: %s' % str(e)[:60])
    out = (p.stdout or '') + (p.stderr or '')
    hits = [m for m in markers if m in out]
    if p.returncode != 0:
        return ok(False, 'rc=%d' % p.returncode)
    return ok(not hits, 'hit: ' + ','.join(hits) if hits else 'clean')


@case('anchor literals survive in memory')
def _anchors():
    anchors = CFG.get('anchors', [])
    if not anchors:
        return ok(False, 'no anchors configured')
    s = _read(CFG.get('memory_a', ''))
    miss = [k for k in anchors if k not in s]
    n = len(anchors)
    return ok(not miss, 'missing: ' + ','.join(miss) if miss else '%d/%d ok' % (n, n))


@case('rule numbering contiguous (no gaps)')
def _rules():
    pat = CFG.get('rule_number_regex', r'(?m)^(\d+)[\.\s]')
    s = _read(CFG.get('memory_a', ''))
    nums = [int(m.group(1)) for m in re.finditer(pat, s)]
    if not nums:
        return ok(False, 'no rule numbers parsed')
    missing = sorted(set(range(1, max(nums) + 1)) - set(nums))
    return ok(not missing, '%d rules' % len(nums) if not missing else 'gaps: %s' % missing)


@case('git repos: >= min commits and clean worktree')
def _git():
    repos = CFG.get('git_repos', [])
    if not repos:
        return ok(False, 'git_repos not configured')
    details, all_ok = [], True
    for repo in repos:
        tag = repo.get('name', repo.get('path', '?'))
        path = repo.get('path', '')
        n = subprocess.run(['git', '-C', path, 'rev-list', '--count', 'HEAD'],
                           capture_output=True, text=True)
        dirty = subprocess.run(['git', '-C', path, 'status', '--porcelain'],
                               capture_output=True, text=True).stdout.strip()
        cnt = int(n.stdout.strip()) if n.returncode == 0 and n.stdout.strip().isdigit() else 0
        good = cnt >= repo.get('min_commits', 1) and not dirty
        all_ok = all_ok and good
        details.append('%s:%d%s' % (tag, cnt, '+dirty' if dirty else ''))
    return ok(all_ok, ' '.join(details))


@case('playbooks: >= min count and non-trivial size')
def _playbooks():
    d = CFG.get('playbooks_dir', '')
    min_n = CFG.get('min_playbooks', 3)
    fs = [f for f in glob.glob(os.path.join(d, '*.md')) if os.path.getsize(f) > 100] if d else []
    return ok(len(fs) >= min_n, '%d found' % len(fs))


@case('skill count within red line')
def _skills():
    d = CFG.get('skills_dir', '')
    maxn = CFG.get('max_skills', 30)
    n = len([x for x in glob.glob(os.path.join(d, '*')) if os.path.isdir(x)]) if d else 0
    return ok(n <= maxn, '%d (red line %d)' % (n, maxn))


@case('gap ledger runnable (report produces output)')
def _ledger():
    script = CFG.get('ledger_script', '')
    if not script:
        return ok(False, 'ledger_script not configured')
    sub = CFG.get('ledger_report_cmd', 'report')
    try:
        p = subprocess.run([PY, script, sub], capture_output=True, text=True,
                           timeout=60, encoding='utf-8', errors='replace')
        return ok(p.returncode == 0 and bool(p.stdout.strip()), 'rc=%d' % p.returncode)
    except Exception as e:  # noqa: BLE001
        return ok(False, str(e)[:60])


@case('postmortems closed-loop: entries past threshold carry a hook')
def _hooks():
    path = CFG.get('postmortem_file', '')
    min_seq = CFG.get('postmortem_hook_since', 1)
    field = CFG.get('postmortem_hook_marker', 'Hooked to')
    if not path:
        return ok(False, 'postmortem_file not configured')
    if not os.path.exists(path):
        return ok(False, 'postmortem file missing')
    s = _read(path)
    blocks = re.split(r'(?m)^### ', s)[1:]
    checked, bare = 0, []
    for b in blocks:
        m = re.match(r'(\d+)[\.\、]', b)
        if not m or int(m.group(1)) < min_seq:
            continue
        checked += 1
        if field not in b:
            bare.append('#%s' % m.group(1))
    if checked == 0:
        return ok(False, 'no entries >= %d (format changed?)' % min_seq)
    return ok(not bare, '%d checked, bare: %s' % (checked, ','.join(bare)) if bare else '%d all hooked' % checked)


# Things a script cannot judge. Walk them by hand after every rule change;
# each one exists because the assistant actually failed this way once.
BEHAVIOR = [
    ('verify before reporting',
     'When asked for a todo/done list, check live state first (git log/status, automation registry). Roadmap docs are hints, never facts.',
     'git log --oneline -3 && git status --short'),
    ('change rules ceremonially',
     'Editing memory/persona/hook/tool rules: snapshot -> commit pre-change state -> edit -> verify -> commit post-change -> log. No hand-made .bak copies.',
     'see docs/governance-playbook.md'),
    ('validate before delivery',
     'Never hand over HTML/scripts/reports that were not executed or statically checked at least once.',
     'run the script / open the file'),
    ('prove redundancy before deleting',
     'Before removing any file or tool: confirm identical content exists in git history, or usage logs show zero references.',
     'git log --all --oneline -- <file>'),
    ('no side-copy backups',
     'Pre-change state lives in git commits, never in .bak files that drift and sneak back into the workflow.',
     'git show <rev>:<file>'),
]


def main():
    global CFG
    argv = [a for a in sys.argv[1:]]
    if '--list' in argv:
        print('Behavior checklist (walk by hand after every rule change):')
        for i, (t, d, how) in enumerate(BEHAVIOR, 1):
            print('  B%d. %s -- %s | check: %s' % (i, t, d, how))
        return 0
    cfg_path = next((a for a in argv if not a.startswith('--')), None)
    if not cfg_path:
        print('usage: python runeval.py <config.json> [--list]')
        return 2
    CFG = Cfg(cfg_path)
    fails = 0
    print('=' * 62)
    print('held-out self-eval -- run after every non-trivial rule change')
    print('=' * 62)
    for name, fn in CASES:
        try:
            st, detail = fn()
        except Exception as e:  # noqa: BLE001
            st, detail = 'FAIL', 'runner error: %s' % str(e)[:60]
        if st == 'FAIL':
            fails += 1
        line = '  [%s] %s' % (st, name)
        if detail:
            line += ' -- %s' % detail
        print(line)
    print('=' * 62)
    print('automatic %d/%d pass; behavior checklist %d items (--list)'
          % (len(CASES) - fails, len(CASES), len(BEHAVIOR)))
    if fails:
        print('FAIL present: fix before commit, or revert. Never move forward sick.')
    return fails


if __name__ == '__main__':
    sys.exit(main())
