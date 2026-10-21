#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
supply_chain_check.py -- supply-chain hygiene for an AI assistant's gear.

Background (public incidents, 2026): typosquatted MCP servers, prompt-
injection hijacks of review agents, arbitrary file-write flaws -- and the
dominant rug-pull pattern: a package that is benign at install time and
turns malicious in a later update. For an assistant that installs skills,
MCP servers and local tools on the user's behalf, "installed once,
forgotten forever" is not an option.

Three checks, report-only (warnings never change the exit code, but every
check must print an explicit line -- a silent pass is a bug):

    1. MCP servers pinned: npx/uvx launch commands must carry an exact
       version, never @latest.
    2. Skill count red line: unvetted skill accumulation degrades routing
       quality (see arXiv 2608.05810 on skill accumulation).
    3. Auto-upgrade scan: local tool scripts must not self-upgrade
       (pip --upgrade / npm -g / pipx upgrade are red flags).

Usage
    python supply_chain_check.py \
        --mcp ~/.your-assistant/mcp.json \
        --skills-dir ~/.your-assistant/skills \
        --tools-dir ./tools
"""
import argparse
import glob
import io
import json
import os
import re
import sys

AUTO_UPGRADE_PAT = re.compile(
    r'pip3?\s+install\s+(--upgrade|-U)|npm\s+install\s+-g|pipx\s+upgrade')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--mcp', default='',
                    help='path to mcp.json (check skipped if empty/missing)')
    ap.add_argument('--skills-dir', default='',
                    help='directory of installed skills')
    ap.add_argument('--tools-dir', default='',
                    help='directory of local tool scripts (*.py)')
    ap.add_argument('--skill-redline', type=int, default=30)
    args = ap.parse_args()

    warnings = 0
    print('=' * 62)
    print('supply-chain check -- report-only, warnings never fail the build')
    print('=' * 62)

    # 1. MCP servers pinned
    if not args.mcp:
        print('  [i] no --mcp given: skipped (new servers still need review)')
    elif not os.path.exists(args.mcp):
        print('  [i] %s not found: skipped' % args.mcp)
    else:
        try:
            with open(args.mcp, encoding='utf-8') as fh:
                cfg = json.load(fh)
            servers = cfg.get('mcpServers', {})
            print('  MCP servers configured: %d' % len(servers))
            for name, spec in servers.items():
                if not isinstance(spec, dict):
                    print('  [!!] %s: spec is not an object -- review by hand' % name)
                    warnings += 1
                    continue
                cmd = ' '.join([str(spec.get('command', ''))]
                               + [str(a) for a in spec.get('args', [])])
                if 'npx' in cmd or 'uvx' in cmd:
                    if '@latest' in cmd or not re.search(r'@[0-9]+\.[0-9]+', cmd):
                        print('  [!!] %s: unpinned (%s) -- an upgrade is a governance event' % (name, cmd[:80]))
                        warnings += 1
                for k in ('env', 'headers'):
                    for var in (spec.get(k) or {}):
                        if re.search(r'(token|key|secret|password)', str(var), re.I):
                            print('  [i] %s: %s carries "%s" -- confirm rotation policy' % (name, k, var))
        except Exception as e:  # noqa: BLE001
            print('  [!!] mcp.json parse failed: %s -- explicit error, never a silent zero' % e)
            warnings += 1

    # 2. skill count red line
    if args.skills_dir and os.path.isdir(args.skills_dir):
        n = len([d for d in glob.glob(os.path.join(args.skills_dir, '*'))
                 if os.path.isdir(d)])
        over = n > args.skill_redline
        print('  [%s] skills: %d (red line %d)' %
              ('!! over red line' if over else 'OK', n, args.skill_redline))
        if over:
            warnings += 1
    else:
        print('  [i] skills dir not given/found: skipped')

    # 3. auto-upgrade scan (skip this file: it contains the pattern words)
    me = os.path.basename(os.path.abspath(__file__))
    hits = []
    if args.tools_dir and os.path.isdir(args.tools_dir):
        for f in glob.glob(os.path.join(args.tools_dir, '*.py')):
            if os.path.basename(f) == me:
                continue
            try:
                for i, ln in enumerate(io.open(f, encoding='utf-8', errors='replace'), 1):
                    if AUTO_UPGRADE_PAT.search(ln):
                        hits.append('%s:%d: %s' % (os.path.basename(f), i, ln.strip()[:80]))
            except Exception:  # noqa: BLE001
                continue
    if hits:
        print('  [!!] %d auto-upgrade pattern(s) in tools dir (verify code vs comment):' % len(hits))
        for h in hits[:6]:
            print('      %s' % h)
        warnings += len(hits)
    else:
        print('  [OK] no auto-upgrade patterns in tools dir')

    print('-' * 62)
    print('done: %d warning(s). Report-only by design; triage by hand.' % warnings)
    return 0


if __name__ == '__main__':
    sys.exit(main())
