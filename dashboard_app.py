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
        
        self.cpu_usage_history = []
        self.mem_usage_history = []
        self.swap_usage_history = []
        self.network_receive_history = []
        self.network_transmit_history = []
        self.max_history_length = 100

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
        # Grid principal
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=1)
        
        # Frame contendo Canvas e Scrollbar
        info_frame_container = tk.Frame(self.root, bg="lightgray")
        info_frame_container.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        info_frame_container.grid_rowconfigure(0, weight=1)
        info_frame_container.grid_columnconfigure(0, weight=1)

        # Canvas para tornar o frame rolável
        canvas = tk.Canvas(info_frame_container, bg="lightgray")
        canvas.grid(row=0, column=0, sticky="nsew")
        
        # Scrollbar vertical
        scrollbar = tk.Scrollbar(info_frame_container, orient="vertical", command=canvas.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Frame interno para conteúdo
        info_frame = tk.Frame(canvas, bg="lightgray")
        canvas.create_window((0, 0), window=info_frame, anchor="nw")

        # Labels para informações do sistema
        for i, field in enumerate(self.sys_info.fields.keys()):
            frame = tk.Frame(info_frame, bg="white", padx=10, pady=5)
            frame.grid(row=i, column=0, sticky="ew", pady=3)
            frame.grid_columnconfigure(0, weight=1)
            label = tk.Label(frame, text=f"{field}:", font=("Arial", 12), anchor="center", bg="white")
            label.pack(fill="x", padx=5)
            self.labels[field] = label
            self.root.after(0, self.update_field, field)

        # Ajusta o tamanho do canvas ao conteúdo
        def update_scrollregion(event):
            canvas.configure(scrollregion=canvas.bbox("all"))

        info_frame.bind("<Configure>", update_scrollregion)

        # Botão da página de processos
        self.process_button = tk.Button(self.root, text="Show Processes", command=self.show_processes)
        self.process_button.grid(row=1, column=0, pady=10, padx=10, sticky="ew")

        # Gráficos de CPU e memória
        self.cpu_memory_frame = tk.Frame(self.root)
        self.cpu_memory_frame.grid(row=0, column=1, rowspan=2, sticky="nsew", padx=10, pady=10)
        self.cpu_memory_frame.grid_rowconfigure(0, weight=1)
        self.cpu_memory_frame.grid_columnconfigure(0, weight=1)

        self.setup_graphs()

    def setup_graphs(self):
        # criando a figura para os graficos
        self.fig, (self.cpu_ax, self.mem_ax, self.net_ax) = plt.subplots(3, 1, figsize=(6, 6))
        self.fig.tight_layout(pad=2.0)

        # canvas para exibir os graficos
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.cpu_memory_frame)
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # atualizacoes periodicas dos graficos
        self.root.after(cycle_time, self.update_cpu_graph)
        self.root.after(cycle_time, self.update_memory_graph)
        self.root.after(cycle_time, self.update_network_graph)
        #self.root.after(cycle_time, self.update_disk_graph)

    def update_field(self, field):
        value = self.sys_info.get_info(field)
        self.labels[field].config(text=f"{field}:\n{value}")
        self.root.after(cycle_time, self.update_field, field)

        self.get_num_threads()

    def update_cpu_graph(self):
        self.cpu_usage = self.sys_info.get_cpu_usage()
        self.cpu_usage_history.append(self.cpu_usage)
        if len(self.cpu_usage_history) > self.max_history_length:
            self.cpu_usage_history.pop(0)
        self.refresh_cpu_graph()
        self.root.after(cycle_time, self.update_cpu_graph)

    def refresh_cpu_graph(self):
        self.cpu_ax.clear()
        self.cpu_ax.plot(self.cpu_usage_history, color="skyblue")
        self.cpu_ax.set_ylim(0, 100)
        self.cpu_ax.set_title("CPU Usage (%)")
        self.cpu_ax.set_yticklabels([])
        self.canvas.draw()

    def update_memory_graph(self):
        self.mem_usage = self.sys_info.get_memory_usage()
        self.swap_usage = self.sys_info.get_swap_usage()
        self.mem_usage_history.append(self.mem_usage)
        self.swap_usage_history.append(self.swap_usage)
        if len(self.mem_usage_history) > self.max_history_length:
            self.mem_usage_history.pop(0)
        if len(self.swap_usage_history) > self.max_history_length:
            self.swap_usage_history.pop(0)
        self.refresh_memory_graph()
        self.root.after(cycle_time, self.update_memory_graph)

    def refresh_memory_graph(self):
        self.mem_ax.clear()
        self.mem_ax.plot(self.mem_usage_history, color="salmon", label="Memory Usage")
        self.mem_ax.plot(self.swap_usage_history, color="blue", label="Swap Usage")
        self.mem_ax.set_ylim(0, 100)
        self.mem_ax.set_title("Memory and Swap Usage (%)")
        self.mem_ax.set_yticklabels([])
        self.mem_ax.legend()
        self.canvas.draw()

    def update_network_graph(self):
        receive_rate = self.sys_info.get_network_receive_rate()
        transmit_rate = self.sys_info.get_network_transmit_rate()
        self.network_receive_history.append(receive_rate)
        self.network_transmit_history.append(transmit_rate)
        if len(self.network_receive_history) > self.max_history_length:
            self.network_receive_history.pop(0)
        if len(self.network_transmit_history) > self.max_history_length:
            self.network_transmit_history.pop(0)
        self.refresh_network_graph()
        self.root.after(cycle_time, self.update_network_graph)

    def refresh_network_graph(self):
        self.net_ax.clear()
        self.net_ax.plot(self.network_receive_history, color="lightgreen", label="Download")
        self.net_ax.plot(self.network_transmit_history, color="orange", label="Upload")
        self.net_ax.set_ylim(0, max(max(self.network_receive_history), max(self.network_transmit_history)) * 1.1)
        self.net_ax.set_title("Network Usage (KB/s)")
        self.net_ax.set_yticklabels([])
        self.net_ax.legend()
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
        self.process_window.geometry("760x530")
        self.process_window.resizable(False, True)
        self.process_window.minsize(760, 200)

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