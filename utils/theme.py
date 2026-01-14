import os
import json

from utils.alerts import AlertManager

class ThemeManager():
	_instance = None

	def __init__(self):
		self.theme_dir = "./themes"
		self.config_path = "./options.json"

		self.themes = {}
		self.current_theme_name = None
		self.current_theme = {}

		self._load_themes()
		self._load_config()

	@classmethod
	def Get(cls, key=None, default="#FF0000") -> str | None:
		"""Gets The ThemeManager Or A Theme Color With Fallback

		Args:
			key (str, optional): The Key Of The Color In The Theme. Defaults to None.
			default (str, optional): The Fallback Color If The Color Isn't Found In The Theme. Defaults to None.

		Returns:
			str | None: Returns Either ThemeManager Or A String With A Hex Color Code
		"""
		if cls._instance is None:
			cls._instance = cls()

		if key is None:
			return cls._instance

		return cls._instance._get_value(key, default)

	def _load_themes(self):
		self.themes.clear()

		if not os.path.isdir(self.theme_dir):
			return

		for file in os.listdir(self.theme_dir):
			if not file.endswith(".json"):
				continue

			path = os.path.join(self.theme_dir, file)
			try:
				with open(path, "r", encoding="utf-8") as f:
					data = json.load(f)

				name = data.get("name")
				if name:
					self.themes[name] = data

			except Exception as e:
				AlertManager.Get().CreateAlert(f"Failed To Load Theme {file}: {e}")

	def _get_value(self, key, default=None):
		colors = self.current_theme.get("colors", {})
		return colors.get(key, default)

	def get_theme_names(self):
		return list(self.themes.keys())

	def set_theme(self, name, save=True):
		if name not in self.themes:
			raise ValueError(f"Theme '{name}' Not Found")

		self.current_theme_name = name
		self.current_theme = self.themes[name]

		if save:
			self._save_config()

	def _load_config(self):
		theme_name = None

		if os.path.isfile(self.config_path):
			try:
				with open(self.config_path, "r", encoding="utf-8") as f:
					cfg = json.load(f)
					theme_name = cfg.get("theme")
			except Exception:
				pass

		if theme_name in self.themes:
			self.set_theme(theme_name, save=False)
		elif self.themes:
			self.set_theme(next(iter(self.themes)), save=False)

	def _save_config(self):
		try:
			with open(self.config_path, "w", encoding="utf-8") as f:
				json.dump(
					{"theme": self.current_theme_name},
					f
				)
		except Exception as e:
			AlertManager.Get().CreateAlert(f"Failed To Save Options: {e}")

	def reload(self):
		self._load_themes()