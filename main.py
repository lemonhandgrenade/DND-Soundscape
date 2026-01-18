import tkinter as tk
from tkinter import ttk, filedialog
from load.load_tab import LoadTab
from map.map_tab import MapTab
from edit.edit_tab import EditTab
from utils.theme import *

class App(tk.Tk):
	def __init__(self):
		super().__init__()
		self.title("DND Soundscape")

		screen_width = self.winfo_screenwidth()
		screen_height = self.winfo_screenheight()

		cx = int((screen_width / 2) - 450)
		cy = int((screen_height / 2) - 300)

		self.geometry(f"900x600+{cx}+{cy}")
		self.configure(bg=ThemeManager.Get("BG_Dark"))

		self.loaded_files = []

		self._setup_style()
		self.create_custom_menu()

		self._setup_tabs()

		self.menu_bar.bind("<Button-1>", self.start_move)
		self.menu_bar.bind("<B1-Motion>", self.do_move)

	def _setup_style(self):
		style = ttk.Style()
		style.theme_use("default")

		style.configure("TNotebook", background=ThemeManager.Get("BG_Panel"), borderwidth=0)

		style.configure(
			"TNotebook.Tab",
			background=ThemeManager.Get("BG_Dark"),
			foreground=ThemeManager.Get("Text"),
			padding=[20, 8],
			borderwidth=0,
		)

		style.map(
			"TNotebook.Tab",
			background=[("selected", ThemeManager.Get("BG_Panel"))],
			foreground=[("selected", ThemeManager.Get("Accent"))],
		)

		style.configure(
			"Vertical.TScrollbar",
			gripcount=0,
			background=ThemeManager.Get("Grid_Color"),
			darkcolor=ThemeManager.Get("BG_Dark"),
			lightcolor=ThemeManager.Get("BG_Panel"),
			troughcolor=ThemeManager.Get("BG_Dark"),
			bordercolor=ThemeManager.Get("BG_Panel"),
			arrowcolor=ThemeManager.Get("BG_Panel"),
			relief="flat",
			borderwidth=0,
			width=10
		)

		style.map(
			"Vertical.TScrollbar",
			background=[("active", ThemeManager.Get("BG_Dark"))]
		)

		style.configure(
			"Edit.TLabel",
			background=ThemeManager.Get("BG_Panel"),
			foreground=ThemeManager.Get("Text"),
			font=("Segoe UI", 9)
		)

		style.configure(
			"EditBold.TLabel",
			background=ThemeManager.Get("BG_Panel"),
			foreground=ThemeManager.Get("Text"),
			font=("Segoe UI", 10, "bold")
		)

		style.configure(
			"Edit.TCombobox",
			fieldbackground=ThemeManager.Get("BG_Panel"),
			background=ThemeManager.Get("BG_Panel"),
			foreground=ThemeManager.Get("Text"),
			arrowcolor=ThemeManager.Get("Text"),
			relief="flat",
			borderwidth=0,
			padding=4
		)

		style.map(
			"Edit.TCombobox",
			fieldbackground=[("readonly", ThemeManager.Get("BG_Panel"))],
			background=[("readonly", ThemeManager.Get("BG_Panel"))],
			foreground=[("readonly", ThemeManager.Get("Text"))]
		)
	
		style.configure(
			"Dark.TCombobox",
			fieldbackground=ThemeManager.Get("BG_Dark"),
			background=ThemeManager.Get("BG_Dark"),
			foreground=ThemeManager.Get("Text"),
			arrowcolor=ThemeManager.Get("Text"),
			relief="flat",
			borderwidth=0,
			padding=4
		)

		style.map(
			"Dark.TCombobox",
			fieldbackground=[("readonly", ThemeManager.Get("BG_Dark"))],
			background=[("readonly", ThemeManager.Get("BG_Dark"))],
			foreground=[("readonly", ThemeManager.Get("Text"))]
		)

		self.option_add("*TCombobox*Listbox*Background", ThemeManager.Get("BG_Panel"))
		self.option_add('*TCombobox*Listbox*Foreground', ThemeManager.Get("Text"))

		style.configure(
			"Edit.TSpinbox",
			relief="flat",
			borderwidth=0,
			padding=4,
			background=ThemeManager.Get("BG_Panel"),
			foreground=ThemeManager.Get("Text"),
			fieldbackground=ThemeManager.Get("BG_Panel"),
			arrowcolor=ThemeManager.Get("Text")
		)

		self.option_add("*Checkbutton.relief", "flat")
		self.option_add("*Checkbutton.borderWidth", 0)
		self.option_add("*Checkbutton.highlightThickness", 0)

		self.option_add("*Checkbutton.background", ThemeManager.Get("BG_Panel"))
		self.option_add("*Checkbutton.foreground", ThemeManager.Get("Text"))
		self.option_add("*Checkbutton.activeBackground", ThemeManager.Get("BG_Panel"))
		self.option_add("*Checkbutton.activeForeground", ThemeManager.Get("Accent"))
		self.option_add("*Checkbutton.selectColor", ThemeManager.Get("BG_Panel"))


	def _setup_tabs(self):
		tabs = ttk.Notebook(self, style="TNotebook")
		self.map_tab = MapTab(tabs, self.loaded_files)
		self.load_tab = LoadTab(tabs, self.loaded_files, self.remove_file, self.refresh)
		
		self.tabs = tabs
		self.edit_tab = EditTab(tabs, self.map_tab)

		tabs.add(self.load_tab, text="Load")
		tabs.add(self.map_tab, text="Map")
		tabs.add(self.edit_tab, text="Edit")
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
		self.edit_tab.refresh()

	def create_custom_menu(self):
		self.menu_bar = tk.Frame(self, bg=ThemeManager.Get("BG_Panel"), height=30)
		self.menu_bar.pack(fill="x", side="top")

		self.file_btn = tk.Menubutton(
			self.menu_bar,
			text="File",
			bg=ThemeManager.Get("BG_Panel"),
			fg=ThemeManager.Get("Text"),
			activebackground=ThemeManager.Get("BG_Dark"),
			activeforeground=ThemeManager.Get("Accent"),
			font=("Segoe UI", 10, "bold"),
		)
		self.file_btn.pack(side="left", padx=5, pady=2)

		self.file_menu = tk.Menu(
			self.file_btn,
			tearoff=0,
			bg=ThemeManager.Get("BG_Dark"),
			fg=ThemeManager.Get("Text"),
			activebackground=ThemeManager.Get("Accent"),
			activeforeground=ThemeManager.Get("BG_Dark"),
		)

		self.file_menu.add_command(label="Save", command=self.save_map)
		self.file_menu.add_command(label="Load", command=self.load_map)
		self.file_menu.add_separator()
		self.file_menu.add_command(label="Exit", command=self.destroy)

		self.file_btn.config(menu=self.file_menu)

		self.view_btn = tk.Menubutton(
			self.menu_bar,
			text="View",
			bg=ThemeManager.Get("BG_Panel"),
			fg=ThemeManager.Get("Text"),
			activebackground=ThemeManager.Get("BG_Dark"),
			activeforeground=ThemeManager.Get("Accent"),
			font=("Segoe UI", 10, "bold"),
		)
		self.view_btn.pack(side="left", padx=5, pady=2)

		self.view_menu = tk.Menu(
			self.view_btn,
			tearoff=0,
			bg=ThemeManager.Get("BG_Dark"),
			fg=ThemeManager.Get("Text"),
			activebackground=ThemeManager.Get("Accent"),
			activeforeground=ThemeManager.Get("BG_Dark"),
		)

		self.view_menu.add_command(label="Theme", command=self.theme_changer)
		self.view_menu.add_command(label="Reload Themes", command=self.reload_themes)

		self.view_btn.config(menu=self.view_menu)

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

	def reload_themes(self):
		tm = ThemeManager.Get()
		tm.force_reload_themes()
		tm.set_theme(tm.current_theme_name)
		self.apply_theme()

	def theme_changer(self):
		tm = ThemeManager.Get()
		theme_names = tm.get_theme_names()

		win = tk.Toplevel(self)
		win.title("Select Theme")

		screen_width = self.winfo_screenwidth()
		screen_height = self.winfo_screenheight()

		cx = int((screen_width / 2) - 150)
		cy = int((screen_height / 2) - 50)

		win.geometry(f"300x100+{cx}+{cy}")
		win.configure(bg=ThemeManager.Get("BG_Panel"))
		win.transient(self)
		win.grab_set()

		if not theme_names:
			tk.Label(
				win,
				text="No themes found",
				bg=ThemeManager.Get("BG_Panel"),
				fg=ThemeManager.Get("Text")
			).pack(pady=20)
			return

		selected = tk.StringVar(value=tm.current_theme_name)

		ttk.Label(win, text="Theme", background=ThemeManager.Get("BG_Panel"), foreground=ThemeManager.Get("Text")).pack(pady=(5, 5))

		box = ttk.Combobox(
			win,
			textvariable=selected,
			values=theme_names,
			state="readonly",
			width=25,
			style="Dark.TCombobox"
		)
		box.pack(pady=5)

		def apply():
			tm.set_theme(selected.get())
			self.apply_theme()
			win.destroy()

		tk.Button(
			win,
			text="Apply",
			bg=ThemeManager.Get("Accent"),
			fg=ThemeManager.Get("BG_Dark"),
			activebackground=ThemeManager.Get("Accent"),
			relief="flat",
			command=apply
		).pack(pady=5)

	def apply_theme(self):
		theme = ThemeManager.Get().current_theme
		if not theme:
			return

		self._setup_style()
		self.configure(bg=ThemeManager.Get("BG_Dark"))

		self.menu_bar.configure(bg=ThemeManager.Get("BG_Panel"))

		self.file_btn.configure(
			bg=ThemeManager.Get("BG_Panel"),
			fg=ThemeManager.Get("Text"),
			activebackground=ThemeManager.Get("BG_Dark"),
			activeforeground=ThemeManager.Get("Accent"),
		)
		self.file_menu.configure(
			bg=ThemeManager.Get("BG_Dark"),
			fg=ThemeManager.Get("Text"),
			activebackground=ThemeManager.Get("Accent"),
			activeforeground=ThemeManager.Get("BG_Dark"),
		)

		self.view_btn.configure(
			bg=ThemeManager.Get("BG_Panel"),
			fg=ThemeManager.Get("Text"),
			activebackground=ThemeManager.Get("BG_Dark"),
			activeforeground=ThemeManager.Get("Accent"),
		)
		self.view_menu.configure(
			bg=ThemeManager.Get("BG_Dark"),
			fg=ThemeManager.Get("Text"),
			activebackground=ThemeManager.Get("Accent"),
			activeforeground=ThemeManager.Get("BG_Dark"),
		)

		self.load_tab.update_theme()
		self.map_tab.update_theme()
		self.edit_tab.update_theme()
		self.refresh()

if __name__ == "__main__":
	ThemeManager.Get()
	App().mainloop()