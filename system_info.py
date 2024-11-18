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
            "CPU Usage": lib.getCpuUsage,
            "CPU Temperature": lib.getCpuTemperature,
            "Network Usage": lib.getNetworkUsage,
            "Swap Usage": lib.getSwapUsage,
            "OS Info": lib.getOsInfo,
            "Architecture Info": lib.getArchitectureInfo,
            "CPU Info": lib.getCpuInfo            
        }

        lib.getProcessesInfo.restype = c_char_p

        # define o tipo de retorno para cada funcao
        for func in self.fields.values():
            func.restype = c_char_p

    def get_info(self, field):
        func = self.fields[field]
        value = func(self.obj).decode('utf-8')

        if field == "CPU Usage":
            value += "%"
        
        elif field in ["Total Memory", "Free Memory"]:
            value += " MB"

        return value

    def get_processes_info(self):
        processes_info = lib.getProcessesInfo(self.obj)
        return processes_info.decode('utf-8')

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