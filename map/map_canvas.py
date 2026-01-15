import tkinter as tk
import math
import numpy as np
from audio_engine import AudioNode, PlayStyle
from enums import GlideMode
from utils.theme import *

class MapNode:
	def __init__(self, canvas, x, y, audio_node, radius=120):
		self.canvas = canvas
		self.audio_node = audio_node
		self.radius = radius

		self.real_x = x
		self.offset_x = 0
		self.real_y = y
		self.offset_y = 0

		# Create Node Elements
		self.circle = self.canvas.create_oval(
			x - radius, y - radius,
			x + radius, y + radius,
			outline=ThemeManager.Get("Node_Circle"),
			width=0.5
		)

		self.node = self.canvas.create_oval(
			x - 8, y - 8,
			x + 8, y + 8,
			fill=ThemeManager.Get("Node"),
			outline=""
		)

		# Visual Connect To Cursor
		self.link_line = self.canvas.create_line(
			0, 0, 0, 0,
			fill=ThemeManager.Get("Link_Line"),
			width=1.5,
			dash=(4, 4),
			state="hidden"
		)

		self.canvas.tag_lower(self.link_line, self.node)
		self.canvas.tag_lower(self.link_line, self.canvas.cursor)

		# Debug Info
		filename = self.audio_node.file_path.split("/")[-1]
		self.text = self.canvas.create_text(
			x + 8, y,
			text=f"{filename}\nVol: 0.00",
			anchor="w",
			fill=ThemeManager.Get("Text"),
			font=("Segoe UI", 9)
		)

		# Bind For Interaction
		self.canvas.tag_bind(self.node, "<Button-1>", self.on_press)
		self.canvas.tag_bind(self.node, "<B1-Motion>", self.on_drag)
		self.canvas.tag_bind(self.node, "<ButtonRelease-1>", self.on_release)
		self.canvas.tag_bind(self.node, "<ButtonRelease-3>", self.on_right_click)

	def on_right_click(self, event):				# Context Menu
		self.canvas.right_clicked_node = self
		node = self.canvas.right_clicked_node
		enabled = node.audio_node.enabled

		self.canvas.generate_node_menu(enabled)

		self.canvas.node_menu.tk_popup(event.x_root, event.y_root)

	def on_press(self, event):						# On Click
		self.canvas.dragging_node = True

	def on_drag(self, event):						# Drag Node
		x = (event.x - self.offset_x) / self.canvas.scale_factor
		y = (event.y - self.offset_y) / self.canvas.scale_factor

		if self.canvas.snap_to_grid.get():
			x = round((x - (self.canvas.offset_x / self.canvas.scale_factor)) / self.canvas.grid_size) * self.canvas.grid_size
			y = round((y - (self.canvas.offset_y / self.canvas.scale_factor)) / self.canvas.grid_size) * self.canvas.grid_size
		else:
			x -= (self.canvas.offset_x / self.canvas.scale_factor)
			y -= (self.canvas.offset_y / self.canvas.scale_factor)
		self.move_to(x, y)
		self.canvas.update_audio()

	def on_release(self, event):
		self.canvas.dragging_node = False
		self.canvas.update_all_positions()

	def move_to(self, x, y):						# Set Location
		self.real_x = x
		self.real_y = y
		r = self.radius
		sx = x * self.canvas.scale_factor + self.canvas.offset_x
		sy = y * self.canvas.scale_factor + self.canvas.offset_y
		sr = r * self.canvas.scale_factor
		self.canvas.coords(self.circle, sx-sr, sy-sr, sx+sr, sy+sr)
		self.canvas.coords(self.node, sx-8, sy-8, sx+8, sy+8)
		self.canvas.coords(self.text, sx + 12, sy)

	def center(self) -> tuple[float, float]:
		"""Gets The Center Coord Of The Node

		Returns:
			float,float: Returns X And Y Seperately
		"""
		x1, y1, x2, y2 = self.canvas.coords(self.node)
		return (x1+x2)/2, (y1+y2)/2


