import cv2, imutils, socket, threading
import numpy as np
import time
import base64
from pyrplidar import PyRPlidar
from vehicle import Vehicle
from gpiozero import Servo
from tdtp import TDTP
from DEBO_SENS_ACC3 import IMU
from identifier_mapping import TDTP_IDENTIFIERS

BUFF_SIZE = 65536
_video_flag = False
steering_servo = Servo(12)
driving_servo = Servo(13)
tdtp_handle = TDTP()
lidar_start = False


def udp_send_webcam():
    global _video_flag
    global lidar_start
    webcam_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    webcam_socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, BUFF_SIZE)
    socket_ip = "0.0.0.0"
    socket_port = 9999
    socket_address = (socket_ip, socket_port)
    webcam_socket.bind(socket_address)

    vid = cv2.VideoCapture(0)

    lidar = PyRPlidar()
    lidar.connect(port="/dev/ttyUSB0", baudrate=256000, timeout=3)

    print("Lidar info: ", lidar.get_info())
    print("Lidar health: ", lidar.get_health())

    lidar_thread = threading.Thread(target=lidar.start_scan, args=())
    lidar_thread.daemon = True

    while True:
        msg, server_address = webcam_socket.recvfrom(BUFF_SIZE)
        print("Got Connection from: ", server_address)
        WIDTH = 400
        while vid.isOpen() and _video_flag:
            if lidar_start:
                lidar_thread.start()
            else:
                lidar_thread.join()

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
    global lidar_start
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
        elif message[0] == [k for k, v in TDTP_IDENTIFIERS.items() if v == "Lidar"][0]:
            if message[1] != 0:
                lidar_start = True
            else:
                lidar_start = False
        # Controls of vehicle
        else:
            vehicle.control_vehicle(message)


def udp_send_telemetry():
    global _video_flag
    telemetry_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    telemetry_socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 26)
    socket_ip = "0.0.0.0"
    socket_port = 50008
    socket_address = (socket_ip, socket_port)
    telemetry_socket.bind(socket_address)
    imu = IMU()

    while True:
        # Get Sensor data and Telemetry
        accelerations = imu.get_acceleration()
        for accl in accelerations:
            identifier = None
            data = None
            match accl:
                case "IMU_AX":
                    data = accelerations[accl]
                    identifier = [k for k, v in TDTP_IDENTIFIERS.items() if v == accl][0]
                case "IMU_AY":
                    data = accelerations[accl]
                    identifier = [k for k, v in TDTP_IDENTIFIERS.items() if v == accl][0]
                case "IMU_AZ":
                    data = accelerations[accl]
                    identifier = [k for k, v in TDTP_IDENTIFIERS.items() if v == accl][0]
                case _:
                    continue
                
            if identifier != None and data != None:
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
