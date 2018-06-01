#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Sniffs RF4CE packets. Supports encryption.
"""

from __future__ import (absolute_import,
                        print_function, unicode_literals)
from builtins import *

import argparse
from datetime import datetime
import binascii

from rf4ce import Dot15d4FCS, Dot15d4Data, Raw, makeFCS
from rf4ce import LinkConfig, Rf4ceNode, Rf4ceFrame, Rf4ceException
from rf4ce.radio import RxFlow
from rf4ce.packetprocessor import PacketProcessor
import huepy as hue


class SnifferProcessor(PacketProcessor):

	"""Sniffer Packet processor

	Parses incoming packets
	If possible, decode them
	"""

	def __init__(self, link_configs=[]):
		PacketProcessor.__init__(self)
		self.link_configs = link_configs

	def process(self, data):
		print(hue.bold(hue.green("\n------ {} ------".format(datetime.now()))))
		print(hue.yellow("Full packet data: ") + hue.italic(binascii.hexlify(data)))
		
		# Checks if the 802.15.4 packet is valid
		if makeFCS(data[:-2]) != data[-2:]:
			print(hue.bad("Invalid packet"))
			return

		# Parses 802.15.4 packet
		packet = Dot15d4FCS(data)
		packet.show()

		if packet.fcf_frametype == 2: # ACK
			return

		# Tries to match received packet with a known link
		# configuration
		matched = False
		for link in self.link_configs:
			if packet.dest_panid != link.dest_panid:
				continue
			if packet.fcf_srcaddrmode == 3: # Long addressing mode
				if packet.src_addr != link.source.get_long_address():
					continue
				if packet.dest_addr != link.destination.get_long_address():
					continue
			else:
				if packet.src_addr != link.source.get_short_address():
					continue
				if packet.dest_addr != link.destination.get_short_address():
					continue
				source = link.source
				destination = link.destination
				key = link.key
				matched = True

		if not matched:
			if packet.fcf_srcaddrmode == 3:
				source = Rf4ceNode(packet.src_addr, None)
				destination = Rf4ceNode(packet.dest_addr, None)
			else:
				source = Rf4ceNode(None, packet.src_addr)
				destination = Rf4ceNode(None, packet.dest_addr)
			key = None

		# Process RF4CE payload
		frame = Rf4ceFrame()
		try:
			rf4ce_payload = bytes(packet[3].fields["load"])
			frame.parse_from_string(rf4ce_payload, source, destination, key)
		except Rf4ceException, e:
			print(hue.bad("Cannot parse RF4CE frame: {}".format(e)))
			return
		print("###[ " + hue.bold(hue.yellow("RF4CE")) + " ]###")
		print(frame)


if __name__ == '__main__':

	parser = argparse.ArgumentParser()
	parser.add_argument("-l", "--link", help="JSON file containing link information")
	parser.add_argument("-c", "--channel", help="RF4CE channel (default: 15)", type=int,
		choices=[15, 20, 25], default=15)
	parser.add_argument("-s", "--sdr", help="SDR Device to use (default: pluto-sdr)", 
		choices=["hackrf", "pluto-sdr"], default="pluto-sdr")
	args = parser.parse_args()

	if args.link:
		try:
			link_config = LinkConfig(args.link)
		except:
			print(hue.bad("Cannot load configuration file"))
			exit(-1)

	if args.link:
		print(link_config)
	print(hue.info("Sniffing on channel {}".format(args.channel)))

	if args.link:
		sniffer_processor = SnifferProcessor([link_config])
	else:
		sniffer_processor = SnifferProcessor([])
	tb = RxFlow(args.channel, sniffer_processor, args.sdr)
	
	sniffer_processor.start()
	tb.start()

	try:
		raw_input(hue.info('Sniffing...\n'))
	except (EOFError, KeyboardInterrupt):
		pass
	
	print(hue.info("Exiting..."))

	tb.stop()
	tb.wait()
	sniffer_processor.stop()
