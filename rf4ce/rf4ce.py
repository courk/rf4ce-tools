# -*- coding: utf-8 -*-
"""
Classes aimed at parsing and crafting RF4CE payloads.
"""

from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
from builtins import *

import struct
import binascii

from Crypto.Cipher import AES
from Crypto.Util.strxor import strxor
import huepy as hue

class Rf4ceConstants(object):
	FRAME_TYPE_RESERVED = 0b00
	FRAME_TYPE_DATA = 0b01
	FRAME_TYPE_COMMAND = 0b10
	FRAME_TYPE_VENDOR = 0b11


def address_to_raw(address):
	"""Converts a string representation of a MAC address
	to bytes"""
	return bytes([int(n, 16) for n in address.split(":")][::-1])


def pad128(data):
	"""Pads data so its length is a multiple of 128"""
	return data + b'\x00' * (16 - (len(data) % 16)) 


class Rf4ceException(Exception):
	pass


class Rf4ceNode(object):

	"""Describes a RF4CE node (target or originator)"""

	def __init__(self, long_address, short_address):

		if isinstance(long_address, int):
			mac = "{:016x}".format(long_address)
			mac = ':'.join(mac[i:i+2] for i in range(0, len(mac), 2))
			self.long_address = mac
		else:
			self.long_address = long_address
		self.short_address = short_address
	
	def get_long_address(self):
		return self.long_address

	def get_short_address(self):
		return self.short_address

	def __repr__(self):
		repr = []
		if self.long_address:
			repr.append(self.long_address)
		if self.short_address:
			repr.append(hue.italic("0x{:x}".format(self.short_address)))
		return " - ".join(repr)


