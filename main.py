import tkinter as tk
from tkinter import ttk, filedialog

from load.load_tab import LoadTab
from map.map_tab import MapTab
from theme import *

class App(tk.Tk):
	def __init__(self):
		super().__init__()
		self.title("Sound Scape")

		screen_width = self.winfo_screenwidth()
		screen_height = self.winfo_screenheight()

		cx = int((screen_width / 2) - 450)
		cy = int((screen_height / 2) - 300)

		self.geometry(f"900x600+{cx}+{cy}")
		self.configure(bg="#1e1e1e")

		self.loaded_files = []
		# self.overrideredirect(True)

		self._setup_style()
		self.create_custom_menu()

		self._setup_tabs()

		self.menu_bar.bind("<Button-1>", self.start_move)
		self.menu_bar.bind("<B1-Motion>", self.do_move)

	def _setup_style(self):
		style = ttk.Style()
		style.theme_use("default")

		style.configure("TNotebook", background=BG_PANEL, borderwidth=0)

		style.configure(
			"TNotebook.Tab",
			background=BG_DARK,
			foreground=FG_TEXT,
			padding=[20, 8],
			borderwidth=0,
		)

		style.map(
			"TNotebook.Tab",
			background=[("selected", BG_PANEL)],
			foreground=[("selected", ACCENT)],
		)

		style.configure(
			"Vertical.TScrollbar",
			gripcount=0,
			background=GRID_COLOR,      # Thumb color
			darkcolor=BG_DARK,
			lightcolor=BG_PANEL,
			troughcolor=BG_DARK,    # Track background
			bordercolor=BG_PANEL,
			arrowcolor=BG_PANEL,
			relief="flat",
			borderwidth=0,
			width=10
		)

		style.map(
			"Vertical.TScrollbar",
			background=[("active", BG_DARK)]
		)

	def _setup_tabs(self):
		tabs = ttk.Notebook(self, style="TNotebook")
		self.map_tab = MapTab(tabs, self.loaded_files)
		self.load_tab = LoadTab(tabs, self.loaded_files, self.remove_file, self.refresh)

		tabs.add(self.load_tab, text="Load")
		tabs.add(self.map_tab, text="Map")
		tabs.pack(fill="both", expand=True)

		tabs.bind("<<NotebookTabChanged>>", self.on_tab_change)

	def on_tab_change(self, event):
		self.refresh()

	def remove_file(self, file_path):
		self.map_tab.remove_file(file_path)

		if file_path in self.loaded_files:
			self.loaded_files.remove(file_path)

		self.refresh()

	def save_map(self):
		file_path = filedialog.asksaveasfilename(
			defaultextension=".nsm",
			filetypes=[("Node Sound Map", "*.nsm")],
			title="Save Map",
		)
		if file_path:
			self.map_tab.save_map(file_path)

	def load_map(self):
		file_path = filedialog.askopenfilename(
			defaultextension=".nsm",
			filetypes=[("Node Sound Map", "*.nsm")],
			title="Load Map",
		)
		if file_path:
			self.map_tab.load_map(file_path, self.loaded_files)
			self.refresh()

	def refresh(self):
		self.map_tab.refresh()
		self.load_tab.refresh()

	def create_custom_menu(self):
		self.menu_bar = tk.Frame(self, bg=BG_PANEL, height=30)
		self.menu_bar.pack(fill="x", side="top")

		file_btn = tk.Menubutton(
			self.menu_bar,
			text="File",
			bg=BG_PANEL,
			fg=FG_TEXT,
			activebackground=BG_DARK,
			activeforeground=ACCENT,
			font=("Segoe UI", 10, "bold"),
		)
		file_btn.pack(side="left", padx=5, pady=2)

		file_menu = tk.Menu(
			file_btn,
			tearoff=0,
			bg=BG_DARK,
			fg=FG_TEXT,
			activebackground=ACCENT,
			activeforeground=BG_DARK,
		)

		file_menu.add_command(label="Save", command=self.save_map)
		file_menu.add_command(label="Load", command=self.load_map)
		file_menu.add_separator()
		file_menu.add_command(label="Exit", command=self.destroy)

		file_btn.config(menu=file_menu)

		if not self.overrideredirect:
			# Close Button
			close_btn = tk.Button(
				self.menu_bar,
				text="✕",
				bg=BG_PANEL,
				fg=FG_TEXT,
				activebackground=CLOSE_RED,
				activeforeground=FG_TEXT,
				bd=0,
				command=self.destroy,
			)
			close_btn.pack(side="right", padx=5)

			# Minimize Button
			min_btn = tk.Button(
				self.menu_bar,
				text="—",
				bg=BG_PANEL,
				fg=FG_TEXT,
				activebackground=ACCENT,
				activeforeground=BG_DARK,
				bd=0,
				command=self.minimize_window,
			)
			min_btn.pack(side="right")

	def minimize_window(self):
		self.overrideredirect(False)
		self.after(10, self._proper_mini)

	def _proper_mini(self):
		self.iconify()
		self.bind("<Map>", self.restore_override)

	def restore_override(self, event=None):
		self.overrideredirect(True)
		self.unbind("<Map>")

	def start_move(self, event):
		self._x_start = event.x
		self._y_start = event.y

	def do_move(self, event):
		x = self.winfo_pointerx() - self._x_start
		y = self.winfo_pointery() - self._y_start
		self.geometry(f"+{x}+{y}")

if __name__ == "__main__":
	App().mainloop()