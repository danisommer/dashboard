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
cycle_time_files = 1000  # milissegundos
cycle_time_process_detail = 500  # milissegundos
last_selected_process = None
processes_thread = 5
last_thread_num = 0

class DashboardApp:
    def __init__(self, root):
        self.root = root
        self.root.title("System Dashboard")
        self.root.geometry("1200x600")
        self.root.resizable(True, True)
        self.root.minsize(800, 600)
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

        # Global Interpreter Lock eh um mutex que impede
        # que multiplas threads executem bytecodes Python ao mesmo tempo

        # as funcoes que obtem informacoes do sistema sao executadas
        # em threads separadas. Essas operacoes, permitem que outras 
        # threads executem enquanto uma thread esta aguardando uma
        # operacao coleta de dados

        # inicializacao do thread pool executor 
        # com threads para N campos + thread para processos 
        self.executor = ThreadPoolExecutor(max_workers=len(self.sys_info.fields) + processes_thread)

        self.result_queue = queue.Queue()

        self.setup_widgets()

        self.process_window = None
        self.files_window = None

        self.initialize_cpu_core_histories()
        self.initialize_memory_histories()
        self.initialize_network_histories()
        self.initialize_disk_histories()
        self.process_queue()
        
        self.files_history = []
        self.files_history_index = -1

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
        self.process_button.grid(row=1, column=0, pady=5, padx=5, sticky="ew")

        # botao para mostrar arquivos
        self.files_button = tk.Button(self.root, text="Show Files", command=self.show_files)
        self.files_button.grid(row=2, column=0, pady=5, padx=5, sticky="ew")

        # graficos de cpu e memoria
        self.cpu_memory_frame = tk.Frame(self.root)
        self.cpu_memory_frame.grid(row=0, column=1, rowspan=3, sticky="nsew", padx=10, pady=10)
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

        # agenda as atualizacoes dos graficos
        self.root.after(cycle_time, self.update_cpu_graph)
        self.root.after(cycle_time, self.update_memory_graph)
        self.root.after(cycle_time, self.update_network_graph)
        self.root.after(cycle_time, self.update_disk_graph)
        

    # para cada campo uma tarefa eh submetida 
    # ao executor para obter informacoes do sistema periodicamente
    def update_field(self, field):
        def worker():
            value = self.sys_info.get_info(field) # coleta de dados 
            self.result_queue.put(('field', field, value)) # coloca o resultado na fila
        self.executor.submit(worker) # submete a tarefa ao executor
        self.root.after(cycle_time, self.update_field, field)

    # a funcao process_queue eh chamada periodicamente para processar itens na 
    # fila de resultados (result_queue)
    # - comunicacao segura entre threads de trabalho e a thread principal
    # - atualizacao eficiente da interface grafica sem bloquear a thread principal
    # - sincronizacao das operacoes realizadas pelas threads de trabalho com a
    #   thread principal
    def process_queue(self):
        # processa itens na fila de resultados
        while not self.result_queue.empty():
            item = self.result_queue.get()
            if item[0] == 'update_processes':
                # atualiza a lista de processos
                self.update_processes()
            elif item[0] == 'kill_process_error':
                # exibe mensagem de erro caso falhe ao matar um processo
                error_message = item[1]
                tk.messagebox.showerror("Error", f"Unexpected error: {error_message}")
            elif item[0] == 'field':
                # atualiza campos de texto na interface
                field, value = item[1], item[2]
                self.label_vars[field].set(f"{field}:\n{value}")
            elif item[0] == 'cpu':
                # atualiza graficos de uso da CPU
                core_usages = item[1]
                for core_index, usage in enumerate(core_usages):
                    self.cpu_core_usage_histories[core_index].append(usage)
                    if len(self.cpu_core_usage_histories[core_index]) > self.max_history_length:
                        self.cpu_core_usage_histories[core_index].pop(0)
                self.refresh_cpu_graph()
            elif item[0] == 'memory':
                # atualiza graficos de memoria e swap
                mem_usage, swap_usage = item[1], item[2]
                self.mem_usage_history.append(mem_usage)
                self.swap_usage_history.append(swap_usage)
                if len(self.mem_usage_history) > self.max_history_length:
                    self.mem_usage_history.pop(0)
                if len(self.swap_usage_history) > self.max_history_length:
                    self.swap_usage_history.pop(0)
                self.refresh_memory_graph()
            elif item[0] == 'network':
                # atualiza graficos de rede
                receive_rate, transmit_rate = item[1], item[2]
                self.network_receive_history.append(receive_rate)
                self.network_transmit_history.append(transmit_rate)
                if len(self.network_receive_history) > self.max_history_length:
                    self.network_receive_history.pop(0)
                if len(self.network_transmit_history) > self.max_history_length:
                    self.network_transmit_history.pop(0)
                self.refresh_network_graph()
            elif item[0] == 'disk':
                # atualiza graficos de disco
                disk_read, disk_write = item[1], item[2]
                self.disk_read_history.append(disk_read)
                self.disk_write_history.append(disk_write)
                if len(self.disk_read_history) > self.max_history_length:
                    self.disk_read_history.pop(0)
                if len(self.disk_write_history) > self.max_history_length:
                    self.disk_write_history.pop(0)
                self.refresh_disk_graph()
            elif item[0] == 'processes_update':
                # atualiza a arvore de processos na interface
                processes = item[1]
                self.refresh_process_tree(processes)
            elif item[0] == 'files_update':
                # atualiza a arvore de arquivos na interface
                files = item[1]
                self.refresh_files_tree(files)                
        self.root.after(100, self.process_queue)

    # funcoes que submetem tarefas de coletar informacoes ao executor para 
    # obter dados e coloca-los na fila de resultados.
    def update_cpu_graph(self):
        def worker():
            core_usages = self.sys_info.get_cpu_usage_per_core()  # coleta de dados 
            self.result_queue.put(('cpu', core_usages))  # coloca o resultado na fila
        self.executor.submit(worker) # submete a tarefa ao executor
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
            mem_usage = self.sys_info.get_memory_usage() # coleta de dados
            swap_usage = self.sys_info.get_swap_usage() # coleta de dados
            self.result_queue.put(('memory', mem_usage, swap_usage)) # coloca o resultado na fila
        self.executor.submit(worker) # submete a tarefa ao executor
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
            receive_rate = self.sys_info.get_network_receive_rate() # coleta de dados
            transmit_rate = self.sys_info.get_network_transmit_rate() # coleta de dados
            self.result_queue.put(('network', receive_rate, transmit_rate)) # coloca o resultado na fila
        self.executor.submit(worker) # submete a tarefa ao executor
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
            disk_read = self.sys_info.get_disk_read() # coleta de dados
            disk_write = self.sys_info.get_disk_write() # coleta de dados
            self.result_queue.put(('disk', disk_read, disk_write)) # coloca o resultado na fila
        self.executor.submit(worker) # submete a tarefa ao executor
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

        self.process_window.protocol("WM_DELETE_WINDOW", self.close_process_window)

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

        # botao para mostrar detalhes do processo
        self.show_details_button = tk.Button(button_frame, text="Show Details", command=self.show_selected_process_details)
        self.show_details_button.pack(side=tk.LEFT, padx=5)
        self.show_details_button.config(state=tk.DISABLED)

        # botao para matar processo
        self.kill_button = tk.Button(button_frame, text="Kill Process", command=self.kill_selected_process)
        self.kill_button.pack(side=tk.LEFT, padx=5)
        self.kill_button.config(state=tk.DISABLED)

        self.process_treeview.bind("<<TreeviewSelect>>", self.handle_treeview_selection)

        self.process_treeview.heading("#0", text="Name", command=lambda: self.sort_process_tree("#0"))
        for col in columns:
            self.process_treeview.heading(col, text=col, command=lambda _col=col: self.sort_process_tree(_col))

        # inicializa a ordenacao
        self.treeview_sort_column = None
        self.treeview_sort_reverse = False

    def handle_treeview_selection(self, event=None):
        # atualiza botoes de acao baseados na selecao na arvore de processos
        self.update_kill_button_state()
        self.update_show_details_button_state()

    def update_kill_button_state(self, event=None):
        # habilita ou desabilita o botao de matar processos com base na selecao
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
        # exibe detalhes do processo selecionado
        tree = self.process_treeview
        selected_item = tree.selection()
        if selected_item:
            pid = tree.item(selected_item[0], 'values')[0]
            self.display_process_details(pid)

    def kill_selected_process(self):
        # mata o processo selecionado apos confirmacao do usuario
        tree = self.process_treeview
        selected_item = tree.selection()
        if selected_item:
            pid = tree.item(selected_item[0], 'values')[0]
            def on_response(confirmed):
                if confirmed:
                    try:
                        pid_int = int(pid)
                        result = self.sys_info.kill_process(pid_int)
                        if result == 0:
                            # atualiza processos apos matar o processo
                            self.update_processes()
                    except ValueError:
                        tk.messagebox.showerror("Error", "Invalid PID")
                else:
                    tk.messagebox.showinfo("Process Not Terminated", f"Process {pid} was not terminated.")
            self.custom_message_box(
                title="Confirm Termination",
                message="Are you sure you want to kill the selected process?",
                callback=on_response,
            )
        else:
            tk.messagebox.showerror("Error", "No process selected")

    def custom_message_box(self, title, message, callback):
        def on_yes():
            callback(True)
            top.destroy()

        def on_no():
            callback(False)
            top.destroy()

        top = tk.Toplevel(self.root)
        top.title(title)
        top.geometry("300x150")
        top.resizable(False, False)
        top.protocol("WM_DELETE_WINDOW", on_no)

        container = ttk.Frame(top)
        container.pack(fill="both", expand=True, padx=10, pady=10)

        custom_font = ("Arial", 12)
        ttk.Style().configure("TButton", font=custom_font)

        ttk.Label(
            container, text="Warning", font=("Arial", 16)
        ).pack(pady=(0, 5), anchor="center")
        ttk.Label(
            container, text=message, wraplength=250, anchor="center"
        ).pack(pady=(0, 10), anchor="center")

        button_frame = ttk.Frame(container)
        button_frame.pack(anchor="center")

        style = ttk.Style()
        style.configure("Small.TButton", font=("Arial", 10))

        ttk.Button(
            button_frame,
            text="Yes",
            command=on_yes,
            style="Small.TButton",
            padding=(10, 5),
        ).pack(side="left", padx=5)
        ttk.Button(
            button_frame,
            text="No",
            command=on_no,
            style="Small.TButton",
            padding=(10, 5),
        ).pack(side="left", padx=5)

    def close_process_window(self):
        self.process_window_running = False
        self.process_window.destroy()

    # cria uma nova thread para obter informacoes dos processos 
    # e coloca os resultados na fila de resultados.
    def update_processes(self):
        if not self.process_window_running:
            return

        def worker():
            processes_info = self.sys_info.get_processes_info() # coleta de dados
            self.result_queue.put(('processes_update', processes_info)) # coloca o resultado na fila

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
        # verifica se a coluna mudou ou se deve inverter a ordem de ordenacao
        if col != self.treeview_sort_column:
            self.treeview_sort_reverse = False
        elif invert_sort:
            self.treeview_sort_reverse = not self.treeview_sort_reverse
        self.treeview_sort_column = col

        def sort_children(parent_item):
            # ordena os filhos de um item na arvore de processos
            children = self.process_treeview.get_children(parent_item)
            data = []
            for child in children:
                item_values = self.process_treeview.item(child)['values']
                if col == "#0":  # ordenar por nome do processo
                    value = self.process_treeview.item(child)['text']
                else:
                    col_index = self.process_treeview['columns'].index(col)
                    value = item_values[col_index]
                data.append((child, value))
            
            # funcao auxiliar para definir a chave de ordenacao
            def sort_key(item):
                value = item[1]
                # caso a coluna seja numerica (PID, PPID, Threads)
                if col in ["PID", "PPID", "Threads"]:
                    return int(value)
                # caso seja memoria (fisica ou virtual)
                elif col in ["Physical Memory", "Virtual Memory"]:
                    try:
                        return float(value.replace(" KB", ""))
                    except ValueError:
                        return 0.0
                return value.lower()  # ordenacao alfabetica para outras colunas

            # ordena os dados conforme a chave de ordenacao
            data.sort(key=sort_key, reverse=self.treeview_sort_reverse)
            for index, (child, _) in enumerate(data):
                # move o item ordenado na arvore
                self.process_treeview.move(child, parent_item, index)
                sort_children(child)  # ordena os filhos recursivamente

        # inicia a ordenacao para o item principal (root)
        sort_children('')

    def display_process_details(self, pid):
        # cria uma nova janela para exibir os detalhes do processo
        detail_window = tk.Toplevel(self.root)
        detail_window.title(f"Process Details - PID {pid}")
        detail_window.geometry("800x600")
        detail_window.configure(bg='#f0f0f0')

        # frame principal dentro da nova janela
        main_frame = ttk.Frame(detail_window, padding="10")
        main_frame.pack(fill="both", expand=True)

        # frame para o titulo da janela
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill="x", pady=(0, 10))

        # rotulo com o titulo do processo
        title_label = ttk.Label(
            title_frame,
            text=f"Process Details (PID: {pid})",
            font=("Helvetica", 14, "bold")
        )
        title_label.pack(side="left")

        # criacao de um notebook para separar as secoes do processo
        notebook = ttk.Notebook(main_frame)
        notebook.pack(side="left", fill="both", expand=True)

        # frames para cada secao do notebook (informacoes basicas, threads, mais informacoes)
        basic_frame = ttk.Frame(notebook, padding="10")
        notebook.add(basic_frame, text="Basic Info")

        threads_frame = ttk.Frame(notebook, padding="10")
        notebook.add(threads_frame, text="Threads")

        resources_frame = ttk.Frame(notebook, padding="10")
        notebook.add(resources_frame, text="More Info")

        treeviews = {}

        # criacao de treeviews para cada secao (basico e recursos)
        for name, frame in zip(["basic", "resources"], [basic_frame, resources_frame]):
            treeview = ttk.Treeview(frame, columns=("Key", "Value"), show="headings")
            treeview.heading("Key", text="Key")
            treeview.heading("Value", text="Value")
            treeview.column("Key", anchor="w", width=200)
            treeview.column("Value", anchor="w", width=400)
            treeview.pack(side="left", fill="both", expand=True)

            # adiciona a barra de rolagem para cada treeview
            scrollbar = ttk.Scrollbar(frame, orient="vertical", command=treeview.yview)
            treeview.configure(yscrollcommand=scrollbar.set)
            scrollbar.pack(side="right", fill="y")

            treeviews[name] = treeview

        # criacao do treeview para as threads do processo
        threads_columns = ("Thread ID (TID)", "Name", "State", "VmRSS")
        threads_treeview = ttk.Treeview(threads_frame, columns=threads_columns, show="headings")
        for col in threads_columns:
            threads_treeview.heading(col, text=col)
            threads_treeview.column(col, anchor="w", width=150)
        threads_treeview.pack(side="left", fill="both", expand=True)

        # barra de rolagem para o treeview de threads
        scrollbar = ttk.Scrollbar(threads_frame, orient="vertical", command=threads_treeview.yview)
        threads_treeview.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        treeviews["threads"] = threads_treeview

        # funcao para formatar e adicionar as informacoes em cada secao do treeview
        def format_section(treeview, content, section_name):
            if section_name == "threads":
                # se for a secao de threads, divide as informacoes para cada thread
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
                # para as outras secoes, insere os dados de chave e valor
                lines = content.strip().split('\n')
                for line in lines:
                    if ':' in line:
                        key, value = line.split(':', 1)
                        treeview.insert("", "end", values=(key.strip(), value.strip()))

        # funcao para atualizar os treeviews com as informacoes do processo
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

        # quando detalhes de um processo especifico sao solicitados,
        # uma tarefa eh submetida ao executor para obter essas informacoes
        # e coloca-las na fila de resultados
        def update_process_info():
            def worker():
                try:
                    # obtem as informacoes detalhadas do processo
                    process_info = self.sys_info.get_specific_process(pid) # coleta de dados
                    self.result_queue.put(('process_detail', process_info)) # coloca o resultado na fila
                except Exception as e:
                    self.result_queue.put(('error', str(e)))

            # envia a tarefa para ser executada em uma thread separada
            self.executor.submit(worker) # submete a tarefa ao executor

        # funcao para processar os dados da fila e atualizar a interface
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

            # chama a atualizacao das informacoes do processo a cada intervalo de tempo
            detail_window.after(cycle_time_process_detail, update_process_info)
            detail_window.after(250, process_detail_queue)

        # inicia a atualizacao das informacoes e o processamento da fila
        update_process_info()
        process_detail_queue()

    def show_files(self):
        if self.files_window is not None and tk.Toplevel.winfo_exists(self.files_window):
            self.files_window.deiconify()
            return

        self.files_window = tk.Toplevel(self.root)
        self.files_window.title("Files Tree")
        self.files_window.geometry("800x400")
        self.files_window.resizable(True, True)

        self.files_window.protocol("WM_DELETE_WINDOW", self.close_files_window)

        # frame para os botoes de navegacao
        nav_frame = tk.Frame(self.files_window)
        nav_frame.pack(fill='x')

        self.back_button = tk.Button(nav_frame, text="<-", command=self.go_back, state=tk.DISABLED)
        self.back_button.pack(side=tk.LEFT)

        self.forward_button = tk.Button(nav_frame, text="->", command=self.go_forward, state=tk.DISABLED)
        self.forward_button.pack(side=tk.LEFT)

        # frame para a arvore de arquivos
        files_tree_frame = ttk.Frame(self.files_window)
        files_tree_frame.pack(fill='both', expand=True)

        self.fs_tree = ttk.Treeview(files_tree_frame)
        self.fs_tree.pack(fill='both', expand=True)

        scrollbar_tree = ttk.Scrollbar(files_tree_frame, orient="vertical", command=self.fs_tree.yview)
        self.fs_tree.configure(yscrollcommand=scrollbar_tree.set)
        scrollbar_tree.pack(side='right', fill='y')

        self.fs_tree.bind("<<TreeviewOpen>>", self.on_treeview_open)

        self.files_window_running = True
        self.update_files()

    def on_treeview_open(self, event):
        item = self.fs_tree.focus()
        path = self.fs_tree.item(item, "text")
        self.navigate_to_directory(path)

    def navigate_to_directory(self, path):
        self.files_history = self.files_history[:self.files_history_index + 1]
        self.files_history.append(path)
        self.files_history_index += 1
        self.update_navigation_buttons()
        self.refresh_files_tree(path)

    def go_back(self):
        if self.files_history_index > 0:
            self.files_history_index -= 1
            self.update_navigation_buttons()
            self.refresh_files_tree(self.files_history[self.files_history_index])

    def go_forward(self):
        if self.files_history_index < len(self.files_history) - 1:
            self.files_history_index += 1
            self.update_navigation_buttons()
            self.refresh_files_tree(self.files_history[self.files_history_index])

    def update_navigation_buttons(self):
        self.back_button.config(state=tk.NORMAL if self.files_history_index > 0 else tk.DISABLED)
        self.forward_button.config(state=tk.NORMAL if self.files_history_index < len(self.files_history) - 1 else tk.DISABLED)

    def refresh_files_tree(self, path="/"):
        for item in self.fs_tree.get_children():
            self.fs_tree.delete(item)
        self.populate_fs_tree(path, "")

    def populate_fs_tree(self, path, parent):
        try:
            files_info = self.sys_info.list_directory(path)
            for file in files_info:
                abs_path = f"{path}/{file}"
                item = self.fs_tree.insert(parent, "end", text=abs_path, open=False)
                if self.sys_info.is_directory(abs_path):
                    self.fs_tree.insert(item, "end")
        except Exception as e:
            print(f"Error populating file tree: {e}")

    def close_files_window(self):
        self.files_window_running = False
        self.files_window.destroy()

    def update_files(self):
        if not self.files_window_running:
            return

        def worker():
            files_info = self.sys_info.list_directory("/")
            self.result_queue.put(('files_update', files_info))

        if self.files_window_running:
            threading.Thread(target=worker).start()
            self.root.after(cycle_time_files, self.update_files)

    def stop(self):
        self.executor.shutdown(wait=False)
        self.root.quit()