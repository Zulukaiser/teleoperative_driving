import socket
import threading
import ctypes
from queue import Queue
import struct
import gamepadReading

class _CONTROLLER_DB_STRUCT(ctypes.Structure):
    _fields_ = [("channel", ctypes.c_float * 20)]

HOST = '192.168.178.31'
PORT = 50007
BUFFER_SIZE = 80
ADDR = (HOST, PORT)

def get_controller_data(controller: gamepadReading.XboxController):
    return controller.read()

def udp_receive():
    while True:
        pass

def udp_send():
    while True:
        controller_data = get_controller_data(controller=controller)
        client.sendto(encode_bytes_from_dict(controller_data), ADDR)

def decode_dict_from_bytes(controller_db: _CONTROLLER_DB_STRUCT):
    return {
            "A": controller_db.channel[0],
            "X": controller_db.channel[1],
            "Y": controller_db.channel[2],
            "B": controller_db.channel[3],
            "RB": controller_db.channel[4],
            "RT": controller_db.channel[5],
            "LB": controller_db.channel[6],
            "LT": controller_db.channel[7],
            "d-up": controller_db.channel[8],
            "d-left": controller_db.channel[9],
            "d-down": controller_db.channel[10],
            "d-right": controller_db.channel[11],
            "LJoyThumb": controller_db.channel[12],
            "RJoyThumb": controller_db.channel[13],
            "Start": controller_db.channel[14],
            "Back": controller_db.channel[15],
            "LJoyX": controller_db.channel[16],
            "LJoyY": controller_db.channel[17],
            "RJoyX": controller_db.channel[18],
            "RJoyY": controller_db.channel[19]
            }

def encode_bytes_from_dict(data: dict):
    controller_db.channel[0] = data["A"]
    controller_db.channel[1] = data["X"]
    controller_db.channel[2] = data["Y"]
    controller_db.channel[3] = data["B"]
    controller_db.channel[4] = data["RB"]
    controller_db.channel[5] = data["RT"]
    controller_db.channel[6] = data["LB"]
    controller_db.channel[7] = data["LT"]
    controller_db.channel[8] = data["d-up"]
    controller_db.channel[9] = data["d-left"]
    controller_db.channel[10] = data["d-down"]
    controller_db.channel[11] = data["d-right"]
    controller_db.channel[12] = data["LJoyThumb"]
    controller_db.channel[13] = data["RJoyThumb"]
    controller_db.channel[14] = data["Start"]
    controller_db.channel[15] = data["Back"]
    controller_db.channel[16] = data["LJoyX"]
    controller_db.channel[17] = data["LJoyY"]
    controller_db.channel[18] = data["RJoyX"]
    controller_db.channel[19] = data["RJoyY"]

    return controller_db

if __name__ == '__main__':

    controller = gamepadReading.XboxController()
    controller_db = _CONTROLLER_DB_STRUCT()

    lock = threading.RLock()
    queue = Queue()

    client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    t1 = threading.Thread(target=udp_send)
    t2 = threading.Thread(target=udp_receive)

    t1.daemon = True
    t2.daemon = True

    t1.start()
    t2.start()