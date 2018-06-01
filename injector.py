#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Injects arbitrary RF4CE packets. Support encryption.
"""

from __future__ import (absolute_import,
                        print_function, unicode_literals)
from builtins import *

import argparse
import time
from datetime import datetime
import binascii
import readline

from rf4ce import Dot15d4FCS, Dot15d4Data, Raw, makeFCS
from rf4ce import LinkConfig, Rf4ceFrame, Rf4ceConstants
from rf4ce.radio import TxFlow
from rf4ce.packetprocessor import PacketProcessor
import huepy as hue


class AckProcessor(PacketProcessor):

	"""ACK processor thread

	Thread processing incomming ACK
	Full-duplex SDR is needed for this to work
	"""

	def __init__(self):
		PacketProcessor.__init__(self)
		self.last_ack = -1

	def process(self, data):
		"""Parses a 802.15.4 ACK and extract the seqnum"""

		# Check if the 802.15.4 packet is valid
		if makeFCS(data[:-2]) != data[-2:]:
			print(hue.bad("Received invalid packet"))
			return

		packet = Dot15d4FCS(data)

		if packet.fcf_frametype == 2: # ACK
			self.last_ack = packet.seqnum

	def get_last_ack(self):
		"""Returns the seqnum of the last received ACK"""
		return self.last_ack


class InjectorCmd(object):

	"""Injector command object

	Contains the command & arguments of all possible
	injector commands
	"""

	PACKET = 1
	PROFILE = 2
	COUNTER = 3
	DELAY = 4
	CIPHERED = 5
	HELP = 6

	def to_int(self, n):
		if type(n) == int:
			return n
		if n.startswith("0x"):
			return int(n, 16)
		else:
			return int(n)

	def to_bool(self, r):
		if type(r) == bool:
			return r
		n = self.to_int(r)
		if not n in (0, 1):
			raise ValueError()
		return n == 1

	def __init__(self, cmd, arg):
		self.action = cmd

		if self.action == self.PROFILE:
			self.arg = self.to_int(arg)
		elif self.action == self.COUNTER:
			self.arg = self.to_int(arg)
		elif self.action == self.DELAY:
			self.arg = float(arg)
		elif self.action == self.CIPHERED:
			self.arg = self.to_bool(arg)
		else:
			self.arg = arg


class Injector(object):

	"""Injector util main class"""

	def __init__(self, link_config, channel, sdr_device):
		self.link_config = link_config
		self.sdr_device = sdr_device

		# Build a RF4CE data frame based on the link configuration
		self.rf4ce_frame = Rf4ceFrame()
		self.rf4ce_frame.source = self.link_config.source
		self.rf4ce_frame.destination = self.link_config.destination
		self.rf4ce_frame.frame_type = Rf4ceConstants.FRAME_TYPE_DATA
		if self.link_config.key:
			self.rf4ce_frame.frame_ciphered = True
			self.rf4ce_frame.key = binascii.unhexlify(self.link_config.key)
		else:
			self.rf4ce_frame.frame_ciphered = False
		self.rf4ce_frame.frame_counter = self.link_config.frame_counter

		self.seqnum = 0
		
		# inter-packet delay
		self.packet_delay = 0.1

		# Pluto-sdr support full duplex
		# ACK can be received
		if self.sdr_device == "pluto-sdr":
			self.ack_processor = AckProcessor()
		else:
			self.ack_processor = None

		self.tb = TxFlow(channel, self.ack_processor, self.sdr_device)

	def run(self):
		self.log("SRC:({}) -> DST:({})".format(self.link_config.source,
			self.link_config.destination), hue.info)
		if not self.link_config.key:
			self.log("No secured configuration provided. Will only send plaintext packets.", hue.info)
		self.log("Loading last frame counter: {}".format(self.link_config.frame_counter), hue.info)
		self.help()

		self.tb.start()
		if self.ack_processor:
			self.ack_processor.start()

		# Main loop, iterate through user-supplied commands
		for cmd in self.prompt():
			if cmd.action == InjectorCmd.PACKET:
				self.seqnum = (self.seqnum + 1) % 255
				self.rf4ce_frame.frame_counter += 1
				self.rf4ce_frame.payload = cmd.arg
				data = self.gen_ieee_packet(self.rf4ce_frame.pack())

				self.log("Transmitting {}".format(binascii.hexlify(data)), hue.info)

				if self.sdr_device == "pluto-sdr":
					self.ack_transmit(data)
				else:
					self.tb.transmit(data)
				
				time.sleep(self.packet_delay)

			elif cmd.action == InjectorCmd.PROFILE:
				self.log("Set profile to 0x{:02x}".format(cmd.arg), hue.info)
				self.rf4ce_frame.profile_indentifier = cmd.arg

			elif cmd.action == InjectorCmd.COUNTER:
				self.log("Set counter to {}".format(cmd.arg), hue.info)
				self.rf4ce_frame.frame_counter = cmd.arg

			elif cmd.action == InjectorCmd.DELAY:
				self.log("Set delay to {}".format(cmd.arg), hue.info)
				self.packet_delay = cmd.arg

			elif cmd.action == InjectorCmd.CIPHERED:
				self.log("Set ciphered to {}".format(cmd.arg), hue.info)
				if cmd.arg:
					if not link_config.key:
						self.log("No key provided. Cannot send ciphered packets.", hue.bad)
					else:
						self.rf4ce_frame.frame_ciphered = True
				else:
					self.rf4ce_frame.frame_ciphered = False

			elif cmd.action == InjectorCmd.HELP:
				self.help()

		self.link_config.frame_counter = self.rf4ce_frame.frame_counter
		self.log("Saving last frame counter: {}".format(self.link_config.frame_counter), hue.info)
		self.link_config.save()

		if self.sdr_device == "pluto-sdr":
			self.ack_processor.stop()

		self.tb.stop()
		self.tb.wait()

	def help(self):
		help_text = """
	Available commands:

	    counter <value>      Set the frame counter value

	    delay <value>        Minimum delay between packet (seconds)

	    ciphered [0, 1]      Send AES ciphered payloads of cleartext payloads. 
	                         Only possible if a key has been configured

	    profile <profile>    Select a profile number

	    exit

	Other inputs will be considered as data to be sent.
		"""
		print(help_text)


	def prompt(self):
		"""Generates the injector util prompt"""
		while True:
			try:
				if self.rf4ce_frame.frame_ciphered:
					ciphered_status = "ciphered"
				else:
					ciphered_status = "plain"
				a = hue.lightblue("{}".format(self.rf4ce_frame.frame_counter))
				b = hue.lightblue("0x{:02x}".format(self.rf4ce_frame.profile_indentifier))
				c = hue.lightblue(ciphered_status)
				cmd = raw_input("({} - {} - {})>>> ".format(a, b, c))
			except KeyboardInterrupt:
				raise StopIteration

			if cmd.startswith("profile"):
				try:
					yield InjectorCmd(InjectorCmd.PROFILE, cmd.split()[1])
				except:
					self.log("Malformed command", hue.bad)
					continue

			elif cmd.startswith("counter"):
				try:
					yield InjectorCmd(InjectorCmd.COUNTER, cmd.split()[1])
				except:
					self.log("Malformed command", hue.bad)
					continue

			elif cmd.startswith("delay"):
				try:
					yield InjectorCmd(InjectorCmd.DELAY, cmd.split()[1])
				except:
					self.log("Malformed command", hue.bad)
					continue

			elif cmd.startswith("ciphered"):
				try:
					yield InjectorCmd(InjectorCmd.CIPHERED, cmd.split()[1])
				except:
					self.log("Malformed command", hue.bad)
					continue

			elif cmd.startswith("help"):
				yield InjectorCmd(InjectorCmd.HELP, None)

			elif cmd.startswith("exit"):
				raise StopIteration

			else:
				for packet in cmd.split():
					try:
						data = binascii.unhexlify(packet)
					except:
						self.log("Malformed command", hue.bad)
						continue
					yield InjectorCmd(InjectorCmd.PACKET, data)

	def gen_ieee_packet(self, data):
		"""Encapsulates data into a 802.15.4 packet"""
		packet = Dot15d4FCS() / Dot15d4Data() / Raw(load=data)

		packet.fcf_srcaddrmode = 2
		packet.fcf_destaddrmode = 2

		packet.fcf_panidcompress = True
		packet.fcf_ackreq = True
		packet.seqnum = self.seqnum

		packet.dest_panid = self.link_config.dest_panid

		packet.dest_addr = self.link_config.destination.get_short_address()
		packet.src_addr = self.link_config.source.get_short_address()

		return packet.build()

	def ack_transmit(self, data, max_freq_retry=5, max_tx_retry=10):
		"""Transmit data with ACK check

		Tries to transmit a packet until a ACK is received
		Full-duplex SDR is needed for this to work
		"""
		transmit_success = False
		for freq_retry in range(max_freq_retry):
			for tx_retry in range(max_tx_retry):
				self.tb.transmit(data)
				time.sleep(0.15)
				if self.ack_processor.get_last_ack() != self.seqnum:
					self.log("Warning: no ACK received, retrying", hue.bad)
				else:
					self.log("ACK received", hue.good)
					transmit_success = True
					return True
			self.log("Warning: switching frequency", hue.bad)
			self.tb.frequency_switch()
		return False

	def log(self, data, format=None):
		if format:
			print(format("[{}] {}".format(datetime.now(), data)))
		else:
			print("[{}] {}".format(datetime.now(), data))


if __name__ == '__main__':

	parser = argparse.ArgumentParser()
	parser.add_argument("config_file", help="JSON file containing link information")
	parser.add_argument("-c", "--channel", help="RF4CE channel (default: 15)", type=int,
		choices=[15, 20, 25], default=15)
	parser.add_argument("-s", "--sdr", help="SDR Device to use (default: pluto-sdr)", 
		choices=["hackrf", "pluto-sdr"], default="pluto-sdr")
	args = parser.parse_args()

	try:
		link_config = LinkConfig(args.config_file)
	except:
		print(hue.bad("Cannot load configuration file"))
		exit(-1)

	print(link_config)

	injector = Injector(link_config, args.channel, args.sdr)
	injector.run()
