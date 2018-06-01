# -*- coding: utf-8 -*-

from rf4ce import Rf4ceNode, Rf4ceFrame, Rf4ceConstants, Rf4ceException
from linkconfig import LinkConfig

from scapy.all import Dot15d4FCS, Dot15d4Data, Raw, makeFCS
# Keep scapy from parsing the RF4CE payload
Dot15d4Data.payload_guess = [({}, Raw)]

import scapy.config
from scapy.themes import ColorOnBlackTheme
scapy.config.conf.color_theme = ColorOnBlackTheme()

