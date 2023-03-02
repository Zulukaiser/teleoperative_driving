import cv2, imutils, socket, threading
import numpy as np
import time
import base64
from udpStructures import VehicleStruct, ControlStruct
from vehicle import Vehicle

BUFF_SIZE = 65536
_video_flag = False

def map_control_to_vehicle_struct(control_struct: ControlStruct):
    pass

def udp_send_webcam():
    global _video_flag
    webcam_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    webcam_socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, BUFF_SIZE)
    socket_ip = "0.0.0.0"
    socket_port = 9999
    socket_address = (socket_ip, socket_port)
    webcam_socket.bind(socket_address)

    vid = cv2.VideoCapture(0)

    while True:
        msg, server_address = webcam_socket.recvfrom(BUFF_SIZE)
        print("Got Connection from: ", server_address)
        WIDTH = 400
        while vid.isOpen() and _video_flag:
            _, frame = vid.read()
            frame = imutils.resize(frame, width=WIDTH)
            encoded, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
            message = base64.b64encode(buffer)
            webcam_socket.sendto(message, server_address)
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                webcam_socket.close()
                break

def udp_receive_controls():
    global _video_flag
    vehicle = Vehicle()
    vehicle_struct = VehicleStruct()
    control_struct = ControlStruct()
    control_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    control_socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 70)
    socket_ip = "0.0.0.0"
    socket_port = 50007
    socket_address = (socket_ip, socket_port)
    control_socket.bind(socket_address)

    while True:
        control_struct, server_address = control_socket.recvfrom(70)
        vehicle_struct = map_control_to_vehicle_struct(control_struct)
        # Controls of vehicle
        vehicle_struct = vehicle.control_lights(vehicle_struct, control_struct)
        vehicle.control_vehicle(control_struct.RT, control_struct.LT)
        vehicle.control_steering(control_struct.LJoyX)
        vehicle.control_shift(control_struct.B)

if __name__ == '__main__':
    webcam_thread = threading.Thread(target=udp_send_webcam)
    webcam_thread.daemon = True
    control_thread = threading.Thread(target=udp_receive_controls)
    control_thread.daemon = True

    webcam_thread.start()
    control_thread.start()