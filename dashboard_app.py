import tkinter as tk
from tkinter import ttk
from concurrent.futures import ThreadPoolExecutor
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from system_info import SystemInfo
import psutil
import queue
import threading

cycle_time = 1000  # milliseconds
processes_thread = 5
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
        self.disk_usage_history = []
        self.network_receive_history = []
        self.network_transmit_history = []
        self.max_history_length = 50

        self.sys_info = SystemInfo()

        self.label_vars = {}  # Using StringVar for label updates
        self.labels = {}
        self.executor = ThreadPoolExecutor(max_workers=len(self.sys_info.fields) + processes_thread)

        self.result_queue = queue.Queue()

        self.setup_widgets()

        self.process_window = None

        # Start processing the result queue
        self.root.after(100, self.process_queue)

    def get_num_threads(self):
        global last_thread_num
        current_process = psutil.Process()
        num_threads = current_process.num_threads()
        if last_thread_num != num_threads:
            last_thread_num = num_threads
            print(f"Number of threads: {num_threads}")

    def setup_widgets(self): 
        # Main grid configuration
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=1)
        
        # Frame with Canvas and Scrollbar
        info_frame_container = tk.Frame(self.root, bg="lightgray")
        info_frame_container.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        info_frame_container.grid_rowconfigure(0, weight=1)
        info_frame_container.grid_columnconfigure(0, weight=1)

        # Scrollable Canvas
        canvas = tk.Canvas(info_frame_container, bg="lightgray")
        canvas.grid(row=0, column=0, sticky="nsew")
        
        # Vertical Scrollbar
        scrollbar = tk.Scrollbar(info_frame_container, orient="vertical", command=canvas.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Internal Frame for content
        info_frame = tk.Frame(canvas, bg="lightgray")
        canvas.create_window((0, 0), window=info_frame, anchor="nw")

        # Labels for system information
        for i, field in enumerate(self.sys_info.fields.keys()):
            frame = tk.Frame(info_frame, bg="white", padx=10, pady=5)
            frame.grid(row=i, column=0, sticky="ew", pady=3)
            frame.grid_columnconfigure(0, weight=1)
            self.label_vars[field] = tk.StringVar()
            label = tk.Label(frame, textvariable=self.label_vars[field], font=("Arial", 12), anchor="center", bg="white")
            label.pack(fill="x", padx=5)
            self.labels[field] = label
            # Schedule updates
            self.update_field(field)

        # Adjust canvas scroll region
        def update_scrollregion(event):
            canvas.configure(scrollregion=canvas.bbox("all"))

        info_frame.bind("<Configure>", update_scrollregion)

        # Button to show processes
        self.process_button = tk.Button(self.root, text="Show Processes", command=self.show_processes)
        self.process_button.grid(row=1, column=0, pady=10, padx=10, sticky="ew")

        # CPU and Memory graphs
        self.cpu_memory_frame = tk.Frame(self.root)
        self.cpu_memory_frame.grid(row=0, column=1, rowspan=2, sticky="nsew", padx=10, pady=10)
        self.cpu_memory_frame.grid_rowconfigure(0, weight=1)
        self.cpu_memory_frame.grid_columnconfigure(0, weight=1)

        self.setup_graphs()

    def setup_graphs(self):
        # Create figure for graphs
        self.fig, (self.cpu_ax, self.mem_ax, self.net_ax, self.disk_ax) = plt.subplots(4, 1, figsize=(6, 8))
        self.fig.tight_layout(pad=2.0)

        # Canvas to display graphs
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.cpu_memory_frame)
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # Initialize line objects
        self.cpu_line, = self.cpu_ax.plot([], [], color="skyblue", label="CPU Usage")
        self.mem_line, = self.mem_ax.plot([], [], color="salmon", label="Memory Usage")
        self.swap_line, = self.mem_ax.plot([], [], color="blue", label="Swap Usage")
        self.net_receive_line, = self.net_ax.plot([], [], color="lightgreen", label="Download")
        self.net_transmit_line, = self.net_ax.plot([], [], color="orange", label="Upload")
        self.disk_line, = self.disk_ax.plot([], [], color="purple", label="Disk Usage")

        self.cpu_ax.set_ylim(0, 100)
        self.cpu_ax.set_title("CPU Usage (%)")
        self.cpu_ax.set_xticks([])
        self.cpu_ax.legend()

        self.mem_ax.set_ylim(0, 100)
        self.mem_ax.set_title("Memory and Swap Usage (%)")
        self.mem_ax.set_xticks([])
        self.mem_ax.legend()

        self.net_ax.set_title("Network Usage (KB/s)")
        self.net_ax.set_xticks([])
        self.net_ax.legend()

        self.disk_ax.set_title("Disk Usage (%)")
        self.disk_ax.set_ylim(0, 100)
        self.disk_ax.set_xticks([])
        self.disk_ax.legend()

        # Schedule graph updates
        self.root.after(cycle_time, self.update_cpu_graph)
        self.root.after(cycle_time, self.update_memory_graph)
        self.root.after(cycle_time, self.update_network_graph)
        self.root.after(cycle_time, self.update_disk_graph)

    def update_field(self, field):
        # Heavy computation in a separate thread
        def worker():
            value = self.sys_info.get_info(field)
            self.result_queue.put(('field', field, value))
        threading.Thread(target=worker).start()
        self.root.after(cycle_time, self.update_field, field)

    def process_queue(self):
        while not self.result_queue.empty():
            item = self.result_queue.get()
            if item[0] == 'field':
                field, value = item[1], item[2]
                self.label_vars[field].set(f"{field}:\n{value}")
            elif item[0] == 'cpu':
                cpu_usage = item[1]
                self.cpu_usage_history.append(cpu_usage)
                if len(self.cpu_usage_history) > self.max_history_length:
                    self.cpu_usage_history.pop(0)
                self.refresh_cpu_graph()
            elif item[0] == 'memory':
                mem_usage, swap_usage = item[1], item[2]
                self.mem_usage_history.append(mem_usage)
                self.swap_usage_history.append(swap_usage)
                if len(self.mem_usage_history) > self.max_history_length:
                    self.mem_usage_history.pop(0)
                if len(self.swap_usage_history) > self.max_history_length:
                    self.swap_usage_history.pop(0)
                self.refresh_memory_graph()
            elif item[0] == 'network':
                receive_rate, transmit_rate = item[1], item[2]
                self.network_receive_history.append(receive_rate)
                self.network_transmit_history.append(transmit_rate)
                if len(self.network_receive_history) > self.max_history_length:
                    self.network_receive_history.pop(0)
                if len(self.network_transmit_history) > self.max_history_length:
                    self.network_transmit_history.pop(0)
                self.refresh_network_graph()
            elif item[0] == 'disk':
                disk_usage = item[1]
                self.disk_usage_history.append(disk_usage)
                if len(self.disk_usage_history) > self.max_history_length:
                    self.disk_usage_history.pop(0)
                self.refresh_disk_graph()
            elif item[0] == 'processes':
                processes = item[1]
                self.update_process_labels(processes)
        self.root.after(100, self.process_queue)

    def update_cpu_graph(self):
        # Heavy computation in a separate thread
        def worker():
            cpu_usage = self.sys_info.get_cpu_usage()
            self.result_queue.put(('cpu', cpu_usage))
        threading.Thread(target=worker).start()
        self.root.after(cycle_time, self.update_cpu_graph)

    def refresh_cpu_graph(self):
        xdata = range(len(self.cpu_usage_history))
        self.cpu_line.set_data(xdata, self.cpu_usage_history)
        self.cpu_ax.set_xlim(0, self.max_history_length)
        self.canvas.draw_idle()

    def update_memory_graph(self):
        # Heavy computation in a separate thread
        def worker():
            mem_usage = self.sys_info.get_memory_usage()
            swap_usage = self.sys_info.get_swap_usage()
            self.result_queue.put(('memory', mem_usage, swap_usage))
        threading.Thread(target=worker).start()
        self.root.after(cycle_time, self.update_memory_graph)

    def refresh_memory_graph(self):
        xdata = range(len(self.mem_usage_history))
        self.mem_line.set_data(xdata, self.mem_usage_history)
        self.swap_line.set_data(xdata, self.swap_usage_history)
        self.mem_ax.set_xlim(0, self.max_history_length)
        self.canvas.draw_idle()

    def update_network_graph(self):
        # Heavy computation in a separate thread
        def worker():
            receive_rate = self.sys_info.get_network_receive_rate()
            transmit_rate = self.sys_info.get_network_transmit_rate()
            self.result_queue.put(('network', receive_rate, transmit_rate))
        threading.Thread(target=worker).start()
        self.root.after(cycle_time, self.update_network_graph)

    def refresh_network_graph(self):
        xdata = range(len(self.network_receive_history))
        self.net_receive_line.set_data(xdata, self.network_receive_history)
        self.net_transmit_line.set_data(xdata, self.network_transmit_history)
        self.net_ax.set_xlim(0, self.max_history_length)
        max_rate = max(max(self.network_receive_history), max(self.network_transmit_history)) * 1.1
        if max_rate == 0:
            max_rate = 1  # Set a minimum y-limit
        self.net_ax.set_ylim(0, max_rate)
        self.canvas.draw_idle()

    def update_disk_graph(self):
        # Heavy computation in a separate thread
        def worker():
            used_disk = self.sys_info.get_used_disk()
            free_disk = self.sys_info.get_free_disk()
            total_disk = used_disk + free_disk
            disk_usage = (used_disk / total_disk) * 100 if total_disk > 0 else 0
            self.result_queue.put(('disk', disk_usage))
        threading.Thread(target=worker).start()
        self.root.after(cycle_time, self.update_disk_graph)

    def refresh_disk_graph(self):
        xdata = range(len(self.disk_usage_history))
        self.disk_line.set_data(xdata, self.disk_usage_history)
        self.disk_ax.set_xlim(0, self.max_history_length)
        self.canvas.draw_idle()

    def load_processes(self):
        self.process_labels = {}
        # Load processes in a separate thread
        def worker():
            processes_info = self.sys_info.get_processes_info()
            processes = self.parse_processes_info(processes_info)
            self.result_queue.put(('processes', processes))
        threading.Thread(target=worker).start()

    def refresh_processes(self):
        if self.process_window is None or not self.process_window.winfo_exists():
            return
        # Refresh processes in a separate thread
        def worker():
            processes_info = self.sys_info.get_processes_info()
            processes = self.parse_processes_info(processes_info)
            self.result_queue.put(('processes', processes))
        threading.Thread(target=worker).start()
        self.root.after(5000, self.refresh_processes)

    def update_process_labels(self, processes):
        if self.process_window is None or not self.process_window.winfo_exists():
            return
        # Filter active processes
        active_processes = [p for p in processes if p['status'] == 'running']
        # Update labels
        for pid, process in enumerate(active_processes):
            text = f"PID: {process['pid']} | Name: {process['name']} | Status: {process['status']} | Threads: {process['threads']} | Memory: {process['memory']}"
            if pid in self.process_labels:
                current_text = self.process_labels[pid]['text']
                if current_text != text:
                    self.process_labels[pid]['label'].config(text=text)
                    self.process_labels[pid]['text'] = text
            else:
                label = tk.Label(self.process_frame, text=text, font=("Arial", 10))
                label.pack(pady=3)
                self.process_labels[pid] = {'label': label, 'text': text}

    def show_processes(self):
        if self.process_window is not None and self.process_window.winfo_exists():
            return
        self.process_window = tk.Toplevel(self.root)
        self.process_window.title("Process Information")
        self.process_window.geometry("760x530")
        self.process_window.resizable(False, True)
        self.process_window.minsize(760, 200)
        # Canvas and scrollbar
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
        lines = processes_info.strip().split('\n')[1:]  # Ignore header line
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
        # Cancel scheduled process refresh
        pass

    def stop(self):
        self.executor.shutdown(wait=False)
        self.root.quit()