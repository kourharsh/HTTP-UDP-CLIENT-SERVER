
class packet:

    def __init__(self, packet_type, seq_num, peer_ip, peer_port, payload):
        self.packet_type = int(packet_type).to_bytes(1,byteorder='big')
        self.seq_num = int(seq_num).to_bytes(4,byteorder='big')
        self.peer_ip = peer_ip.packed
        self.peer_port = int(peer_port).to_bytes(2,byteorder='big')
        self.payload = payload.encode("utf-8")


    def encode_packet(self):
        buffer = bytearray()
        buffer.extend(self.packet_type, self.seq_num, self.peer_ip, self.peer_port, self.payload)
        return buffer

