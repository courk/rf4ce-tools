# Introduction

This is a small and simple set of SDR tools that can be used to experiment with the Zigbee RF4CE protocol.

The following features are supported:

They do have the following features:

* RF4CE packets parsing and crafting. This includes support for the AES-128-CCM cryptographic algorithm used by RF4CE devices after the pairing process.
* RF4CE packets sniffing. This includes deciphering packets in case the ciphering key is known. This key can be computed in case the pairing process can be sniffed.
* RF4CE packets injection.

# Requirements 

My code is based on:

* [GNU Radio](https://www.gnuradio.org)GNU Radio
* The IEEE 802.15.4 MAC and PHY layers are provided by the [gr-ieee802-15-4](https://github.com/bastibl/gr-ieee802-15-4/) project

I've successfully tested these tools with both a [HackRF](https://greatscottgadgets.com/hackrf) and a newer [PlutoSDR](http://www.analog.com/en/design-center/evaluation-hardware-and-software/evaluation-boards-kits/adalm-pluto.html).

Please note that a device like the PlutoSDR supports full-duplex communication. That's why after it has send a packet, it can immediately wait for a `ACK` from the receiver and try to switch frequency if this packet is not acknowledged.

The HackRF on the other side is only half-duplex and cannot do that. I haven't find a way to switch between RX and TX modes fast enough to handle `ACK`  packets.

In other word, only the PlutoSDR can handle the frequency agility feature of the RF4CE protocol.

# Usage #

## Packet Sniffer

```
$ ./sniffer.py -h
usage: sniffer.py [-h] [-l LINK] [-c {15,20,25}] [-s {hackrf,pluto-sdr}]

optional arguments:
  -h, --help            show this help message and exit
  -l LINK, --link LINK  JSON file containing link information
  -c {15,20,25}, --channel {15,20,25}
                        RF4CE channel (default: 15)
  -s {hackrf,pluto-sdr}, --sdr {hackrf,pluto-sdr}
                        SDR Device to use (default: pluto-sdr)
```

## Pairing Sniffer

This "pairing sniffer" can be used to generate the optional JSON file containing a link information.

```
$ ./pairing_sniffer.py -h
usage: pairing_sniffer.py [-h] [-c {15,20,25}] [-s {hackrf,pluto-sdr}]
                          output_file

positional arguments:
  output_file           output JSON file storing link information

optional arguments:
  -h, --help            show this help message and exit
  -c {15,20,25}, --channel {15,20,25}
                        RF4CE channel (default: 15)
  -s {hackrf,pluto-sdr}, --sdr {hackrf,pluto-sdr}
                        SDR Device to use (default: pluto-sdr)
```

## Packet Injection

```
$ ./injector.py -h
usage: injector.py [-h] [-c {15,20,25}] [-s {hackrf,pluto-sdr}] config_file

positional arguments:
  config_file           JSON file containing link information

optional arguments:
  -h, --help            show this help message and exit
  -c {15,20,25}, --channel {15,20,25}
                        RF4CE channel (default: 15)
  -s {hackrf,pluto-sdr}, --sdr {hackrf,pluto-sdr}
                        SDR Device to use (default: pluto-sdr)
```