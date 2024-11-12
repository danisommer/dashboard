import tkinter as tk
import time
from concurrent.futures import ThreadPoolExecutor
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from system_info import SystemInfo

cycle_time = 0.5  # segundos

class DashboardApp:
    def __init__(self, root):
        self.root = root
        self.root.title("System Dashboard")
        self.root.geometry("600x900")
        
        self.sys_info = SystemInfo()
        
        self.labels = {}
        self.executor = ThreadPoolExecutor(max_workers=len(self.sys_info.fields))
        
        self.cpu_usage = 0
        self.mem_usage = 0
        
        self.setup_widgets()
        
        self.process_window = None

    def setup_widgets(self):
        # frames para organizar layout
        info_frame = tk.Frame(self.root, bg="lightgray")
        info_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # adiciona rotulos para as informacoes do sistema
        for field in self.sys_info.fields.keys():
            frame = tk.Frame(info_frame, bg="white")
            frame.pack(fill="x", pady=5)
            label = tk.Label(frame, text=f"{field}:", font=("Arial", 14), anchor="center", bg="white")
            label.pack(fill="x", padx=10, pady=2)
            self.labels[field] = label
            self.executor.submit(self.update_field, field)

        # botao para exibir processos
        self.process_button = tk.Button(self.root, text="Show Processes", command=self.show_processes)
        self.process_button.pack(pady=10)

        # adiciona graficos para monitoramento de CPU e Memoria
        self.cpu_memory_frame = tk.Frame(self.root)
        self.cpu_memory_frame.pack(fill="both", expand=True)

        self.setup_graphs()

    def setup_graphs(self):
        # cria figura do matplotlib
        self.fig, (self.cpu_ax, self.mem_ax) = plt.subplots(2, 1, figsize=(5, 3))
        self.fig.tight_layout(pad=2.0)
        
        # canvas para exibir graficos
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.cpu_memory_frame)
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        # atualiza graficos em threads separadas
        self.executor.submit(self.update_cpu_graph)
        self.executor.submit(self.update_memory_graph)

    def update_field(self, field):
        while True:
            value = self.sys_info.get_info(field)
            self.labels[field].config(text=f"{field}:\n{value}")
            time.sleep(cycle_time)

    def update_cpu_graph(self):
        while True:
            self.cpu_usage = self.sys_info.get_cpu_usage()
            self.root.after(0, self.refresh_cpu_graph)  # Update graph in the main thread
            time.sleep(cycle_time)

    def refresh_cpu_graph(self):
        self.cpu_ax.clear()
        self.cpu_ax.barh(["CPU"], [self.cpu_usage], color="skyblue")
        self.cpu_ax.set_xlim(0, 100)
        self.cpu_ax.set_title("CPU Usage (%)")
        self.canvas.draw()

    def update_memory_graph(self):
        while True:
            self.mem_usage = self.sys_info.get_memory_usage()
            self.root.after(0, self.refresh_memory_graph)  # Update graph in the main thread
            time.sleep(cycle_time)

    def refresh_memory_graph(self):
        self.mem_ax.clear()
        self.mem_ax.barh(["Memory"], [self.mem_usage], color="salmon")
        self.mem_ax.set_xlim(0, 100)
        self.mem_ax.set_title("Memory Usage (%)")
        self.canvas.draw()

    def show_processes(self):
        if self.process_window is not None:
            self.process_window.destroy()

        self.process_window = tk.Toplevel(self.root)
        self.process_window.title("Process List")
        self.process_window.geometry("500x500")

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
            label.pack(pady=5)

    def stop(self):
        self.executor.shutdown(wait=False)
        self.root.quit()
