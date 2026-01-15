from concurrent.futures import ThreadPoolExecutor

from os import environ

from enums import PlayStyle
environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'

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
	def __init__(self, file_path, is_file_load=False):
		self.file_path = file_path
		self.enabled = True

		self.playstyle = PlayStyle.LOOP_FOREVER
		self.loops = -1

		self.sound = None
		self.channel = pygame.mixer.find_channel(True)
		self.is_playing = False

		self.update(is_file_load)

	def update(self, is_file_load=False):
		if self.sound is None:
			if is_file_load:
				self.sound = _load_sound_sync(self.file_path)
			else:
				self.sound = load_sound_async(self.file_path)

		if self.playstyle == PlayStyle.LOOP_FOREVER:
			self.play()
		else:
			self.stop()

	def play(self):
		if not self.sound or not self.channel:
			return
		if self.is_playing:
			return
		
		self.channel.play(self.sound, loops=self.loops)
		self.channel.set_volume(0.0)
		self.is_playing = True

	def stop(self):
		if not self.channel:
			return
		self.channel.stop()
		self.is_playing = False

	def set_volume(self, volume):
		if self.channel:
			vol = max(0.0, min(1.0, volume))
			self.channel.set_volume(vol)