from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
DB_PATH = Path(os.environ.get("SIMULATOR_DB_PATH", ROOT / "instance" / "simulator.db"))


def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def init_database() -> None:
    with _connect() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS Process (
                Process_ID TEXT PRIMARY KEY,
                Process_Name TEXT NOT NULL,
                Arrival_Time INTEGER NOT NULL,
                Burst_Time INTEGER NOT NULL,
                Priority INTEGER NOT NULL,
                Status TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS Simulation (
                Simulation_ID INTEGER PRIMARY KEY AUTOINCREMENT,
                Algorithm TEXT NOT NULL,
                Time_Quantum INTEGER,
                Process_Count INTEGER NOT NULL,
                Avg_Waiting_Time REAL NOT NULL,
                Avg_Turnaround_Time REAL NOT NULL,
                Created_At TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS Execution (
                Execution_ID INTEGER PRIMARY KEY AUTOINCREMENT,
                Simulation_ID INTEGER NOT NULL,
                Process_ID TEXT NOT NULL,
                Start_Time INTEGER NOT NULL,
                End_Time INTEGER NOT NULL,
                FOREIGN KEY (Simulation_ID) REFERENCES Simulation(Simulation_ID) ON DELETE CASCADE
            );
            """
        )


def save_simulation(result: dict[str, Any]) -> int:
    with _connect() as connection:
        cursor = connection.execute(
            """
            INSERT INTO Simulation
                (Algorithm, Time_Quantum, Process_Count, Avg_Waiting_Time, Avg_Turnaround_Time)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                result["algorithm"],
                result["time_quantum"],
                len(result["metrics"]),
                result["avg_waiting"],
                result["avg_turnaround"],
            ),
        )
        simulation_id = int(cursor.lastrowid) # type: ignore
        for metric in result["metrics"]:
            connection.execute(
                """
                INSERT INTO Process
                    (Process_ID, Process_Name, Arrival_Time, Burst_Time, Priority, Status)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(Process_ID) DO UPDATE SET
                    Process_Name=excluded.Process_Name,
                    Arrival_Time=excluded.Arrival_Time,
                    Burst_Time=excluded.Burst_Time,
                    Priority=excluded.Priority,
                    Status=excluded.Status
                """,
                (
                    metric["id"],
                    metric["name"],
                    metric["arrival"],
                    metric["burst"],
                    metric["priority"],
                    metric["status"],
                ),
            )
        for segment in result["segments"]:
            if segment["process_id"] == "IDLE":
                continue
            connection.execute(
                """
                INSERT INTO Execution
                    (Simulation_ID, Process_ID, Start_Time, End_Time)
                VALUES (?, ?, ?, ?)
                """,
                (
                    simulation_id,
                    segment["process_id"],
                    segment["start"],
                    segment["end"],
                ),
            )
    return simulation_id


def get_simulations(limit: int = 100) -> list[dict[str, Any]]:
    with _connect() as connection:
        rows = connection.execute(
            """
            SELECT Simulation_ID AS id, Algorithm AS algorithm, Time_Quantum AS time_quantum,
                   Process_Count AS process_count, Avg_Waiting_Time AS avg_waiting,
                   Avg_Turnaround_Time AS avg_turnaround, Created_At AS created_at
            FROM Simulation
            ORDER BY Simulation_ID DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [dict(row) for row in rows]


def get_simulation_detail(simulation_id: int) -> dict[str, Any] | None:
    with _connect() as connection:
        simulation = connection.execute(
            """
            SELECT Simulation_ID AS id, Algorithm AS algorithm, Time_Quantum AS time_quantum,
                   Process_Count AS process_count, Avg_Waiting_Time AS avg_waiting,
                   Avg_Turnaround_Time AS avg_turnaround, Created_At AS created_at
            FROM Simulation WHERE Simulation_ID = ?
            """,
            (simulation_id,),
        ).fetchone()
        if simulation is None:
            return None
        executions = connection.execute(
            """
            SELECT e.Process_ID AS process_id, p.Process_Name AS name,
                   e.Start_Time AS start, e.End_Time AS end
            FROM Execution e
            LEFT JOIN Process p ON p.Process_ID = e.Process_ID
            WHERE e.Simulation_ID = ?
            ORDER BY e.Execution_ID
            """,
            (simulation_id,),
        ).fetchall()
    return {"simulation": dict(simulation), "executions": [dict(row) for row in executions]}