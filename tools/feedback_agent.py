#!/usr/bin/env python3
"""
EstradaBot Feedback Agent — Automated Triage & Action Drafting

Reads fetched feedback (from feedback/inbox.json) and produces a structured
triage report with classification, codebase mapping, and draft action plans.

This is the foundation for autonomous feedback processing. Currently it
generates structured output for a human + Claude Code session to act on.
Future: can be called by an autonomous agent loop.

Usage:
    python tools/feedback_agent.py triage                # Triage all entries in inbox
    python tools/feedback_agent.py triage --index 3      # Triage a specific entry
    python tools/feedback_agent.py summary               # High-level actionable summary

Output:
    feedback/triage.md    — Triage report with actions for each entry
    feedback/triage.json  — Structured triage data for programmatic use
"""

import json
import os
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

FEEDBACK_DIR = REPO_ROOT / 'feedback'
INBOX_JSON = FEEDBACK_DIR / 'inbox.json'
TRIAGE_MD = FEEDBACK_DIR / 'triage.md'
TRIAGE_JSON = FEEDBACK_DIR / 'triage.json'

# ── Codebase mapping ──────────────────────────────────────────────
# Maps feedback categories and pages to relevant source locations.
# The agent uses this to suggest where to look when acting on feedback.

PAGE_MAP = {
    'Dashboard': {
        'template': 'backend/templates/index.html',
        'description': 'Main dashboard with schedule overview and stats',
    },
    'Upload': {
        'template': 'backend/templates/upload.html',
        'routes': 'backend/app.py (upload routes)',
        'parsers': 'backend/parsers/',
        'description': 'File upload page — parsers and validation',
    },
    'Schedule': {
        'template': 'backend/templates/schedule.html',
        'engine': 'backend/algorithms/des_scheduler.py',
        'description': 'Schedule view and DES engine output',
    },
    'Reports': {
        'template': 'backend/templates/reports.html',
        'exporters': 'backend/exporters/',
        'description': 'Report generation and Excel export',
    },
    'Simulation': {
        'template': 'backend/templates/simulation.html',
        'engine': 'backend/algorithms/des_scheduler.py',
        'description': 'Factory simulation and scenario analysis',
    },
    'Planner': {
        'template': 'backend/templates/planner.html',
        'description': 'Planner workflow — multi-step guided process',
    },
}

CATEGORY_MAP = {
    'Bug Report': {
        'action_type': 'fix',
        'priority_boost': 1,  # Bugs get priority attention
        'description': 'Something is broken — identify root cause and fix',
    },
    'Feature Request': {
        'action_type': 'plan',
        'priority_boost': 0,
        'description': 'New capability requested — evaluate scope and plan',
    },
    'Data Issue': {
        'action_type': 'investigate',
        'priority_boost': 1,
        'locations': ['backend/parsers/', 'backend/data_loader.py', 'backend/validators.py'],
        'description': 'Data parsing or validation problem — check parsers',
    },
    'UI/UX Improvement': {
        'action_type': 'design',
        'priority_boost': 0,
        'locations': ['backend/templates/', 'backend/static/'],
        'description': 'Visual or interaction improvement — update templates/CSS',
    },
    'Example File': {
        'action_type': 'review',
        'priority_boost': 0,
        'description': 'Sample data provided for analysis or testing',
    },
    'Other': {
        'action_type': 'review',
        'priority_boost': 0,
        'description': 'General feedback — review and classify manually',
    },
}

# Priority scoring: higher = more urgent
PRIORITY_SCORES = {'High': 3, 'Medium': 2, 'Low': 1}


def load_inbox():
    """Load the fetched feedback inbox."""
    if not INBOX_JSON.exists():
        print("[Agent] No inbox found. Run 'python tools/feedback_pipeline.py fetch' first.")
        sys.exit(1)

    with open(INBOX_JSON) as f:
        return json.load(f)


def triage_entry(entry: dict) -> dict:
    """Triage a single feedback entry. Returns structured triage result."""
    category = entry.get('category', 'Other')
    priority = entry.get('priority', 'Medium')
    page = entry.get('page', '')
    message = entry.get('message', '')

    cat_info = CATEGORY_MAP.get(category, CATEGORY_MAP['Other'])
    page_info = PAGE_MAP.get(page, {})

    # Compute urgency score
    base_score = PRIORITY_SCORES.get(priority, 2)
    urgency = base_score + cat_info.get('priority_boost', 0)

    # Determine relevant code locations
    locations = []
    if page_info:
        if 'template' in page_info:
            locations.append(page_info['template'])
        for key in ('routes', 'engine', 'parsers', 'exporters'):
            if key in page_info:
                locations.append(page_info[key])
    if 'locations' in cat_info:
        locations.extend(cat_info['locations'])

    # If no page specified, infer from message keywords
    if not locations:
        locations = _infer_locations(message, category)

    # Build action plan
    action = {
        'type': cat_info['action_type'],
        'description': cat_info['description'],
        'suggested_locations': locations,
    }

    # Keyword analysis for additional context
    keywords = _extract_keywords(message)

    return {
        'pipeline_index': entry.get('pipeline_index'),
        'urgency_score': urgency,
        'action': action,
        'keywords': keywords,
        'page_context': page_info.get('description', ''),
        'original': {
            'category': category,
            'priority': priority,
            'page': page,
            'message': message,
            'username': entry.get('username', ''),
            'submitted_at': entry.get('submitted_at', ''),
            'status': entry.get('status', ''),
            'has_attachment': bool(entry.get('attachment')),
        },
    }


