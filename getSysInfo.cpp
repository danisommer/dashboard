#include <iostream>

// para manipulacao de usuarios
#include <pwd.h>   // Para getpwuid()
#include <unistd.h> // Para getuid()

// para manipulacao de arquivos
#include <fstream>
#include <sstream>

// para manipulacao de strings
#include <string>
#include <cstring>
#include <iomanip>

// para manipulacao de diretorios
#include <dirent.h>
#include <unistd.h>

// informacoes do sistema
#include <sys/sysinfo.h>
#include <sys/statvfs.h>
#include <sys/utsname.h>

// para manipulacao de processos
#include <chrono>
#include <algorithm>
#include <signal.h>

class SystemInfo {
public:

    // funcao para obter a memoria total
    const char* getTotalMemory() {
        static std::string info;
        info.clear();
        struct sysinfo sys_info;
        if (sysinfo(&sys_info) == 0) {
            unsigned long long total_memory = sys_info.totalram * sys_info.mem_unit; 
            std::ostringstream memoryInfo;
            memoryInfo << total_memory / (1024 * 1024); // convertido para MB
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
            unsigned long long free_memory = sys_info.freeram * sys_info.mem_unit; 
            std::ostringstream memoryInfo;
            memoryInfo << free_memory / (1024 * 1024); // convertido para MB
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
            long uptime_seconds = sys_info.uptime;
            long hours = uptime_seconds / 3600;
            long minutes = (uptime_seconds % 3600) / 60;
            long seconds = uptime_seconds % 60;

            std::ostringstream uptimeInfo;
            uptimeInfo << hours << " hours, "
                    << minutes << " minutes, "
                    << seconds << " seconds";
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
            loadInfo << "Load Average: "
                    << "1 min: " << sys_info.loads[0] / 65536.0 << ", "
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
            procInfo << sys_info.procs << " processes";
            info = procInfo.str();
        }
        return info.c_str();
    }

