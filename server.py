# Firewall has to be disabled
# Ports don't necessarily have to be opened in router

import threading
import ctypes
import socket
from queue import Queue
import vehicle

class _CONTROLLER_DB_STRUCT(ctypes.Structure):
    _fields_ = [("Channel", ctypes.c_float * 20)]

HOST = '0.0.0.0'    # To accept connections from all IPv4 addresses, this needs to be '0.0.0.0'
PORT = 50007        # Use a Port, that is UDP enabled and not reserved
BUFFER_SIZE = 80  # Buffer size should be bigger than the message or else the message is dropped or incomplete

def udp_receive(lock: threading.RLock):
    while True:
        with lock:
            controller_db, address = server.recvfrom(BUFFER_SIZE)
            decoded_data = decode_dict_from_bytes(controller_db)
            car.control_lights(decoded_data)
            car.control_steering(decoded_data["LJoyX"])
            car.control_vehicle(decoded_data["RT"], decoded_data["LT"])
            car.control_shift(decoded_data["A"], decoded_data["X"])

def udp_send(lock: threading.RLock):
    while True:
        with lock:
            pass

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

def control_vehicle():
    pass

if __name__ == '__main__':
    car = vehicle.vehicle()

    controller_db = _CONTROLLER_DB_STRUCT()

    address = socket.gethostbyname(socket.gethostname())
    lock = threading.RLock()
    queue = Queue()
    data = b'Initialized'
    server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server.bind((HOST, PORT))

    t1 = threading.Thread(target=udp_receive, args=lock)
    t2 = threading.Thread(target=udp_send, args=lock)
    t3 = threading.Thread(target=control_vehicle)

    t1.daemon = True
    t2.daemon = True
    t3.daemon = True

    t1.start()
    t2.start()
    t3.start()