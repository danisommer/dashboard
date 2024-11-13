#include <iostream>
#include <sstream>
#include <sys/sysinfo.h>
#include <fstream>
#include <string>
#include <cstring>

class SystemInfo {
public:

    // Function to obtain total memory
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

    // Function to obtain free memory
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

    // Function to obtain system uptime
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

    // Function to obtain load average
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

    // Function to obtain the number of running processes
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

    // Function to calculate and return CPU usage as a percentage
    const char* getCpuUsage() {
        static std::string info;
        info.clear();
        
        // Read the CPU usage stats from /proc/stat
        std::ifstream statFile("/proc/stat");
        std::string line;
        if (statFile.is_open()) {
            std::getline(statFile, line);  // Read the first line (CPU stats)
            statFile.close();
            
            // Parse the CPU statistics from the line
            unsigned long long user, nice, system, idle, iowait, irq, softirq, steal;
            std::istringstream ss(line);
            ss >> line >> user >> nice >> system >> idle >> iowait >> irq >> softirq >> steal;
            
            // Calculate CPU usage percentage
            unsigned long long total = user + nice + system + idle + iowait + irq + softirq + steal;
            unsigned long long idleTime = idle + iowait;
            
            // Compute CPU usage as percentage
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
}
