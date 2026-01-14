import tkinter as tk
from tkinter import messagebox
import threading

class AlertManager:
	_instance = None

	def __init__(self):
		if AlertManager._instance is not None:
			raise RuntimeError("Use Get()")
		AlertManager._instance = self

	@classmethod
	def Get(cls):
		if cls._instance is None:
			cls._instance = cls()

		return cls._instance
	
	def CreateAlert(self, message: str):
		"""This Function Creates A Generic MessageBox Alert

		Args:
			message (str): The Alert Message
		"""
		self._show_popup(message, "Alert", icon="info")

	def CreateWarning(self, message: str):
		"""This Function Create A Generic MessageBox Warning

		Args:
			message (str): The Warning Message
		"""
		self._show_popup(message, "Warning", icon="warning")

	def _show_popup(self, message: str, title: str, icon: str):
		def popup():
			root = tk.Tk()
			root.withdraw()
			if icon == "info":
				messagebox.showinfo(title, message)
			elif icon == "warning":
				messagebox.showwarning(title, message)
			root.destroy()

		threading.Thread(target=popup, daemon=True).start()