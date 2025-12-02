# -*- coding: utf-8 -*-

from rf4ce import Rf4ceNode, Rf4ceFrame, Rf4ceConstants, Rf4ceException
from linkconfig import LinkConfig

from scapy.all import Dot15d4FCS, Dot15d4Data, Raw

# Keep scapy from parsing the RF4CE payload
Dot15d4Data.payload_guess = [({}, Raw)]

import scapy.config
from scapy.themes import ColorOnBlackTheme
scapy.config.conf.color_theme = ColorOnBlackTheme()


# https://github.com/zeroSteiner/scapy-com/blob/79f55855a4d55b4eaba5370cb4c7b094ab956c79/scapy/layers/dot15d4.py#L856C1-L865C1
def makeFCS(data):
    crc = 0
    for i in range(0, len(data)):
        c = ord(data[i])
        q = (crc ^ c) & 15              #Do low-order 4 bits
        crc = (crc // 16) ^ (q * 4225)
        q = (crc ^ (c // 16)) & 15      #And high 4 bits
        crc = (crc // 16) ^ (q * 4225)
    return struct.pack('<H', crc) #return as bytes in little endian order
