Overview
This project is a system dashboard application that displays real-time system metrics using a Python GUI (dashboard_app.py) and a C++ backend (getSysInfo.cpp).

Compilation and Execution
To compile the C++ library and run the Python application, go to the directory and use the following command (Linux):

g++ -c -fPIC getSysInfo.cpp -o getSysInfo.o; g++ -shared -Wl,-soname,getSysInfo.so -o libGetSysInfo.so  getSysInfo.o; /bin/python3 main.py