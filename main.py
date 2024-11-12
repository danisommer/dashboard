# main.py
import tkinter as tk
from dashboard_app import DashboardApp

root = tk.Tk()
app = DashboardApp(root)

root.protocol("WM_DELETE_WINDOW", app.stop)
root.mainloop()
