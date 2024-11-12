import tkinter as tk
import time
from concurrent.futures import ThreadPoolExecutor
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from system_info import SystemInfo

cycle_time = 500  # milliseconds
processes_thread = 1

class DashboardApp:
    def __init__(self, root):
        self.root = root
        self.root.title("System Dashboard")
        self.root.geometry("1600x610")
        self.root.resizable(True, True)

        self.sys_info = SystemInfo()

        self.labels = {}
        self.executor = ThreadPoolExecutor(max_workers=len(self.sys_info.fields) + processes_thread)

        self.cpu_usage = 0
        self.mem_usage = 0

        self.setup_widgets()

        self.process_window = None

    def setup_widgets(self):
        # grid principal
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=1)

        # infos do sistema
        info_frame = tk.Frame(self.root, bg="lightgray")
        info_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        info_frame.grid_rowconfigure(0, weight=1)
        info_frame.grid_columnconfigure(0, weight=1)

        # labels para infos do sistema
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

        # gráficos de cpu e memoria
        self.cpu_memory_frame = tk.Frame(self.root)
        self.cpu_memory_frame.grid(row=0, column=1, rowspan=2, sticky="nsew", padx=10, pady=10)
        self.cpu_memory_frame.grid_rowconfigure(0, weight=1)
        self.cpu_memory_frame.grid_columnconfigure(0, weight=1)

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
        self.process_window.geometry("790x500")

        # Canvas e Scrollbar para a lista de processos
        process_canvas = tk.Canvas(self.process_window)  # Renomeado para evitar conflito
        scrollbar = tk.Scrollbar(self.process_window, orient="vertical", command=process_canvas.yview)
        self.process_frame = tk.Frame(process_canvas)

        self.process_frame.bind(
            "<Configure>",
            lambda e: process_canvas.configure(scrollregion=process_canvas.bbox("all"))
        )

        process_canvas.create_window((0, 0), window=self.process_frame, anchor="nw")
        process_canvas.configure(yscrollcommand=scrollbar.set)

        process_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Botão de Refresh
        refresh_button = tk.Button(self.process_window, text="Refresh", command=lambda: self.executor.submit(self.refresh_processes))
        refresh_button.pack(pady=5)

        # Carregar processos iniciais assincronamente
        self.executor.submit(self.load_processes)


    def load_processes(self):
        self.process_labels = []
        
        # Initial process info loading, creating a label for each process.
        processes = self.sys_info.get_processes_info()
        for process in processes:
            text = f"PID: {process['pid']} | Name: {process['name']} | Status: {process['status']} | Memory: {process['memory']}"
            label = tk.Label(self.process_frame, text=text, font=("Arial", 10))
            label.pack(pady=3)
            self.process_labels.append(label)

    def refresh_processes(self):
        processes = self.sys_info.get_processes_info()

        # Adjust the number of labels based on the current process list
        if len(processes) > len(self.process_labels):
            for _ in range(len(processes) - len(self.process_labels)):
                label = tk.Label(self.process_frame, font=("Arial", 10))
                label.pack(pady=3)
                self.process_labels.append(label)
        elif len(processes) < len(self.process_labels):
            for i in range(len(self.process_labels) - len(processes)):
                self.process_labels[i].pack_forget()

        # Update each label's text and re-pack it
        for i, process in enumerate(processes):
            text = f"PID: {process['pid']} | Name: {process['name']} | Status: {process['status']} | Memory: {process['memory']}"
            self.process_labels[i].config(text=text)
            self.process_labels[i].pack()



    def stop(self):
        self.executor.shutdown(wait=False)
        self.root.quit()