    // TODO: pendente
    // funcao para calcular e retornar o uso da cpu em percentual
    const char* getCpuUsage() {
        static std::string info;
        info.clear();
        
        // le as estatisticas de uso da cpu em /proc/stat
        std::ifstream statFile("/proc/stat");
        std::string line;
        if (statFile.is_open()) {
            std::getline(statFile, line);  // le a primeira linha (estatisticas da cpu)
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

    // funcao para obter o percentual de tempo ocioso da cpu
    const char* getCpuIdlePercentage() {
        static std::string info;
        info.clear();

        std::ifstream statFile("/proc/stat");
        std::string line;
        
        if (statFile.is_open()) {
            std::getline(statFile, line);  // le a primeira linha com as estatísticas da cpu
            statFile.close();

            // analisa a linha
            unsigned long long user, nice, system, idle, iowait, irq, softirq, steal;
            std::istringstream ss(line);
            ss >> line >> user >> nice >> system >> idle >> iowait >> irq >> softirq >> steal;

            // calcula o tempo total da cpu
            unsigned long long total = user + nice + system + idle + iowait + irq + softirq + steal;

            // percentual de tempo ocioso
            double idlePercentage = (double)idle / total * 100.0;

            // armazena a saida
            std::ostringstream idleInfo;
            idleInfo << idlePercentage << "%";
            info = idleInfo.str();
        }

        return info.c_str();
    }

    // TODO: pendente
    // funcao para obter o numero de threads
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

    const char* getUsedDisk() {
        static std::string info;
        info.clear();
        struct statvfs stat;
        if (statvfs("/", &stat) == 0) {
            // total de blocos e o tamanho de cada bloco
            unsigned long total = stat.f_blocks * stat.f_frsize;
            unsigned long free = stat.f_bfree * stat.f_frsize;
            unsigned long used = total - free;

            double usedDisk = used / (1024.0 * 1024.0); 
            std::ostringstream diskInfo;
            usedDisk /= 1024.0;
            diskInfo << usedDisk;
            
            info = diskInfo.str();
        }
        return info.c_str();
    }

    const char* getFreeDisk() { 
        static std::string info;
        info.clear();
        struct statvfs stat;
        if (statvfs("/", &stat) == 0) {
            // total de blocos e o tamanho de cada bloco
            unsigned long total = stat.f_blocks * stat.f_frsize;
            unsigned long free = stat.f_bfree * stat.f_frsize;

            double freeDisk = free / (1024.0 * 1024.0); 
            std::ostringstream diskInfo;
            freeDisk /= 1024.0;
            diskInfo << freeDisk;
            
            info = diskInfo.str();
        } else {
            info = "Error";
        }
        return info.c_str();
    }

    // TODO: pendente 
    // funcao para obter o uso do disco em leitura
    const char* getDiskRead() {
        static std::string info;
        info.clear();

        static unsigned long long prevRead = 0;
        unsigned long long currRead = 0;

        // le as estatisticas do disco a partir de /proc/diskstats
        std::ifstream statFile("/proc/diskstats");
        std::string line;
        if (statFile.is_open()) {
            while (std::getline(statFile, line)) {
                std::istringstream ss(line);
                std::string device;
                unsigned long long readSectors;

                // encontra a linha que corresponde ao dispositivo de disco desejado
                ss >> device; // nome do dispositivo
                for (int i = 0; i < 3; ++i) ss.ignore(std::numeric_limits<std::streamsize>::max(), ' '); // ignora campos desnecessarios
                ss >> readSectors; // leitura de setores

                // Para o calculo de uso de leitura, vamos apenas considerar o primeiro dispositivo (geralmente o principal)
                if (device == "sda" || device == "nvme0n1") {  // considera o dispositivo principal (ajuste conforme necessario)
                    currRead = readSectors;
                    break;
                }
            }
            statFile.close();
        }

        // calcula a diferenca de leitura de setores
        unsigned long long readDiff = currRead - prevRead;
        prevRead = currRead;

        // converte para MB (assumindo que cada setor tem 512 bytes)
        double readMB = readDiff * 512.0 / (1024 * 1024); // convertendo para MB
        std::ostringstream readInfo;
        readInfo.precision(2);
        readInfo << std::fixed << readMB; // MB
        info = readInfo.str();

        return info.c_str();
    }

    //  TODO: pendente 
    // funcao para obter o uso do disco em escrita
    const char* getDiskWrite() {
        static std::string info;
        info.clear();

        static unsigned long long prevWrite = 0;
        unsigned long long currWrite = 0;

        // le as estatisticas do disco a partir de /proc/diskstats
        std::ifstream statFile("/proc/diskstats");
        std::string line;
        if (statFile.is_open()) {
            while (std::getline(statFile, line)) {
                std::istringstream ss(line);
                std::string device;
                unsigned long long writeSectors;

                // encontra a linha que corresponde ao dispositivo de disco desejado
                ss >> device; // nome do dispositivo
                for (int i = 0; i < 7; ++i) ss.ignore(std::numeric_limits<std::streamsize>::max(), ' '); // ignora campos desnecessarios
                ss >> writeSectors; // escrita de setores

                // Para o calculo de uso de escrita, vamos apenas considerar o primeiro dispositivo (geralmente o principal)
                if (device == "sda" || device == "nvme0n1") {  // considera o dispositivo principal (ajuste conforme necessario)
                    currWrite = writeSectors;
                    break;
                }
            }
            statFile.close();
        }

        // calcula a diferenca de escrita de setores
        unsigned long long writeDiff = currWrite - prevWrite;
        prevWrite = currWrite;

        // converte para MB (assumindo que cada setor tem 512 bytes)
        double writeMB = writeDiff * 512.0 / (1024 * 1024); // convertendo para MB
        std::ostringstream writeInfo;
        writeInfo.precision(2);
        writeInfo << std::fixed << writeMB; // MB
        info = writeInfo.str();

        return info.c_str();
    }

    // funcao para obter a temperatura da cpu
    const char* getCpuTemperature() {
        static std::string info;
        info.clear();

        // tenta abrir o arquivo que contem a temperatura da cpu
        std::ifstream tempFile("/sys/class/thermal/thermal_zone0/temp");
        if (tempFile.is_open()) {
            int temp;
            tempFile >> temp; // le a temperatura em miligrados
            tempFile.close();

            std::ostringstream tempInfo;
            tempInfo.precision(2); 
            tempInfo << std::fixed << temp / 1000.0 << " °C";
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

            auto currentTime = std::chrono::steady_clock::now();
            std::chrono::duration<double> elapsedSeconds = currentTime - prevTime;

            if (elapsedSeconds.count() > 0) {
                double receiveRate = (totalReceived - prevTotalReceived) / elapsedSeconds.count();

                std::ostringstream netInfo;
                netInfo.precision(2);
                netInfo << std::fixed << (receiveRate / 1024);
                info = netInfo.str();
            }

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

            std::getline(netFile, line);
            std::getline(netFile, line);

            while (std::getline(netFile, line)) {
                std::istringstream ss(line);
                std::string iface;
                unsigned long long transmitted;
                // avanca 9 campos para chegar ao valor de transmissoes
                for (int i = 0; i < 9; ++i) ss >> transmitted;
                totalTransmitted += transmitted;
            }
            netFile.close();

            auto currentTime = std::chrono::steady_clock::now();
            std::chrono::duration<double> elapsedSeconds = currentTime - prevTime;

            if (elapsedSeconds.count() > 0) {
                double transmitRate = (totalTransmitted - prevTotalTransmitted) / elapsedSeconds.count();

                std::ostringstream netInfo;
                netInfo.precision(2);
                netInfo << std::fixed << (transmitRate / 1024);
                info = netInfo.str();
            }

            prevTotalTransmitted = totalTransmitted;
            prevTime = currentTime;
        } else {
            info = "Unable to read network stats";
        }

        return info.c_str();
    }

    // funcao para obter o uso da memoria swap
    const char* getSwapUsage() {
        static std::string info;
        info.clear();

        struct sysinfo sys_info;
        if (sysinfo(&sys_info) == 0) {
            double totalSwap = sys_info.totalswap / (1024.0 * 1024.0);  // convertendo para MB
            double freeSwap = sys_info.freeswap / (1024.0 * 1024.0);    // convertendo para MB
            double usedSwap = totalSwap - freeSwap;
            double swapUsagePercentage = (usedSwap / totalSwap) * 100.0;

            std::ostringstream swapInfo;
            swapInfo << std::fixed << std::setprecision(2) << swapUsagePercentage;
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

    // funcao para obter uso de cada core da cpu
    const char* getCpuInfo() {
        static std::string info;
        info.clear();
        std::ifstream cpuFile("/proc/cpuinfo");
        if (cpuFile.is_open()) {
            std::string line;
            std::ostringstream cpuInfo;
            while (std::getline(cpuFile, line)) {
                if (line.find("cpu MHz") != std::string::npos) {
                    // localiza a posicao do ":" e pega o valor apos ela
                    size_t pos = line.find(":");
                    if (pos != std::string::npos) {
                        std::string value = line.substr(pos + 1);
                        cpuInfo << value << "\t"; 
                    }
                }
            }
            cpuFile.close();
            info = cpuInfo.str();
        }
        return info.c_str();
    }

    std::string replaceTabsWithSpaces(const std::string& input) {
        std::string output = input;
        std::replace(output.begin(), output.end(), '\t', ' ');
        return output;
    }

    // funcao para obter informacoes detalhadas dos processos
    const char* getProcessesInfo() {
        static std::string info;

        std::ostringstream processesInfo;
        processesInfo << "\n";

        DIR* dir = opendir("/proc");
        if (!dir) {
            perror("Nao foi possível abrir /proc");
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
                        std::string threads = "0"; // inicializa threads com "0"
                        std::string state;
                        unsigned long vsize = 0;   // memória virtual
                        long rss = 0;              // memória física
                        std::string userName;

                        while (std::getline(statusFile, line)) {
                            line = replaceTabsWithSpaces(line);

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
                                vsize = std::stoul(line.substr(line.find(":") + 2)) / 1024; // em KB
                            }
                            if (line.find("VmRSS:") == 0) {
                                rss = std::stol(line.substr(line.find(":") + 2)) / 1024; // em KB
                            }
                            if (line.find("Uid:") == 0) {
                                // Obtém o UID do processo
                                std::string uid = line.substr(line.find(":") + 2);
                                uid = replaceTabsWithSpaces(uid); // Remove espaços extras
                                struct passwd *pw = getpwuid(std::stoi(uid));
                                if (pw != NULL) {
                                    userName = pw->pw_name; // Nome do usuário
                                }
                                else {
                                    userName = "Unknown"; // Se não encontrar o usuário
                                }
                            }
                        }
                        processesInfo << pid << "\t" << name << "\t" << userName << "\t" << state << "\t" 
                                    << threads << "\t" << vsize << "\t" << rss << "\n";
                        statusFile.close();
                    }
                }
            }
        }
        closedir(dir);
        
        info = processesInfo.str();
        return info.c_str();
    }

