import tkinter as tk
from tkinter import ttk
from concurrent.futures import ThreadPoolExecutor
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from system_info import SystemInfo
import queue
import threading

cycle_time = 1000  # milissegundos
cycle_time_graphs = 500  # milissegundos
cycle_time_processes = 1000  # milissegundos
cycle_time_process_detail = 500  # milissegundos
last_selected_process = None
processes_thread = 5
last_thread_num = 0

class DashboardApp:
    def __init__(self, root):
        self.root = root
        self.root.title("System Dashboard")
        self.root.geometry("1200x590")
        self.root.resizable(True, True)
        self.root.minsize(800, 590)
        self.heading_click_locked = False 

        self.cpu_usage_history = []
        self.mem_usage_history = []
        self.swap_usage_history = []
        self.disk_read_history = []
        self.disk_write_history = []
        self.network_receive_history = []
        self.network_transmit_history = []
        self.cpu_core_lines = []
        self.max_history_length = 50

        self.sys_info = SystemInfo()
        self.num_cores = len(self.sys_info.get_cpu_usage_per_core())
        self.cpu_core_usage_histories = [[] for _ in range(self.num_cores)]

        self.label_vars = {}
        self.labels = {}
        self.executor = ThreadPoolExecutor(max_workers=len(self.sys_info.fields) + processes_thread)

        self.result_queue = queue.Queue()

        self.setup_widgets()

        self.process_window = None

        self.initialize_cpu_core_histories()
        self.initialize_memory_histories()
        self.initialize_network_histories()
        self.initialize_disk_histories()
        self.root.after(100, self.process_queue)
        
    #funcoes de inicializacao de historicos dos graficos
    def initialize_cpu_core_histories(self):
        core_usages = self.sys_info.get_cpu_usage_per_core()
        for core_index, usage in enumerate(core_usages):
            # inicializa o historico de uso de cada nucleo com zeros
            self.cpu_core_usage_histories[core_index] = [0] * self.max_history_length
    def initialize_memory_histories(self):
        mem_usage = self.sys_info.get_memory_usage()
        swap_usage = self.sys_info.get_swap_usage()
        self.mem_usage_history = [mem_usage] * self.max_history_length
        self.swap_usage_history = [swap_usage] * self.max_history_length
    def initialize_network_histories(self):
        receive_rate = self.sys_info.get_network_receive_rate()
        transmit_rate = self.sys_info.get_network_transmit_rate()
        self.network_receive_history = [receive_rate] * self.max_history_length
        self.network_transmit_history = [transmit_rate] * self.max_history_length
    def initialize_disk_histories(self):
        disk_read = self.sys_info.get_disk_read()
        disk_write = self.sys_info.get_disk_write()
        self.disk_read_history = [disk_read] * self.max_history_length
        self.disk_write_history = [disk_write] * self.max_history_length

    def setup_widgets(self): 
        # configuracao principal da grade
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=1)
        
        # quadro para conteudo
        info_frame = tk.Frame(self.root, bg="lightgray")
        info_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        info_frame.grid_rowconfigure(0, weight=1)
        info_frame.grid_columnconfigure(0, weight=1)

        # rotulos para informacoes do sistema
        for i, field in enumerate(self.sys_info.fields.keys()):
            frame = tk.Frame(info_frame, bg="white", padx=10, pady=5)
            frame.grid(row=i, column=0, sticky="ew", pady=3)
            frame.grid_columnconfigure(0, weight=1)
            self.label_vars[field] = tk.StringVar()
            label = tk.Label(frame, textvariable=self.label_vars[field], font=("Arial", 12), anchor="center", bg="white")
            label.pack(fill="x", padx=5)
            self.labels[field] = label
            # agendar atualizacoes
            self.update_field(field)

        # botao para mostrar processos
        self.process_button = tk.Button(self.root, text="Show Processes", command=self.show_processes)
        self.process_button.grid(row=1, column=0, pady=10, padx=10, sticky="ew")

        # graficos de cpu e memoria
        self.cpu_memory_frame = tk.Frame(self.root)
        self.cpu_memory_frame.grid(row=0, column=1, rowspan=2, sticky="nsew", padx=10, pady=10)
        self.cpu_memory_frame.grid_rowconfigure(0, weight=1)
        self.cpu_memory_frame.grid_columnconfigure(0, weight=1)

        self.setup_graphs()

    def setup_graphs(self):
        # criar figura para graficos
        self.fig, ((self.cpu_ax, self.mem_ax), (self.net_ax, self.disk_ax)) = plt.subplots(2, 2, figsize=(12, 8))
        self.fig.tight_layout(pad=2.0)

        # canvas para exibir graficos
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.cpu_memory_frame)
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # inicializar objetos de linha
        self.mem_line, = self.mem_ax.plot([], [], color="salmon", label="Memory Usage")
        self.swap_line, = self.mem_ax.plot([], [], color="blue", label="Swap Usage")
        self.net_receive_line, = self.net_ax.plot([], [], color="lightgreen", label="Download")
        self.net_transmit_line, = self.net_ax.plot([], [], color="orange", label="Upload")
        self.disk_read_line, = self.disk_ax.plot([], [], color="purple", label="Disk Read")
        self.disk_write_line, = self.disk_ax.plot([], [], color="red", label="Disk Write")

        self.cpu_ax.set_ylim(0, 100)
        self.cpu_ax.set_title("CPU Usage (MHz)")
        self.cpu_ax.set_xticks([])

        self.mem_ax.set_ylim(0, 100)
        self.mem_ax.set_title("Memory and Swap Usage (%)")
        self.mem_ax.set_xticks([])
        self.mem_ax.legend()

        self.net_ax.set_title("Network Usage (KB/s)")
        self.net_ax.set_xticks([])
        self.net_ax.legend()

        self.disk_ax.set_title("Disk Usage (MB/s)")
        self.disk_ax.set_ylim(0, 100)
        self.disk_ax.set_xticks([])
        self.disk_ax.legend()

        for core in range(self.num_cores):
            line, = self.cpu_ax.plot([], [], label=f"Core {core + 1}")
            self.cpu_core_lines.append(line)

        self.cpu_ax.legend()

        # agendar atualizacoes dos graficos
        self.root.after(cycle_time, self.update_cpu_graph)
        self.root.after(cycle_time, self.update_memory_graph)
        self.root.after(cycle_time, self.update_network_graph)
        self.root.after(cycle_time, self.update_disk_graph)
        
    def update_field(self, field):
        def worker():
            value = self.sys_info.get_info(field)
            self.result_queue.put(('field', field, value))
        self.executor.submit(worker)
        self.root.after(cycle_time, self.update_field, field)

    def process_queue(self):
        while not self.result_queue.empty():
            item = self.result_queue.get()
            if item[0] == 'field':
                field, value = item[1], item[2]
                self.label_vars[field].set(f"{field}:\n{value}")
            elif item[0] == 'cpu':
                core_usages = item[1]
                for core_index, usage in enumerate(core_usages):
                    self.cpu_core_usage_histories[core_index].append(usage)
                    if len(self.cpu_core_usage_histories[core_index]) > self.max_history_length:
                        self.cpu_core_usage_histories[core_index].pop(0)
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
                disk_read, disk_write = item[1], item[2]
                self.disk_read_history.append(disk_read)
                self.disk_write_history.append(disk_write)
                if len(self.disk_read_history) > self.max_history_length:
                    self.disk_read_history.pop(0)
                if len(self.disk_write_history) > self.max_history_length:
                    self.disk_write_history.pop(0)
                self.refresh_disk_graph()
            elif item[0] == 'processes_update':
                processes = item[1]
                self.refresh_process_tree(processes)
        self.root.after(100, self.process_queue)

    # funcoes de atualizacao e refresh do grafico de cpu
    def update_cpu_graph(self):
        def worker():
            core_usages = self.sys_info.get_cpu_usage_per_core()
            self.result_queue.put(('cpu', core_usages))
        self.executor.submit(worker)
        self.root.after(cycle_time_graphs, self.update_cpu_graph)
    def refresh_cpu_graph(self):
        xdata = range(len(self.cpu_core_usage_histories[0]))
        for core_index, line in enumerate(self.cpu_core_lines):
            ydata = self.cpu_core_usage_histories[core_index]
            # calcular a media usando os ultimos 10 valores
            avg_ydata = [sum(ydata[max(0, i - 9):i + 1]) / min(10, i + 1) for i in range(len(ydata))]            
            line.set_data(xdata[-len(avg_ydata):], avg_ydata)
        self.cpu_ax.set_xlim(0, self.max_history_length)
        self.cpu_ax.set_ylim(0, max(max(core_data) for core_data in self.cpu_core_usage_histories) * 1.1)
        self.canvas.draw_idle()

    # funcoes de atualizacao e refresh dos graficos de memoria
    def update_memory_graph(self):
        def worker():
            mem_usage = self.sys_info.get_memory_usage()
            swap_usage = self.sys_info.get_swap_usage()
            self.result_queue.put(('memory', mem_usage, swap_usage))
        self.executor.submit(worker)
        self.root.after(cycle_time_graphs, self.update_memory_graph)
    def refresh_memory_graph(self):
        xdata = range(len(self.mem_usage_history))
        self.mem_line.set_data(xdata, self.mem_usage_history)
        self.swap_line.set_data(xdata, self.swap_usage_history)
        self.mem_ax.set_xlim(0, self.max_history_length)
        self.canvas.draw_idle()

    # funcoes de atualizacao e refresh dos graficos de rede
    def update_network_graph(self):
        def worker():
            receive_rate = self.sys_info.get_network_receive_rate()
            transmit_rate = self.sys_info.get_network_transmit_rate()
            self.result_queue.put(('network', receive_rate, transmit_rate))
        self.executor.submit(worker)
        self.root.after(cycle_time_graphs, self.update_network_graph)
    def refresh_network_graph(self):
        xdata = range(len(self.network_receive_history))
        self.net_receive_line.set_data(xdata, self.network_receive_history)
        self.net_transmit_line.set_data(xdata, self.network_transmit_history)
        self.net_ax.set_xlim(0, self.max_history_length)
        max_rate = max(max(self.network_receive_history), max(self.network_transmit_history)) * 1.1
        if max_rate == 0:
            max_rate = 1  # definir um limite minimo para y
        self.net_ax.set_ylim(0, max_rate)
        self.canvas.draw_idle()

    # funcoes de atualizacao e refresh do grafico de disco
    def update_disk_graph(self):
        def worker():
            disk_read = self.sys_info.get_disk_read()
            disk_write = self.sys_info.get_disk_write()
            self.result_queue.put(('disk', disk_read, disk_write))
        self.executor.submit(worker)
        self.root.after(cycle_time_graphs, self.update_disk_graph)
    def refresh_disk_graph(self):
        xdata = range(len(self.disk_read_history))
        self.disk_read_line.set_data(xdata, self.disk_read_history)
        self.disk_write_line.set_data(xdata, self.disk_write_history)
        self.disk_ax.set_xlim(0, self.max_history_length)
        max_disk_usage = max(max(self.disk_read_history), max(self.disk_write_history)) * 1.1
        if max_disk_usage == 0:
            max_disk_usage = 1  # limite minimo para y
        self.disk_ax.set_ylim(0, max_disk_usage + 1e-9)  
        self.canvas.draw_idle()

    def unlock_heading_click(self):
        self.heading_click_locked = False

    def show_processes(self):
        if self.process_window is not None and tk.Toplevel.winfo_exists(self.process_window):
            self.process_window.deiconify()
            return

        self.process_window = tk.Toplevel(self.root)
        self.process_window.title("Process Tree")
        self.process_window.geometry("800x400")
        self.process_window.resizable(True, True)

        # tab 1: arvore de processos
        process_tree_frame = ttk.Frame(self.process_window)
        process_tree_frame.pack(fill='both', expand=True)

        columns = ("PID", "PPID", "Name", "Uid", "State", "Threads", "Physical Memory", "Virtual Memory")
        self.process_treeview = ttk.Treeview(process_tree_frame, columns=columns, show="tree headings")
        column_widths = {"PID": 60, "PPID": 60, "Name": 200, "Uid": 100, "State": 80, "Threads": 60,
                        "Physical Memory": 100, "Virtual Memory": 100}
        for col in columns:
            self.process_treeview.heading(col, text=col, 
                                        command=lambda _col=col: self.sort_process_tree(_col))
            self.process_treeview.column(col, anchor='center', width=column_widths[col])
        self.process_treeview.pack(fill='both', expand=True)

        scrollbar_tree = ttk.Scrollbar(process_tree_frame, orient="vertical", command=self.process_treeview.yview)
        self.process_treeview.configure(yscrollcommand=scrollbar_tree.set)
        scrollbar_tree.pack(side='right', fill='y')

        # ocultar a barra de rolagem
        scrollbar_tree.pack_forget()

        self.process_window_running = True
        self.update_processes()

        self.sort_column = None
        self.sort_reverse = False

        # frame para agrupar os botoes
        button_frame = tk.Frame(self.process_window)
        button_frame.pack(pady=10)

        # botao para matar processo
        self.kill_button = tk.Button(button_frame, text="Kill Process", command=self.kill_selected_process)
        self.kill_button.pack(side=tk.LEFT, padx=5)
        self.kill_button.config(state=tk.DISABLED)
        self.process_treeview.bind("<<TreeviewSelect>>", self.update_kill_button_state)

        # botao para mostrar detalhes do processo
        self.show_details_button = tk.Button(button_frame, text="Show Details", command=self.show_selected_process_details)
        self.show_details_button.pack(side=tk.LEFT, padx=5)
        self.show_details_button.config(state=tk.DISABLED)
        self.process_treeview.bind("<<TreeviewSelect>>", self.update_show_details_button_state)

        self.process_treeview.heading("#0", text="Name", command=lambda: self.sort_process_tree("#0"))
        for col in columns:
            self.process_treeview.heading(col, text=col, 
                                        command=lambda _col=col: self.sort_process_tree(_col))

        # inicializa a ordenacao
        self.treeview_sort_column = None
        self.treeview_sort_reverse = False

        # eventos de clique
        self.process_treeview.bind("<<TreeviewSelect>>", self.update_kill_button_state)
        self.process_treeview.bind("<<TreeviewSelect>>", self.update_show_details_button_state)

    def update_kill_button_state(self, event=None):
        tree = self.process_treeview
        selected_item = tree.selection()
        if selected_item:
            self.kill_button.config(state=tk.NORMAL)
        else:
            self.kill_button.config(state=tk.DISABLED)

    def update_show_details_button_state(self, event=None):
        tree = self.process_treeview
        selected_item = tree.selection()
        if selected_item:
            self.show_details_button.config(state=tk.NORMAL)
        else:
            self.show_details_button.config(state=tk.DISABLED)

    def show_selected_process_details(self):
        tree = self.process_treeview
        selected_item = tree.selection()
        if selected_item:
            pid = tree.item(selected_item[0], 'values')[0]
            self.display_process_details(pid)

    def kill_selected_process(self):
        tree = self.process_treeview
        selected_item = tree.selection()
        if selected_item:
            pid = tree.item(selected_item[0], 'values')[0]
            try:
                pid = int(pid)
                result = self.sys_info.kill_process(pid)
                if result == "0":
                    self.update_processes()
            except ValueError:
                tk.messagebox.showerror("Error", "Invalid PID")
        else:
            tk.messagebox.showerror("Error", "No process selected")

    def close_process_window(self):
        self.process_window_running = False
        self.process_window.destroy()

    def update_processes(self):
        def worker():
            processes_info = self.sys_info.get_processes_info()
            self.result_queue.put(('processes_update', processes_info))

        if self.process_window_running:
            threading.Thread(target=worker).start()
            self.root.after(cycle_time_processes, self.update_processes) 

    def refresh_process_tree(self, processes):
        if not hasattr(self, 'process_treeview') or not self.process_treeview.winfo_exists():
            return

        # salvar a expansao
        expanded_pids = set()
        def save_expansion_state(item):
            if self.process_treeview.item(item, 'open'):
                pid = self.process_treeview.item(item, 'values')[0]
                expanded_pids.add(pid)
            for child in self.process_treeview.get_children(item):
                save_expansion_state(child)
        for item in self.process_treeview.get_children():
            save_expansion_state(item)

        # salvar o processo selecionado
        selected_item = self.process_treeview.selection()
        last_selected_pid = None
        if selected_item:
            last_selected_pid = self.process_treeview.item(selected_item[0], 'values')[0]

        # salva a posicao da barra de rolagem
        treeview_yview = self.process_treeview.yview()

        # salva a ordenacao
        sort_column = self.treeview_sort_column
        sort_reverse = self.treeview_sort_reverse

        self.process_treeview.delete(*self.process_treeview.get_children())

        # constroi um dicionario de informacoes de processo
        process_info = {}
        lines = processes.strip().split('\n')
        for line in lines:
            parts = line.split('\t')
            if len(parts) >= 8:
                pid, ppid, name, uid, state, threads, vsize, rss = parts
                process_info[pid] = {
                    'ppid': ppid,
                    'pid': pid,
                    'name': name,
                    'uid': uid,
                    'state': state,
                    'threads': threads,
                    'vsize': vsize,
                    'rss': rss
                }

        # insere os processos na arvore
        inserted_items = {}
        def insert_process(pid):
            if pid in inserted_items:
                return inserted_items[pid]
            info = process_info.get(pid)
            if info:
                ppid = info['ppid']
                if ppid != '0' and ppid in process_info and ppid != pid:
                    parent_item = insert_process(ppid)
                else:
                    parent_item = ''
                item = self.process_treeview.insert(parent_item, 'end', text=info['name'], values=(
                    info['pid'],
                    info['ppid'],
                    info['name'],
                    info['uid'],
                    info['state'],
                    info['threads'],
                    f"{info['vsize']} KB",
                    f"{info['rss']} KB"
                ))
                inserted_items[pid] = item
                # restaura a expansao
                if pid in expanded_pids:
                    self.process_treeview.item(item, open=True)
                # restaura a selecao
                if pid == last_selected_pid:
                    self.process_treeview.selection_set(item)
                    self.process_treeview.see(item)
                return item
            return ''

        for pid in process_info.keys():
            insert_process(pid)

        # restaura a posicao da barra de rolagem
        self.process_treeview.yview_moveto(treeview_yview[0])

        # aplicar ordenacao
        if sort_column:
            self.sort_process_tree(sort_column, invert_sort=False)

    def sort_process_tree(self, col, invert_sort=True):
        if col != self.treeview_sort_column:
            self.treeview_sort_reverse = False
        elif invert_sort:
            self.treeview_sort_reverse = not self.treeview_sort_reverse
        self.treeview_sort_column = col

        def sort_children(parent_item):
            children = self.process_treeview.get_children(parent_item)
            data = []
            for child in children:
                item_values = self.process_treeview.item(child)['values']
                if col == "#0":  # ordenar por nome
                    value = self.process_treeview.item(child)['text']
                else:
                    col_index = self.process_treeview['columns'].index(col)
                    value = item_values[col_index]
                data.append((child, value))
            def sort_key(item):
                value = item[1]
                if col in ["PID", "PPID", "Threads"]:
                    return int(value)
                elif col in ["Physical Memory", "Virtual Memory"]:
                    try:
                        return float(value.replace(" KB", ""))
                    except ValueError:
                        return 0.0
                return value.lower()
            data.sort(key=sort_key, reverse=self.treeview_sort_reverse)
            for index, (child, _) in enumerate(data):
                self.process_treeview.move(child, parent_item, index)
                sort_children(child)
        sort_children('')

    def display_process_details(self, pid):
        detail_window = tk.Toplevel(self.root)
        detail_window.title(f"Process Details - PID {pid}")
        detail_window.geometry("800x600")
        detail_window.configure(bg='#f0f0f0')

        main_frame = ttk.Frame(detail_window, padding="10")
        main_frame.pack(fill="both", expand=True)

        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill="x", pady=(0, 10))

        title_label = ttk.Label(
            title_frame,
            text=f"Process Details (PID: {pid})",
            font=("Helvetica", 14, "bold")
        )
        title_label.pack(side="left")

        # notebook para as secoes
        notebook = ttk.Notebook(main_frame)
        notebook.pack(side="left", fill="both", expand=True)

        # frame para cada secao
        basic_frame = ttk.Frame(notebook, padding="10")
        notebook.add(basic_frame, text="Basic Info")

        threads_frame = ttk.Frame(notebook, padding="10")
        notebook.add(threads_frame, text="Threads")

        resources_frame = ttk.Frame(notebook, padding="10")
        notebook.add(resources_frame, text="More Info")

        treeviews = {}

        # treeviews para cada secao
        for name, frame in zip(["basic", "resources"], [basic_frame, resources_frame]):
            treeview = ttk.Treeview(frame, columns=("Key", "Value"), show="headings")
            treeview.heading("Key", text="Key")
            treeview.heading("Value", text="Value")
            treeview.column("Key", anchor="w", width=200)
            treeview.column("Value", anchor="w", width=400)
            treeview.pack(side="left", fill="both", expand=True)

            scrollbar = ttk.Scrollbar(frame, orient="vertical", command=treeview.yview)
            treeview.configure(yscrollcommand=scrollbar.set)
            scrollbar.pack(side="right", fill="y")

            treeviews[name] = treeview

        # treeview para threads
        threads_columns = ("Thread ID (TID)", "Name", "State", "VmRSS")
        threads_treeview = ttk.Treeview(threads_frame, columns=threads_columns, show="headings")
        for col in threads_columns:
            threads_treeview.heading(col, text=col)
            threads_treeview.column(col, anchor="w", width=150)
        threads_treeview.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(threads_frame, orient="vertical", command=threads_treeview.yview)
        threads_treeview.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        treeviews["threads"] = threads_treeview

        def format_section(treeview, content, section_name):
            if section_name == "threads":
                threads = content.strip().split('Thread ID (TID):')
                for thread_info in threads[1:]:
                    lines = thread_info.strip().split('\n')
                    thread_data = {}
                    thread_data["Thread ID (TID)"] = lines[0].strip()
                    for line in lines[1:]:
                        if ':' in line:
                            key, value = line.split(':', 1)
                            thread_data[key.strip()] = value.strip()
                    if thread_data:
                        treeview.insert("", "end", values=(
                            thread_data.get("Thread ID (TID)", ""),
                            thread_data.get("Name", ""),
                            thread_data.get("State", ""),
                            thread_data.get("VmRSS", "")
                        ))
            else:
                lines = content.strip().split('\n')
                for line in lines:
                    if ':' in line:
                        key, value = line.split(':', 1)
                        treeview.insert("", "end", values=(key.strip(), value.strip()))

        def update_treeviews(process_info):
            sections = process_info.split('Title')
            for name, treeview in treeviews.items():
                treeview.delete(*treeview.get_children())
                for section in sections:
                    section = section.strip()
                    if section:
                        if name == "basic" and section.startswith("1"):
                            content = section.split('\n', 1)[1]
                            format_section(treeview, content, name)
                        elif name == "threads" and section.startswith("3"):
                            content = section.split('\n', 1)[1]
                            format_section(treeview, content, name)
                        elif name == "resources" and section.startswith("2"):
                            content = section.split('\n', 1)[1]
                            format_section(treeview, content, name)

        def update_process_info():
            def worker():
                try:
                    process_info = self.sys_info.get_specific_process(pid)
                    self.result_queue.put(('process_detail', process_info))
                except Exception as e:
                    self.result_queue.put(('error', str(e)))

            self.executor.submit(worker)

        def process_detail_queue():
            if not detail_window.winfo_exists():
                return

            while not self.result_queue.empty():
                try:
                    item = self.result_queue.get_nowait()
                except queue.Empty:
                    break
                if item[0] == 'process_detail':
                    process_info = item[1]
                    update_treeviews(process_info)
                elif item[0] == 'error':
                    print(f"Error fetching process info: {item[1]}")

            detail_window.after(cycle_time_process_detail, update_process_info)
            detail_window.after(250, process_detail_queue)

        update_process_info()
        process_detail_queue()

    def stop(self):
        self.executor.shutdown(wait=False)
        self.root.quit()