#include <iostream>
#include <sstream>
#include <sys/sysinfo.h>
#include <string>
#include <cstring>

class SystemInfo {
public:
    // funcao para obter infos gerais do sistema
    const char* getSystemInfo() {
        static std::string info;
        info.clear();
        FILE* fp = popen("uname -a", "r");
        if (fp) {
            char buffer[256];
            while (fgets(buffer, sizeof(buffer), fp) != NULL) {
                info += buffer;
            }
            pclose(fp);
        }
        return info.c_str();
    }

    // funcao para obter a mem total
    const char* getTotalMemory() {
        static std::string info;
        info.clear();
        struct sysinfo sys_info;
        if (sysinfo(&sys_info) == 0) {
            std::ostringstream memoryInfo;
            memoryInfo << sys_info.totalram / (1024 * 1024) << " MB\n";
            info = memoryInfo.str();
        }
        return info.c_str();
    }

    // funcao para obter a mem livre
    const char* getFreeMemory() {
        static std::string info;
        info.clear();
        struct sysinfo sys_info;
        if (sysinfo(&sys_info) == 0) {
            std::ostringstream memoryInfo;
            memoryInfo << sys_info.freeram / (1024 * 1024) << " MB\n";
            info = memoryInfo.str();
        }
        return info.c_str();
    }

    // funcao para obter o tempo de atividade do sistema
    const char* getUptime() {
        static std::string info;
        info.clear();
        struct sysinfo sys_info;
        if (sysinfo(&sys_info) == 0) {
            std::ostringstream uptimeInfo;
            uptimeInfo << sys_info.uptime / 3600 << " hours, "
                       << (sys_info.uptime % 3600) / 60 << " minutes\n";
            info = uptimeInfo.str();
        }
        return info.c_str();
    }

    // funcao para obter a carga media do sistema
    const char* getLoadAverage() {
        static std::string info;
        info.clear();
        struct sysinfo sys_info;
        if (sysinfo(&sys_info) == 0) {
            std::ostringstream loadInfo;
            loadInfo << "1 min: " << sys_info.loads[0] / 65536.0 << ", "
                     << "5 min: " << sys_info.loads[1] / 65536.0 << ", "
                     << "15 min: " << sys_info.loads[2] / 65536.0 << "\n";
            info = loadInfo.str();
        }
        return info.c_str();
    }

    // funcao para obter o num de processos em execucao
    const char* getProcessCount() {
        static std::string info;
        info.clear();
        struct sysinfo sys_info;
        if (sysinfo(&sys_info) == 0) {
            std::ostringstream procInfo;
            procInfo << sys_info.procs << " processes\n";
            info = procInfo.str();
        }
        return info.c_str();
    }
};

extern "C" {
    SystemInfo* SystemInfo_new() { 
        return new SystemInfo(); 
    }

    const char* getSystemInfo(SystemInfo* systemInfo) { 
        return systemInfo->getSystemInfo();
    }

    const char* getTotalMemory(SystemInfo* systemInfo) { 
        return systemInfo->getTotalMemory();
    }

    const char* getFreeMemory(SystemInfo* systemInfo) { 
        return systemInfo->getFreeMemory();
    }

    const char* getUptime(SystemInfo* systemInfo) { 
        return systemInfo->getUptime();
    }

    const char* getLoadAverage(SystemInfo* systemInfo) { 
        return systemInfo->getLoadAverage();
    }

    const char* getProcessCount(SystemInfo* systemInfo) { 
        return systemInfo->getProcessCount();
    }
}
