import tkinter as tk
from tkinter import ttk
from map.map_canvas import MapNode
from utils.theme import *
from audio_engine import PlayStyle

class EditTab(tk.Frame):
	def __init__(self, parent, map_tab):
		super().__init__(parent, bg=ThemeManager.Get("BG_Panel"))
		self.map_tab = map_tab

		self.current_node_id = None

		self.search_var = tk.StringVar()
		self.search_var.trace_add("write", lambda *_: self.refresh())

		self.container = tk.Frame(self, bg=ThemeManager.Get("BG_Panel"))
		self.container.pack(fill="both", expand=True, padx=10, pady=10)

		self.canvas = tk.Canvas(
			self.container,
			bg=ThemeManager.Get("BG_Dark"),
			highlightthickness=0
		)
		self.canvas.pack(side="left", fill="both", expand=True)

		self.scrollbar = ttk.Scrollbar(
			self.container,
			orient="vertical",
			command=self.canvas.yview,
			style="Vertical.TScrollbar"
		)
		self.scrollbar.pack(side="right", fill="y")
		self.canvas.configure(yscrollcommand=self.scrollbar.set)

		self.list_frame = tk.Frame(self.canvas, bg=ThemeManager.Get("BG_Dark"))
		self.list_frame.pack(fill="both", expand=True)
		
		self.window_id = self.canvas.create_window(
			(0, 0), window=self.list_frame, anchor="nw", width=self.canvas.winfo_reqwidth()
		)

		self.list_frame.bind(
			"<Configure>",
			lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
		)

	def open_node(self, node: MapNode):
		self.current_node_id = node.id
		self.refresh()

	def refresh(self):
		for w in self.list_frame.winfo_children():
			w.destroy()

		query = self.search_var.get().lower()

		for node in self.map_tab.canvas.nodes:
			searchable = f"{node.id} {node.audio_node.file_path}".lower()
			if query and query not in searchable:
				continue

			self._create_node_editor(node)

	def _create_node_editor(self, node: MapNode):
		audio = node.audio_node
		expanded = tk.BooleanVar(value=(node.id == self.current_node_id))

		outer = tk.Frame(self.list_frame, bg=ThemeManager.Get("BG_Panel"))
		outer.pack(fill="x", expand=True, pady=4)

		header = tk.Frame(outer, bg=ThemeManager.Get("BG_Panel"))
		header.pack(fill="x", expand=True)

		arrow = tk.Label(
			header,
			text="▼" if expanded.get() else "▶",
			width=2,
			bg=ThemeManager.Get("BG_Panel"),
			fg=ThemeManager.Get("Accent"),
			font=("Segoe UI", 10, "bold")
		)
		arrow.pack(side="left")

		title = ttk.Label(
			header,
			text=f"#{node.id} {audio.file_path.split('/')[-1]}",
			style="EditBold.TLabel"
		)
		title.pack(side="left", padx=4, expand=True, fill="x")

		content = tk.Frame(
			outer,
			bg=ThemeManager.Get("BG_Dark"),
			highlightbackground=ThemeManager.Get("Grid_Color"),
			highlightthickness=1
		)

		content.columnconfigure(0, weight=1)
		content.columnconfigure(1, weight=0)

		ttk.Label(
			content,
			text="Playstyle",
			style="Edit.TLabel",
			background=ThemeManager.Get("BG_Dark")
		).grid(row=0, column=0, sticky="w", padx=6, pady=4)

		playstyle = ttk.Combobox(
			content,
			state="readonly",
			values=["Loop Forever", "Play On Cursor Enter"],
			style="Edit.TCombobox",
			width=22
		)

		playstyle.set(
			"Loop Forever"
			if audio.playstyle == PlayStyle.LOOP_FOREVER
			else "Play On Cursor Enter"
		)

		playstyle.grid(row=0, column=1, padx=6, pady=4, sticky="e")

		ttk.Label(
			content,
			text="Loops",
			style="Edit.TLabel",
			background=ThemeManager.Get("BG_Dark")
		).grid(row=1, column=0, sticky="w", padx=6, pady=4)

		loops = ttk.Spinbox(
			content,
			from_=-1,
			to=100,
			style="Edit.TSpinbox",
			width=8
		)
		loops.set(audio.loops)
		loops.grid(row=1, column=1, sticky="e", padx=6, pady=4)

		def apply_changes(event=None):
			audio.playstyle = (
				PlayStyle.LOOP_FOREVER
				if playstyle.get() == "Loop Forever"
				else PlayStyle.CURSOR_ENTER
			)

			try:
				audio.loops = int(loops.get())
			except ValueError:
				loops.set(audio.loops)

			content.focus_set()

		playstyle.bind("<<ComboboxSelected>>", apply_changes)
		loops.bind("<FocusOut>", apply_changes)
		loops.bind("<Return>", apply_changes)

		def toggle(event=None):
			is_open = not expanded.get()
			expanded.set(is_open)

			self.expanded_node_id = node.id if is_open else None

			if is_open:
				arrow.config(text="▼")
				content.pack(fill="x", padx=20, pady=6)
			else:
				arrow.config(text="▶")
				content.pack_forget()

		header.bind("<Button-1>", toggle)
		arrow.bind("<Button-1>", toggle)
		title.bind("<Button-1>", toggle)

		if expanded.get():
			content.pack(fill="x", padx=20, pady=6)

		focus_button = tk.Button(
			content,
			text="Focus Node",
			bg=ThemeManager.Get("Accent"),
			fg=ThemeManager.Get("BG_Dark"),
			activebackground=ThemeManager.Get("Accent"),
			relief="flat",
			command=lambda: self.focus_node(node)
		)
		focus_button.grid(row=2, column=0, columnspan=2, pady=6)
	
	def focus_node(self, node):
		main = self.winfo_toplevel()
		main.tabs.select(main.map_tab)
		main.map_tab.canvas.focus_node(node)


	def update_theme(self):
		self.configure(bg=ThemeManager.Get("BG_Panel"))

		self.container.configure(bg=ThemeManager.Get("BG_Panel"))
		self.canvas.configure(bg=ThemeManager.Get("BG_Dark"))
		self.list_frame.configure(bg=ThemeManager.Get("BG_Dark"))

		for w in self.list_frame.winfo_children():
			if isinstance(w, tk.Button):
				w.configure(
					bg=ThemeManager.Get("Accent"),
					fg=ThemeManager.Get("BG_Dark"),
					activebackground=ThemeManager.Get("Accent"),
				)