import ipaddress
import time
from datetime import datetime

MIN_LEN = 22
MAX_LEN = 1024


class Packet:
    """
    Packet represents a simulated UDP packet.
    """

    def __init__(self, packet_type, seq_num, peer_ip_addr, peer_port, is_last, timestamp, payload):
        self.packet_type = int(packet_type)
        self.seq_num = int(seq_num)
        self.peer_ip_addr = peer_ip_addr
        self.peer_port = int(peer_port)
        self.payload = payload
        self.is_last = is_last
        self.timestamp = timestamp

    def to_bytes(self):
        """
        to_raw returns a bytearray representation of the packet in big-endian order.
        """
        buf = bytearray()
        buf.extend(self.packet_type.to_bytes(1, byteorder='big'))
        buf.extend(self.seq_num.to_bytes(4, byteorder='big'))
        buf.extend(self.peer_ip_addr.packed)
        buf.extend(self.peer_port.to_bytes(2, byteorder='big'))
        if self.is_last == True:
            val = 1
        else:
            val = 0
        buf.extend(val.to_bytes(1, byteorder='big'))
        buf.extend(self.timestamp.to_bytes(10, byteorder='big'))
        buf.extend(self.payload)


        return buf

    def __repr__(self, *args, **kwargs):
        return "#%d, peer=%s:%s, size=%d" % (self.seq_num, self.peer_ip_addr, self.peer_port, len(self.payload))

    @staticmethod
    def from_bytes(raw):
        """from_bytes creates a packet from the given raw buffer.

            Args:
                raw: a bytearray that is the raw-representation of the packet in big-endian order.

            Returns:
                a packet from the given raw bytes.

            Raises:
                ValueError: if packet is too short or too long or invalid peer address.
        """
        if len(raw) < MIN_LEN:
            raise ValueError("packet is too short: {} bytes".format(len(raw)))
        if len(raw) > MAX_LEN:
            print(len(raw))
            raise ValueError("packet is exceeded max length: {} bytes".format(len(raw)))

        curr = [0, 0]

        def nbytes(n):
            curr[0], curr[1] = curr[1], curr[1] + n
            return raw[curr[0]: curr[1]]

        packet_type = int.from_bytes(nbytes(1), byteorder='big')
        seq_num = int.from_bytes(nbytes(4), byteorder='big')
        peer_addr = ipaddress.ip_address(nbytes(4))
        peer_port = int.from_bytes(nbytes(2), byteorder='big')
        last = int.from_bytes(nbytes(1), byteorder='big')
        is_last = (last == 1)
        timestamp1 = int.from_bytes(nbytes(10), byteorder='big')
        #print(timestamp1)
        payload = raw[curr[1]:]

        return Packet(packet_type=packet_type,
                      seq_num=seq_num,
                      peer_ip_addr=peer_addr,
                      peer_port=peer_port,
                      is_last= is_last,
                      timestamp=timestamp1,
                      payload=payload)
