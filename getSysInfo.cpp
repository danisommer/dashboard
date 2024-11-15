#include <iostream>
#include <sstream>
#include <sys/sysinfo.h>
#include <fstream>
#include <string>
#include <cstring>
#include <dirent.h>
#include <unistd.h>

class SystemInfo {
public:

    // funcao para obter a memoria total
    const char* getTotalMemory() {
        static std::string info;
        info.clear();
        struct sysinfo sys_info;
        if (sysinfo(&sys_info) == 0) {
            std::ostringstream memoryInfo;
            memoryInfo << sys_info.totalram / (1024 * 1024);
            info = memoryInfo.str();
        }
        return info.c_str();
    }

    // funcao para obter a memoria livre
    const char* getFreeMemory() {
        static std::string info;
        info.clear();
        struct sysinfo sys_info;
        if (sysinfo(&sys_info) == 0) {
            std::ostringstream memoryInfo;
            memoryInfo << sys_info.freeram / (1024 * 1024);
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

    // funcao para obter a media de carga
    const char* getLoadAverage() {
        static std::string info;
        info.clear();
        struct sysinfo sys_info;
        if (sysinfo(&sys_info) == 0) {
            std::ostringstream loadInfo;
            loadInfo << "1 min: " << sys_info.loads[0] / 65536.0 << ", "
                     << "5 min: " << sys_info.loads[1] / 65536.0 << ", "
                     << "15 min: " << sys_info.loads[2] / 65536.0;
            info = loadInfo.str();
        }
        return info.c_str();
    }

    // funcao para obter o numero de processos em execucao
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

    // funcao para calcular e retornar o uso da cpu em percentual
    const char* getCpuUsage() {
        static std::string info;
        info.clear();
        
        // le as estatísticas de uso da cpu em /proc/stat
        std::ifstream statFile("/proc/stat");
        std::string line;
        if (statFile.is_open()) {
            std::getline(statFile, line);  // le a primeira linha (estatísticas da cpu)
            statFile.close();
            
            // analisa as estatisticas da cpu a partir da linha
            unsigned long long user, nice, system, idle, iowait, irq, softirq, steal;
            std::istringstream ss(line);
            ss >> line >> user >> nice >> system >> idle >> iowait >> irq >> softirq >> steal;
            
            // calcula a porcentagem de uso da cpu
            unsigned long long total = user + nice + system + idle + iowait + irq + softirq + steal;
            unsigned long long idleTime = idle + iowait;
            
            // computa o uso da cpu em percentual
            double cpuUsage = 100.0 * (total - idleTime) / total;
            std::ostringstream usageInfo;
            usageInfo << cpuUsage;
            info = usageInfo.str();
        }
        return info.c_str();
    }

    const char* getThreadCount() {
        static std::string info;
        info.clear();
        std::ifstream statFile("/proc/stat");
        std::string line;
        if (statFile.is_open()) {
            while (std::getline(statFile, line)) {
                if (line.find("processes") != std::string::npos) {
                    std::istringstream ss(line);
                    std::string key;
                    int value;
                    ss >> key >> value;
                    std::ostringstream threadInfo;
                    threadInfo << value << " threads\n";
                    info = threadInfo.str();
                    break;
                }
            }
            statFile.close();
        }
        return info.c_str();
    }

    // funcao para obter informacoes detalhadas dos processos
    const char* getProcessesInfo() {
        static std::string info;

        std::ostringstream processesInfo;
        processesInfo << "PID\tName\tStatus\tVirtual Memory\tPhysical Memory\n";

        DIR* dir = opendir("/proc");
        if (!dir) {
            perror("Não foi possível abrir /proc");
            return "";
        }

        struct dirent* entry;
        while ((entry = readdir(dir)) != NULL) {
            if (entry->d_type == DT_DIR) {
                int pid = atoi(entry->d_name);
                if (pid > 0) {
                    std::string processDir = std::string("/proc/") + entry->d_name;
                    std::string statusPath = processDir + "/status";
                    
                    std::ifstream statusFile(statusPath);
                    if (statusFile.is_open()) {
                        std::string line;
                        std::string name;
                        std::string state;
                        unsigned long vsize = 0;   // memoria virtual
                        long rss = 0;              // memoria fisica

                        while (std::getline(statusFile, line)) {
                            if (line.find("Name:") == 0) {
                                name = line.substr(line.find(":") + 2);
                            }
                            if (line.find("State:") == 0) {
                                state = line.substr(line.find(":") + 2);
                            }
                            if (line.find("VmSize:") == 0) {
                                vsize = std::stoul(line.substr(line.find(":") + 2)) / 1024; // Em KB
                            }
                            if (line.find("VmRSS:") == 0) {
                                rss = std::stol(line.substr(line.find(":") + 2)) / 1024; // Em KB
                                break;
                            }
                        }
                        processesInfo << pid << "\t" << name << "\t" << state << "\t" 
                                      << vsize << " KB\t" << rss << " KB\n";
                        statusFile.close();
                    }
                }
            }
        }
        closedir(dir);
        
        info = processesInfo.str();
        return info.c_str();

    }

};

extern "C" {
    SystemInfo* SystemInfo_new() { 
        return new SystemInfo(); 
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

    const char* getCpuUsage(SystemInfo* systemInfo) {
        return systemInfo->getCpuUsage();
    }

    const char* getThreadCount(SystemInfo* systemInfo) {
        return systemInfo->getThreadCount();
    }

    const char* getProcessesInfo(SystemInfo* systemInfo) { 
        return systemInfo->getProcessesInfo();
    }
}
