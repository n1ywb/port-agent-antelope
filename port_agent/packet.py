#!/usr/bin/env python
"""
Port agent packet manipulation.
"""

from struct import Struct

# Howto create packet from scratch
# Given type, timestamp, & data:
# create empty packet
# set sync
# set timestamp
# set msgtype
# set pkt len to len data + header size
# set checksum to zero
# serialize header to buffer
# append data bytes to buffer
# calculate checksum of buffer
# set checksum in header
# serialize header to buffer again
# return buffer

# Howto decode packet

# Step 1:
# Given buffer containing HEADER_SIZE bytes:
# unpack header
# validate sync bytes
# save timestamp
# save msgtype
# save pktsize
# save checksum
# set checksum to zero
# save buffer
# return

# Step 2:
# Given buffer containing pktsize bytes:
# calculate checksum
# compare calculated checksum to received checksum
# make data available


SYNC = (0xA3, 0x9D, 0x7A)
HEADER_FORMAT = "!BBBBHHd"
header_struct = Struct(HEADER_FORMAT)
HEADER_SIZE = header_struct.size


class HeaderSizeError(Exception): pass
class SyncError(Exception): pass
class ChecksumError(Exception): pass


def calculateChecksum(data):
    n = 0
    for datum in data:
        n ^= datum
    return n


def pack_header(buf, msgtype, pktsize, checksum, timestamp):
    sync1, sync2, sync3 = SYNC
    header_struct.pack_into(buf, 0, sync1, sync2, sync3, msgtype, pktsize,
                            checksum, timestamp)


def unpack_header(buf):
    fields = header_struct.unpack_from(buffer(buf))
    (sync1, sync2, sync3, msgtype, pktsize, checksum, timestamp) = fields
    return (sync1, sync2, sync3), msgtype, pktsize, checksum, timestamp


def makepacket(msgtype, timestamp, data):
    """Returns a serialized packet buffer.

    :param msgtype: Message type code
    :type msgtype:  int
    :param timestamp: NTP timestamp
    :type timestamp: long
    :param data: Data buffer
    :type data: bytearray

    :rtype: bytearray
    """
    pktsize = HEADER_SIZE + len(data)
    pkt = bytearray(pktsize)
    pack_header(pkt, msgtype, pktsize, 0, timestamp)
    pkt[HEADER_SIZE:] = data
    checksum = calculateChecksum(pkt)
    pack_header(pkt, msgtype, pktsize, checksum, timestamp)
    return pkt


class ReceivedPacket(object):
    """Represents a received port agent packet.

    :param buf: 16 byte buffer containing header
    :type buf: `bytearray`

    :raises: `HeaderSizeError`
    :raises: `SyncError`

    Before calling `ReceivedPacket`, the caller should receieve the 16 header
    bytes into a new `bytearray` object. The caller should pass this
    `bytearray` as the `buf` param to the new `ReceivedPacket` object. Once
    constructed, the `ReceivedPacket` object 'owns' the `bytearray` object, and
    the caller should not reuse it for any other purpose.

    After the constructor returns, the caller should get the `pktsize` attribute
    from the ReceivedPacket object, and receive that number of additional bytes
    into the same `bytearray` object. The caller is also free to access other
    header attributes at this time.

    The caller should then call `ReceivedPacket.validate()`, which validates the
    packet checksum. The caller may now access the received data using the
    `data` attribute.
    """
    def __init__(self, buf):
        self.buf = buf
        if len(buf) != HEADER_SIZE:
            raise HeaderSizeError(len(buf))
        sync, self.msgtype, self.pktsize, self.checksum, self.timestamp = unpack_header(buf)
        if sync != SYNC:
            raise SyncError(sync)
        # Set checksum to zero so we don't checksum the checksum
        pack_header(buf, self.msgtype, self.pktsize, 0, self.timestamp)

    def validate(self):
        """Compares the received checksum to the calculated checksum.

        :raises: `ChecksumError`
        """
        rxchecksum = calculateChecksum(self.buf)
        if rxchecksum != self.checksum:
            raise ChecksumError(rxchecksum)

    @property
    def data(self):
        """The data portion of the received packet.

        :rtype: `bytearray`
        """
        return self.buf[HEADER_SIZE:]

