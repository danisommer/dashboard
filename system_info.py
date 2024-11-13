import os
from ctypes import cdll, c_char_p

# carrega a biblioteca c++
lib = cdll.LoadLibrary('./libGetSysInfo.so')

class SystemInfo:
    def __init__(self):
        self.obj = lib.SystemInfo_new()

        # dicionario de funcoes a serem chamadas
        self.fields = {
            "Uptime": lib.getUptime,
            "Total Memory": lib.getTotalMemory,
            "Free Memory": lib.getFreeMemory,
            "Load Average": lib.getLoadAverage,
            "Process Count": lib.getProcessCount,
            "Thread Count": lib.getThreadCount,
            "CPU Usage": lib.getCpuUsage
        }

        # define o tipo de retorno para cada funcao
        for func in self.fields.values():
            func.restype = c_char_p
        
        # define as funcoes de uso de cpu e memoria separadamente
        lib.getCpuUsage.restype = c_char_p
        lib.getTotalMemory.restype = c_char_p
        lib.getFreeMemory.restype = c_char_p

    def get_info(self, field):
        func = self.fields[field]
        value = func(self.obj).decode('utf-8')

        if field == "CPU Usage":
            value += "%"
        
        elif field in ["Total Memory", "Free Memory"]:
            value += " MB"

        return value

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
        process_memory_info = {"Physical memory": "N/A", "Virtual memory": "N/A"} 
        try:
            with open(f'/proc/{pid}/status') as f:
                for line in f:
                    if line.startswith('VmRSS'):
                        process_memory_info["Physical memory"] = line.strip().split()[1] + ' KB'
                    elif line.startswith('VmSize'):
                        process_memory_info["Virtual memory"] = line.strip().split()[1] + ' KB'
        except FileNotFoundError:
            pass  # o processo pode ter terminado
        return process_memory_info


    def get_cpu_usage(self):
        # chama a funcao em c++ e retorna o resultado decodificado como um float
        return float(lib.getCpuUsage(self.obj).decode('utf-8'))

    def get_memory_usage(self):
        # obtem memoria total e livre da biblioteca c++
        total_memory = float(lib.getTotalMemory(self.obj).decode('utf-8'))
        free_memory = float(lib.getFreeMemory(self.obj).decode('utf-8'))

        # calcula o uso de memoria como a diferença entre memoria total e livre
        used_memory = total_memory - free_memory

        # retorna o uso de memoria como uma porcentagem
        return (used_memory / total_memory) * 100
