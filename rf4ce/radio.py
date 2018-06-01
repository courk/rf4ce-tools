# -*- coding: utf-8 -*-
"""
Low level gnuradio graphs for 802.15.4.
"""

from math import pi, sin
import numpy

from gnuradio import blocks
from gnuradio import digital
from gnuradio import eng_notation
from gnuradio import gr
from gnuradio import iio
from gnuradio.eng_option import eng_option
from gnuradio.filter import firdes
import es
import foo
import ieee802_15_4
import osmosdr
import pmt

from autognuradio.ieee802_15_4_oqpsk_phy import ieee802_15_4_oqpsk_phy


class TxFlow(gr.top_block):

	def __init__(self, channel, processor, sdr_device="pluto-sdr"):
		gr.top_block.__init__(self, "Tx Flow")

		##################################################
		# Variables
		##################################################
		self.channel = channel
		self.sdr_device = sdr_device
		self.processor = processor

		##################################################
		# Blocks
		##################################################
		if self.sdr_device == "hackrf":
			self.sdr_sink = osmosdr.sink(args="numchan=1")
			self.sdr_sink.set_sample_rate(4e6)
			self.sdr_sink.set_center_freq(self.get_center_freq(), 0)
			self.sdr_sink.set_freq_corr(0, 0)
			self.sdr_sink.set_gain(10, 0)
			self.sdr_sink.set_if_gain(20, 0)
			self.sdr_sink.set_bb_gain(20, 0)
			self.sdr_sink.set_antenna('', 0)
			self.sdr_sink.set_bandwidth(0, 0)
		elif self.sdr_device == "pluto-sdr":
			self.sdr_sink = iio.pluto_sink('192.168.2.1', self.get_center_freq(),
				int(4e6), int(4e6), 0x8000, False, 0, '', True)
			self.sdr_source = iio.pluto_source('192.168.2.1', self.get_center_freq(),
				int(4e6), int(4e6), 0x8000, True, True, True, "manual", 50, '', True)

		self.ieee802_15_4_access_code_prefixer_0 = ieee802_15_4.access_code_prefixer()
		self.es_source_0 = es.source(1*[gr.sizeof_gr_complex], 1, 2, 0)
		self.digital_chunks_to_symbols_xx_0 = digital.chunks_to_symbols_bc(([(1+1j), (-1+1j), (1-1j), (-1+1j), (1+1j), (-1-1j), (-1-1j), (1+1j), (-1+1j), (-1+1j), (-1-1j), (1-1j), (-1-1j), (1-1j), (1+1j), (1-1j), (1-1j), (-1-1j), (1+1j), (-1-1j), (1-1j), (-1+1j), (-1+1j), (1-1j), (-1-1j), (-1-1j), (-1+1j), (1+1j), (-1+1j), (1+1j), (1-1j), (1+1j), (-1+1j), (-1+1j), (-1-1j), (1-1j), (-1-1j), (1-1j), (1+1j), (1-1j), (1+1j), (-1+1j), (1-1j), (-1+1j), (1+1j), (-1-1j), (-1-1j), (1+1j), (-1-1j), (-1-1j), (-1+1j), (1+1j), (-1+1j), (1+1j), (1-1j), (1+1j), (1-1j), (-1-1j), (1+1j), (-1-1j), (1-1j), (-1+1j), (-1+1j), (1-1j), (-1-1j), (1-1j), (1+1j), (1-1j), (1+1j), (-1+1j), (1-1j), (-1+1j), (1+1j), (-1-1j), (-1-1j), (1+1j), (-1+1j), (-1+1j), (-1-1j), (1-1j), (-1+1j), (1+1j), (1-1j), (1+1j), (1-1j), (-1-1j), (1+1j), (-1-1j), (1-1j), (-1+1j), (-1+1j), (1-1j), (-1-1j), (-1-1j), (-1+1j), (1+1j), (1+1j), (-1-1j), (-1-1j), (1+1j), (-1+1j), (-1+1j), (-1-1j), (1-1j), (-1-1j), (1-1j), (1+1j), (1-1j), (1+1j), (-1+1j), (1-1j), (-1+1j), (1-1j), (-1+1j), (-1+1j), (1-1j), (-1-1j), (-1-1j), (-1+1j), (1+1j), (-1+1j), (1+1j), (1-1j), (1+1j), (1-1j), (-1-1j), (1+1j), (-1-1j), (1+1j), (1-1j), (1+1j), (-1+1j), (1-1j), (-1+1j), (1+1j), (-1-1j), (-1-1j), (1+1j), (-1+1j), (-1+1j), (-1-1j), (1-1j), (-1-1j), (1-1j), (1-1j), (1+1j), (1-1j), (-1-1j), (1+1j), (-1-1j), (1-1j), (-1+1j), (-1+1j), (1-1j), (-1-1j), (-1-1j), (-1+1j), (1+1j), (-1+1j), (1+1j), (-1-1j), (1+1j), (-1+1j), (-1+1j), (-1-1j), (1-1j), (-1-1j), (1-1j), (1+1j), (1-1j), (1+1j), (-1+1j), (1-1j), (-1+1j), (1+1j), (-1-1j), (-1+1j), (1-1j), (-1-1j), (-1-1j), (-1+1j), (1+1j), (-1+1j), (1+1j), (1-1j), (1+1j), (1-1j), (-1-1j), (1+1j), (-1-1j), (1-1j), (-1+1j), (-1-1j), (1-1j), (-1-1j), (1-1j), (1+1j), (1-1j), (1+1j), (-1+1j), (1-1j), (-1+1j), (1+1j), (-1-1j), (-1-1j), (1+1j), (-1+1j), (-1+1j), (-1+1j), (1+1j), (-1+1j), (1+1j), (1-1j), (1+1j), (1-1j), (-1-1j), (1+1j), (-1-1j), (1-1j), (-1+1j), (-1+1j), (1-1j), (-1-1j), (-1-1j), (1-1j), (-1+1j), (1+1j), (-1-1j), (-1-1j), (1+1j), (-1+1j), (-1+1j), (-1-1j), (1-1j), (-1-1j), (1-1j), (1+1j), (1-1j), (1+1j), (-1+1j), (1+1j), (-1-1j), (1-1j), (-1+1j), (-1+1j), (1-1j), (-1-1j), (-1-1j), (-1+1j), (1+1j), (-1+1j), (1+1j), (1-1j), (1+1j), (1-1j), (-1-1j)]), 16)
		self.blocks_vector_source_x_0 = blocks.vector_source_c([0, sin(pi/4), 1, sin(3*pi/4)], True, 1, [])
		self.blocks_tagged_stream_to_pdu_0 = blocks.tagged_stream_to_pdu(blocks.complex_t, 'pdu_length')
		self.blocks_tagged_stream_multiply_length_0 = blocks.tagged_stream_multiply_length(gr.sizeof_gr_complex*1, 'pdu_length', 128)
		self.blocks_tagged_stream_multiply_length_0.set_min_output_buffer(20000)
		self.blocks_repeat_0 = blocks.repeat(gr.sizeof_gr_complex*1, 4)
		self.blocks_pdu_to_tagged_stream_0_0_0 = blocks.pdu_to_tagged_stream(blocks.byte_t, 'pdu_length')
		self.blocks_packed_to_unpacked_xx_0 = blocks.packed_to_unpacked_bb(4, gr.GR_LSB_FIRST)
		self.blocks_multiply_xx_0 = blocks.multiply_vcc(1)
		self.blocks_float_to_complex_0 = blocks.float_to_complex(1)
		self.blocks_delay_0 = blocks.delay(gr.sizeof_float*1, 2)
		self.blocks_complex_to_float_0 = blocks.complex_to_float(1)

		self.msg_in_0 = msg_block_source()

		if self.sdr_device == "pluto-sdr":
			self.ieee802_15_4_oqpsk_phy_0 = ieee802_15_4_oqpsk_phy()
			self.blocks_null_sink_0 = blocks.null_sink(gr.sizeof_gr_complex*1)

			self.msg_out_0 = msg_sink_block(self.processor)

		##################################################
		# Connections
		##################################################
		self.msg_connect((self.blocks_tagged_stream_to_pdu_0, 'pdus'), (self.es_source_0, 'schedule_event'))
		self.msg_connect((self.ieee802_15_4_access_code_prefixer_0, 'out'), (self.blocks_pdu_to_tagged_stream_0_0_0, 'pdus'))
		self.msg_connect((self.msg_in_0, 'msg_out'), (self.ieee802_15_4_access_code_prefixer_0, 'in'))
		self.connect((self.blocks_complex_to_float_0, 1), (self.blocks_delay_0, 0))
		self.connect((self.blocks_complex_to_float_0, 0), (self.blocks_float_to_complex_0, 0))
		self.connect((self.blocks_delay_0, 0), (self.blocks_float_to_complex_0, 1))
		self.connect((self.blocks_float_to_complex_0, 0), (self.sdr_sink, 0))
		self.connect((self.blocks_multiply_xx_0, 0), (self.blocks_tagged_stream_multiply_length_0, 0))
		self.connect((self.blocks_packed_to_unpacked_xx_0, 0), (self.digital_chunks_to_symbols_xx_0, 0))
		self.connect((self.blocks_pdu_to_tagged_stream_0_0_0, 0), (self.blocks_packed_to_unpacked_xx_0, 0))
		self.connect((self.blocks_repeat_0, 0), (self.blocks_multiply_xx_0, 1))
		self.connect((self.blocks_tagged_stream_multiply_length_0, 0), (self.blocks_tagged_stream_to_pdu_0, 0))
		self.connect((self.blocks_vector_source_x_0, 0), (self.blocks_multiply_xx_0, 0))
		self.connect((self.digital_chunks_to_symbols_xx_0, 0), (self.blocks_repeat_0, 0))
		self.connect((self.es_source_0, 0), (self.blocks_complex_to_float_0, 0))

		if self.sdr_device == "pluto-sdr":
			self.msg_connect((self.ieee802_15_4_oqpsk_phy_0, 'rxout'), (self.msg_out_0, 'msg_in'))
			self.connect((self.ieee802_15_4_oqpsk_phy_0, 0), (self.blocks_null_sink_0, 0))
			self.connect((self.sdr_source, 0), (self.ieee802_15_4_oqpsk_phy_0, 0))


	def get_channel(self):
		return self.channel

	def set_channel(self, channel):
		self.channel = channel
		if self.sdr_device == "hackrf":
			self.sdr_source.set_center_freq(self.get_center_freq())
		elif self.sdr_device == "pluto-sdr":
			self.sdr_source.set_params(self.get_center_freq(),
					int(4e6), int(20e6), True, True, True, "manual", 50, '', True)
			self.sdr_sink.set_params(self.get_center_freq(), int(4e6), int(20e6), 0, '', True)

	def frequency_switch(self):
		channels = [15, 20, 25]
		i = channels.index(self.get_channel())
		self.set_channel(channels[(i+1)%3])

	def get_center_freq(self):
		return 1000000 * (2400 + 5 * (self.channel - 10))


	def transmit(self, data):
		self.msg_in_0.transmit(data)


