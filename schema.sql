CREATE DATABASE process_management_simulator;
USE process_management_simulator;

CREATE TABLE Process (
    Process_ID VARCHAR(32) PRIMARY KEY,
    Process_Name VARCHAR(120) NOT NULL,
    Arrival_Time INT NOT NULL,
    Burst_Time INT NOT NULL,
    Priority INT NOT NULL,
    Status VARCHAR(32) NOT NULL
);

CREATE TABLE Simulation (
    Simulation_ID INT PRIMARY KEY AUTO_INCREMENT,
    Algorithm VARCHAR(32) NOT NULL,
    Time_Quantum INT NULL,
    Process_Count INT NOT NULL,
    Avg_Waiting_Time DECIMAL(10, 2) NOT NULL,
    Avg_Turnaround_Time DECIMAL(10, 2) NOT NULL,
    Created_At TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE Execution (
    Execution_ID INT PRIMARY KEY AUTO_INCREMENT,
    Simulation_ID INT NOT NULL,
    Process_ID VARCHAR(32) NOT NULL,
    Start_Time INT NOT NULL,
    End_Time INT NOT NULL,
    CONSTRAINT fk_execution_simulation
        FOREIGN KEY (Simulation_ID) REFERENCES Simulation(Simulation_ID)
        ON DELETE CASCADE,
    CONSTRAINT fk_execution_process
        FOREIGN KEY (Process_ID) REFERENCES Process(Process_ID)
);