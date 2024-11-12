import tkinter as tk
import time
from concurrent.futures import ThreadPoolExecutor
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from system_info import SystemInfo

cycle_time = 500  # milliseconds

class DashboardApp:
    def __init__(self, root):
        self.root = root
        self.root.title("System Dashboard")
        self.root.geometry("1600x610")
        self.root.resizable(False, False)

        self.sys_info = SystemInfo()

        self.labels = {}
        self.executor = ThreadPoolExecutor(max_workers=len(self.sys_info.fields))

        self.cpu_usage = 0
        self.mem_usage = 0

        self.setup_widgets()

        self.process_window = None

    def setup_widgets(self):
        # Configura o grid principal
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=1)  # Nova coluna para os gráficos

        # Frame para as informações do sistema
        info_frame = tk.Frame(self.root, bg="lightgray")
        info_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        # Adicionando os labels para informações do sistema
        for i, field in enumerate(self.sys_info.fields.keys()):
            frame = tk.Frame(info_frame, bg="white", padx=10, pady=5)
            frame.grid(row=i, column=0, sticky="ew", pady=3)
            label = tk.Label(frame, text=f"{field}:", font=("Arial", 12), anchor="center", bg="white")
            label.pack(fill="x", padx=5)
            self.labels[field] = label
            self.root.after(0, self.update_field, field)

        # Botão para exibir os processos
        self.process_button = tk.Button(self.root, text="Show Processes", command=self.show_processes)
        self.process_button.grid(row=1, column=0, pady=10, padx=10, sticky="ew")

        # Frame para os gráficos de CPU e Memória (coluna 1)
        self.cpu_memory_frame = tk.Frame(self.root)
        self.cpu_memory_frame.grid(row=0, column=1, rowspan=2, sticky="nsew", padx=10, pady=10)

        self.setup_graphs()

    def setup_graphs(self):
        # Criando a figura para os gráficos
        self.fig, (self.cpu_ax, self.mem_ax) = plt.subplots(2, 1, figsize=(6, 4))
        self.fig.tight_layout(pad=2.0)

        # Canvas para exibir os gráficos
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.cpu_memory_frame)
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # Atualizações periódicas dos gráficos
        self.root.after(cycle_time, self.update_cpu_graph)
        self.root.after(cycle_time, self.update_memory_graph)

    def update_field(self, field):
        value = self.sys_info.get_info(field)
        self.labels[field].config(text=f"{field}:\n{value}")
        self.root.after(cycle_time, self.update_field, field)

    def update_cpu_graph(self):
        self.cpu_usage = self.sys_info.get_cpu_usage()
        self.refresh_cpu_graph()
        self.root.after(cycle_time, self.update_cpu_graph)

    def refresh_cpu_graph(self):
        self.cpu_ax.clear()
        self.cpu_ax.barh([0], [self.cpu_usage], color="skyblue")  
        self.cpu_ax.set_xlim(0, 100)
        self.cpu_ax.set_title("CPU Usage (%)")
        self.cpu_ax.set_yticklabels([]) 
        self.canvas.draw()

    def update_memory_graph(self):
        self.mem_usage = self.sys_info.get_memory_usage()
        self.refresh_memory_graph()
        self.root.after(cycle_time, self.update_memory_graph)

    def refresh_memory_graph(self):
        self.mem_ax.clear()
        self.mem_ax.barh([0], [self.mem_usage], color="salmon")  
        self.mem_ax.set_xlim(0, 100)
        self.mem_ax.set_title("Memory Usage (%)")
        self.mem_ax.set_yticklabels([])  
        self.canvas.draw()

    def show_processes(self):
        if self.process_window is not None:
            self.process_window.destroy()

        self.process_window = tk.Toplevel(self.root)
        self.process_window.title("Process List")
        self.process_window.geometry("500x400")

        canvas = tk.Canvas(self.process_window)
        scrollbar = tk.Scrollbar(self.process_window, orient="vertical", command=canvas.yview)
        process_frame = tk.Frame(canvas)

        process_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=process_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        processes = self.sys_info.get_processes_info()
        
        for process in processes:
            text = f"PID: {process['pid']} | Name: {process['name']} | Status: {process['status']} | Memory: {process['memory']}"
            label = tk.Label(process_frame, text=text, font=("Arial", 10))
            label.pack(pady=3)

    def stop(self):
        self.executor.shutdown(wait=False)
        self.root.quit()
