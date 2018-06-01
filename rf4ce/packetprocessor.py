# -*- coding: utf-8 -*-
"""
Packet processor tread. Used to process the incoming RF4CE packets.
"""

import threading
import Queue

from linkconfig import LinkConfig
from rf4ce import Rf4ceNode, Rf4ceFrame


class PacketProcessor(threading.Thread):

	"""Packet processor thread"""

	def __init__(self):
		threading.Thread.__init__(self)
		self.q = Queue.Queue()
		self.stopped = False

	def stop(self):
		self.stopped = True

	def run(self):
		while not self.stopped:
			try:
				data = self.q.get(timeout=1)
			except Queue.Empty:
				continue
			self.process(data)
	
	def feed(self, data):
		"""Adds packets to the queue"""
		self.q.put(data)

	def process(self, data):
		"""This should process the incoming data"""
		pass
