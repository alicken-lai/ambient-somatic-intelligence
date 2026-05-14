"""
DAG Visualizer — Debug output and rendering for TaskGraph instances.

Provides multiple output formats for inspecting task graph structure and
execution state:
  - ASCII art:    Terminal-friendly tree/dag rendering
  - Mermaid:      Copy-paste into docs or GitHub for rendered diagrams
  - Status table: Tabular summary of all tasks and their states

Usage:
    from runtime.task_graph.visualizer import DAGVisualizer
    viz = DAGVisualizer()
    print(viz.to_ascii(graph))
    print(viz.to_mermaid(graph))
    print(viz.to_status_table(graph))
"""

from __future__ import annotations

from typing import Any

from runtime.task_graph.dag import TaskGraph, TaskStatus


_STATUS_SYMBOLS = {
    TaskStatus.PENDING:   "[ ]",
    TaskStatus.BLOCKED:   "[B]",
    TaskStatus.READY:     "[R]",
    TaskStatus.RUNNING:   "[>]",
    TaskStatus.COMPLETED: "[v]",
    TaskStatus.FAILED:    "[X]",
    TaskStatus.CANCELLED: "[-]",
    TaskStatus.SKIPPED:   "[~]",
}

_MERMAID_STYLES = {
    TaskStatus.COMPLETED: "fill:#2d6a2d,color:#fff",
    TaskStatus.FAILED:    "fill:#8b1a1a,color:#fff",
    TaskStatus.RUNNING:   "fill:#1a4a8b,color:#fff",
    TaskStatus.SKIPPED:   "fill:#555,color:#aaa",
    TaskStatus.CANCELLED: "fill:#555,color:#aaa",
    TaskStatus.PENDING:   "fill:#333,color:#ccc",
    TaskStatus.BLOCKED:   "fill:#8b6914,color:#fff",
    TaskStatus.READY:     "fill:#1a6a6a,color:#fff",
}


