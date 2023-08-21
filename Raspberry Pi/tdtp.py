# TDTP - Teleoperative Data Transfer Protocol

# Author David Rieger - Zulukaiser
import time
import struct
from crc8 import crc8
from identifier_mapping import TDTP_IDENTIFIERS


class TDTP(object):
    """Teleoperated Dirving Transfer Protocol for UDP communication

    This class provides functionality for packet loss and latency recording for UDP.
    The class also provides functionality for packing and unpacking messages. Overall this
    class extends the UDP Protocol with latency measuring and packet loss capturing.

    Attributes:
    -----------
    package_id : int
        increasing counter for every message that gets sent
    package_id_remote : int
        increasing counter for every message that gets received
    package_loss : int
        increasing counter for difference between received package_id and current package_id_remote
    package_loss_remote : int
        value received from remote host via message
    timestamp_host : int
        timestamp in milliseconds
    master : bool
        True if host is master in communication, False if host is slave in communication
    crc_object : object crc8()
        crc8() object to calculate crc8 checksums
    latency : int
        communication delay in milliseconds

    Methods:
    --------
    assemble(identifier, data):
        Gets an identifier for the message and data. Assembles a byte string ready for sending via UDP. Also calculates the checksum for the data and adds a timestamp and unique package_id to the message. Returns the byte string
    
    disassemble(msg):
        Gets a byte string and disassembles it into the corresponding variables for message identifier, data, package_id, checksum and timestamp. Checks if checksum is correct and returns a tuple with identifier, data, package_id and timestamp. Keeps track of package ids and package loss
    """
    def __init__(self, master=False):
        self.package_id = 0
        self.package_id_remote = 0
        self.package_loss = 0
        self.package_loss_remote = 0
        self.timestamp_host = 0
        self.master = master
        self.crc_object = crc8()
        self.latency = 0

    def __getcrc(self, data, crc_format="hex"):
        self.crc_object.update(data)
        if crc_format == "hex":
            return self.crc_object.hexdigest()
        elif crc_format == "bytes":
            return self.crc_object.digest()
        else:
            return False

    def __float_to_hex(self, e: float) -> bytes:
        return bytes(struct.pack("d", e))

    def assemble(self, identifier: int, data: float) -> bytes:
        self.package_id += 1
        if self.master:
            timestamp = round(time.time() * 1000)
        else:
            timestamp = self.timestamp_host
        package_id_bytes = self.package_id.to_bytes(8, "big")
        timestamp_bytes = timestamp.to_bytes(8, "big")
        identifier_bytes = identifier.to_bytes(1, "big")
        if identifier != 16:
            data_bytes = self.__float_to_hex(data)
        else:
            data_bytes = self.__float_to_hex(float(self.package_loss_remote))
        crc = self.__getcrc(data_bytes).encode()

        msg = b"".join([identifier_bytes, data_bytes, crc, package_id_bytes, timestamp_bytes])
        return msg

    def disassemble(self, msg: bytes):
        if len(msg) != 27:
            return False
        identifier = int.from_bytes(msg[:1], "big")
        data = struct.unpack("d", msg[1:9])[0]
        crc = msg[9:11]
        package_id = int.from_bytes(msg[11:19], "big")
        timestamp = int.from_bytes(msg[19:], "big")
        crc_check = self.__getcrc(msg[1:9]).encode()
        self.package_loss_remote += package_id - (self.package_id_remote + 1.0)
        self.package_id_remote = package_id
        if TDTP_IDENTIFIERS[identifier] == "PACKAGE_LOSS":
            self.package_loss = data
        if self.master:
            self.latency = round(time.time() * 1000) - timestamp
        if not self.master:
            self.timestamp_host = timestamp

        if crc == crc_check:
            return identifier, data, package_id, timestamp

        else:
            return False

    def get_package_loss(self) -> float:
        return (self.package_loss_remote + self.package_loss) / (
            self.package_id + self.package_id_remote
        )
