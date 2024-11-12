# system_info.py
import os
from ctypes import cdll, c_char_p

# Load the C++ library
lib = cdll.LoadLibrary('./libGetSysInfo.so')

class SystemInfo:
    def __init__(self):
        self.obj = lib.SystemInfo_new()

        # Dictionary of functions to be called
        self.fields = {
            "System Info": lib.getSystemInfo,
            "Total Memory": lib.getTotalMemory,
            "Free Memory": lib.getFreeMemory,
            "Uptime": lib.getUptime,
            "Load Average": lib.getLoadAverage,
            "Process Count": lib.getProcessCount
        }

        # Define the return type for each function
        for func in self.fields.values():
            func.restype = c_char_p

    def get_info(self, field):
        func = self.fields[field]
        return func(self.obj).decode('utf-8')

    def get_processes_info(self):
        processes = []
        for pid in os.listdir('/proc'):
            if pid.isdigit():
                try:
                    process_info = {}
                    with open(f'/proc/{pid}/stat') as f:
                        data = f.read().split()
                        process_info['pid'] = pid
                        process_info['name'] = data[1]
                        process_info['status'] = data[2]
                        process_info['memory'] = self.get_process_memory(pid)
                        processes.append(process_info)
                except FileNotFoundError:
                    continue
        return processes

    def get_process_memory(self, pid):
        try:
            with open(f'/proc/{pid}/status') as f:
                for line in f:
                    if line.startswith('VmRSS'):
                        return line.strip().split()[1] + ' KB'
        except FileNotFoundError:
            return 'N/A'
        return 'N/A'
