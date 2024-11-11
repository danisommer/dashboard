import tkinter as tk
import threading
import time
import os
from ctypes import cdll, c_char_p

cycle_time = 0.5  # segundos para atualizacao

# carrega a biblioteca C++
lib = cdll.LoadLibrary('./libGetSysInfo.so')


class SystemInfo:
    def __init__(self):
        self.obj = lib.SystemInfo_new()

        # lista de funcoes a serem chamadas
        self.fields = {
            "System Info": lib.getSystemInfo,
            "Total Memory": lib.getTotalMemory,
            "Free Memory": lib.getFreeMemory,
            "Uptime": lib.getUptime,
            "Load Average": lib.getLoadAverage,
            "Process Count": lib.getProcessCount
        }

        # define o tipo de retorno
        for func in self.fields.values():
            func.restype = c_char_p

    def get_info(self, field):
        # retorna a informacao individual para o campo solicitado
        func = self.fields[field]
        return func(self.obj).decode('utf-8')

    def get_processes_info(self):
        processes = []
        for pid in os.listdir('/proc'):
            if pid.isdigit():
                process_info = {}
                with open(f'/proc/{pid}/stat') as f:
                    data = f.read().split()
                    process_info['pid'] = pid
                    process_info['name'] = data[1]
                    process_info['status'] = data[2]
                    process_info['memory'] = self.get_process_memory(pid)
                    processes.append(process_info)
        return processes

    def get_process_memory(self, pid):
        with open(f'/proc/{pid}/status') as f:
            for line in f:
                if line.startswith('VmRSS'):
                    return line.strip().split()[1] + ' KB'
        return 'N/A'


class DashboardApp:
    def __init__(self, root):
        self.root = root
        self.root.title("System Dashboard")
        
        # instancia que chama as funcoes C++
        self.sys_info = SystemInfo()
        
        # criacao dos labels
        self.labels = {}
        self.threads = {}
        
        # cria uma thread para atualizar cada campo individualmente
        for field in self.sys_info.fields.keys():
            label = tk.Label(root, text=f"{field}:", font=("Arial", 16))
            label.pack(pady=10)
            self.labels[field] = label

            thread = threading.Thread(target=self.update_field, args=(field,))
            thread.daemon = True
            thread.start()
            self.threads[field] = thread
        
        # tela para exibir os processos
        self.process_button = tk.Button(root, text="Show Processes", command=self.show_processes)
        self.process_button.pack(pady=10)
        
        self.process_window = None

    def update_field(self, field):
        while True:
            # obter a informacao do campo específico
            value = self.sys_info.get_info(field)

            # atualiza o label do campo específico
            self.labels[field].config(text=f"{field}:\n{value}")

            # aguarda o próximo ciclo de atualizacao
            time.sleep(cycle_time)

    def show_processes(self):
        # exibe uma nova janela com os processos
        if self.process_window is not None:
            self.process_window.destroy()

        self.process_window = tk.Toplevel(self.root)
        self.process_window.title("Process List")
        
        processes = self.sys_info.get_processes_info()
        
        # adiciona informacoes dos processos na nova janela
        for process in processes:
            text = f"PID: {process['pid']} | Name: {process['name']} | Status: {process['status']} | Memory: {process['memory']}"
            label = tk.Label(self.process_window, text=text, font=("Arial", 10))
            label.pack(pady=5)
        
        # botao para fechar a janela de processos
        close_button = tk.Button(self.process_window, text="Close", command=self.process_window.destroy)
        close_button.pack(pady=10)
    
    def stop(self):
        self.root.quit()


root = tk.Tk()
app = DashboardApp(root)

root.protocol("WM_DELETE_WINDOW", app.stop)
root.mainloop()
