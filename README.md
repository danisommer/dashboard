# System Dashboard Application

## Overview
This project is a system dashboard application that displays real-time system metrics. It consists of:
- A **Python GUI** (`dashboard_app.py`) for visualizing system metrics.
- A **C++ backend** (`getSysInfo.cpp`) for fetching system information.

## Compilation and Execution

### Prerequisites
- **g++**: For compiling the C++ backend.
- **Python 3**: For running the GUI application.

### Steps to Compile and Run (Linux)
1. Navigate to the project directory.
2. Run the following command to compile the C++ library and start the Python application:
    ```bash
    g++ -c -fPIC getSysInfo.cpp -o getSysInfo.o
    g++ -shared -Wl,-soname,getSysInfo.so -o libGetSysInfo.so getSysInfo.o
    /bin/python3 main.py
    ```

## File Structure
- `dashboard_app.py`: Python GUI for displaying metrics.
- `getSysInfo.cpp`: C++ backend for system information.
- `main.py`: Entry point for the application, linking the GUI with the backend.
