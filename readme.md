# Process Management Simulator

A web-based **Process Management Simulator** developed using **Python Flask, HTML, CSS, JavaScript, and MySQL**.

The project demonstrates important Operating System concepts such as **process creation, CPU scheduling, waiting time, turnaround time, and process execution**. The simulation results are stored in a MySQL database and can be viewed using MySQL Workbench.

## Features

* Create and manage processes
* Enter process ID, name, arrival time, burst time, and priority
* Simulate CPU scheduling algorithms
* Calculate:

  * Waiting Time
  * Turnaround Time
* Display process execution/Gantt chart
* Store simulation results in MySQL
* Store process execution details in MySQL
* View previous simulation results
* Simple web-based interface

## Technologies Used

* **Python**
* **Flask**
* **HTML5**
* **CSS3**
* **JavaScript**
* **MySQL**
* **MySQL Workbench**

## Project Structure

```text
Process-Management-Simulator/
│
├── app.py
├── database.py
├── scheduler.py
├── schema.sql
├── requirements.txt
├── .env
├── .gitignore
├── README.md
│
├── templates/
│   └── index.html
│
└── static/
    ├── css/
    │   └── style.css
    │
    └── js/
        └── app.js
```

> **Note:** `.env` contains database credentials and should not be uploaded to GitHub.

## Database

The project uses MySQL with the following database:

```text
process_management_simulator
```

The database contains three main tables:

### Process

Stores information about processes.

```text
Process_ID
Process_Name
Arrival_Time
Burst_Time
Priority
Status
```

### Simulation

Stores information about each scheduling simulation.

```text
Simulation_ID
Algorithm
Time_Quantum
Process_Count
Avg_Waiting_Time
Avg_Turnaround_Time
Created_At
```

### Execution

Stores the execution timeline of processes.

```text
Execution_ID
Simulation_ID
Process_ID
Start_Time
End_Time
```

## Setup

### 1. Clone the repository

```bash
git clone <your-github-repository-url>
cd Process-Management-Simulator
```

### 2. Create a virtual environment

```bash
python -m venv venv
```

Activate it on Windows:

```bash
venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure MySQL

Open **MySQL Workbench** and create the database:

```sql
CREATE DATABASE process_management_simulator;
```

Then run the SQL commands from:

```text
schema.sql
```

to create the required tables.

### 5. Configure database credentials

Create a `.env` file in the project root:

```env
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=process_management_simulator
DB_PORT=3306
```

Replace `your_mysql_password` with your local MySQL password.

**Do not upload the `.env` file to GitHub.**

### 6. Run the application

```bash
python app.py
```

Open the application in your browser:

```text
http://127.0.0.1:5000
```

## How It Works

```text
Create Process
      ↓
Enter Process Details
      ↓
Select Scheduling Algorithm
      ↓
Run Simulation
      ↓
Calculate Waiting & Turnaround Time
      ↓
Display Execution / Gantt Chart
      ↓
Save Results
      ↓
MySQL Database
```

## Database Verification

After running a simulation, the stored data can be checked using MySQL Workbench.

### View processes

```sql
USE process_management_simulator;

SELECT * FROM Process;
```

### View simulations

```sql
SELECT * FROM Simulation;
```

### View execution details

```sql
SELECT * FROM Execution;
```

### View complete simulation information

```sql
SELECT
    s.Simulation_ID,
    s.Algorithm,
    s.Time_Quantum,
    s.Process_Count,
    s.Avg_Waiting_Time,
    s.Avg_Turnaround_Time,
    e.Process_ID,
    p.Process_Name,
    e.Start_Time,
    e.End_Time
FROM Simulation s
JOIN Execution e
    ON s.Simulation_ID = e.Simulation_ID
JOIN Process p
    ON e.Process_ID = p.Process_ID
ORDER BY s.Simulation_ID, e.Execution_ID;
```

## Purpose

The purpose of this project is to provide a simple practical demonstration of **Operating System process management and CPU scheduling** while also demonstrating how a **database management system** can be used to store and retrieve process and simulation data.

## Future Scope

* Add more CPU scheduling algorithms
* Add process priority visualization
* Improve simulation visualization
* Add performance comparison between algorithms
* Add additional process management features
* Improve user interface and responsiveness
