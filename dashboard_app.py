# dashboard_app.py
import tkinter as tk
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from system_info import SystemInfo

cycle_time = 0.5  # Time in seconds for updates

class DashboardApp:
    def __init__(self, root):
        self.root = root
        self.root.title("System Dashboard")
        
        self.sys_info = SystemInfo()
        
        self.labels = {}
        self.executor = ThreadPoolExecutor(max_workers=len(self.sys_info.fields))
        
        self.setup_labels_and_threads()
        
        self.process_button = tk.Button(root, text="Show Processes", command=self.show_processes)
        self.process_button.pack(pady=10)
        
        self.process_window = None

    def setup_labels_and_threads(self):
        for field in self.sys_info.fields.keys():
            label = tk.Label(self.root, text=f"{field}:", font=("Arial", 16))
            label.pack(pady=10)
            self.labels[field] = label
            self.executor.submit(self.update_field, field)

    def update_field(self, field):
        while True:
            value = self.sys_info.get_info(field)
            self.labels[field].config(text=f"{field}:\n{value}")
            time.sleep(cycle_time)

    def show_processes(self):
        if self.process_window is not None:
            self.process_window.destroy()

        self.process_window = tk.Toplevel(self.root)
        self.process_window.title("Process List")

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
        
        close_button = tk.Button(self.process_window, text="Close", command=self.process_window.destroy)
        close_button.pack(pady=10)

    def stop(self):
        self.executor.shutdown(wait=False)
        self.root.quit()
