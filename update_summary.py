import json
from pathlib import Path

observed_path = Path("docs/audit/bugs-observed.json")
summary_path = Path("docs/audit/bugs-summary.md")
data = json.loads(observed_path.read_text())

bugs = data["bugs_database"]
fixed = len([b for b in bugs if b["status"] == "FIXED"])
open_bugs = [b for b in bugs if b["status"] == "OPEN"]
deferred = len([b for b in bugs if b["status"] == "DEFERRED"])
invalid = len([b for b in bugs if b["status"] == "INVALID"])

stats = data["progress_tracking"]
meta = data["session_metadata"]

summary = f"""# Bug Hunt Progress Report
Generated: {meta['last_checkpoint']}

## Statistics
- Files analyzed: {meta['analyzed_files']}/{meta['total_files']} ({stats['coverage_percentage']}%)
- Bugs Found: {len(bugs)} (Fixed: {fixed}, Open: {len(open_bugs)}, Deferred: {deferred}, Invalid: {invalid})
- Tools Executed: {', '.join(meta['tools_executed'])}

## Open Findings
"""

for b in open_bugs:
    loc = f"{b['location']['file']}:{b['location']['line']}"
    desc = f"{b['chain_of_thought']['description'][:100]}..."
    summary += f"| {b['id']} | {loc} | {b['severity']} | {desc} | {b['status']} |\n"

summary += (
    "\n## Recent Activity\n"
    "- Completed deep dive of core services.\n"
    "- Integrated static analysis findings from Mypy and Vulture.\n"
    "- Identified several low-severity type mismatches and potential resource leaks."
)

summary_path.write_text(summary)
