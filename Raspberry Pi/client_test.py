import cv2, imutils, socket, threading
import base64
from vehicle import Vehicle
from tdtp import TDTP
from DEBO_SENS_ACC3 import IMU
from identifier_mapping import TDTP_IDENTIFIERS

BUFF_SIZE = 65536
_video_flag = True
tdtp_handle = TDTP()
vehicle = Vehicle()


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
        while _video_flag:
            try:
                _, frame = vid.read()
            except:
                continue
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
    control_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    control_socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 26)
    socket_ip = "0.0.0.0"
    socket_port = 50007
    socket_address = (socket_ip, socket_port)
    control_socket.bind(socket_address)
    vehicle.day_light_output.on()

    while True:
        message_raw, server_address = control_socket.recvfrom(26)
        message = tdtp_handle.disassemble(message_raw)
        if not message:
            continue
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

    msg, server_address = telemetry_socket.recvfrom(26)
    print("Got telemetry connection from: ", server_address)

    while True:
        # Get Sensor data and Telemetry
        accelerations = imu.get_acceleration()
        for accl in accelerations:
            if accl not in ["IMU_AX", "IMU_AY", "IMU_AZ"]:
                continue
            identifier = [k for k, v in TDTP_IDENTIFIERS.items() if v == accl][0]
            data = accelerations[accl]
                
            if identifier != None and data != None:
                message = tdtp_handle.assemble(identifier=identifier, data=data)
                ret = telemetry_socket.sendto(message, server_address)
                print(ret)

if __name__ == "__main__":
    webcam_thread = threading.Thread(target=udp_send_webcam)
    webcam_thread.daemon = True
    control_thread = threading.Thread(target=udp_receive_controls)
    control_thread.daemon = True
    telemetry_thread = threading.Thread(target=udp_send_telemetry)
    telemetry_thread.daemon = True

    vehicle.drive.value = 0.1

    webcam_thread.start()
    control_thread.start()
    telemetry_thread.start()

    try:
        while True:
            pass
    except KeyboardInterrupt:
        webcam_thread.join()
        control_thread.join()
        vehicle.horn_output.off()
        vehicle.low_beam_output.off()
        vehicle.brake_lights_output.off()
        vehicle.day_light_output.off()
        vehicle.high_beam_output.off()
        vehicle.indicator_left_output.off()
        vehicle.indicator_right_output.off()
        vehicle.drive.value = 0.0
        vehicle.steer.value = 0.0