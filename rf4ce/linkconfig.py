# -*- coding: utf-8 -*-
"""
Describes a RF4CE link.
"""

import json
import binascii

from rf4ce import Rf4ceNode


class LinkConfig(object):

	"""Stores a RF4CE link information.

	Stored RF4CE link information are:
	source, destination, key, frame_counter, dest_panid
	"""

	def __init__(self, config_filename=None):
		self.config_filename = config_filename
		if config_filename:
			self.load()
		else:
			self.dest_panid = None
			self.source = None
			self.destination = None
			self.key = None
			self.frame_counter = 0

	def load(self):
		"""Loads link configuration from supplied JSON file"""
		try:
			f = open(self.config_filename, "rb")
		except IOError:
			print("Cannot open configuration file '{}'".format(self.config_filename))
			raise

		try:
			json_config = json.load(f)
			self.dest_panid = int(json_config["dest_panid"], 16)
			self.source = Rf4ceNode(json_config["full_source"], 
				int(json_config["short_source"], 16))
			self.destination = Rf4ceNode(json_config["full_destination"],
				int(json_config["short_destination"], 16))
			if "key" in json_config:
				self.key = json_config["key"]
			else:
				self.key = None
			if "frame_counter" in json_config:
				self.frame_counter = json_config["frame_counter"]
			else:
				self.frame_counter = 0
		except (ValueError, KeyError):
			print("Invalid JSON file")
			raise


	def save(self, config_filename=None):
		"""Saves link configuration to supplied JSON file"""
		if config_filename:
			self.config_filename = config_filename
		json_config = {}
		json_config["full_source"] = self.source.get_long_address()
		json_config["short_source"] = "0x{:x}".format(self.source.get_short_address())
		json_config["full_destination"] = self.destination.get_long_address()
		json_config["short_destination"] = "0x{:x}".format(self.destination.get_short_address())
		json_config["dest_panid"] = "0x{:x}".format(self.dest_panid)
		json_config["frame_counter"] = self.frame_counter
		if self.key:
			json_config["key"] = self.key
		try:
			f = open(self.config_filename, "wb")
		except IOError:
			print("Cannot open configuration file '{}'".format(self.config_filename))
			raise		
		json.dump(json_config, f, indent=4)
		f.close()

	def __repr__(self):
		result = "Link configuration:\n"
		if self.config_filename:
			result += "\tLoaded from '{}'\n".format(self.config_filename)
		result += "\tSource: {}\n".format(self.source)
		result += "\tDestination: {}\n".format(self.destination)
		result += "\tPanid: 0x{:x}\n".format(self.dest_panid)
		if self.key:
			result += "\tKey: {}\n".format(self.key)
		result += "\tFrame Counter: {}".format(self.frame_counter)
		return result