class DAGVisualizer:
    """
    Renders a TaskGraph in various human-readable formats.

    All methods are stateless — they take a graph and return a string.
    """

    def to_ascii(self, graph: TaskGraph) -> str:
        """
        Render the DAG as ASCII art showing stages and dependencies.

        Example output:
            === deploy-feature ===
            Stage 0: [v] schema (migrate_db) 120.5ms
            Stage 1: [v] backend (deploy_backend) 340.2ms
                     [v] frontend (deploy_frontend) 280.1ms
            Stage 2: [>] tests (run_e2e) ...
        """
        lines: list[str] = []
        lines.append(f"=== {graph.name} (id: {graph.id}) ===")
        lines.append("")

        try:
            stages = graph.parallel_stages()
        except RuntimeError:
            lines.append("ERROR: Graph contains a cycle, cannot render stages")
            return "\n".join(lines)

        for stage_idx, stage_tasks in enumerate(stages):
            for i, task_id in enumerate(stage_tasks):
                node = graph.nodes[task_id]
                symbol = _STATUS_SYMBOLS.get(node.status, "[?]")

                duration_str = ""
                if node.duration_ms is not None:
                    duration_str = f" {node.duration_ms:.1f}ms"
                elif node.status == TaskStatus.RUNNING:
                    duration_str = " ..."

                error_str = ""
                if node.error and node.status in (TaskStatus.FAILED, TaskStatus.SKIPPED):
                    short_err = node.error[:60]
                    if len(node.error) > 60:
                        short_err += "..."
                    error_str = f'  err="{short_err}"'

                prefix = f"Stage {stage_idx}: " if i == 0 else "          "
                handler_info = f"({node.handler})"

                lines.append(
                    f"{prefix}{symbol} {node.name} {handler_info}"
                    f"{duration_str}{error_str}"
                )

            deps_in_stage = []
            for task_id in stage_tasks:
                for dep_id in graph.get_dependencies(task_id):
                    deps_in_stage.append(f"{dep_id} -> {task_id}")

            if deps_in_stage:
                lines.append(f"          deps: {', '.join(deps_in_stage)}")

            lines.append("")

        progress = graph.progress
        lines.append(
            f"Progress: {progress['done']}/{progress['total']} "
            f"({progress['progress_pct']}%)"
        )

        status_parts = []
        for status_name, count in sorted(progress["by_status"].items()):
            if count > 0:
                status_parts.append(f"{status_name}={count}")
        if status_parts:
            lines.append(f"Status:   {', '.join(status_parts)}")

        return "\n".join(lines)

    def to_mermaid(self, graph: TaskGraph) -> str:
        """
        Render the DAG as a Mermaid flowchart diagram.

        Output can be pasted into GitHub markdown or Mermaid Live Editor.
        """
        lines: list[str] = []
        lines.append("```mermaid")
        lines.append(f"graph TD")

        for task_id, node in graph.nodes.items():
            label = f"{node.name}\\n{node.status.value}"
            if node.duration_ms is not None:
                label += f"\\n{node.duration_ms:.0f}ms"
            safe_id = task_id.replace("-", "_").replace(" ", "_")
            lines.append(f"    {safe_id}[\"{label}\"]")

        lines.append("")

        for edge in graph.edges:
            src = edge.source.replace("-", "_").replace(" ", "_")
            tgt = edge.target.replace("-", "_").replace(" ", "_")
            if edge.condition == "success":
                lines.append(f"    {src} --> {tgt}")
            elif edge.condition == "failure":
                lines.append(f"    {src} -.->|on fail| {tgt}")
            else:
                lines.append(f"    {src} -.->|any| {tgt}")

        lines.append("")

        for task_id, node in graph.nodes.items():
            style = _MERMAID_STYLES.get(node.status)
            if style:
                safe_id = task_id.replace("-", "_").replace(" ", "_")
                lines.append(f"    style {safe_id} {style}")

        lines.append("```")
        return "\n".join(lines)

    def to_status_table(self, graph: TaskGraph) -> str:
        """
        Render a tabular summary of all tasks.

        Columns: ID, Name, Status, Handler, Duration, Attempts, Error
        """
        headers = ["ID", "Name", "Status", "Handler", "Duration", "Attempts", "Error"]

        rows: list[list[str]] = []
        for task_id in graph.topological_order():
            node = graph.nodes[task_id]

            duration = ""
            if node.duration_ms is not None:
                duration = f"{node.duration_ms:.1f}ms"
            elif node.status == TaskStatus.RUNNING:
                duration = "running..."

            error = ""
            if node.error:
                error = node.error[:50]
                if len(node.error) > 50:
                    error += "..."

            deps = graph.get_dependencies(task_id)
            dep_str = ",".join(deps) if deps else "-"

            rows.append([
                task_id,
                node.name,
                node.status.value,
                node.handler,
                duration,
                str(node.attempts),
                error,
            ])

        col_widths = [len(h) for h in headers]
        for row in rows:
            for i, cell in enumerate(row):
                col_widths[i] = max(col_widths[i], len(cell))

        def _format_row(cells: list[str]) -> str:
            parts = []
            for i, cell in enumerate(cells):
                parts.append(cell.ljust(col_widths[i]))
            return " | ".join(parts)

        lines: list[str] = []
        lines.append(f"Task Graph: {graph.name} (id: {graph.id})")
        lines.append("")
        lines.append(_format_row(headers))
        lines.append("-+-".join("-" * w for w in col_widths))

        for row in rows:
            lines.append(_format_row(row))

        lines.append("")
        progress = graph.progress
        lines.append(
            f"Total: {progress['total']} | "
            f"Done: {progress['done']} | "
            f"Progress: {progress['progress_pct']}%"
        )

        return "\n".join(lines)

    def to_json(self, graph: TaskGraph) -> dict[str, Any]:
        """
        Structured JSON representation for programmatic consumption.

        Includes stages, dependency edges, and per-node status details.
        """
        stages = graph.parallel_stages()

        nodes_info = []
        for task_id in graph.topological_order():
            node = graph.nodes[task_id]
            nodes_info.append({
                "id": task_id,
                "name": node.name,
                "handler": node.handler,
                "status": node.status.value,
                "duration_ms": node.duration_ms,
                "attempts": node.attempts,
                "error": node.error,
                "dependencies": graph.get_dependencies(task_id),
                "dependents": graph.get_dependents(task_id),
            })

        return {
            "graph_id": graph.id,
            "graph_name": graph.name,
            "stages": stages,
            "stage_count": len(stages),
            "nodes": nodes_info,
            "edges": [
                {
                    "source": e.source,
                    "target": e.target,
                    "condition": e.condition,
                }
                for e in graph.edges
            ],
            "progress": graph.progress,
        }