class Rf4ceAES(object):

	"""Implements the algorythm used by RF4CE to cipher payload"""

	def __init__(self, key, source, destination):
		self.source = address_to_raw(source.get_long_address())
		self.destination = address_to_raw(destination.get_long_address())
		self.cipher_engine = AES.new(key, AES.MODE_ECB)

		self.M = 4

	def E(self, data):
		return self.cipher_engine.encrypt(data)

	def gen_nonce(self, frame_counter_value):
		frame_counter = struct.pack("I", frame_counter_value)
		security_level = b'\x05'
		return self.source + frame_counter + security_level
		
	def gen_a(self, frame_control_value, frame_counter_value):
		frame_control = struct.pack("B", frame_control_value)
		frame_counter = struct.pack("I", frame_counter_value)
		return frame_control + frame_counter + self.destination

	def gen_auth(self, plain_text, frame_control_value, frame_counter_value):
		a = self.gen_a(frame_control_value, frame_counter_value)
		nonce = self.gen_nonce(frame_counter_value)
		
		auth_data = pad128(struct.pack(">H", len(a)) + a)
		auth_data += pad128(plain_text)

		B = b'\x49' + nonce + struct.pack(">H", len(plain_text))
		X = b'\x00' * 16
		X = self.E(strxor(X, B))
		for i in range(1, len(auth_data) // 16 + 1):
			B = auth_data[(i-1)*16:i*16]
			X = self.E(strxor(X, B))		

		return X[:self.M]

	def cipher(self, plain_text, frame_control_value, frame_counter_value):
		nonce = self.gen_nonce(frame_counter_value)

		T = self.gen_auth(plain_text, frame_control_value, frame_counter_value)

		padded_data = pad128(plain_text)

		flags = b'\x01'
		A = [flags + nonce + struct.pack(">H", counter) for counter in range(len(padded_data)//16 + 1)]

		U = strxor(T, self.E(A[0])[:self.M])

		ciphered_data = b''
		for i in range(1, len(padded_data)//16 + 1):
			data_chunck = padded_data[(i-1)*16:i*16]
			ciphered_data += strxor(self.E(A[i]), data_chunck)

		ciphered_data = ciphered_data[:len(plain_text)]

		return ciphered_data + U

	def decipher(self, data, frame_control_value, frame_counter_value):

		nonce = self.gen_nonce(frame_counter_value)

		padded_C = pad128(data[:len(data)-self.M])
		U = data[len(data)-self.M:]

		flags = b'\x01'
		A = [flags + nonce + struct.pack(">H", counter) for counter in range(len(padded_C)//16 + 1)]

		T = strxor(U, self.E(A[0])[:self.M])

		plain_text = b''
		for i in range(1, len(padded_C)//16 + 1):
			data_chunck = padded_C[(i-1)*16:i*16]
			plain_text += strxor(self.E(A[i]), data_chunck)

		plain_text = plain_text[:len(data)-self.M]

		if self.gen_auth(plain_text, frame_control_value, frame_counter_value) != T:
			raise Rf4ceException("Frame authentification error")

		return plain_text


class Rf4ceFrame(object):

	"""Describes a RF4CE frame"""

	def __init__(self):
		self.source = None
		self.destination = None
		self.frame_type = Rf4ceConstants.FRAME_TYPE_RESERVED
		self.frame_ciphered = False
		self.protocol_version = 1
		self.channel_designator = 0
		self.frame_counter = 0
		self.payload = None
		self.profile_indentifier = 0x1
		self.key = None

	def get_frame_control(self):
		"""Generates the frame control byte from the frame's parameters"""
		frame_control = self.frame_type
		frame_control |= self.frame_ciphered << 2
		frame_control |= self.protocol_version << 3
		frame_control |= 1 << 5
		frame_control |= self.channel_designator << 6

		return frame_control

	def pack(self):
		"""Returns a string representation of the RF4CE frame

		The string representation returned by this function can be
		encapsulated into a 802.15.4 packet.
		"""
		result = struct.pack("B", self.get_frame_control())
		result += struct.pack("I", self.frame_counter)

		if self.frame_type == Rf4ceConstants.FRAME_TYPE_COMMAND:
			data = struct.pack("B", self.command) + self.payload
			if self.frame_ciphered:
				cipher = Rf4ceAES(self.key, self.source, self.destination)
				result += cipher.cipher(data, self.get_frame_control(), self.frame_counter)
			else:
				result += data

		elif self.frame_type == Rf4ceConstants.FRAME_TYPE_DATA:
			result += struct.pack("B", self.profile_indentifier)
			data = self.payload
			if self.frame_ciphered:
				cipher = Rf4ceAES(self.key, self.source, self.destination)
				result += cipher.cipher(data, self.get_frame_control(), self.frame_counter)
			else:
				result += data

		elif self.frame_type == Rf4ceConstants.FRAME_TYPE_VENDOR:
			result += struct.pack("B", self.profile_indentifier)
			result += struct.pack("H", self.vendor_indentifier)
			
			data = self.payload
			if self.frame_ciphered:
				cipher = Rf4ceAES(self.key, self.source, self.destination)
				result += cipher.cipher(data, self.get_frame_control(), self.frame_counter)
			else:
				result += data

		return result

	def parse_from_string(self, data, source, destination, key=None):
		"""Parses a string representation of a RF4CE frame"""
		if key:
			self.key = binascii.unhexlify(key)

		self.source = source
		self.destination = destination

		frame_control = data[0]

		self.frame_type = frame_control & 0b11
		
		if self.frame_type == Rf4ceConstants.FRAME_TYPE_RESERVED:
			raise Rf4ceException("Unknown frame type")

		if (data[0] & (1 << 2)):
			self.frame_ciphered = True
		else:
			self.frame_ciphered = False
		
		self.protocol_version = (frame_control >> 3) & 0b11

		self.channel_designator = (frame_control >> 6) & 0b11

		self.frame_counter = struct.unpack("I", data[1:5])[0]

		if self.frame_type == Rf4ceConstants.FRAME_TYPE_DATA:
			self.data_frame_from_string(data)
		elif self.frame_type == Rf4ceConstants.FRAME_TYPE_COMMAND:
			self.command_frame_from_string(data)
		elif self.frame_type == Rf4ceConstants.FRAME_TYPE_VENDOR:
			self.data_frame_from_string(data, True)

	def data_frame_from_string(self, data, vendor_specific=False):
		"""Parses a RF4CE data pyload from a string"""
		self.profile_indentifier = data[5]
		if vendor_specific:
			self.vendor_indentifier = struct.unpack("H", data[6:8])[0]
			raw_payload = data[8:]
		else:
			raw_payload = data[6:]

		if self.frame_ciphered:
			if not self.key:
				raise Rf4ceException("Missing key")
			cipher = Rf4ceAES(self.key, self.source, self.destination)
			self.payload = cipher.decipher(raw_payload, self.get_frame_control(), self.frame_counter)
		else:
			self.payload = raw_payload

	def command_frame_from_string(self, data):
		"""Parses a RF4CE command pyload from a string"""
		raw_payload = data[5:]
		if self.frame_ciphered:
			if not self.key:
				raise Rf4ceException("Missing key")
			cipher = Rf4ceAES(self.key, self.source, self.destination)
			command_data = cipher.decipher(raw_payload, self.get_frame_control(), self.frame_counter)
		else:
			command_data = raw_payload

		self.command = bytes(command_data)[0]
		self.payload = command_data[1:]

	def __repr__(self):
		if self.frame_type == Rf4ceConstants.FRAME_TYPE_DATA:
			type = hue.lightblue("DATA") + " - "
			type += "profile:" + hue.lightblue("0x{:x}".format(self.profile_indentifier))
		elif self.frame_type == Rf4ceConstants.FRAME_TYPE_COMMAND:
			type = hue.lightblue("COMMAND") + " - "
			type += "cmd:" + hue.lightblue("0x{:x}".format(self.command))
		elif self.frame_type == Rf4ceConstants.FRAME_TYPE_VENDOR:
			type = hue.lightblue("VENDOR") + " - "
			type += "profile:" + hue.lightblue("0x{:x}").format(self.profile_indentifier)
			type += " - vendor:" + hue.lightblue("0x{:x}".format(self.vendor_indentifier))

		data = hue.bold(binascii.hexlify(self.payload).decode())
		counter = hue.lightblue("0x{:x}".format(self.frame_counter))

		result = "({}) -> ({}) : ".format(self.source, self.destination)
		result += "[{} - counter:{}] : {}".format(type, counter, data)

		return result
