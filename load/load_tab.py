import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from threading import Thread
from theme import *
from audio_engine import load_sound_async


class LoadTab(tk.Frame):
	def __init__(self, parent, shared_files, remove_file, refresh):
		super().__init__(parent, bg=BG_PANEL)
		self.shared_files = shared_files
		self.remove_file = remove_file
		self.refresh_all = refresh

		# Scrollable Container For Loaded Files
		container = tk.Frame(self, bg=BG_PANEL)
		container.pack(fill="both", expand=True, padx=10, pady=10)

		self.canvas = tk.Canvas(
			container,
			bg=BG_DARK,
			highlightthickness=0
		)

		self.scrollbar = ttk.Scrollbar(
			container,
			orient="vertical",
			command=self.canvas.yview,
			style="Vertical.TScrollbar"
		)
		self.canvas.configure(yscrollcommand=self.scrollbar.set)

		self.scrollbar.pack(side="right", fill="y")
		self.canvas.pack(side="left", fill="both", expand=True)

		self.list_frame = tk.Frame(self.canvas, bg=BG_DARK)
		
		self.window_id = self.canvas.create_window(
			(0, 0),
			window=self.list_frame,
			anchor="nw"
		)

		self.list_frame.bind(
			"<Configure>",
			lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
		)

		self.canvas.bind(
			"<Configure>",
			lambda e: self.canvas.itemconfigure(
				self.window_id,
				width=e.width
			)
		)

		# Buttons Row
		button_row = tk.Frame(self, bg=BG_PANEL)
		button_row.pack(pady=5)

		tk.Button(
			button_row,
			text="Add Music",
			bg=ACCENT,
			fg=BG_DARK,
			activebackground=ACCENT,
			relief="flat",
			command=self.add_file
		).pack(side="left", padx=5)

		self.canvas.bind("<Enter>", self.bind_mousewheel)
		self.canvas.bind("<Leave>", self.unbind_mousewheel)

	def bind_mousewheel(self, event):
		self.canvas.bind_all("<MouseWheel>", self.on_mousewheel)

	def unbind_mousewheel(self, event):
		self.canvas.unbind_all("<MouseWheel>")

	def on_mousewheel(self, event):
		if event.num == 4 or event.delta > 0:
			self.canvas.yview_scroll(-1, "units")
		elif event.num == 5 or event.delta < 0:
			self.canvas.yview_scroll(1, "units")

	def add_file(self):
		files = filedialog.askopenfilenames(
			title="Load Music",
			initialdir="./",
			filetypes=[
				("Audio Files", "*.mp3 *.wav *.ogg")
			]
		)
		Thread(target=self.add_file_thread, args=(files,), daemon=True).start()

	def add_file_thread(self, files):
		for f in files:
			if f not in self.shared_files:
				load_sound_async(f)
				self.shared_files.append(f)
		self.refresh_all()

	def remove_file_clicked(self, file_path):
		self.remove_file(file_path)
		self.refresh_all()

	def refresh(self):
		# Clear UI
		for widget in self.list_frame.winfo_children():
			widget.destroy()

		# Rebuild File Lists
		for file_path in self.shared_files:
			row = tk.Frame(self.list_frame, bg=BG_DARK)
			row.pack(fill="x", pady=2)

			label = tk.Label(
				row,
				text=file_path,
				bg=BG_DARK,
				fg=FG_TEXT,
				anchor="w",
				font=("Segoe UI", 11)
			)
			label.pack(side="left", fill="x", expand=True, padx=(6, 0))

			button = tk.Button(
				row,
				text="✕",
				bg=BG_DARK,
				fg=FG_TEXT,
				activebackground=CLOSE_RED,
				activeforeground=FG_TEXT,
				bd=0,
				command=lambda p=file_path: self.remove_file_clicked(p)
			)
			button.pack(side="right", padx=6)

			def on_enter(self, b=button):
				b.configure(bg=CLOSE_RED, fg=FG_TEXT)

			def on_leave(self, b=button):
				b.configure(bg=BG_DARK, fg=FG_TEXT)

			button.bind("<Enter>", on_enter)
			button.bind("<Leave>", on_leave)