class RxFlow(gr.top_block):

	def __init__(self, channel, processor, device="pluto-sdr"):
		gr.top_block.__init__(self, "Sniffer Flow")

		self.processor = processor

		##################################################
		# Variables
		##################################################
		self.channel = channel
		self.device = device

		##################################################
		# Blocks
		##################################################
		if self.device == "hackrf":
			self.sdr_source = osmosdr.source(args="numchan=1")
			self.sdr_source.set_sample_rate(4e6)
			self.sdr_source.set_center_freq(self.get_center_freq(), 0)
			self.sdr_source.set_freq_corr(0, 0)
			self.sdr_source.set_dc_offset_mode(0, 0)
			self.sdr_source.set_iq_balance_mode(0, 0)
			self.sdr_source.set_gain_mode(False, 0)
			self.sdr_source.set_gain(14, 0)
			self.sdr_source.set_if_gain(16, 0)
			self.sdr_source.set_bb_gain(16, 0)
			self.sdr_source.set_antenna('', 0)
			self.sdr_source.set_bandwidth(0, 0)
		elif self.device == "pluto-sdr":
			self.sdr_source = iio.pluto_source('192.168.2.1', self.get_center_freq(),
				int(4e6), int(20e6), 0x8000, True, True, True, "manual", 50, '', True)


		self.ieee802_15_4_oqpsk_phy_0 = ieee802_15_4_oqpsk_phy()
		self.blocks_null_sink_0 = blocks.null_sink(gr.sizeof_gr_complex*1)

		self.msg_out_0 = msg_sink_block(self.processor)

		##################################################
		# Connections
		##################################################
		self.msg_connect((self.ieee802_15_4_oqpsk_phy_0, 'rxout'), (self.msg_out_0, 'msg_in'))
		self.connect((self.ieee802_15_4_oqpsk_phy_0, 0), (self.blocks_null_sink_0, 0))
		self.connect((self.sdr_source, 0), (self.ieee802_15_4_oqpsk_phy_0, 0))

	def get_channel(self):
		return self.channel

	def set_channel(self, channel):
		self.channel = channel
		if self.device == "hackrf":
			self.sdr_source.set_center_freq(self.get_center_freq())
		elif self.device == "pluto-sdr":
			self.sdr_source.set_params('192.168.2.1', self.get_center_freq(),
				int(4e6), int(20e6), 0x8000, True, True, True, "manual", 50, '', True)

	def get_center_freq(self):
		return 1000000 * (2400 + 5 * (self.channel - 10))



class msg_sink_block(gr.basic_block):

	def __init__(self, processor):

		gr.basic_block.__init__(
			 self,
			 name="msg_block",
			 in_sig=None,
			 out_sig=None)

		self.processor = processor
		self.message_port_register_in(pmt.intern('msg_in'))
		self.set_msg_handler(pmt.intern('msg_in'), self.handle_msg)

	def handle_msg(self, msg):
		messages = pmt.to_python(msg)
		for message in messages:
			if type(message) == numpy.ndarray:
				self.processor.feed(message.tostring())


class msg_block_source(gr.basic_block):

	def __init__(self):

		gr.basic_block.__init__(
			 self,
			 name="msg_block",
			 in_sig=None,
			 out_sig=None)

		self.message_port_register_out(pmt.intern('msg_out'))
	
	def transmit(self, data):
		vector = pmt.make_u8vector(len(data), 0)
		for i, c in enumerate(data):
			pmt.u8vector_set(vector, i, ord(data[i]))
		pdu = pmt.cons(pmt.make_dict(), vector)
		self.message_port_pub(pmt.intern('msg_out'), pdu)