    const int killProcess(int pid) {
        if (kill(pid, SIGKILL) == -1) {
            return -1; // erro
        } else {
            return 0; // sucesso
        }
    }

    // funcao para obter informacoes especificas de um processo
    const char* getSpecificProcess(int pid) {
        static std::string info;
        info.clear();

        std::ostringstream processInfo;
        std::string processDir = "/proc/" + std::to_string(pid);
        std::string statusPath = processDir + "/status";

        std::ifstream statusFile(statusPath);
        if (statusFile.is_open()) {
            // Update section title
            processInfo << "Title 1\n";
            processInfo << "Process ID (PID): " << pid << "\n";

            std::string line;
            std::string name, state, vmRSS, vmSize, threadsCount;
            while (std::getline(statusFile, line)) {
                // Capture specific information
                if (line.find("Name:") == 0) name = line;
                else if (line.find("State:") == 0) state = line;
                else if (line.find("VmRSS:") == 0) vmRSS = line;
                else if (line.find("VmSize:") == 0) vmSize = line;
                else if (line.find("Threads:") == 0) threadsCount = line;

                // Add other relevant lines
                processInfo << line << "\n";
            }
            statusFile.close();

            // Add organized information
            processInfo << "\nTitle 2\n";
            if (!name.empty()) processInfo << name << "\n";
            if (!state.empty()) processInfo << state << "\n";
            if (!vmRSS.empty()) processInfo << "Resident Memory (RAM): " << vmRSS << "\n";
            if (!vmSize.empty()) processInfo << "Virtual Memory: " << vmSize << "\n";
            if (!threadsCount.empty()) processInfo << threadsCount << "\n";

            // Threads information
            std::string taskDir = processDir + "/task/";
            DIR* dir = opendir(taskDir.c_str());
            if (dir) {
                struct dirent* entry;
                processInfo << "\nTitle 3\n";

                while ((entry = readdir(dir)) != NULL) {
                    if (entry->d_type == DT_DIR) {
                        std::string tidStr = entry->d_name;
                        if (std::all_of(tidStr.begin(), tidStr.end(), ::isdigit)) {
                            int tid = std::stoi(tidStr);
                            std::string threadStatusPath = taskDir + tidStr + "/status";
                            std::ifstream threadStatusFile(threadStatusPath);
                            if (threadStatusFile.is_open()) {
                                processInfo << "Thread ID (TID): " << tid << "\n";
                                while (std::getline(threadStatusFile, line)) {
                                    if (line.find("State:") == 0 || line.find("VmRSS:") == 0 ||
                                        line.find("Name:") == 0 || line.find("Priority:") == 0) {
                                        processInfo << "  " << line << "\n";
                                    }
                                }
                                threadStatusFile.close();
                            }
                        }
                    }
                }
                closedir(dir);
            }
        } 
        info = processInfo.str();
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

    const char* getCpuIdlePercentage(SystemInfo* systemInfo) {
        return systemInfo->getCpuIdlePercentage();
    }

    const char* getThreadCount(SystemInfo* systemInfo) {
        return systemInfo->getThreadCount();
    }

    const char* getUsedDisk(SystemInfo* systemInfo) {
        return systemInfo->getUsedDisk();
    }

    const char* getFreeDisk(SystemInfo* systemInfo) {
        return systemInfo->getFreeDisk();
    }

    const char* getDiskRead(SystemInfo* systemInfo) {
        return systemInfo->getDiskRead();
    }

    const char* getDiskWrite(SystemInfo* systemInfo) {
        return systemInfo->getDiskWrite();
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

    const int killProcess(SystemInfo* systemInfo, int pid) {
        return systemInfo->killProcess(pid);
    }

    const char* getSpecificProcess(SystemInfo* systemInfo, int pid) {
        return systemInfo->getSpecificProcess(pid);
    }
}