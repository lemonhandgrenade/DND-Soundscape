import tkinter as tk
from tkinter import ttk
import json
import gzip

from enums import GlideMode
from map.map_canvas import MapCanvas, MapNode
from audio_engine import AudioNode, PlayStyle, load_sound_async
from utils.theme import *
from utils.alerts import AlertManager

class MapTab(tk.Frame):
	def __init__(self, parent, shared_files):
		super().__init__(parent, bg=ThemeManager.Get("BG_Panel"))
		self.shared_files = shared_files
		
		# Left Side
		self.left_panel = tk.Frame(self, bg=ThemeManager.Get("BG_Panel"))
		self.left_panel.pack(side="left", fill="y")

		# Search Bar
		self.filtered_files = list(shared_files)
		self.search_var = tk.StringVar()
		self.search_var.trace_add("write", self.update_search)

		self.search_entry = tk.Entry(
			self.left_panel,
			textvariable=self.search_var,
			bg=ThemeManager.Get("BG_Dark"),
			fg=ThemeManager.Get("Text"),
			insertbackground=ThemeManager.Get("Text"),
			takefocus=0,
			relief="flat",
			font=("Segoe UI", 10)
		)
		self.search_entry.pack(side="top", fill="x", padx=0, pady=(10, 2))

		# Loaded MP3 Paths
		self.sidebar = tk.Listbox(
			self.left_panel,
			width=30,
			bg=ThemeManager.Get("BG_Dark"),
			fg=ThemeManager.Get("Text"),
			selectbackground=ThemeManager.Get("Accent"),
			highlightthickness=0,
			border=0,
			activestyle='none'
		)
		self.sidebar.pack(side="left", fill="y")

		self.search_entry.insert(0, "Search...")
		self.search_entry.bind("<FocusIn>", self.remove_ghost_text)
		self.search_entry.bind("<FocusOut>", self.add_ghost_text)

		self.drag_active = False
		self.dragged_index = None
		self.drag_label = None

		# Node Canvas
		self.canvas = MapCanvas(self)
		self.canvas.pack(side="right", fill="both", expand=True)

		# Snap To Grid Checkbox
		self.grid_snap_check = tk.Checkbutton(
			self,
			text="Snap to Grid",
			variable=self.canvas.snap_to_grid,
			bg=ThemeManager.Get("BG_Panel"),
			fg=ThemeManager.Get("Text"),
			selectcolor=ThemeManager.Get("BG_Panel"),
			activebackground=ThemeManager.Get("BG_Panel"),
			activeforeground=ThemeManager.Get("Accent"),
			relief="flat"
		)
		self.grid_snap_check.pack(anchor="nw", padx=10, pady=2)

		# Cursor Interp Checkbox
		self.glide_frame = tk.Frame(self, bg=ThemeManager.Get("BG_Panel"))
		self.glide_frame.pack(anchor="nw", padx=10, pady=2, fill="x")

		self.glide_label = tk.Label(
			self.glide_frame,
			text="Glide",
			bg=ThemeManager.Get("BG_Panel"),
			fg=ThemeManager.Get("Text"),
			font=("Segoe UI", 9)
		)
		self.glide_label.pack(side="left")

		self.glide_combo = ttk.Combobox(
			self.glide_frame,
			state="readonly",
			values=["Snap", "Linear", "Ease Out"],
			width=10,
			style="Dark.TCombobox"
		)
		self.glide_combo.pack(side="right")

		mode_map = {
			GlideMode.SNAP: "Snap",
			GlideMode.LINEAR: "Linear",
			GlideMode.EASE_OUT: "Ease Out"
		}
		self.glide_combo.set(mode_map[self.canvas.glide_mode.get()])

		def on_glide_change(event):
			text = self.glide_combo.get()

			if text == "Snap":
				self.canvas.glide_mode.set(GlideMode.SNAP)
			elif text == "Linear":
				self.canvas.glide_mode.set(GlideMode.LINEAR)
			elif text == "Ease Out":
				self.canvas.glide_mode.set(GlideMode.EASE_OUT)

			self.glide_combo.selection_clear()
			self.glide_combo.master.focus_set()

		self.glide_combo.bind("<<ComboboxSelected>>", on_glide_change)

		# Simple Debug Info
		self.simple_ui_check = tk.Checkbutton(
			self,
			text="Simple Debug UI",
			variable=self.canvas.is_simple,
		)
		self.simple_ui_check.pack(anchor="nw", padx=10, pady=2)

		# Binds For List Drag And Drop
		self.sidebar.bind("<ButtonPress-1>", self.start_drag)
		self.sidebar.bind("<ButtonRelease-1>", self.end_drag)
		self.sidebar.bind("<B1-Motion>", self.on_drag_motion)


	def start_drag(self, event):							# On Mouse Down
		self.dragged_index = self.sidebar.nearest(event.y)

		self.sidebar.selection_clear(0, tk.END)				# Lock Selection To Avoid Weird List Visuals
		self.sidebar.selection_set(self.dragged_index)		#
		self.sidebar.activate(self.dragged_index)			#

		filename = self.sidebar.get(self.dragged_index)

		self.drag_label = tk.Label(
			self.winfo_toplevel(),
			text=filename,
			bg=ThemeManager.Get("Accent"),
			fg=ThemeManager.Get("BG_Dark"),
			font=("Segoe UI", 9, "bold"),
			padx=10,
			pady=4,
			relief="flat"
		)

		root = self.winfo_toplevel()
		x = event.x_root - root.winfo_rootx() + 4
		y = event.y_root - root.winfo_rooty() + 4
		self.drag_label.place(x=x, y=y)


		self.sidebar.config(cursor="hand2")
		self.canvas.show_drop_indicator()


	def on_drag_motion(self, event):						# When Moving Drag
		if self.dragged_index is not None:
			self.sidebar.selection_clear(0, tk.END)
			self.sidebar.selection_set(self.dragged_index)

		if self.drag_label:
			root = self.winfo_toplevel()
			x = event.x_root - root.winfo_rootx() + 4
			y = event.y_root - root.winfo_rooty() + 4
			self.drag_label.place(x=x, y=y)

		return "break"


	def end_drag(self, event):								# On Drop
		if self.drag_label:
			self.drag_label.destroy()
			self.drag_label = None

		index = self.dragged_index
		self.dragged_index = None

		self.sidebar.config(cursor="")
		self.canvas.hide_drop_indicator()

		if index is None:
			return

		widget = event.widget.winfo_containing(event.x_root, event.y_root)
		if widget == self.canvas:
			file_path = self.shared_files[index]
			x = self.canvas.canvasx(event.x_root - self.canvas.winfo_rootx())
			y = self.canvas.canvasy(event.y_root - self.canvas.winfo_rooty())
			self.canvas.add_node(x - self.canvas.offset_x, y - self.canvas.offset_y, file_path)

	def update_search(self, *args):
		filter = self.search_var.get().lower()
		
		if filter == "search...":
			self.filtered_files = self.shared_files
		else:
			self.filtered_files = [f for f in self.shared_files if filter in f.lower()]
		self.refresh_searching()

	def refresh_searching(self):
		if self.sidebar is None:
			return
		self.sidebar.delete(0, tk.END)
		for f in self.filtered_files:
			self.sidebar.insert(tk.END, "    " + f.split("/")[-1])

	def add_ghost_text(self, event):
		if self.search_entry.get() == '':
			self.search_entry.insert(0, 'Search...')
			self.search_entry.config(fg=ThemeManager.Get("Text_Ghost"))

	def remove_ghost_text(self, event):
		if self.search_entry.get() == 'Search...':
			self.search_entry.delete(0, "end")
			self.search_entry.insert(0, '')
			self.search_entry.config(fg=ThemeManager.Get("Text"))

	def save_map(self, file_path):
		data = {
			"version": 1,
			"cursor": {
				"x": self.canvas.cursor_x,
				"y": self.canvas.cursor_y
			},
			"nodes": []
		}

		for node in self.canvas.nodes:
			audio = node.audio_node
			data["nodes"].append({
				"file_path": audio.file_path,
				"x": node.real_x,
				"y": node.real_y,
				"radius": node.radius,
				"enabled": audio.enabled,
				"playstyle": audio.playstyle,
				"loops": audio.loops
			})

		with gzip.open(file_path, "wt", encoding="utf-8") as f:
			json.dump(data, f)

	def load_map(self, file_path, shared_files):
		try:
			with gzip.open(file_path, "r") as f:
				data = json.load(f)

			for node in self.canvas.nodes[:]:
				node.audio_node.channel.stop()
				self.canvas.delete(node.node)
				self.canvas.delete(node.circle)
				self.canvas.delete(node.text)
			self.canvas.nodes.clear()

			cursor = data.get("cursor", {"x": 200, "y": 200})
			self.canvas.cursor_x = cursor["x"]
			self.canvas.cursor_y = cursor["y"]
			self.canvas.cursor_target_x = cursor["x"]
			self.canvas.cursor_target_y = cursor["y"]

			for node_data in data.get("nodes", []):
				file = node_data["file_path"]
				load_sound_async(file)

				if file not in shared_files:
					shared_files.append(file)

				audio = AudioNode(file, True)

				audio.enabled = node_data.get("enabled", True)
				audio.playstyle = node_data.get("playstyle", PlayStyle.LOOP_FOREVER)
				audio.loops = node_data.get("loops", -1)

				node = MapNode(
					self.canvas,
					node_data["x"],
					node_data["y"],
					audio,
					radius=node_data.get("radius", 120)
				)
				self.canvas.nodes.append(node)

			self.canvas.update_all_positions()
		except Exception as e:
			AlertManager.Get().CreateWarning(f"The File Could Not Be Loaded, It May Be Corrupted: {e}")


	def remove_file(self, file_path):						# Remove File
		self.canvas.remove_nodes_with_file(file_path)

	def refresh(self):										# Refresh MP3 List
		if self.search_var.get():
			self.update_search()
		else:
			self.filtered_files = list(self.shared_files)
			self.sidebar.delete(0, tk.END)
			for f in self.shared_files:
				self.sidebar.insert(tk.END, "    " + f.split("/")[-1])

	def update_theme(self):
		self.configure(
			bg=ThemeManager.Get("BG_Panel")
		)

		self.left_panel.configure(bg=ThemeManager.Get("BG_Panel"))

		self.sidebar.configure(
			bg=ThemeManager.Get("BG_Dark"),
			selectbackground=ThemeManager.Get("Accent"),
			fg=ThemeManager.Get("Text")
		)
		self.grid_snap_check.configure(
			activeforeground=ThemeManager.Get("Accent"),
			bg=ThemeManager.Get("BG_Panel"),
			selectcolor=ThemeManager.Get("BG_Panel"),
			activebackground=ThemeManager.Get("BG_Panel"),
			fg=ThemeManager.Get("Text"),
		)
		self.simple_ui_check.configure(
			activeforeground=ThemeManager.Get("Accent"),
			bg=ThemeManager.Get("BG_Panel"),
			selectcolor=ThemeManager.Get("BG_Panel"),
			activebackground=ThemeManager.Get("BG_Panel"),
			fg=ThemeManager.Get("Text"),
		)

		self.search_entry.configure(
			bg=ThemeManager.Get("BG_Dark"),
			fg=ThemeManager.Get("Text"),
			insertbackground=ThemeManager.Get("Text")
		)

		self.glide_frame.configure(bg=ThemeManager.Get("BG_Panel"))

		self.glide_label.configure(
			bg=ThemeManager.Get("BG_Panel"),
			fg=ThemeManager.Get("Text")
		)

		self.canvas.update_theme()