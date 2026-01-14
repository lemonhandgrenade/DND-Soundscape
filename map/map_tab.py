import tkinter as tk
import json
import gzip

from map.map_canvas import MapCanvas, MapNode
from audio_engine import AudioNode, load_sound_async
from theme import *

class MapTab(tk.Frame):
	def __init__(self, parent, shared_files):
		super().__init__(parent, bg=BG_PANEL)
		self.shared_files = shared_files
		
		# Left Side
		left_panel = tk.Frame(self, bg=BG_PANEL)
		left_panel.pack(side="left", fill="y")

		# Search Bar
		self.filtered_files = list(shared_files)
		self.search_var = tk.StringVar()
		self.search_var.trace_add("write", self.update_search)

		self.search_entry = tk.Entry(
			left_panel,
			textvariable=self.search_var,
			bg=BG_DARK,
			fg=FG_TEXT,
			insertbackground=FG_TEXT,
			takefocus=0,
			relief="flat",
			font=("Segoe UI", 10)
		)
		self.search_entry.pack(side="top", fill="x", padx=0, pady=(10, 2))

		# Loaded MP3 Paths
		self.sidebar = tk.Listbox(
			left_panel,
			width=30,
			bg=BG_DARK,
			fg=FG_TEXT,
			selectbackground=ACCENT,
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
		grid_snap_check = tk.Checkbutton(
			self,
			text="Snap to Grid",
			variable=self.canvas.snap_to_grid,
			bg=BG_PANEL,
			fg=FG_TEXT,
			selectcolor=BG_PANEL,
			activebackground=BG_PANEL,
			activeforeground=ACCENT
		)
		grid_snap_check.pack(anchor="nw", padx=10, pady=2)

		# Cursor Interp Checkbox
		glide_check = tk.Checkbutton(
			self,
			text="Glide",
			variable=self.canvas.glide_enabled,
			bg=BG_PANEL,
			fg=FG_TEXT,
			selectcolor=BG_PANEL,
			activebackground=BG_PANEL,
			activeforeground=ACCENT
		)
		glide_check.pack(anchor="nw", padx=10, pady=2)

		# Simple Debug Info
		simple_ui_check = tk.Checkbutton(
			self,
			text="Simple Debug UI",
			variable=self.canvas.is_simple,
			bg=BG_PANEL,
			fg=FG_TEXT,
			selectcolor=BG_PANEL,
			activebackground=BG_PANEL,
			activeforeground=ACCENT
		)
		simple_ui_check.pack(anchor="nw", padx=10, pady=2)

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
			bg=ACCENT,
			fg=BG_DARK,
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
			self.search_entry.config(fg = FG_TEXT_GHOST)

	def remove_ghost_text(self, event):
		if self.search_entry.get() == 'Search...':
			self.search_entry.delete(0, "end")
			self.search_entry.insert(0, '')
			self.search_entry.config(fg = FG_TEXT)

	def save_map(self, file_path):
		data = {
			"cursor": {"x": self.canvas.cursor_x, "y": self.canvas.cursor_y},
			"nodes": []
		}
		for node in self.canvas.nodes:
			data["nodes"].append({
				"file_path": node.audio_node.file_path,
				"x": node.real_x,
				"y": node.real_y,
				"radius": node.radius,
				"enabled": getattr(node.audio_node, "enabled", True)
			})
		with gzip.open(file_path, "wt", encoding="utf-8") as f:
			json.dump(data, f)

	def load_map(self, file_path, shared_files):
		with gzip.open(file_path, "r") as f:
			data = json.load(f)

		for node in self.canvas.nodes[:]:
			node.audio_node.channel.stop()
			self.delete(node.node)
			self.delete(node.circle)
			self.delete(node.text)
		self.canvas.nodes.clear()

		self.canvas.cursor_x = data["cursor"]["x"]
		self.canvas.cursor_y = data["cursor"]["y"]
		self.canvas.cursor_target_x = self.canvas.cursor_x
		self.canvas.cursor_target_y = self.canvas.cursor_y

		for node_data in data["nodes"]:
			file = node_data["file_path"]
			load_sound_async(file)
			shared_files.append(file)
			audio = AudioNode(file)
			audio.enabled = node_data.get("enabled", True)
			node = MapNode(
				self.canvas,
				node_data["x"],
				node_data["y"],
				audio,
				radius=node_data.get("radius", 120)
			)
			self.canvas.nodes.append(node)

		self.canvas.update_all_positions()

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