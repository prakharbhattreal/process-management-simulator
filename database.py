from __future__ import annotations

from typing import Any
from dotenv import load_dotenv
import os
import mysql.connector

load_dotenv()

def _connect():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
        port=int(os.getenv("DB_PORT", "3306"))
    )


def init_database() -> None:
    """
    Database tables are already created in MySQL Workbench.
    Nothing needs to be created here.
    """
    connection = _connect()
    connection.close()


def save_simulation(result: dict[str, Any]) -> int:
    connection = _connect()
    cursor = connection.cursor()

    try:
        # Insert simulation
        cursor.execute(
            """
            INSERT INTO Simulation
                (
                    Algorithm,
                    Time_Quantum,
                    Process_Count,
                    Avg_Waiting_Time,
                    Avg_Turnaround_Time
                )
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                result["algorithm"],
                result["time_quantum"],
                len(result["metrics"]),
                result["avg_waiting"],
                result["avg_turnaround"],
            ),
        )

        # Get the newly created Simulation_ID
        simulation_id = cursor.lastrowid

        if simulation_id is None:
            raise RuntimeError("Failed to create simulation record.")

        # Insert / update processes
        for metric in result["metrics"]:
            cursor.execute(
                """
                INSERT INTO Process
                    (
                        Process_ID,
                        Process_Name,
                        Arrival_Time,
                        Burst_Time,
                        Priority,
                        Status
                    )
                VALUES (%s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    Process_Name = VALUES(Process_Name),
                    Arrival_Time = VALUES(Arrival_Time),
                    Burst_Time = VALUES(Burst_Time),
                    Priority = VALUES(Priority),
                    Status = VALUES(Status)
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

        # Insert execution segments
        for segment in result["segments"]:
            if segment["process_id"] == "IDLE":
                continue

            cursor.execute(
                """
                INSERT INTO Execution
                    (
                        Simulation_ID,
                        Process_ID,
                        Start_Time,
                        End_Time
                    )
                VALUES (%s, %s, %s, %s)
                """,
                (
                    simulation_id,
                    segment["process_id"],
                    segment["start"],
                    segment["end"],
                ),
            )

        connection.commit()

        return int(simulation_id)

    except Exception:
        connection.rollback()
        raise

    finally:
        cursor.close()
        connection.close()


def get_simulations(limit: int = 100) -> list[dict[str, Any]]:
    connection = _connect()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT
                Simulation_ID AS id,
                Algorithm AS algorithm,
                Time_Quantum AS time_quantum,
                Process_Count AS process_count,
                Avg_Waiting_Time AS avg_waiting,
                Avg_Turnaround_Time AS avg_turnaround,
                Created_At AS created_at
            FROM Simulation
            ORDER BY Simulation_ID DESC
            LIMIT %s
            """,
            (limit,),
        )

        rows = cursor.fetchall()

        # Convert MySQL rows to normal dictionaries
        return [dict(row) for row in rows] # type: ignore

    finally:
        cursor.close()
        connection.close()


def get_simulation_detail(
    simulation_id: int
) -> dict[str, Any] | None:

    connection = _connect()
    cursor = connection.cursor(dictionary=True)

    try:
        # Get simulation information
        cursor.execute(
            """
            SELECT
                Simulation_ID AS id,
                Algorithm AS algorithm,
                Time_Quantum AS time_quantum,
                Process_Count AS process_count,
                Avg_Waiting_Time AS avg_waiting,
                Avg_Turnaround_Time AS avg_turnaround,
                Created_At AS created_at
            FROM Simulation
            WHERE Simulation_ID = %s
            """,
            (simulation_id,),
        )

        simulation_row = cursor.fetchone()

        if simulation_row is None:
            return None

        # Convert the returned row to a normal dictionary
        simulation = dict(simulation_row) # type: ignore

        # Get execution details
        cursor.execute(
            """
            SELECT
                e.Process_ID AS process_id,
                p.Process_Name AS name,
                e.Start_Time AS start,
                e.End_Time AS end
            FROM Execution e
            LEFT JOIN Process p
                ON p.Process_ID = e.Process_ID
            WHERE e.Simulation_ID = %s
            ORDER BY e.Execution_ID
            """,
            (simulation_id,),
        )

        execution_rows = cursor.fetchall()

        # Convert MySQL rows to normal dictionaries
        executions = [dict(row) for row in execution_rows] # type: ignore

        return {
            "simulation": simulation,
            "executions": executions
        }

    finally:
        cursor.close()
        connection.close()