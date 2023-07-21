import cv2, imutils, socket, threading
import numpy as np
import time
import base64
from vehicle import Vehicle
from gpiozero import Servo
from tdtp import TDTP

BUFF_SIZE = 65536
_video_flag = False
steering_servo = Servo(12)
driving_servo = Servo(13)
tdtp_handle = TDTP()


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
            encoded, buffer = cv2.imencode(
                ".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 80]
            )
            message = base64.b64encode(buffer)
            webcam_socket.sendto(message, server_address)
            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                webcam_socket.close()
                break


def udp_receive_controls():
    global _video_flag
    vehicle = Vehicle()
    control_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    control_socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 26)
    socket_ip = "0.0.0.0"
    socket_port = 50007
    socket_address = (socket_ip, socket_port)
    control_socket.bind(socket_address)

    while True:
        message_raw, server_address = control_socket.recvfrom(26)
        message = tdtp_handle.disassemble(message_raw)
        if not message:
            continue
        # Controls of vehicle
        vehicle.control_vehicle(message)


def udp_send_telemetry():
    global _video_flag
    telemetry_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    telemetry_socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 26)
    socket_ip = "0.0.0.0"
    socket_port = 50008
    socket_address = (socket_ip, socket_port)
    telemetry_socket.bind(socket_address)

    while True:
        # Get Sensor data and Telemetry
        data = 0
        identifier = 1
        message = tdtp_handle.assemble(identifier=identifier, data=data)
        telemetry_socket.sendall(message)


if __name__ == "__main__":
    webcam_thread = threading.Thread(target=udp_send_webcam)
    webcam_thread.daemon = True
    control_thread = threading.Thread(target=udp_receive_controls)
    control_thread.daemon = True
    telemetry_thread = threading.Thread(target=udp_send_telemetry)
    telemetry_thread.daemon = True

    webcam_thread.start()
    control_thread.start()
    telemetry_thread.start()
