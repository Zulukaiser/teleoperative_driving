# TDTP - Teleoperative Data Transfer Protocol

# Author David Rieger - Zulukaiser
import time
import struct
from crc8 import crc8


class tdtp(object):
    def __init__(self):
        self.package_id = 0
        self.package_loss = 0

    def getcrc(self, data, crc_format="hex"):
        crc_object = crc8()
        crc_object.update(data)
        if crc_format == "hex":
            return crc_object.hexdigest()
        elif crc_format == "bytes":
            return crc_object.digest()
        else:
            return False

    def float_to_hex(self, e: float):
        return hex(struct.unpack("<I", struct.pack("<e", e))[0])

    def assemble(self, identifier: int, data) -> bytes:
        self.package_id += 1
        crc = self.getcrc(data)
        timestamp = time.time_ns()
        package_id_bytes = self.package_id.to_bytes(2, "big")
        crc_bytes = crc.to_bytes(1, "big")
        timestamp_bytes = timestamp.to_bytes(4, "big")
        identifier_bytes = identifier.to_bytes(1, "big")
        if type(data) == float:
            data_bytes = self.float_to_hex(data)
        elif type(data) == int:
            data_bytes = data.to_bytes(4, "big")
        msg = b"".join(
            [identifier_bytes, data_bytes, crc_bytes, package_id_bytes, timestamp_bytes]
        )
        return msg

    def disassemble(self, msg: bytes):
        identifier = int.from_bytes(msg[:1], "big")
        data = int.from_bytes(msg[1:5], "big")
        crc = hex(int.from_bytes(msg[5:6], "big"))
        package_id = int.from_bytes(msg[6:8], "big")
        timestamp = int.from_bytes(msg[8:], "big")

        if crc == self.getcrc(data):
            return identifier, data, package_id, timestamp

        else:
            return False
