import tkinter as tk
from tkinter import ttk
from concurrent.futures import ThreadPoolExecutor
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from system_info import SystemInfo
import psutil


cycle_time = 500  # milissegundos
processes_thread = 10
last_thread_num = 0

class DashboardApp:
    def __init__(self, root):
        self.root = root
        self.root.title("System Dashboard")
        self.root.geometry("1200x530")
        self.root.resizable(True, False)

        self.root.minsize(600, 500)
        self.sys_info = SystemInfo()

        self.labels = {}
        self.executor = ThreadPoolExecutor(max_workers=len(self.sys_info.fields) + processes_thread)

        self.cpu_usage = 0
        self.mem_usage = 0

        self.setup_widgets()

        self.process_window = None
        
    def get_num_threads(self):
        global last_thread_num
        current_process = psutil.Process()
        num_threads = current_process.num_threads()

        if last_thread_num != num_threads:
            last_thread_num = num_threads
            print(f"Number of threads: {num_threads}")

    def setup_widgets(self):
        # grid principal
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=1)

        # informacoes do sistema
        info_frame = tk.Frame(self.root, bg="lightgray")
        info_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        info_frame.grid_rowconfigure(0, weight=1)
        info_frame.grid_columnconfigure(0, weight=1)

        # labels para informacoes do sistema
        for i, field in enumerate(self.sys_info.fields.keys()):
            frame = tk.Frame(info_frame, bg="white", padx=10, pady=5)
            frame.grid(row=i, column=0, sticky="ew", pady=3)
            frame.grid_columnconfigure(0, weight=1)
            label = tk.Label(frame, text=f"{field}:", font=("Arial", 12), anchor="center", bg="white")
            label.pack(fill="x", padx=5)
            self.labels[field] = label
            self.root.after(0, self.update_field, field)

        # botao da pagina de processos
        self.process_button = tk.Button(self.root, text="Show Processes", command=self.show_processes)
        self.process_button.grid(row=1, column=0, pady=10, padx=10, sticky="ew")

        # graficos de CPU e memoria
        self.cpu_memory_frame = tk.Frame(self.root)
        self.cpu_memory_frame.grid(row=0, column=1, rowspan=2, sticky="nsew", padx=10, pady=10)
        self.cpu_memory_frame.grid_rowconfigure(0, weight=1)
        self.cpu_memory_frame.grid_columnconfigure(0, weight=1)

        self.setup_graphs()

    def setup_graphs(self):
        # criando a figura para os graficos
        self.fig, (self.cpu_ax, self.mem_ax) = plt.subplots(2, 1, figsize=(6, 4))
        self.fig.tight_layout(pad=2.0)

        # canvas para exibir os graficos
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.cpu_memory_frame)
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # atualizacoes periodicas dos graficos
        self.root.after(cycle_time, self.update_cpu_graph)
        self.root.after(cycle_time, self.update_memory_graph)

    def update_field(self, field):
        value = self.sys_info.get_info(field)
        self.labels[field].config(text=f"{field}:\n{value}")
        self.root.after(cycle_time, self.update_field, field)

        self.get_num_threads()

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

    def load_processes(self):
        self.process_labels = []
        
        # carregamento inicial das informacoes de processos, criando um label para cada processo
        processes_info = self.sys_info.get_processes_info()
        processes = self.parse_processes_info(processes_info)
        for process in processes:
            text = f"PID: {process['pid']} | Name: {process['name']} | Status: {process['status']} | Memory: {process['memory']}"
            label = tk.Label(self.process_frame, text=text, font=("Arial", 10))
            label.pack(pady=3)
            self.process_labels.append(label)

    def refresh_processes(self):
        # verifica se a janela de processos ainda está aberta
        if self.process_window is None or not self.process_window.winfo_exists():
            return

        processes_info = self.sys_info.get_processes_info()
        processes = self.parse_processes_info(processes_info)

        # ajusta o número de labels com base na lista atual de processos
        if len(processes) > len(self.process_labels):
            for _ in range(len(processes) - len(self.process_labels)):
                label = tk.Label(self.process_frame, font=("Arial", 10))
                label.pack(pady=3)
                self.process_labels.append(label)

        # atualiza o texto de cada label com as novas informacoes de processos
        for i, process in enumerate(processes):
            text = f"PID: {process['pid']} | Name: {process['name']} | Status: {process['status']} | Threads: {process['threads']} | Memory: {process['memory']}"
            self.process_labels[i].config(text=text)

        # agenda a próxima atualização
        self.refresh_processes_id = self.root.after(5000, self.refresh_processes)

    def show_processes(self):
        if self.process_window is not None and self.process_window.winfo_exists():
            return

        self.process_window = tk.Toplevel(self.root)
        self.process_window.title("Process Information")

        # canvas e scrollbar
        self.process_canvas = tk.Canvas(self.process_window)
        self.scrollbar = ttk.Scrollbar(self.process_window, orient="vertical", command=self.process_canvas.yview)
        self.scrollbar.pack(side="right", fill="y")
        self.process_canvas.pack(side="left", fill="both", expand=True)
        self.process_canvas.configure(yscrollcommand=self.scrollbar.set)

        self.process_frame = ttk.Frame(self.process_canvas)
        self.process_canvas.create_window((0, 0), window=self.process_frame, anchor="nw")

        self.process_frame.bind("<Configure>", lambda e: self.process_canvas.configure(scrollregion=self.process_canvas.bbox("all")))

        self.load_processes()
        self.refresh_processes()

    def parse_processes_info(self, processes_info):
        processes = []
        lines = processes_info.split('\n')[1:]  # ignora a primeira linha
        for line in lines:
            if line.strip():
                parts = line.split('\t')
                process = {
                    'pid': parts[0],
                    'name': parts[1],
                    'status': parts[2],
                    'threads': parts[3],
                    'memory': f"Virtual: {parts[4]}, Physical: {parts[5]}"
                }
                processes.append(process)
        return processes

    def stop_refreshing_processes(self):
        if self.refresh_processes_id is not None:
            self.root.after_cancel(self.refresh_processes_id)
            self.refresh_processes_id = None

    def stop(self):
        self.executor.shutdown(wait=False)
        self.root.quit()