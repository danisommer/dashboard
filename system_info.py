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
            "Network Receive Rate": lib.getNetworkReceiveRate,
            "Network Transmit Rate": lib.getNetworkTransmitRate,
            "Swap Usage": lib.getSwapUsage,
            "OS Info": lib.getOsInfo,
            "Architecture Info": lib.getArchitectureInfo
        }
        # define o tipo de retorno para cada funcao
        for func in self.fields.values():
            func.restype = c_char_p

    def get_info(self, field):
        func = self.fields[field]
        value = func(self.obj).decode('utf-8')

        if field in ["Network Receive Rate", "Network Transmit Rate"]:
            value += " KB/s"

        if field == "CPU Usage":
            value += "%"
        
        elif field in ["Total Memory", "Free Memory"]:
            value += " MB"

        return value

    def get_cpu_usage_per_core(self):
        lib.getCpuInfo.restype = c_char_p
        cpu_usage_str = lib.getCpuInfo(self.obj).decode('utf-8')
        cpu_usage_list = cpu_usage_str.split("\t")
        
        # remove strings vazias e converte para float
        cpu_usage_list = [float(usage.strip()) for usage in cpu_usage_list if usage.strip()]
        return cpu_usage_list

    def get_memory_usage(self):
        # obtem memoria total e livre da biblioteca c++
        total_memory = float(lib.getTotalMemory(self.obj).decode('utf-8'))
        free_memory = float(lib.getFreeMemory(self.obj).decode('utf-8'))

        # calcula o uso de memoria como a diferença entre memoria total e livre
        used_memory = total_memory - free_memory

        # retorna o uso de memoria como uma porcentagem
        return (used_memory / total_memory) * 100
    
    def get_swap_usage(self):
        return float(lib.getSwapUsage(self.obj).decode('utf-8'))

    def get_network_receive_rate(self):
        return float(lib.getNetworkReceiveRate(self.obj).decode('utf-8'))

    def get_network_transmit_rate(self):
        return float(lib.getNetworkTransmitRate(self.obj).decode('utf-8'))
    
    def get_processes_info(self):
        lib.getProcessesInfo.restype = c_char_p
        print(lib.getProcessesInfo(self.obj).decode('utf-8'))
        return lib.getProcessesInfo(self.obj).decode('utf-8')
    
    def get_used_disk(self):
        lib.getUsedDisk.restype = c_char_p
        return float(lib.getUsedDisk(self.obj).decode('utf-8'))
    
    def get_free_disk(self):
        lib.getFreeDisk.restype = c_char_p
        return float(lib.getFreeDisk(self.obj).decode('utf-8'))