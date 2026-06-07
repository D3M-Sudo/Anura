import json
from pathlib import Path

path = Path("docs/audit/bugs-observed.json")
data = json.loads(path.read_text())

# Add NEW-024: Potential Resource Leak in ClipboardService (Watchdog timer)
data["bugs_database"].append({
    "id": "NEW-024",
    "severity": "LOW",
    "confidence_score": 0.85,
    "personality_detecting": "Memory Surgeon",
    "personality_agreement": ["Variable Forensics Investigator"],
    "location": {
        "file": "anura/services/clipboard_service.py",
        "line": 286,
        "function": "_on_clipboard_timeout",
    },
    "chain_of_thought": {
        "description": (
            "Watchdog timer ID might persist if an operation completes exactly "
            "when the timer fires. Although _stop_timeout is called in callbacks, "
            "a race condition could leave a stale ID if not careful."
        ),
        "root_cause": "Asynchronous callback vs timeout firing race condition.",
        "impact": "Minor resource leak (GLib source IDs).",
    },
    "status": "OPEN",
    "pattern_matched": "UNUSED-CODE",
})

# Add pattern: ASYNC-TIMEOUT-RACE
data["learned_patterns"]["ASYNC-TIMEOUT-RACE"] = (
    "Race condition between async operation completion and its watchdog timeout firing."
)

path.write_text(json.dumps(data, indent=2))
