import tkinter as tk
from tkinter import ttk
from utils.theme import *
from audio_engine import PlayStyle

class EditTab(tk.Frame):
	def __init__(self, parent, shared_files, map_tab):
		super().__init__(parent, bg=ThemeManager.Get("BG_Panel"))
		self.shared_files = shared_files
		self.map_tab = map_tab

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

	def refresh(self):
		for w in self.list_frame.winfo_children():
			w.destroy()

		for file_path in self.shared_files:
			self._create_file_editor(file_path)

	def _create_file_editor(self, file_path):
		expanded = tk.BooleanVar(value=False)

		outer = tk.Frame(self.list_frame, bg=ThemeManager.Get("BG_Panel"))
		outer.pack(fill="x", expand=True, pady=4)

		header = tk.Frame(outer, bg=ThemeManager.Get("BG_Panel"))
		header.pack(fill="x", expand=True)

		arrow = tk.Label(
			header,
			text="▶",
			width=2,
			bg=ThemeManager.Get("BG_Panel"),
			fg=ThemeManager.Get("Accent"),
			font=("Segoe UI", 10, "bold")
		)
		arrow.pack(side="left")

		title = ttk.Label(
			header,
			text=file_path.split("/")[-1],
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

		audio_playstyle, audio_loops = OptionsManager.GetAudioSettings(file_path)

		# Playstyle
		ttk.Label(content, text="Playstyle", style="Edit.TLabel", background=ThemeManager.Get("BG_Dark")).grid(row=0, column=0, sticky="w", padx=6, pady=4)

		playstyle = ttk.Combobox(
			content,
			state="readonly",
			values=["Loop Forever", "Play On Cursor Enter"],
			style="Edit.TCombobox",
		)
		if audio_playstyle == PlayStyle.LOOP_FOREVER:
			playstyle.current(0)
		elif audio_playstyle == PlayStyle.CURSOR_ENTER:
			playstyle.current(1)
		else:
			AlertManager.CreateWarning(f"Unknown Audio Settings Detected On {file_path}")
		playstyle.grid(row=0, column=1, padx=6, pady=4, sticky="e")

		# Loops
		ttk.Label(content, text="Loops", style="Edit.TLabel", background=ThemeManager.Get("BG_Dark")).grid(row=1, column=0, sticky="w", padx=6, pady=4)

		loops = ttk.Spinbox(
			content,
			from_=-1,
			to=100,
			style="Edit.TSpinbox"
		)
		loops.set(audio_loops)
		loops.grid(row=1, column=1, sticky="e", padx=6, pady=4)

		def toggle(event):
			expanded.set(not expanded.get())
			if expanded.get():
				arrow.config(text="▼")
				content.pack(fill="x", padx=20, pady=6)
			else:
				arrow.config(text="▶")
				content.pack_forget()

		header.bind("<Button-1>", toggle)
		arrow.bind("<Button-1>", toggle)
		title.bind("<Button-1>", toggle)

		def apply_changes(event):
			clear_focus(event)

			loop_type = PlayStyle.LOOP_FOREVER if playstyle.get() == "Loop Forever" else PlayStyle.CURSOR_ENTER
			loop_count = int(loops.get())
			OptionsManager.SetAudioSettings(file_path, loop_type, loop_count)

			for node in self.map_tab.canvas.nodes:
				if node.audio_node.file_path == file_path:
					node.audio_node.playstyle = loop_type
					node.audio_node.loops = loop_count

		def clear_focus(event):
			event.widget.selection_clear()
			event.widget.icursor("end")
			event.widget.master.focus_set()

		playstyle.bind("<<ComboboxSelected>>", apply_changes)
		loops.bind("<FocusOut>", apply_changes)
		loops.bind("<Return>", apply_changes)

	def update_theme(self):
		self.configure(bg=ThemeManager.Get("BG_Panel"))

		self.container.configure(bg=ThemeManager.Get("BG_Panel"))
		self.canvas.configure(bg=ThemeManager.Get("BG_Dark"))
		self.list_frame.configure(bg=ThemeManager.Get("BG_Dark"))