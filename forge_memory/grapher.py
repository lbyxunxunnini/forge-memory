"""图谱写入：nodes.jsonl、edges.jsonl、graph.md、mermaid.md。"""

from __future__ import annotations

import json
from pathlib import Path

from .renderer import render_mermaid
from .utils import stable_id


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def render_graph(scan_result: dict) -> str:
    lines = [
        "# 知识图谱",
        "",
        f"节点数：{len(scan_result['nodes'])}",
        f"关系数：{len(scan_result['edges'])}",
        "",
        "## 主要模块",
        "",
    ]
    for module, files in scan_result["modules"].items():
        lines.append(
            f"- `{stable_id('mod', module, module)}` `{module}`：{len(files)} 个文件"
        )
    lines.extend(
        [
            "",
            "## 说明",
            "",
            "- Graph JSONL 是机器可读的主数据源。",
            "- Mermaid 图谱故意保持紧凑，只表达主干关系。",
        ]
    )
    return "\n".join(lines) + "\n"


def write_graph(root: Path, scan_result: dict, branch_dir: Path | None = None) -> None:
    """写出 graph/nodes.jsonl、graph/edges.jsonl、graph/graph.md、graph/mermaid.md。"""
    graph_dir = (branch_dir or root / ".project-context") / "graph"
    graph_dir.mkdir(parents=True, exist_ok=True)

    write_jsonl(graph_dir / "nodes.jsonl", scan_result["nodes"])
    write_jsonl(graph_dir / "edges.jsonl", scan_result["edges"])

    (graph_dir / "graph.md").write_text(render_graph(scan_result), encoding="utf-8")
    (graph_dir / "mermaid.md").write_text(render_mermaid(scan_result), encoding="utf-8")
