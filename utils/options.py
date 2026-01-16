import json
import os

OPTIONS_FILE = "./options.json"

DEFAULT_OPTIONS = {
	"snap_to_grid": True,
	"glide_mode": "linear",
	"simple_ui": False,
	"theme": "Default",
	"files": {}
}

class OptionsManager:
	_options = None

	@classmethod
	def _load(cls):
		if cls._options is not None:
			return cls._options

		if os.path.exists(OPTIONS_FILE):
			try:
				with open(OPTIONS_FILE, "r", encoding="utf-8") as f:
					cls._options = json.load(f)
			except Exception:
				cls._options = DEFAULT_OPTIONS.copy()
		else:
			cls._options = DEFAULT_OPTIONS.copy()

		for k, v in DEFAULT_OPTIONS.items():
			cls._options.setdefault(k, v)

		return cls._options

	@classmethod
	def _save(cls):
		if cls._options is None:
			return

		with open(OPTIONS_FILE, "w", encoding="utf-8") as f:
			json.dump(cls._options, f, indent='\t')

	@classmethod
	def Get(cls, key: str) -> str | bool:
		"""Returns An Persistent Option Value

		Args:
			key (str): The Key Of The Option

		Returns:
			str|bool: The Gotten Value / Default Fallback
		"""
		return cls._load().get(key, DEFAULT_OPTIONS.get(key))

	@classmethod
	def Set(cls, key: str, value: str):
		"""Save The Option Of Key With A Given Value

		Args:
			key (str): The Option Key To Set
			value (str): The Value Of The Option
		"""
		cls._load()[key] = value
		cls._save()

	@classmethod
	def GetAudioSettings(cls, file_path: str) -> str | bool:
		"""Returns An Persistent Option Value

		Args:
			file_path (str): The File Path Of The Option

		Returns:
			str|bool: The Gotten Value / Default Fallback
		"""
		return cls._load()["files"].get(file_path, ["loop_forever", -1])

	@classmethod
	def SetAudioSettings(cls, file_path: str, value: str, loops: int):
		"""Save The Option Of Key With A Given Value

		Args:
			file_path (str): The File Path To Set
			value (str): The Loop Behaviour Of The Option
			loops (int): The Loops Of The Audio
		"""
		cls._load()["files"][file_path] = [value, loops]
		cls._save()