def _infer_locations(message: str, category: str) -> list:
    """Infer relevant code locations from message content."""
    msg_lower = message.lower()
    locations = []

    keyword_map = {
        'backend/algorithms/des_scheduler.py': [
            'schedule', 'scheduling', 'simulation', 'des', 'shift',
            'capacity', 'bottleneck', 'throughput', 'scenario',
        ],
        'backend/parsers/': [
            'upload', 'parse', 'import', 'excel', 'file', 'column',
            'sales order', 'hot list', 'dispatch',
        ],
        'backend/exporters/': [
            'export', 'report', 'download', 'excel output',
        ],
        'backend/templates/': [
            'page', 'display', 'layout', 'button', 'table', 'chart',
            'ui', 'interface', 'screen',
        ],
        'backend/app.py': [
            'login', 'logout', 'permission', 'route', 'api', 'error',
            'crash', 'server',
        ],
    }

    for location, keywords in keyword_map.items():
        if any(kw in msg_lower for kw in keywords):
            locations.append(location)

    return locations if locations else ['backend/app.py']


def _extract_keywords(message: str) -> list:
    """Extract notable keywords from feedback message."""
    important_words = {
        'error', 'crash', 'broken', 'slow', 'wrong', 'missing',
        'add', 'need', 'want', 'should', 'could', 'please',
        'schedule', 'upload', 'report', 'export', 'simulation',
        'shift', 'capacity', 'order', 'priority', 'date',
        'planner', 'dashboard', 'login', 'permission',
    }

    words = message.lower().split()
    found = [w for w in words if w.strip('.,!?;:()') in important_words]
    return list(dict.fromkeys(found))[:10]  # Deduplicate, limit to 10


def triage(args):
    """Run triage on inbox entries."""
    data = load_inbox()
    entries = data.get('entries', [])

    if args.index is not None:
        # Triage a single entry
        matches = [e for e in entries if e.get('pipeline_index') == args.index]
        if not matches:
            print(f"[Agent] No entry with pipeline_index {args.index} in inbox.")
            sys.exit(1)
        entries = matches

    print(f"[Agent] Triaging {len(entries)} entries...")

    results = []
    for entry in entries:
        result = triage_entry(entry)
        results.append(result)

    # Sort by urgency (highest first)
    results.sort(key=lambda r: r['urgency_score'], reverse=True)

    # Write outputs
    FEEDBACK_DIR.mkdir(exist_ok=True)

    # JSON output
    triage_output = {
        'triaged_at': datetime.now().isoformat(),
        'entry_count': len(results),
        'results': results,
    }
    with open(TRIAGE_JSON, 'w') as f:
        json.dump(triage_output, f, indent=2, default=str)
    print(f"[Agent] Wrote {TRIAGE_JSON}")

    # Markdown output
    md = _generate_triage_md(results)
    with open(TRIAGE_MD, 'w') as f:
        f.write(md)
    print(f"[Agent] Wrote {TRIAGE_MD}")

    # Print top items
    print(f"\n[Agent] Top priority items:")
    for r in results[:5]:
        idx = r.get('pipeline_index', '?')
        score = r['urgency_score']
        action = r['action']['type']
        msg = r['original']['message'][:50]
        print(f"  #{idx} (urgency:{score}) [{action}] {msg}...")


