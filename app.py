from __future__ import annotations

import json
import os
from typing import Any

from flask import (
    Flask,
    flash,
    get_flashed_messages,
    redirect,
    render_template,
    request,
    url_for,
)

from database import (
    get_simulation_detail,
    get_simulations,
    init_database,
    save_simulation,
)
from scheduler import ALGORITHMS, simulate


app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = os.environ.get("SESSION_SECRET", "process-simulator-development-key")
app.config["TEMPLATES_AUTO_RELOAD"] = True

init_database()


def sample_processes() -> list[dict[str, Any]]:
    return [
        {"id": "P1", "name": "Compiler", "arrival": 0, "burst": 7, "priority": 2},
        {"id": "P2", "name": "Browser", "arrival": 1, "burst": 4, "priority": 1},
        {"id": "P3", "name": "Database", "arrival": 2, "burst": 5, "priority": 3},
        {"id": "P4", "name": "Editor", "arrival": 4, "burst": 2, "priority": 2},
    ]


def parse_processes(form: Any) -> list[dict[str, Any]]:
    raw_json = form.get("processes", "").strip()
    if raw_json:
        try:
            payload = json.loads(raw_json)
            if isinstance(payload, list):
                return normalize_processes(payload)
        except (TypeError, ValueError):
            pass

    ids = form.getlist("process_id[]") or form.getlist("process_id")
    names = form.getlist("process_name[]") or form.getlist("process_name")
    arrivals = form.getlist("arrival_time[]") or form.getlist("arrival_time")
    bursts = form.getlist("burst_time[]") or form.getlist("burst_time")
    priorities = form.getlist("priority[]") or form.getlist("priority")

    processes = []
    for index, process_id in enumerate(ids):
        try:
            processes.append(
                {
                    "id": process_id,
                    "name": names[index] if index < len(names) else process_id,
                    "arrival": arrivals[index] if index < len(arrivals) else 0,
                    "burst": bursts[index] if index < len(bursts) else 1,
                    "priority": priorities[index] if index < len(priorities) else 1,
                }
            )
        except (IndexError, TypeError):
            continue
    return normalize_processes(processes)


def normalize_processes(processes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized = []
    seen_ids: set[str] = set()
    for index, process in enumerate(processes):
        process_id = str(process.get("id", "")).strip() or f"P{index + 1}"
        if process_id in seen_ids:
            process_id = f"{process_id}-{index + 1}"
        seen_ids.add(process_id)
        try:
            arrival = max(0, int(process.get("arrival", 0)))
            burst = int(process.get("burst", 0))
            priority = int(process.get("priority", 1))
        except (TypeError, ValueError):
            continue
        if burst <= 0:
            continue
        normalized.append(
            {
                "id": process_id,
                "name": str(process.get("name", "")).strip() or process_id,
                "arrival": arrival,
                "burst": burst,
                "priority": priority,
            }
        )
    return normalized


@app.context_processor
def inject_navigation() -> dict[str, Any]:
    return {
        "algorithms": ALGORITHMS,
        "flashes": get_flashed_messages(with_categories=True),
    }


def dashboard_view(
    processes: list[dict[str, Any]],
    selected_algorithm: str = "FCFS",
    time_quantum: int = 2,
    result: dict[str, Any] | None = None,
    simulations: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    result = result or {}
    segments = []
    for segment in result.get("segments", []):
        enriched = dict(segment)
        enriched["duration"] = segment["end"] - segment["start"]
        enriched["width"] = enriched["duration"]
        segments.append(enriched)

    metrics = result.get("metrics", [])
    makespan = result.get("makespan", 0)
    total_burst = result.get("total_burst", 0)
    response_times = []
    for metric in metrics:
        first_run = next(
            (
                segment["start"]
                for segment in segments
                if segment["process_id"] == metric["id"]
            ),
            metric["arrival"],
        )
        response_times.append(first_run - metric["arrival"])

    return {
        "processes": processes,
        "selected_algorithm": selected_algorithm,
        "quantum": time_quantum,
        "result": result,
        "execution_segments": segments,
        "process_states": metrics,
        "metrics": {
            "average_waiting_time": f"{result['avg_waiting']:.2f}" if result else "—",
            "average_turnaround_time": f"{result['avg_turnaround']:.2f}" if result else "—",
            "average_response_time": f"{sum(response_times) / len(response_times):.2f}"
            if response_times
            else "—",
            "cpu_utilization": f"{(total_burst / makespan) * 100:.1f}"
            if makespan
            else "—",
            "throughput": f"{len(metrics) / makespan:.2f}" if makespan else "—",
        },
        "timeline_end": makespan or "—",
        "timeline_ticks": list(range(0, makespan + 1, max(1, makespan // 5)))
        if makespan
        else [],
        "history": simulations if simulations is not None else get_simulations(limit=5),
    }


@app.get("/", endpoint="index")
def home():
    return render_template("index.html", **dashboard_view(sample_processes()))


@app.post("/simulate", endpoint="simulate")
def run_simulation():
    processes = parse_processes(request.form)
    algorithm_value = request.form.get("algorithm", "FCFS").strip().lower()
    algorithm = algorithm_value.replace("_", " ").upper()
    try:
        time_quantum = max(
            1, int(request.form.get("time_quantum", request.form.get("quantum", "2")))
        )
    except ValueError:
        time_quantum = 2

    if algorithm not in ALGORITHMS:
        flash("Choose a valid scheduling algorithm.", "error")
        return redirect(url_for("home"))
    if not processes:
        flash("Add at least one process with a burst time greater than zero.", "error")
        return redirect(url_for("home"))

    result = simulate(processes, algorithm, time_quantum)
    simulation_id = save_simulation(result)
    result["simulation_id"] = simulation_id
    flash(f"{algorithm} simulation completed and saved to history.", "success")
    return render_template(
        "index.html",
        **dashboard_view(
            processes,
            selected_algorithm=algorithm_value,
            time_quantum=time_quantum,
            result=result,
            simulations=get_simulations(limit=5),
        ),
    )


@app.get("/history")
def history():
    return render_template(
        "index.html",
        page_is_history=True,
        history=get_simulations(limit=100),
        selected_ids=request.args.get("compare", ""),
    )


@app.get("/history/<int:id>")
def history_detail(id: int):
    detail = get_simulation_detail(id)
    if detail is None:
        flash("That simulation could not be found.", "error")
        return redirect(url_for("history"))
    executions = []
    for execution in detail["executions"]:
        item = dict(execution)
        item["width"] = item["end"] - item["start"]
        executions.append(item)
    detail["id"] = detail["simulation"]["id"]
    detail["execution_segments"] = executions
    return render_template(
        "index.html",
        page_is_history=True,
        history=get_simulations(limit=100),
        history_detail=detail,
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=os.environ.get("FLASK_DEBUG") == "1")