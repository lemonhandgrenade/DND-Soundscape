from concurrent.futures import ThreadPoolExecutor
import pygame

pygame.mixer.init()
pygame.mixer.set_num_channels(32)

_SOUND_CACHE = {}
_SOUND_FUTURES = {}

_sound_executor = ThreadPoolExecutor(max_workers=2)

def _load_sound_sync(path):
	return pygame.mixer.Sound(path)

def load_sound_async(path):
	if path in _SOUND_CACHE:
		return _SOUND_CACHE[path]

	if path in _SOUND_FUTURES:
		future = _SOUND_FUTURES[path]
		if future.done():
			_SOUND_CACHE[path] = future.result()
			del _SOUND_FUTURES[path]
			return _SOUND_CACHE[path]
		return None

	future = _sound_executor.submit(_load_sound_sync, path)
	_SOUND_FUTURES[path] = future
	return None

class AudioNode:
	def __init__(self, file_path):
		self.file_path = file_path
		self.enabled = True
		self.sound = None
		self.channel = pygame.mixer.find_channel(True)
		self.update()

	def update(self):
		if self.sound is None:
			self.sound = load_sound_async(self.file_path)
			if self.sound:
				self.channel.play(self.sound, loops=-1)
				self.channel.set_volume(0.0)

	def set_volume(self, volume):
		if self.channel:
			vol = max(0.0, min(1.0, volume))
			self.channel.set_volume(vol)