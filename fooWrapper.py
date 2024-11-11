import tkinter as tk
import threading
from ctypes import cdll, c_char_p
import time

cycle_time = 0.5  # segundos

# carrega a biblioteca 
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
        # retorna a informação individual para o campo solicitado
        func = self.fields[field]
        return func(self.obj).decode('utf-8')

class DashboardApp:
    def __init__(self, root):
        self.root = root
        self.root.title("System Dashboard")

        # instancia que chama as funções c++
        self.sys_info = SystemInfo()

        # criação dos labels
        self.labels = {}
        self.threads = {}

        for field in self.sys_info.fields.keys():
            label = tk.Label(root, text=f"{field}:", font=("Arial", 16))
            label.pack(pady=10)
            self.labels[field] = label
            # cria uma thread para atualizar cada campo individualmente
            thread = threading.Thread(target=self.update_field, args=(field,))
            thread.daemon = True
            thread.start()
            self.threads[field] = thread

    def update_field(self, field):
        while True:
            # obter a informação do campo específico
            value = self.sys_info.get_info(field)

            # atualiza o label do campo específico
            self.labels[field].config(text=f"{field}:\n{value}")

            # aguarda o próximo ciclo de atualização
            time.sleep(cycle_time)

    # parar todas as threads
    def stop(self):
        self.root.quit()

root = tk.Tk()
app = DashboardApp(root)

root.protocol("WM_DELETE_WINDOW", app.stop)
root.mainloop()
