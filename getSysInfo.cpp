#include <iostream>
#include <sstream>
#include <sys/sysinfo.h>
#include <fstream>
#include <string>
#include <cstring>
#include <dirent.h>
#include <unistd.h>
#include <sys/statvfs.h>
#include <fstream>
#include <sstream>
#include <sys/utsname.h>
#include <chrono>

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

    const char* getDiskUsage() {
        static std::string info;
        info.clear();
        struct statvfs stat;
        if (statvfs("/", &stat) == 0) {
            unsigned long total = stat.f_blocks * stat.f_frsize / (1024 * 1024);
            unsigned long free = stat.f_bfree * stat.f_frsize / (1024 * 1024);
            unsigned long used = total - free;
            std::ostringstream diskInfo;
            diskInfo << "Total: " << total << " MB, Used: " << used << " MB, Free: " << free << " MB";
            info = diskInfo.str();
        }
        return info.c_str();
    }

    // funcao para obter a temperatura da CPU
    const char* getCpuTemperature() {
        static std::string info;
        info.clear();
        std::ifstream tempFile("/sys/class/thermal/thermal_zone0/temp");
        if (tempFile.is_open()) {
            int temp;
            tempFile >> temp;
            tempFile.close();
            std::ostringstream tempInfo;
            tempInfo << temp / 1000.0 << " °C";
            info = tempInfo.str();
        }
        return info.c_str();
    }

    // funcao para obter a taxa de recebimento de rede
    const char* getNetworkReceiveRate() {
        static std::string info;
        info.clear();

        static unsigned long long prevTotalReceived = 0;
        static auto prevTime = std::chrono::steady_clock::now();

        std::ifstream netFile("/proc/net/dev");
        if (netFile.is_open()) {
            std::string line;
            unsigned long long totalReceived = 0;

            // Skip the first two lines
            std::getline(netFile, line);
            std::getline(netFile, line);

            while (std::getline(netFile, line)) {
                std::istringstream ss(line);
                std::string iface;
                unsigned long long received;
                ss >> iface >> received;
                totalReceived += received;
            }
            netFile.close();

            // Get current time
            auto currentTime = std::chrono::steady_clock::now();
            std::chrono::duration<double> elapsedSeconds = currentTime - prevTime;

            if (elapsedSeconds.count() > 0) {
                double receiveRate = (totalReceived - prevTotalReceived) / elapsedSeconds.count();

                std::ostringstream netInfo;
                netInfo << receiveRate / 1024;
                info = netInfo.str();
            }

            // Update previous values
            prevTotalReceived = totalReceived;
            prevTime = currentTime;
        }

        return info.c_str();
    }

    // funcao para obter a taxa de transmissao de rede
    const char* getNetworkTransmitRate() {
        static std::string info;
        info.clear();

        static unsigned long long prevTotalTransmitted = 0;
        static auto prevTime = std::chrono::steady_clock::now();

        std::ifstream netFile("/proc/net/dev");
        if (netFile.is_open()) {
            std::string line;
            unsigned long long totalTransmitted = 0;

            // Skip the first two lines
            std::getline(netFile, line);
            std::getline(netFile, line);

            while (std::getline(netFile, line)) {
                std::istringstream ss(line);
                std::string iface;
                unsigned long long transmitted;
                for (int i = 0; i < 9; ++i) ss >> transmitted;
                totalTransmitted += transmitted;
            }
            netFile.close();

            // Get current time
            auto currentTime = std::chrono::steady_clock::now();
            std::chrono::duration<double> elapsedSeconds = currentTime - prevTime;

            if (elapsedSeconds.count() > 0) {
                double transmitRate = (totalTransmitted - prevTotalTransmitted) / elapsedSeconds.count();

                std::ostringstream netInfo;
                netInfo << transmitRate / 1024;
                info = netInfo.str();
            }

            // Update previous values
            prevTotalTransmitted = totalTransmitted;
            prevTime = currentTime;
        }

        return info.c_str();
    }

    // funcao para obter o uso da memoria swap
    const char* getSwapUsage() {
        static std::string info;
        info.clear();
        struct sysinfo sys_info;
        if (sysinfo(&sys_info) == 0) {
            double totalSwap = sys_info.totalswap / (1024.0 * 1024.0);
            double freeSwap = sys_info.freeswap / (1024.0 * 1024.0);
            double usedSwap = totalSwap - freeSwap;
            double swapUsagePercentage = (usedSwap / totalSwap) * 100.0;
            std::ostringstream swapInfo;
            swapInfo << swapUsagePercentage;
            info = swapInfo.str();
        }
        return info.c_str();
    }

    // funcao para obter informacoes sobre o sistema operacional
    const char* getOsInfo() {
        static std::string info;
        info.clear();
        struct utsname buffer;
        if (uname(&buffer) == 0) {
            std::ostringstream osInfo;
            osInfo << "OS: " << buffer.sysname << ", Release: " << buffer.release << ", Version: " << buffer.version;
            info = osInfo.str();
        }
        return info.c_str();
    }

    // funcao para obter informacoes sobre a arquitetura
    const char* getArchitectureInfo() {
        static std::string info;
        info.clear();
        struct utsname buffer;
        if (uname(&buffer) == 0) {
            std::ostringstream archInfo;
            archInfo << "Architecture: " << buffer.machine;
            info = archInfo.str();
        }
        return info.c_str();
    }

    // funcao para obter informacoes sobre a CPU
    const char* getCpuInfo() {
        static std::string info;
        info.clear();
        std::ifstream cpuFile("/proc/cpuinfo");
        if (cpuFile.is_open()) {
            std::string line;
            std::ostringstream cpuInfo;
            while (std::getline(cpuFile, line)) {
                if (line.find("model name") != std::string::npos) {
                    cpuInfo << line << "\n";
                }
                if (line.find("cpu cores") != std::string::npos) {
                    cpuInfo << line << "\n";
                }
                if (line.find("cpu MHz") != std::string::npos) {
                    cpuInfo << line << "\n";
                }
            }
            cpuFile.close();
            info = cpuInfo.str();
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
                        std::string threads;
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
                            if (line.find("Threads:") == 0) {
                                threads = line.substr(line.find(":") + 2);
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
                        << threads << "\t" << vsize << " KB\t" << rss << " KB\n";
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

    const char* getDiskUsage(SystemInfo* systemInfo) {
        return systemInfo->getDiskUsage();
    }

    const char* getCpuTemperature(SystemInfo* systemInfo) {
    return systemInfo->getCpuTemperature();
    }

    const char* getNetworkReceiveRate(SystemInfo* systemInfo) {
        return systemInfo->getNetworkReceiveRate();
    }

    const char* getNetworkTransmitRate(SystemInfo* systemInfo) {
        return systemInfo->getNetworkTransmitRate();
    }

    const char* getSwapUsage(SystemInfo* systemInfo) {
        return systemInfo->getSwapUsage();
    }

    const char* getOsInfo(SystemInfo* systemInfo) {
        return systemInfo->getOsInfo();
    }

    const char* getArchitectureInfo(SystemInfo* systemInfo) {
        return systemInfo->getArchitectureInfo();
    }

    const char* getCpuInfo(SystemInfo* systemInfo) {
        return systemInfo->getCpuInfo();
    }

    const char* getProcessesInfo(SystemInfo* systemInfo) { 
        return systemInfo->getProcessesInfo();
    }
}