class MapCanvas(tk.Canvas):
	def __init__(self, parent, grid_size=40):
		super().__init__(
			parent,
			bg=ThemeManager.Get("BG_Dark"),
			highlightthickness=0
		)
		self.parent = parent
		self.scale_factor = 1.0
		self.offset_x = 0
		self.offset_y = 0
		self.nodes = []
		self.dragging_node = False
		self.drop_outline = None

		self.node_menu = tk.Menu(
			self,
			tearoff=0,
			bg=ThemeManager.Get("BG_Dark"),
			fg=ThemeManager.Get("Text"),
			activebackground=ThemeManager.Get("Accent"),
			activeforeground=ThemeManager.Get("BG_Dark"),
			disabledforeground=ThemeManager.Get("Close_Red"),
			bd=0,
			borderwidth=0,
			relief="flat"
		)

		self.node_menu.configure(
			selectcolor=ThemeManager.Get("Accent"),
			disabledforeground="#777777"
		)

		self.generate_node_menu(True)

		self.right_clicked_node = None

		self.debug_text = self.create_text(
			self.winfo_width() - 10, 10,
			text="Offset: (0, 0)\nZoom: 1.00",
			anchor="ne",
			fill=ThemeManager.Get("Accent"),
			font=("Segoe UI", 10, "bold"),
		)

		self.grid_size = grid_size
		self.snap_to_grid = tk.BooleanVar(value=OptionsManager.Get("snap_to_grid"))
		def _on_snap_change(*_):
			OptionsManager.Set("snap_to_grid", self.snap_to_grid.get())
		self.snap_to_grid.trace_add("write", _on_snap_change)

		self.glide_mode = tk.StringVar(value=OptionsManager.Get("glide_mode"))
		def _on_glide_changed(*_):
			OptionsManager.Set("glide_mode", self.glide_mode.get())
		self.glide_mode.trace_add("write", _on_glide_changed)

		self.is_simple = tk.BooleanVar(value=OptionsManager.Get("simple_ui"))
		def _on_simple_change(*_):
			OptionsManager.Set("simple_ui", self.is_simple.get())
		self.is_simple.trace_add("write", _on_simple_change)
		
		# Cursor
		self.cursor = self.create_oval(
			0, 0, 12, 12,
			fill=ThemeManager.Get("Text"),
			outline=""
		)
		self.cursor_x = 200
		self.cursor_target_x = 200
		self.cursor_y = 200
		self.cursor_target_y = 200
		self.move_cursor(200, 200)

		# Bindings
		self.bind("<Configure>", self.on_resize)		# Resize Window

		self.bind("<MouseWheel>", self.on_zoom)			# Translations
		self.bind("<ButtonPress-2>", self.start_pan)	#
		self.bind("<B2-Motion>", self.do_pan)			#

		self.bind("<B1-Motion>", self.drag_cursor)

		self.bind("<KeyPress-f>", self.refocus)
		self.configure(takefocus=True)
		self.bind("<Button-1>", lambda e: self.focus_set(), add="+")

		# Glide Loop Every 16~ ms
		self.after(16, self._glide_loop)

	def _calc_zoom_from_dist(self, x: float) -> float:
		scalar = ((586 / self.winfo_width()) + (536 / self.winfo_height())) / 2
		magic = 13.6 * (x ** (-0.475))
		return min(magic, 2) / scalar

	def _refocus_nodes(self):
		coords_min = np.array([1000000000.0, 1000000000.0])
		coords_max = np.array([-1000000000.0, -1000000000.0])
		for node in self.nodes:
			cx, cy = node.center()
			coord = np.array([cx,cy])							# Get Pos Without Panning / Zooming
			coord -= np.array([self.offset_x,self.offset_y])	#
			coord /= self.scale_factor							#
			
			coords_min = np.minimum(coords_min, coord)
			coords_max = np.maximum(coords_max, coord)

		node_dist = np.linalg.norm(coords_max-coords_min)
		calc_zoom = self._calc_zoom_from_dist(node_dist)
		self.set_zoom(calc_zoom)

		offset_x = ((coords_min[0] + coords_max[0]) / 2.0) * self.scale_factor
		offset_y = ((coords_min[1] + coords_max[1]) / 2.0) * self.scale_factor

		self.offset_x = -offset_x + (self.winfo_width() / 2)
		self.offset_y = -offset_y + (self.winfo_height() / 2)

	def _refocus_nodeless(self):
		self.set_zoom(1)

		offset_x = 0.0
		offset_y = 0.0

		offset_x = -self.cursor_x
		offset_y = -self.cursor_y

		self.offset_x = offset_x + (self.winfo_width() / 2)
		self.offset_y = offset_y + (self.winfo_height() / 2)

	def refocus(self, event):
		count = len(self.nodes)

		if count > 0:
			self._refocus_nodes()
		else:
			self._refocus_nodeless()
		
		self.pan_start = (0, 0)
		self.update_all_positions()
		self.update_debug_info()

	def generate_node_menu(self, enabled: bool):
		"""Creates The Right Click Menu For Nodes

		Args:
			enabled (bool): Whether The Clicked Node Is Enabled
		"""
		self.node_menu.delete(0, "end")
		self.node_menu.add_command(label="Radius", command=self.adjust_node_radius)
		self.node_menu.add_separator()
		if not enabled:
			self.node_menu.add_command(label="Enable", command=self.enable_node)
		else:
			self.node_menu.add_command(label="Disable", command=self.disable_node)
		self.node_menu.add_separator()
		self.node_menu.add_command(label="Delete", command=self.delete_node)

	def move_cursor(self, x: float, y: float):
		"""Sets The Target Of For The Cursor To Interp/Snap To

		Args:
			x (float): X Coord
			y (float): Y Coord
		"""
		self.cursor_target_x = (x - self.offset_x) / self.scale_factor
		self.cursor_target_y = (y - self.offset_y) / self.scale_factor

		if self.glide_mode.get() == GlideMode.SNAP:
			self.cursor_x = self.cursor_target_x
			self.cursor_y = self.cursor_target_y
			self.update_cursor_position()

	def glide_linear(self, current: np.ndarray[float, float], target: np.ndarray[float, float], speed: float) -> np.ndarray[float, float]:
		delta = target - current
		delta_size = np.linalg.norm(delta)
		step = speed * .016666

		if delta_size <= step:
			return target
		
		if step > 0:
			delta_norm = delta / delta_size
			return current + delta_norm * step
		else:
			return current
		
	def glide_ease_out(self, current: np.ndarray[float, float], target: np.ndarray[float, float], speed: float) -> np.ndarray[float, float]:
		delta = target - current
		step = delta * .016666 * speed
		return current + step

	def update_cursor_position(self):
		if self.glide_mode.get() == GlideMode.SNAP:
			self.cursor_x = self.cursor_target_x
			self.cursor_y = self.cursor_target_y
		else:
			pos = np.array([self.cursor_x, self.cursor_y])
			target = np.array([self.cursor_target_x, self.cursor_target_y])
			real = np.array([0,0])
			
			if self.glide_mode.get() == GlideMode.LINEAR:
				real = self.glide_linear(pos, target, 75)
			elif self.glide_mode.get() == GlideMode.EASE_OUT:
				real = self.glide_ease_out(pos, target, 2)
			self.cursor_x = real[0]
			self.cursor_y = real[1]

		sx = self.cursor_x * self.scale_factor + self.offset_x
		sy = self.cursor_y * self.scale_factor + self.offset_y
		self.coords(self.cursor, sx-6, sy-6, sx+6, sy+6)
		self.update_audio()

	def _glide_loop(self):
		self.update_cursor_position()
		self.after(16, self._glide_loop)

	def drag_cursor(self, event):
		if self.dragging_node:
			return

		self.move_cursor(event.x, event.y)

	def add_node(self, x: float, y: float, file_path: str):
		"""Creates And Adds A Node To The Canvas Grid

		Args:
			x (float): The Nodes X Coord
			y (float): The Nodes Y Coord
			file_path (str): The File Path For The Audio File
		"""
		audio = AudioNode(file_path)
		node = MapNode(self, x / self.scale_factor, y / self.scale_factor, audio)
		self.nodes.append(node)
		self.update_all_positions()


	def update_audio(self):
		cx, cy = self.get_cursor_center()

		for node in self.nodes:
			if hasattr(node.audio_node, "enabled") and not node.audio_node.enabled:
				node.audio_node.set_volume(0)
				self.itemconfig(node.text, fill=ThemeManager.Get("Text_Ghost"))
				continue
			
			nx, ny = node.center()
			dist = math.dist((cx, cy), (nx, ny))
			nRad = node.radius * self.scale_factor

			if dist < nRad:
				vol = 1 - (dist / nRad)

				self.coords(
					node.link_line,
					nx, ny,
					cx, cy
				)

				self.itemconfig(node.link_line, state="normal")
			else:
				vol = 0
				self.itemconfig(node.link_line, state="hidden")

			#node.audio_node.set_volume(vol)
			audio = node.audio_node

			if audio.playstyle == PlayStyle.CURSOR_ENTER:
				if vol > 0 and not audio.is_playing:
					audio.play()
				elif vol == 0 and audio.is_playing:
					audio.stop()

			audio.set_volume(vol)


			filename = node.audio_node.file_path.split("/")[-1]
			self.itemconfig(node.text, text=self.get_node_text(filename, vol))
			if vol > 0:
				self.itemconfig(node.text, fill=ThemeManager.Get("Text"))
			else:
				self.itemconfig(node.text, fill=ThemeManager.Get("Text_Ghost"))

	def get_node_text(self, filename: str, vol: float) -> str:
		"""Creates And Returns The Text To The Right Of The Node

		Args:
			filename (str): The File Name Of The Audio
			vol (float): The Volume Of The Node With Respect To The Cursor

		Returns:
			str: Formatted String Of Node Info
		"""
		if self.is_simple.get():
			volume = int(vol * 100)
			return f"{filename}\nVolume: {volume}"
		else:
			width = 24
			bars = '|' * math.ceil(vol * width)
			bars = bars.ljust(width)
			return f"{filename}\n[{bars}]"

	def get_cursor_center(self):
		x1, y1, x2, y2 = self.coords(self.cursor)
		return (x1 + x2) / 2, (y1 + y2) / 2

	def draw_grid(self):
		self.delete("grid")

		w = self.winfo_width()
		h = self.winfo_height()

		start_x = -self.offset_x / self.scale_factor
		start_y = -self.offset_y / self.scale_factor
		end_x = (w - self.offset_x) / self.scale_factor
		end_y = (h - self.offset_y) / self.scale_factor

		start_x = math.floor(start_x / self.grid_size) * self.grid_size
		start_y = math.floor(start_y / self.grid_size) * self.grid_size

		x = start_x
		while x <= end_x:
			screen_x = x * self.scale_factor + self.offset_x
			self.create_line(screen_x, 0, screen_x, h, fill=ThemeManager.Get("Grid_Color"), tags="grid")
			x += self.grid_size

		y = start_y
		while y <= end_y:
			screen_y = y * self.scale_factor + self.offset_y
			self.create_line(0, screen_y, w, screen_y, fill=ThemeManager.Get("Grid_Color"), tags="grid")
			y += self.grid_size

		self.tag_lower("grid")


	def on_resize(self, event):
		self.draw_grid()
		x = self.winfo_width() - 10
		y = 10
		self.coords(self.debug_text, x, y)

	def show_drop_indicator(self):
		if self.drop_outline:
			return

		w = self.winfo_width()
		h = self.winfo_height()

		self.drop_outline = self.create_rectangle(
			2, 2, w-2, h-2,
			outline=ThemeManager.Get("Accent"),
			width=3,
			dash=(6, 4)
		)

	def hide_drop_indicator(self):
		if self.drop_outline:
			self.delete(self.drop_outline)
			self.drop_outline = None

	def on_zoom(self, event):
		self.focus_set()

		factor = 1.1 if event.delta > 0 else 1 / 1.1

		old_scale = self.scale_factor
		new_scale = old_scale * factor
		new_scale = max(0.2, min(3.0, new_scale))

		factor = new_scale / old_scale
		mouse_x, mouse_y = event.x, event.y

		grid_x = (mouse_x - self.offset_x) / old_scale
		grid_y = (mouse_y - self.offset_y) / old_scale

		self.scale_factor = new_scale

		self.offset_x = mouse_x - grid_x * self.scale_factor
		self.offset_y = mouse_y - grid_y * self.scale_factor

		self.update_all_positions()
		self.update_debug_info()

	def set_zoom(self, zoom):
		self.scale_factor = zoom
		self.update_all_positions()
		self.update_debug_info()

	def start_pan(self, event):
		self.focus_set()
		self.pan_start = (event.x, event.y)

	def do_pan(self, event):
		dx = event.x - self.pan_start[0]
		dy = event.y - self.pan_start[1]
		self.offset_x += dx
		self.offset_y += dy
		self.update_all_positions()
		self.pan_start = (event.x, event.y)
		self.update_debug_info()

	def update_all_positions(self):
		for node in self.nodes:
			node.move_to(node.real_x, node.real_y)
		
		self.move_cursor(
			self.cursor_x * self.scale_factor + self.offset_x,
			self.cursor_y * self.scale_factor + self.offset_y
		)
		self.draw_grid()

	def update_debug_info(self):
		text = f"Offset: ({int(self.offset_x)}, {int(self.offset_y)})\nZoom: {self.scale_factor:.2f}"
		self.itemconfig(self.debug_text, text=text, fill=ThemeManager.Get("Accent"))

	def enable_node(self):
		node = self.right_clicked_node
		if node:
			node.audio_node.enabled = True
			self.itemconfig(node.node, fill=ThemeManager.Get("Node"))
			self.update_audio()

	def disable_node(self):
		node = self.right_clicked_node
		if node:
			node.audio_node.enabled = False
			self.itemconfig(node.node, fill=ThemeManager.Get("Node_Disabled"))
			node.audio_node.set_volume(0)
			self.update_audio()

	def delete_node(self):
		node = self.right_clicked_node
		if node:
			node.audio_node.channel.stop()
			self.delete(node.node)
			self.delete(node.circle)
			self.delete(node.text)
			self.delete(node.link_line)
			self.nodes.remove(node)
			self.update_audio()

	def adjust_node_radius(self):
		node = self.right_clicked_node
		if not node:
			return
		
		x = self.winfo_pointerx()
		y = self.winfo_pointery()

		popup = tk.Toplevel(self)
		popup.overrideredirect(True)
		popup.geometry(f"220x60+{x}+{y}")
		popup.configure(bg=ThemeManager.Get("BG_Panel"))
		popup.attributes("-topmost", True)
		
		label = tk.Label(
			popup,
			text="Radius",
			bg=ThemeManager.Get("BG_Panel"),
			fg=ThemeManager.Get("Text"),
			font=("Segoe UI", 10, "bold"),
		)
		label.pack(padx=0, ipadx=0, pady=0, ipady=0)

		slider = tk.Scale(
			popup,
			from_=20,
			to=300,
			orient="horizontal",
			bg=ThemeManager.Get("Grid_Color"),
			fg=ThemeManager.Get("Text"),
			troughcolor=ThemeManager.Get("BG_Dark"),
			highlightthickness=0,
			length=200,
			showvalue=0,
			sliderrelief="flat",
			activebackground=ThemeManager.Get("Accent")
		)
		slider.set(node.radius)
		slider.pack(padx=0, ipadx=0, pady=0, ipady=0)

		def on_slide(val):
			node.radius = float(val)
			node.move_to(node.real_x, node.real_y)

		slider.config(command=on_slide)

		def close(event):
			if event.widget != slider:
				popup.destroy()

		self.bind("<Button-1>", close, add="+")
		self.bind("<Button-3>", close, add="+")

	def remove_nodes_with_file(self, file_path):
		for node in self.nodes[:]:
			if node.audio_node.file_path == file_path:
				if node.audio_node.channel:
					node.audio_node.channel.stop()

				self.delete(node.node)
				self.delete(node.circle)
				self.delete(node.text)

				self.nodes.remove(node)

		self.update_audio()

	def get_audio_settings_for_file(self, file_path):
		for node in self.nodes:
			if node.audio_node.file_path == file_path:
				audio = node.audio_node
				return audio.playstyle, audio.loops

		return "loop_forever", -1

	def update_theme(self):
		self.update_debug_info()
		self.configure(bg=ThemeManager.Get("BG_Dark"))

		self.itemconfig(self.cursor, fill=ThemeManager.Get("Text"))

		self.node_menu.configure(
			selectcolor=ThemeManager.Get("Accent"),
			activebackground=ThemeManager.Get("Accent"),
			bg=ThemeManager.Get("BG_Dark"),
			activeforeground=ThemeManager.Get("BG_Dark"),
			disabledforeground=ThemeManager.Get("Close_Red"),
			fg=ThemeManager.Get("Text")
		)

		self.draw_grid()

		for node in self.nodes:
			self.itemconfig(node.circle, outline=ThemeManager.Get("Node_Circle"))
			self.itemconfig(node.link_line, fill=ThemeManager.Get("Link_Line"))
			self.itemconfig(node.text, fill=ThemeManager.Get("Text"))
			node_color = ThemeManager.Get("Node") if node.audio_node.enabled else ThemeManager.Get("Node_Disabled")
			self.itemconfig(node.node, fill=node_color)