from __future__ import annotations

from collections import deque
from copy import deepcopy
from typing import Any, Callable


ALGORITHMS = {
    "FCFS": "First Come, First Served",
    "SJF": "Shortest Job First",
    "PRIORITY": "Priority Scheduling",
    "ROUND ROBIN": "Round Robin",
}


def _add_segment(segments: list[dict[str, Any]], process_id: str, start: int, end: int) -> None:
    if end <= start:
        return
    if segments and segments[-1]["process_id"] == process_id and segments[-1]["end"] == start:
        segments[-1]["end"] = end
    else:
        segments.append({"process_id": process_id, "start": start, "end": end})


def _non_preemptive(
    processes: list[dict[str, Any]],
    chooser: Callable[[list[dict[str, Any]]], dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    remaining = deepcopy(processes)
    segments: list[dict[str, Any]] = []
    completion: dict[str, int] = {}
    clock = 0
    while remaining:
        available = [item for item in remaining if item["arrival"] <= clock]
        if not available:
            next_arrival = min(item["arrival"] for item in remaining)
            _add_segment(segments, "IDLE", clock, next_arrival)
            clock = next_arrival
            available = [item for item in remaining if item["arrival"] <= clock]
        current = chooser(available)
        start = clock
        clock += current["burst"]
        _add_segment(segments, current["id"], start, clock)
        completion[current["id"]] = clock
        remaining.remove(current)
    return segments, completion


def _round_robin(
    processes: list[dict[str, Any]], quantum: int
) -> tuple[list[dict[str, Any]], dict[str, int], dict[str, int]]:
    ordered = sorted(processes, key=lambda item: (item["arrival"], item["_order"]))
    remaining = {item["id"]: item["burst"] for item in processes}
    completion: dict[str, int] = {}
    run_counts: dict[str, int] = {item["id"]: 0 for item in processes}
    ready: deque[dict[str, Any]] = deque()
    segments: list[dict[str, Any]] = []
    cursor = 0
    index = 0

    while index < len(ordered) or ready:
        if not ready and index < len(ordered) and cursor < ordered[index]["arrival"]:
            _add_segment(segments, "IDLE", cursor, ordered[index]["arrival"])
            cursor = ordered[index]["arrival"]
        while index < len(ordered) and ordered[index]["arrival"] <= cursor:
            ready.append(ordered[index])
            index += 1
        if not ready:
            continue
        current = ready.popleft()
        start = cursor
        duration = min(quantum, remaining[current["id"]])
        cursor += duration
        remaining[current["id"]] -= duration
        run_counts[current["id"]] += 1
        _add_segment(segments, current["id"], start, cursor)
        while index < len(ordered) and ordered[index]["arrival"] <= cursor:
            ready.append(ordered[index])
            index += 1
        if remaining[current["id"]] > 0:
            ready.append(current)
        else:
            completion[current["id"]] = cursor
    return segments, completion, run_counts


def simulate(
    raw_processes: list[dict[str, Any]], algorithm: str, time_quantum: int = 2
) -> dict[str, Any]:
    processes = []
    for order, process in enumerate(raw_processes):
        item = deepcopy(process)
        item["_order"] = order
        processes.append(item)

    if algorithm == "FCFS":
        segments, completion = _non_preemptive(
            processes, lambda available: min(available, key=lambda item: (item["arrival"], item["_order"]))
        )
        run_counts = {item["id"]: 1 for item in processes}
    elif algorithm == "SJF":
        segments, completion = _non_preemptive(
            processes,
            lambda available: min(
                available, key=lambda item: (item["burst"], item["arrival"], item["_order"])
            ),
        )
        run_counts = {item["id"]: 1 for item in processes}
    elif algorithm == "PRIORITY":
        segments, completion = _non_preemptive(
            processes,
            lambda available: min(
                available, key=lambda item: (item["priority"], item["arrival"], item["_order"])
            ),
        )
        run_counts = {item["id"]: 1 for item in processes}
    else:
        algorithm = "ROUND ROBIN"
        segments, completion, run_counts = _round_robin(processes, max(1, time_quantum))

    metrics = []
    for process in sorted(processes, key=lambda item: item["_order"]):
        finished_at = completion[process["id"]]
        turnaround = finished_at - process["arrival"]
        waiting = turnaround - process["burst"]
        slices = run_counts[process["id"]]
        lifecycle = ["New", "Ready", "Running"]
        if slices > 1:
            lifecycle.extend(["Ready", "Running"] * (slices - 1))
        lifecycle.append("Terminated")
        metrics.append(
            {
                "id": process["id"],
                "name": process["name"],
                "arrival": process["arrival"],
                "burst": process["burst"],
                "priority": process["priority"],
                "completion": finished_at,
                "waiting": waiting,
                "turnaround": turnaround,
                "runs": slices,
                "status": "Terminated",
                "status_class": "completed",
                "lifecycle": lifecycle,
            }
        )

    total_burst = sum(item["burst"] for item in processes)
    avg_waiting = sum(item["waiting"] for item in metrics) / len(metrics)
    avg_turnaround = sum(item["turnaround"] for item in metrics) / len(metrics)
    return {
        "algorithm": algorithm,
        "algorithm_name": ALGORITHMS[algorithm],
        "time_quantum": time_quantum if algorithm == "ROUND ROBIN" else None,
        "processes": processes,
        "segments": segments,
        "metrics": metrics,
        "avg_waiting": avg_waiting,
        "avg_turnaround": avg_turnaround,
        "total_burst": total_burst,
        "makespan": max(segment["end"] for segment in segments),
    }