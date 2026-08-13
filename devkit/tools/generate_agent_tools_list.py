"""从统一 Registry 生成 MCP Agent 实际可见的工具快照。"""
from __future__ import annotations

import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
RUNTIME_SCRIPTS = REPO_ROOT / "skills" / "cst-runtime-cli" / "scripts"


def main() -> None:
    sys.path.insert(0, str(RUNTIME_SCRIPTS))
    from cst_runtime.api import describe_tools

    records = []
    for tool in describe_tools():
        if tool.get("exposure") != "agent":
            continue
        risk = str(tool.get("risk", "read"))
        records.append(
            {
                "name": tool["name"],
                "description": tool.get("description", ""),
                "inputSchema": tool["input_schema"],
                "outputSchema": tool.get("output_schema"),
                "annotations": {
                    "readOnlyHint": risk == "read",
                    "destructiveHint": risk in {
                        "write",
                        "filesystem-write",
                        "session",
                        "process-control",
                        "long-running",
                    },
                },
                "exposure": "agent",
                "risk": risk,
            }
        )
    output = REPO_ROOT / "tools-list.json"
    output.write_text(
        json.dumps(records, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