def _generate_triage_md(results: list) -> str:
    """Generate markdown triage report."""
    now = datetime.now().strftime('%Y-%m-%d %H:%M')

    lines = [
        "# EstradaBot Feedback Triage Report",
        "",
        f"**Generated:** {now}  ",
        f"**Entries triaged:** {len(results)}",
        "",
        "---",
        "",
    ]

    # Urgency distribution
    urgency_counts = Counter(r['urgency_score'] for r in results)
    lines.append("## Urgency Distribution")
    lines.append("")
    lines.append("| Score | Count | Meaning |")
    lines.append("|-------|-------|---------|")
    for score in sorted(urgency_counts.keys(), reverse=True):
        meaning = {4: 'Critical', 3: 'High', 2: 'Normal', 1: 'Low'}.get(score, 'Unknown')
        lines.append(f"| {score} | {urgency_counts[score]} | {meaning} |")
    lines.append("")

    # Action type distribution
    action_counts = Counter(r['action']['type'] for r in results)
    lines.append("## Actions Needed")
    lines.append("")
    lines.append("| Action | Count |")
    lines.append("|--------|-------|")
    for action, count in action_counts.most_common():
        lines.append(f"| {action} | {count} |")
    lines.append("")

    lines.append("---")
    lines.append("")

    # Individual entries
    lines.append("## Triage Details")
    lines.append("")

    for r in results:
        idx = r.get('pipeline_index', '?')
        score = r['urgency_score']
        orig = r['original']
        action = r['action']

        urgency_label = {4: 'CRITICAL', 3: 'HIGH', 2: 'NORMAL', 1: 'LOW'}.get(score, '?')

        lines.append(f"### Entry #{idx} — Urgency: {urgency_label} ({score})")
        lines.append("")
        lines.append(f"- **Category:** {orig['category']}")
        lines.append(f"- **Priority:** {orig['priority']}")
        lines.append(f"- **User:** {orig['username']} ({orig['submitted_at'][:10]})")
        lines.append(f"- **Admin status:** {orig['status']}")
        if orig.get('page'):
            lines.append(f"- **Page:** {orig['page']}")
        if r.get('page_context'):
            lines.append(f"- **Context:** {r['page_context']}")
        lines.append("")
        lines.append(f"> {orig['message']}")
        lines.append("")

        if orig.get('has_attachment'):
            lines.append(f"*Has file attachment*")
            lines.append("")

        lines.append(f"**Action:** `{action['type']}` — {action['description']}")
        lines.append("")

        if action.get('suggested_locations'):
            lines.append("**Look at:**")
            for loc in action['suggested_locations']:
                lines.append(f"- `{loc}`")
            lines.append("")

        if r.get('keywords'):
            lines.append(f"**Keywords:** {', '.join(r['keywords'])}")
            lines.append("")

        lines.append("---")
        lines.append("")

    # Agent instructions section
    lines.append("## Agent Processing Instructions")
    lines.append("")
    lines.append("For each triaged entry above, the recommended workflow is:")
    lines.append("")
    lines.append("1. **Review** the entry and suggested code locations")
    lines.append("2. **Investigate** the relevant files")
    lines.append("3. **Draft** a fix, plan, or response")
    lines.append("4. **Create** a GitHub issue if warranted: "
                 "`python tools/feedback_pipeline.py create-issue <index>`")
    lines.append("5. **Mark** as actioned: "
                 "`python tools/feedback_pipeline.py mark <index> actioned`")
    lines.append("")

    return '\n'.join(lines)


def summary(args):
    """Print a high-level actionable summary of the inbox."""
    data = load_inbox()
    entries = data.get('entries', [])

    if not entries:
        print("[Agent] Inbox is empty.")
        return

    results = [triage_entry(e) for e in entries]
    results.sort(key=lambda r: r['urgency_score'], reverse=True)

    # Counts
    action_counts = Counter(r['action']['type'] for r in results)
    urgency_high = sum(1 for r in results if r['urgency_score'] >= 3)

    print(f"\n{'='*55}")
    print(f"  Feedback Agent Summary — {len(results)} entries")
    print(f"{'='*55}")
    print(f"\n  High urgency items:  {urgency_high}")
    print(f"  Actions breakdown:")
    for action, count in action_counts.most_common():
        print(f"    {action:<15} {count}")

    # All unique code locations
    all_locations = set()
    for r in results:
        all_locations.update(r['action'].get('suggested_locations', []))

    print(f"\n  Code areas involved:")
    for loc in sorted(all_locations):
        print(f"    {loc}")

    print(f"\n  Quick actions:")
    print(f"    triage all:    python tools/feedback_agent.py triage")
    print(f"    create issues: python tools/feedback_pipeline.py create-issues")
    print()


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='EstradaBot Feedback Agent — Triage & Action Drafting',
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest='command', help='Agent commands')

    # triage command
    triage_parser = subparsers.add_parser('triage',
                                           help='Triage inbox entries with classification and action plans')
    triage_parser.add_argument('--index', type=int, default=None,
                               help='Triage a specific entry by pipeline_index')
    triage_parser.set_defaults(func=triage)

    # summary command
    summary_parser = subparsers.add_parser('summary',
                                            help='High-level actionable summary')
    summary_parser.set_defaults(func=summary)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)

    args.func(args)


if __name__ == '__main__':
    main()
