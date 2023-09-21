from singlemotiondetector import SingleMotionDetector
from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtWidgets import QWidget, QApplication, QLabel
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtCore import pyqtSignal, pyqtSlot, Qt, QThread
from identifier_mapping import TDTP_IDENTIFIERS
from tdtp import TDTP
import cv2, imutils, socket, sys, ctypes, fanatec_hid, time, base64, urllib, gamepadReading
import numpy as np

tdtp_handle = TDTP(master=True)
REMOTE_HOST_IP = "10.3.141.1"


class ControlsThread(QThread):
    controls_signal = pyqtSignal(dict)

    def __init__(self, ai_overlay: QtWidgets.QCheckBox):
        super().__init__()
        self._run_flag = True
        self.ai_overlay = ai_overlay
        self.controls_state = False
        self.xbox = True
        self.xbox_old = self.xbox
        self.ai_overlay_status = self.ai_overlay.isChecked()
        self.controller = None
        if self.xbox:
            self.controller = gamepadReading.XboxController()
        else:
            self.controller = fanatec_hid.ControlInput()
        self.get_packet_loss_time = time.time() * 1000 + 1000

    def run(self):
        self.control_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.control_socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 26)
        self.control_socket.bind(("0.0.0.0", 50007))
        self.host_ip = REMOTE_HOST_IP
        self.host_port = 50007
        message = b"Initializing ..."
        try:
            self.control_socket.sendto(message, (self.host_ip, self.host_port))
            self.control_socket.connect_ex((self.host_ip, self.host_port))
        except TypeError as e:
            ui.log_console.append("Controls Error")
            print(e)
            self.stop()
        while self._run_flag:
            if self.xbox and (self.xbox != self.xbox_old):
                try:
                    self.controller = gamepadReading.XboxController()
                except:
                    continue
                self.xbox_old = self.xbox
            elif not self.xbox and (self.xbox != self.xbox_old):
                try:
                    self.controller = fanatec_hid.ControlInput()
                except:
                    continue
                self.xbox_old = self.xbox
            
            time.sleep(0.05)

            if self.controls_state:
                controller_data = self.get_controller_data()
            else:
                controller_data = {
                    "Gas": 0.0,
                    "Brake": 0.0,
                    "SWA": 0.0,
                    "Lowbeam": False,
                    "Highbeam": False,
                    "Horn": False,
                    "Indicator_L": False,
                    "Indicator_R": False,
                    }
            for data in controller_data:
                try:
                    identifier = [k for k, v in TDTP_IDENTIFIERS.items() if v == data][0]
                except:
                    continue
                value = controller_data[data]
                try:
                    message = tdtp_handle.assemble(identifier=identifier, data=value)
                    self.control_socket.sendall(message)
                except:
                    continue
            if self.get_packet_loss_time < time.time():
                self.get_packet_loss_time = time.time() * 1000 + 1000
                try:
                    identifier = [k for k, v in TDTP_IDENTIFIERS.items() if v == "PACKAGE_LOSS"][0]
                except:
                    continue
                value = self.tdtp_handle.package_loss_remote
                message = tdtp_handle.assemble(identifier=identifier, data=value)
                self.control_socket.sendall(message)
                self.package_loss = tdtp_handle.get_package_loss()
            if self.ai_overlay_status != self.ai_overlay.isChecked():
                self.ai_overlay_status = self.ai_overlay.isChecked()
                identifier = [k for k, v in TDTP_IDENTIFIERS.items() if v == "Lidar"][0]
                message = tdtp_handle.assemble(identifier=identifier, data=int(self.ai_overlay_status))
                self.control_socket.sendall(message)
            self.controls_signal.emit(controller_data)


    def stop(self):
        self._run_flag = False
        self.control_socket.close()
        self.wait()

    def get_controller_data(self):
        return self.controller.read()


class VideoThread(QThread):
    change_pixmap_signal = pyqtSignal(np.ndarray)

    def __init__(self):
        super().__init__()
        self._run_flag = True
        self._ai_overlay_flag = False

    def run(self):
        self.cap = cv2.VideoCapture(0)
        while self._run_flag:
            if self._ai_overlay_flag:
                self.detect_motion(15)
            if not self._ai_overlay_flag:
                ret, cv_img = self.cap.read()
                if ret:
                    self.change_pixmap_signal.emit(cv_img)
        self.cap.release()

    def stop(self):
        self._run_flag = False
        self.wait()

    def detect_motion(self, frame_count):
        md = SingleMotionDetector(accumWeight=0.1)
        total = 0
        while self._run_flag and self._ai_overlay_flag:
            _ret, frame = self.cap.read()
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray = cv2.GaussianBlur(gray, (7, 7), 0)

            if total > frame_count:
                motion = md.detect(gray)
                if motion is not None:
                    (thresh, (minX, minY, maxX, maxY)) = motion
                    cv2.rectangle(frame, (minX, minY), (maxX, maxY), (0, 0, 255), 2)
            md.update(gray)
            total += 1
            output_frame = frame.copy()
            self.change_pixmap_signal.emit(output_frame)


class WebcamThread(QThread):
    udp_webcam_signal = pyqtSignal(np.ndarray)

    def __init__(self):
        super().__init__()
        self.BUFF_SIZE = 65536
        self._run_flag = True
        self._ai_overlay_flag = False

    def run(self):
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, self.BUFF_SIZE)
        self.udp_socket.bind(("0.0.0.0", 9999))
        self.host_ip = REMOTE_HOST_IP
        # self.host_ip = "169.254.117.19"
        self.host_port = 9999
        message = b"Initializing ..."
        try:
            self.udp_socket.sendto(message, (self.host_ip, self.host_port))
        except:
            ui.log_console.append("No Webcam Signal")
            self.stop()
        while self._run_flag:
            if self._run_flag and self._ai_overlay_flag:
                self.detect_motion(15)

            if not self._ai_overlay_flag:
                try:
                    raw_img, _ = self.udp_socket.recvfrom(65535)
                except:
                    continue
                img = base64.b64decode(raw_img, " /")
                npdata = np.frombuffer(img, dtype=np.uint8)
                frame = cv2.imdecode(npdata, 1)
                if frame is None:
                    continue
                self.udp_webcam_signal.emit(frame)
                key = cv2.waitKey(1) & 0xFF

    def stop(self):
        self._run_flag = False
        self.udp_socket.close()
        self.wait()

    def detect_motion(self, frame_count):
        md = SingleMotionDetector(accumWeight=0.1)
        total = 0
        while self._run_flag and self._ai_overlay_flag:
            try:
                raw_img, _ = self.udp_socket.recvfrom(65535)
            except:
                continue
            img = base64.b64decode(raw_img, " /")
            npdata = np.frombuffer(img, dtype=np.uint8)
            frame = cv2.imdecode(npdata, 1)
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray = cv2.GaussianBlur(gray, (7, 7), 0)

            if total > frame_count:
                motion = md.detect(gray)
                if motion is not None:
                    (thresh, (minX, minY, maxX, maxY)) = motion
                    cv2.rectangle(frame, (minX, minY), (maxX, maxY), (0, 0, 255), 2)
            md.update(gray)
            total += 1
            output_frame = frame.copy()
            self.udp_webcam_signal.emit(output_frame)


class TelemetryThread(QThread):
    telemetry_signal = pyqtSignal(str, float)

    def __init__(self):
        super().__init__()
        self._run_flag = True

    def run(self):
        self.telemetry_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.telemetry_socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 26)
        self.telemetry_socket.bind(("0.0.0.0", 50008))
        self.host_ip = REMOTE_HOST_IP
        self.host_port = 50008
        message = b"Initializing ..."
        try:
            self.telemetry_socket.sendto(message, (self.host_ip, self.host_port))
        except:
            ui.log_console.append("No Telemetry Signal")
            self.stop()
        while self._run_flag:
            message_raw = None
            try:
                message_raw, _ = self.telemetry_socket.recvfrom(27)
            except:
                continue
            message = tdtp_handle.disassemble(message_raw)
            if not message:
                continue
            self.telemetry_signal.emit(TDTP_IDENTIFIERS[message[0]], message[1])

    def stop(self):
        self._run_flag = False
        self.telemetry_socket.close()
        self.wait()


class Ui_window_title(object):
    def setupUi(self, window_title):
        window_title.setObjectName("window_title")
        window_title.resize(1850, 1200)
        font = QtGui.QFont()
        font.setPointSize(12)
        font.setBold(False)
        font.setWeight(50)
        window_title.setFont(font)
        window_title.setAutoFillBackground(True)
        window_title.setToolButtonStyle(QtCore.Qt.ToolButtonStyle.ToolButtonIconOnly)
        self.centralwidget = QtWidgets.QWidget(parent=window_title)
        self.centralwidget.setObjectName("centralwidget")
        self.ip_input = QtWidgets.QLineEdit(parent=self.centralwidget)
        self.ip_input.setGeometry(QtCore.QRect(1410, 20, 321, 31))
        font = QtGui.QFont()
        font.setPointSize(12)
        self.ip_input.setFont(font)
        self.ip_input.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.ip_input.setObjectName("ip_input")
        self.establish_connection = QtWidgets.QPushButton(parent=self.centralwidget)
        self.establish_connection.setGeometry(QtCore.QRect(1410, 100, 321, 31))
        font = QtGui.QFont()
        font.setPointSize(12)
        self.establish_connection.setFont(font)
        self.establish_connection.setObjectName("establish_connection")
        self.close_connection = QtWidgets.QPushButton(parent=self.centralwidget)
        self.close_connection.setGeometry(QtCore.QRect(1410, 140, 321, 31))
        font = QtGui.QFont()
        font.setPointSize(12)
        self.close_connection.setFont(font)
        self.close_connection.setObjectName("close_connection")
        self.ai_overlay = QtWidgets.QCheckBox(parent=self.centralwidget)
        self.ai_overlay.setGeometry(QtCore.QRect(40, 990, 191, 51))
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Policy.Maximum, QtWidgets.QSizePolicy.Policy.Maximum
        )
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.ai_overlay.sizePolicy().hasHeightForWidth())
        self.ai_overlay.setSizePolicy(sizePolicy)
        self.ai_overlay.setMinimumSize(QtCore.QSize(80, 20))
        self.ai_overlay.setBaseSize(QtCore.QSize(0, 0))
        font = QtGui.QFont()
        font.setPointSize(20)
        self.ai_overlay.setFont(font)
        self.ai_overlay.setAutoFillBackground(False)
        self.ai_overlay.setIconSize(QtCore.QSize(100, 100))
        self.ai_overlay.setObjectName("ai_overlay")

        self.controller_select = QtWidgets.QCheckBox(parent=self.centralwidget)
        self.controller_select.setGeometry(QtCore.QRect(1410, 50, 191, 51))
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Policy.Maximum, QtWidgets.QSizePolicy.Policy.Maximum
        )
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.ai_overlay.sizePolicy().hasHeightForWidth())
        self.controller_select.setSizePolicy(sizePolicy)
        self.controller_select.setMinimumSize(QtCore.QSize(80, 20))
        self.controller_select.setBaseSize(QtCore.QSize(0, 0))
        font = QtGui.QFont()
        font.setPointSize(20)
        self.controller_select.setFont(font)
        self.controller_select.setAutoFillBackground(False)
        self.controller_select.setIconSize(QtCore.QSize(100, 100))
        self.controller_select.setObjectName("XBox")

        self.connection_status = QtWidgets.QLabel(parent=self.centralwidget)
        self.connection_status.setGeometry(QtCore.QRect(1410, 180, 161, 21))
        palette = QtGui.QPalette()
        brush = QtGui.QBrush(QtGui.QColor(0, 0, 0))
        brush.setStyle(QtCore.Qt.BrushStyle.SolidPattern)
        palette.setBrush(
            QtGui.QPalette.ColorGroup.Active, QtGui.QPalette.ColorRole.WindowText, brush
        )
        brush = QtGui.QBrush(QtGui.QColor(0, 0, 0))
        brush.setStyle(QtCore.Qt.BrushStyle.SolidPattern)
        palette.setBrush(
            QtGui.QPalette.ColorGroup.Inactive,
            QtGui.QPalette.ColorRole.WindowText,
            brush,
        )
        brush = QtGui.QBrush(QtGui.QColor(120, 120, 120))
        brush.setStyle(QtCore.Qt.BrushStyle.SolidPattern)
        palette.setBrush(
            QtGui.QPalette.ColorGroup.Disabled,
            QtGui.QPalette.ColorRole.WindowText,
            brush,
        )
        self.connection_status.setPalette(palette)
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        font.setKerning(True)
        font.setStyleStrategy(QtGui.QFont.StyleStrategy.PreferDefault)
        self.connection_status.setFont(font)
        self.connection_status.setContextMenuPolicy(
            QtCore.Qt.ContextMenuPolicy.NoContextMenu
        )
        self.connection_status.setAutoFillBackground(True)
        self.connection_status.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        self.connection_status.setTextFormat(QtCore.Qt.TextFormat.RichText)
        self.connection_status.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.connection_status.setTextInteractionFlags(
            QtCore.Qt.TextInteractionFlag.NoTextInteraction
        )
        self.connection_status.setObjectName("connection_status")
        self.controls_label = QtWidgets.QLabel(parent=self.centralwidget)
        self.controls_label.setGeometry(QtCore.QRect(1320, 450, 81, 21))
        font = QtGui.QFont()
        font.setPointSize(14)
        self.controls_label.setFont(font)
        self.controls_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.controls_label.setObjectName("controls_label")
        self.log_console = QtWidgets.QTextEdit(parent=self.centralwidget)
        self.log_console.setGeometry(QtCore.QRect(1340, 240, 441, 201))
        self.log_console.setObjectName("log_console")
        self.console_label = QtWidgets.QLabel(parent=self.centralwidget)
        self.console_label.setGeometry(QtCore.QRect(1320, 210, 81, 21))
        font = QtGui.QFont()
        font.setPointSize(14)
        self.console_label.setFont(font)
        self.console_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.console_label.setObjectName("console_label")
        self.clear_console_button = QtWidgets.QPushButton(parent=self.centralwidget)
        self.clear_console_button.setGeometry(QtCore.QRect(1660, 210, 121, 23))
        self.clear_console_button.setObjectName("clear_console_button")
        self.webcam_preview = QtWidgets.QLabel(parent=self.centralwidget)
        self.webcam_preview.setGeometry(QtCore.QRect(20, 20, 1296, 972))
        self.webcam_preview.setAutoFillBackground(True)
        self.webcam_preview.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.webcam_preview.setFrameShape(QtWidgets.QFrame.Shape.WinPanel)
        font = QtGui.QFont()
        font.setPointSize(30)
        self.webcam_preview.setFont(font)
        self.webcam_preview.setText("No Video")
        self.webcam_preview.setObjectName("webcam_preview")
        font = QtGui.QFont()
        font.setPointSize(14)
        self.SHOW = QtWidgets.QPushButton(parent=self.centralwidget)
        self.SHOW.setGeometry(QtCore.QRect(20, 1050, 231, 31))
        self.SHOW.setObjectName("SHOW")
        self.low_beam_indicator = QtWidgets.QLabel(parent=self.centralwidget)
        self.low_beam_indicator.setGeometry(QtCore.QRect(1450, 480, 101, 31))
        font = QtGui.QFont()
        font.setPointSize(12)
        self.low_beam_indicator.setFont(font)
        self.low_beam_indicator.setAutoFillBackground(False)
        self.low_beam_indicator.setStyleSheet("background-color: rgb(255, 255, 255);")
        self.low_beam_indicator.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        self.low_beam_indicator.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.low_beam_indicator.setObjectName("low_beam_indicator")
        self.high_beam = QtWidgets.QLabel(parent=self.centralwidget)
        self.high_beam.setGeometry(QtCore.QRect(1550, 480, 101, 31))
        font = QtGui.QFont()
        font.setPointSize(12)
        self.high_beam.setFont(font)
        self.high_beam.setAutoFillBackground(False)
        self.high_beam.setStyleSheet("background-color: rgb(255, 255, 255);")
        self.high_beam.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        self.high_beam.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.high_beam.setObjectName("high_beam")
        self.left_indicator = QtWidgets.QLabel(parent=self.centralwidget)
        self.left_indicator.setGeometry(QtCore.QRect(1350, 480, 101, 31))
        font = QtGui.QFont()
        font.setPointSize(12)
        self.left_indicator.setFont(font)
        self.left_indicator.setAutoFillBackground(False)
        self.left_indicator.setStyleSheet("background-color: rgb(255, 255, 255);")
        self.left_indicator.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        self.left_indicator.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.left_indicator.setObjectName("left_indicator")
        self.right_indicator = QtWidgets.QLabel(parent=self.centralwidget)
        self.right_indicator.setGeometry(QtCore.QRect(1650, 480, 111, 31))
        font = QtGui.QFont()
        font.setPointSize(12)
        self.right_indicator.setFont(font)
        self.right_indicator.setAutoFillBackground(False)
        self.right_indicator.setStyleSheet("background-color: rgb(255, 255, 255);")
        self.right_indicator.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        self.right_indicator.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.right_indicator.setObjectName("right_indicator")
        self.brake_light = QtWidgets.QLabel(parent=self.centralwidget)
        self.brake_light.setGeometry(QtCore.QRect(1500, 510, 101, 31))
        font = QtGui.QFont()
        font.setPointSize(12)
        self.brake_light.setFont(font)
        self.brake_light.setAutoFillBackground(False)
        self.brake_light.setStyleSheet("background-color: rgb(255, 255, 255);")
        self.brake_light.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        self.brake_light.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.brake_light.setObjectName("brake_light")
        self.steering_wheel_image = QtGui.QImage()
        self.steering_wheel_image.loadFromData(
            bytearray(open("Host PC\\steering_wheel.png", "rb").read())
        )
        self.steering_wheel_image_pixmap = QtGui.QPixmap(
            self.steering_wheel_image
        ).scaled(256, 256)
        self.steering_wheel = QtWidgets.QLabel(parent=self.centralwidget)
        self.steering_wheel.setGeometry(QtCore.QRect(1330, 560, 256, 256))
        self.steering_wheel.setFrameShape(QtWidgets.QFrame.Shape.WinPanel)
        self.steering_wheel.setText("")
        self.steering_wheel.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.steering_wheel.setObjectName("steering_wheel")
        self.steering_wheel_angle_label = QtWidgets.QLabel(parent=self.centralwidget)
        self.steering_wheel_angle_label.setGeometry(QtCore.QRect(1330, 830, 81, 21))
        self.steering_wheel_angle_label.setAlignment(
            QtCore.Qt.AlignmentFlag.AlignCenter
        )
        self.steering_wheel_angle_label.setObjectName("steering_wheel_angle_label")
        self.steering_wheel_angle = QtWidgets.QTextBrowser(parent=self.centralwidget)
        self.steering_wheel_angle.setGeometry(QtCore.QRect(1410, 830, 161, 31))
        self.steering_wheel_angle.setObjectName("steering_wheel_angle")
        self.activate_controls = QtWidgets.QPushButton(parent=self.centralwidget)
        self.activate_controls.setGeometry(QtCore.QRect(1410, 870, 161, 31))
        font = QtGui.QFont()
        font.setPointSize(12)
        self.activate_controls.setFont(font)
        self.activate_controls.setObjectName("activate_controls")
        self.gas_label = QtWidgets.QLabel(parent=self.centralwidget)
        self.gas_label.setGeometry(QtCore.QRect(1600, 590, 71, 21))
        self.gas_label.setAlignment(
            QtCore.Qt.AlignmentFlag.AlignLeading
            | QtCore.Qt.AlignmentFlag.AlignLeft
            | QtCore.Qt.AlignmentFlag.AlignVCenter
        )
        self.gas_label.setObjectName("gas_label")
        self.gas_value = QtWidgets.QTextBrowser(parent=self.centralwidget)
        self.gas_value.setGeometry(QtCore.QRect(1600, 620, 161, 31))
        self.gas_value.setObjectName("gas_value")
        self.gas_label_2 = QtWidgets.QLabel(parent=self.centralwidget)
        self.gas_label_2.setGeometry(QtCore.QRect(1600, 660, 81, 21))
        self.gas_label_2.setAlignment(
            QtCore.Qt.AlignmentFlag.AlignLeading
            | QtCore.Qt.AlignmentFlag.AlignLeft
            | QtCore.Qt.AlignmentFlag.AlignVCenter
        )
        self.gas_label_2.setObjectName("gas_label_2")
        self.brake_value = QtWidgets.QTextBrowser(parent=self.centralwidget)
        self.brake_value.setGeometry(QtCore.QRect(1600, 690, 161, 31))
        self.brake_value.setObjectName("brake_value")
        self.latency_one_way_label = QtWidgets.QLabel(parent=self.centralwidget)
        self.latency_one_way_label.setGeometry(QtCore.QRect(1600, 760, 161, 21))
        self.latency_one_way_label.setAlignment(
            QtCore.Qt.AlignmentFlag.AlignLeading
            | QtCore.Qt.AlignmentFlag.AlignLeft
            | QtCore.Qt.AlignmentFlag.AlignVCenter
        )
        self.latency_one_way_label.setObjectName("latency_one_way_label")
        self.latency_one_way_value = QtWidgets.QTextBrowser(parent=self.centralwidget)
        self.latency_one_way_value.setGeometry(QtCore.QRect(1600, 790, 161, 31))
        self.latency_one_way_value.setObjectName("latency_one_way_value")

        self.imu_ax_label = QtWidgets.QLabel(parent=self.centralwidget)
        self.imu_ax_label.setGeometry(QtCore.QRect(1500, 940, 161, 21))
        self.imu_ax_label.setAlignment(
            QtCore.Qt.AlignmentFlag.AlignLeading
            | QtCore.Qt.AlignmentFlag.AlignLeft
            | QtCore.Qt.AlignmentFlag.AlignVCenter
        )
        self.imu_ax_label.setObjectName("imu_ax_label")
        self.imu_ax_value = QtWidgets.QTextBrowser(parent=self.centralwidget)
        self.imu_ax_value.setGeometry(QtCore.QRect(1600, 940, 161, 31))
        self.imu_ax_value.setObjectName("imu_ax_value")

        self.imu_ay_label = QtWidgets.QLabel(parent=self.centralwidget)
        self.imu_ay_label.setGeometry(QtCore.QRect(1500, 970, 161, 21))
        self.imu_ay_label.setAlignment(
            QtCore.Qt.AlignmentFlag.AlignLeading
            | QtCore.Qt.AlignmentFlag.AlignLeft
            | QtCore.Qt.AlignmentFlag.AlignVCenter
        )
        self.imu_ay_label.setObjectName("imu_ay_label")
        self.imu_ay_value = QtWidgets.QTextBrowser(parent=self.centralwidget)
        self.imu_ay_value.setGeometry(QtCore.QRect(1600, 970, 161, 31))
        self.imu_ay_value.setObjectName("imu_ay_value")

        self.imu_az_label = QtWidgets.QLabel(parent=self.centralwidget)
        self.imu_az_label.setGeometry(QtCore.QRect(1500, 1000, 161, 21))
        self.imu_az_label.setAlignment(
            QtCore.Qt.AlignmentFlag.AlignLeading
            | QtCore.Qt.AlignmentFlag.AlignLeft
            | QtCore.Qt.AlignmentFlag.AlignVCenter
        )
        self.imu_az_label.setObjectName("imu_az_label")
        self.imu_az_value = QtWidgets.QTextBrowser(parent=self.centralwidget)
        self.imu_az_value.setGeometry(QtCore.QRect(1600, 1000, 161, 31))
        self.imu_az_value.setObjectName("imu_az_value")

        self.imu_yaw_label = QtWidgets.QLabel(parent=self.centralwidget)
        self.imu_yaw_label.setGeometry(QtCore.QRect(1500, 1030, 161, 21))
        self.imu_yaw_label.setAlignment(
            QtCore.Qt.AlignmentFlag.AlignLeading
            | QtCore.Qt.AlignmentFlag.AlignLeft
            | QtCore.Qt.AlignmentFlag.AlignVCenter
        )
        self.imu_yaw_label.setObjectName("imu_yaw_label")
        self.imu_yaw_value = QtWidgets.QTextBrowser(parent=self.centralwidget)
        self.imu_yaw_value.setGeometry(QtCore.QRect(1600, 1030, 161, 31))
        self.imu_yaw_value.setObjectName("imu_yaw_value")

        self.imu_pitch_label = QtWidgets.QLabel(parent=self.centralwidget)
        self.imu_pitch_label.setGeometry(QtCore.QRect(1500, 1060, 161, 21))
        self.imu_pitch_label.setAlignment(
            QtCore.Qt.AlignmentFlag.AlignLeading
            | QtCore.Qt.AlignmentFlag.AlignLeft
            | QtCore.Qt.AlignmentFlag.AlignVCenter
        )
        self.imu_pitch_label.setObjectName("imu_pitch_label")
        self.imu_pitch_value = QtWidgets.QTextBrowser(parent=self.centralwidget)
        self.imu_pitch_value.setGeometry(QtCore.QRect(1600, 1060, 161, 31))
        self.imu_pitch_value.setObjectName("imu_pitch_value")

        self.imu_roll_label = QtWidgets.QLabel(parent=self.centralwidget)
        self.imu_roll_label.setGeometry(QtCore.QRect(1500, 1090, 161, 21))
        self.imu_roll_label.setAlignment(
            QtCore.Qt.AlignmentFlag.AlignLeading
            | QtCore.Qt.AlignmentFlag.AlignLeft
            | QtCore.Qt.AlignmentFlag.AlignVCenter
        )
        self.imu_roll_label.setObjectName("imu_roll_label")
        self.imu_roll_value = QtWidgets.QTextBrowser(parent=self.centralwidget)
        self.imu_roll_value.setGeometry(QtCore.QRect(1600, 1090, 161, 31))
        self.imu_roll_value.setObjectName("imu_roll_value")

        self.batt_u_label = QtWidgets.QLabel(parent=self.centralwidget)
        self.batt_u_label.setGeometry(QtCore.QRect(1500, 1120, 161, 21))
        self.batt_u_label.setAlignment(
            QtCore.Qt.AlignmentFlag.AlignLeading
            | QtCore.Qt.AlignmentFlag.AlignLeft
            | QtCore.Qt.AlignmentFlag.AlignVCenter
        )
        self.batt_u_label.setObjectName("batt_u_label")
        self.batt_u_value = QtWidgets.QTextBrowser(parent=self.centralwidget)
        self.batt_u_value.setGeometry(QtCore.QRect(1600, 1120, 161, 31))
        self.batt_u_value.setObjectName("batt_u_value")

        self.latency_two_way_label = QtWidgets.QLabel(parent=self.centralwidget)
        self.latency_two_way_label.setGeometry(QtCore.QRect(1600, 820, 161, 21))
        self.latency_two_way_label.setAlignment(
            QtCore.Qt.AlignmentFlag.AlignLeading
            | QtCore.Qt.AlignmentFlag.AlignLeft
            | QtCore.Qt.AlignmentFlag.AlignVCenter
        )
        self.latency_two_way_label.setObjectName("latency_two_way_label")
        self.latency_two_way_value = QtWidgets.QTextBrowser(parent=self.centralwidget)
        self.latency_two_way_value.setGeometry(QtCore.QRect(1600, 850, 161, 31))
        self.latency_two_way_value.setObjectName("latency_two_way_value")
        self.velocity_value = QtWidgets.QLCDNumber(parent=self.centralwidget)
        self.velocity_value.setGeometry(QtCore.QRect(740, 1000, 151, 111))
        self.velocity_value.setStyleSheet("background-color: rgb(255, 255, 255);")
        self.velocity_value.setFrameShape(QtWidgets.QFrame.Shape.WinPanel)
        self.velocity_value.setFrameShadow(QtWidgets.QFrame.Shadow.Plain)
        self.velocity_value.setDigitCount(3)
        self.velocity_value.setSegmentStyle(QtWidgets.QLCDNumber.SegmentStyle.Flat)
        self.velocity_value.setObjectName("velocity_value")
        self.velocity_label = QtWidgets.QLabel(parent=self.centralwidget)
        self.velocity_label.setGeometry(QtCore.QRect(390, 1000, 341, 91))
        font = QtGui.QFont()
        font.setPointSize(36)
        self.velocity_label.setFont(font)
        self.velocity_label.setObjectName("velocity_label")
        window_title.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(parent=window_title)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 1767, 21))
        self.menubar.setObjectName("menubar")
        self.menuTeleoperative_Driving = QtWidgets.QMenu(parent=self.menubar)
        self.menuTeleoperative_Driving.setObjectName("menuTeleoperative_Driving")
        window_title.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(parent=window_title)
        self.statusbar.setObjectName("statusbar")
        window_title.setStatusBar(self.statusbar)
        self.menubar.addAction(self.menuTeleoperative_Driving.menuAction())

        self.display_width = 1920
        self.display_height = 1080
        self.ai_overlay_flag = False

        self.video_source = False

        self.controls_state = False
        self.lights = {
            "low_beam": {"state": 0, "z": 0},
            "high_beam": {"state": 0, "z": 0},
            "indicator_left": {"state": 0, "z": 0},
            "indicator_right": {"state": 0, "z": 0},
            "brake": {"state": 0, "z": 0},
        }

        self.get_packet_loss_time = time.time() * 1000 + 1000
        self.package_loss = 0

        self.imu_ax = 0
        self.imu_ay = 0
        self.imu_az = 0
        self.imu_yaw = 0
        self.imu_roll = 0
        self.imu_pitch = 0
        self.batt_u = 0

        self.time_epoch_obj = time.gmtime(0)
        self.time_epoch = time.asctime(self.time_epoch_obj)

        self.retranslateUi(window_title)

        self.establish_connection.pressed.connect(self.on_establish_connection_pressed)
        self.establish_connection.clicked.connect(self.on_establish_connection_click)
        self.close_connection.clicked.connect(self.on_close_connection_click)
        self.ai_overlay.clicked.connect(self.clicked_ai_overlay)
        self.controller_select.clicked.connect(self.clicked_controller_select)
        self.clear_console_button.clicked.connect(self.on_clear_console_click)
        self.SHOW.clicked.connect(self.on_show_webcam_click_start)
        self.activate_controls.clicked.connect(self.on_activate_controls)

        QtCore.QMetaObject.connectSlotsByName(window_title)

        # Functions for actions here

    def on_establish_connection_click(self):
        ip = self.ip_input.text()
        if self.valid_ip(ip, False):
            global REMOTE_HOST_IP
            REMOTE_HOST_IP = ip
            self.controller_thread = ControlsThread(self.ai_overlay)
            self.controller_thread.controls_signal.connect(self.handle_controller)
            self.controller_thread.start()

            self.telemetry_thread = TelemetryThread()
            self.telemetry_thread.telemetry_signal.connect(self.get_udp_message)
            self.telemetry_thread.start()
            self.log_console.append(f"Connection to {ip} established")
            self.connection_status.setStyleSheet("background-color: green")


    def on_establish_connection_pressed(self):
        ip = self.ip_input.text()
        if self.valid_ip(ip, True):
            self.log_console.append(f"Connecting to {ip} ...")

    def on_close_connection_click(self):
        self.log_console.append("Closing connection ...")
        try:
            self.thread.stop()
            self.controller_thread.stop()
            self.telemetry_thread.stop()
            self.connection_status.setStyleSheet("background-color: red")
        except:
            self.log_console.append("Error in closing connection")
            return
        self.log_console.append("Connection closed")

    def clicked_ai_overlay(self):
        if self.ai_overlay.isChecked():
            try:
                self.thread._ai_overlay_flag = True
                self.log_console.append("AI Overlay activated")
            except:
                self.log_console.append("No Video Thread available")
        else:
            try:
                self.thread._ai_overlay_flag = False
                self.log_console.append("AI Overlay deactivated")
            except:
                self.log_console.append("No Video Thread available")

    def clicked_controller_select(self):
        if self.controller_select.isChecked():
            try:
                self.controller_thread.xbox = True
            except:
                self.log_console.append("No connection!")
        else:
            try:
                self.controller_thread.xbox = False
            except:
                self.log_console.append("No connection!")

    def on_clear_console_click(self):
        self.log_console.clear()

    def on_show_webcam_click_start(self):
        self.SHOW.clicked.disconnect(self.on_show_webcam_click_start)
        self.SHOW.setText("Stop Video")
        if self.video_source:
            self.thread = VideoThread()
            self.thread.change_pixmap_signal.connect(self.update_image)
        else:
            self.thread = WebcamThread()
            self.thread.udp_webcam_signal.connect(self.update_image)
        self.thread.start()
        self.SHOW.clicked.connect(self.thread.stop)
        self.SHOW.clicked.connect(self.on_show_webcam_click_stop)
        self.webcam_preview.setText("")

    def on_show_webcam_click_stop(self):
        if self.video_source:
            self.thread.change_pixmap_signal.disconnect()
        else:
            self.thread.udp_webcam_signal.disconnect()
        self.SHOW.setText("Start Video")
        self.SHOW.clicked.disconnect(self.on_show_webcam_click_stop)
        self.SHOW.clicked.disconnect(self.thread.stop)
        self.SHOW.clicked.connect(self.on_show_webcam_click_start)

        qt_img = QPixmap(self.display_width, self.display_height)
        qt_img.fill(QtGui.QColor(0, 0, 0, 0))

        self.webcam_preview.setPixmap(qt_img)
        self.webcam_preview.setText("No Video")

    def on_activate_controls(self):
        try:
            if self.controller_thread.controls_state:
                self.controller_thread.controls_state = False
                self.activate_controls.setText("Activate Controls")
                self.log_console.append("Controls deactivated")
            elif not self.controller_thread.controls_state:
                self.controller_thread.controls_state = True
                self.activate_controls.setText("Deactivate Controls")
                self.log_console.append("Controls activated")
        except:
            self.log_console.append("No connection!")

    def check_connection(self, ip, port):
        self.log_console.append(f"Connection established")

    def valid_ip(self, ip, log):
        parts = ip.split(".")
        if len(parts) != 4:
            if log:
                self.log_console.append(f"Invalid IP format: {ip} != xxx.xxx.xxx.xxx")
            return False
        for item in parts:
            try:
                if not 0 <= int(item) <= 255:
                    if log:
                        self.log_console.append(
                            f"Invalid IP: {item} not in range(0,255)"
                        )
                    return False
            except ValueError as e:
                if log:
                    self.log_console.append("Invalid IP! " + str(e))
                return False
        return True

    def retranslateUi(self, window_title):
        _translate = QtCore.QCoreApplication.translate
        window_title.setWindowTitle(_translate("window_title", "Teleoperative Driving"))
        self.ip_input.setPlaceholderText(_translate("window_title", "IP Address"))
        self.establish_connection.setText(
            _translate("window_title", "Establish Connection")
        )
        self.close_connection.setText(_translate("window_title", "Close Connection"))
        self.ai_overlay.setText(_translate("window_title", "AI Overlay"))
        self.controller_select.setText(_translate("window_title", "XBox Controller"))
        self.connection_status.setText(
            _translate(
                "window_title",
                "<html><head/><body><p>Connection Status</p></body></html>",
            )
        )
        self.controls_label.setText(_translate("window_title", "Controls"))
        self.console_label.setText(_translate("window_title", "Console"))
        self.clear_console_button.setText(_translate("window_title", "Clear Console"))
        self.SHOW.setText(_translate("window_title", "Start Video"))
        self.low_beam_indicator.setText(_translate("window_title", "Low Beam"))
        self.high_beam.setText(_translate("window_title", "High Beam"))
        self.left_indicator.setText(_translate("window_title", "Left Indicator"))
        self.right_indicator.setText(_translate("window_title", "Right Indicator"))
        self.brake_light.setText(_translate("window_title", "Brake Lights"))
        self.steering_wheel_angle_label.setText(_translate("window_title", "SWA [°]:"))
        self.activate_controls.setText(_translate("window_title", "Activate Controls"))
        self.gas_label.setText(_translate("window_title", "Gas [%]:"))
        self.gas_label_2.setText(_translate("window_title", "Brake [%]:"))
        self.latency_one_way_label.setText(
            _translate("window_title", "Latency 1-way [ms]:")
        )

        self.imu_ax_label.setText(_translate("window_title", "ax [m/s^2]:"))
        self.imu_ay_label.setText(_translate("window_title", "ay [m/s^2]:"))
        self.imu_az_label.setText(_translate("window_title", "az [m/s^2]:"))
        self.imu_yaw_label.setText(_translate("window_title", "Yaw [°]:"))
        self.imu_pitch_label.setText(_translate("window_title", "Pitch [°]:"))
        self.imu_roll_label.setText(_translate("window_title", "Roll [°]:"))
        self.batt_u_label.setText(_translate("window_title", "Batt [V]:"))

        self.latency_two_way_label.setText(
            _translate("window_title", "Latency 2-way [ms]:")
        )
        self.velocity_label.setText(_translate("window_title", "Velocity [km/h]:"))
        self.menuTeleoperative_Driving.setTitle(
            _translate("window_title", "Teleoperative Driving")
        )

    def close_event(self, event):
        self.thread.stop()
        self.controller_thread.stop()
        event.accept()

    # @pyqtSlot(np.ndarray)
    def update_image(self, cv_img):
        qt_img = self.convert_cv_qt(cv_img)
        self.webcam_preview.setPixmap(qt_img)

    def update_webcam(self, img):
        # img = cv2.resize(img, (1296, 972))
        # cv2.imshow("Preview",img)
        qt_img = QtGui.QPixmap(img)
        self.webcam_preview.setPixmap(qt_img)

    def convert_cv_qt(self, cv_img):
        rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        convert_to_Qt_format = QtGui.QImage(
            rgb_image.data, w, h, bytes_per_line, QtGui.QImage.Format.Format_RGB888
        )
        p = convert_to_Qt_format.scaled(
            self.display_width,
            self.display_height,
            aspectRatioMode=Qt.AspectRatioMode.KeepAspectRatio,
        )
        return QPixmap.fromImage(p)

    def handle_controller(self, controller_data: dict):
        # Update all qt labels
        if controller_data["Indicator_L"] and not self.lights["indicator_left"]["z"]:
            if not self.lights["indicator_left"]["state"]:
                self.left_indicator.setStyleSheet("background-color: orange")
                self.lights["indicator_left"]["state"] = 1
            else:
                self.left_indicator.setStyleSheet("background-color: white")
                self.lights["indicator_left"]["state"] = 0
        self.lights["indicator_left"]["z"] = controller_data["Indicator_L"]

        if controller_data["Indicator_R"] and not self.lights["indicator_right"]["z"]:
            if not self.lights["indicator_right"]["state"]:
                self.right_indicator.setStyleSheet("background-color: orange")
                self.lights["indicator_right"]["state"] = 1
            else:
                self.right_indicator.setStyleSheet("background-color: white")
                self.lights["indicator_right"]["state"] = 0
        self.lights["indicator_right"]["z"] = controller_data["Indicator_R"]

        if controller_data["Lowbeam"] and not self.lights["low_beam"]["z"]:
            if not self.lights["low_beam"]["state"]:
                self.low_beam_indicator.setStyleSheet("background-color: green;\ncolor: white")
                self.lights["low_beam"]["state"] = 1
            else:
                self.low_beam_indicator.setStyleSheet("background-color: white;\ncolor: black")
                self.lights["low_beam"]["state"] = 0
        self.lights["low_beam"]["z"] = controller_data["Lowbeam"]

        if controller_data["Highbeam"] and not self.lights["high_beam"]["z"]:
            if not self.lights["high_beam"]["state"]:
                self.high_beam.setStyleSheet("background-color: blue;\ncolor: white")
                self.lights["high_beam"]["state"] = 1
            else:
                self.high_beam.setStyleSheet("background-color: white;\ncolor: black")
                self.lights["high_beam"]["state"] = 0
        self.lights["high_beam"]["z"] = controller_data["Highbeam"]

        if controller_data["Brake"] != 0.0:
            self.brake_light.setStyleSheet("background-color: red")
        else:
            self.brake_light.setStyleSheet("background-color: white")
        self.gas_value.setText(str(controller_data["Gas"] * 100.0))
        self.velocity_value.display(int(controller_data["Gas"] * 30.0))
        self.brake_value.setText(str(controller_data["Brake"] * 100.0))
        self.steering_wheel_angle.setText(
            str(
                np.sign(controller_data["SWA"])
                * controller_data["SWA"]
                * controller_data["SWA"]
                * 90.0
            )
        )
        self.rotate_steering_wheel(
            np.sign(controller_data["SWA"])
            * controller_data["SWA"]
            * controller_data["SWA"]
            * 90.0
        )  # delta = sign(swa) * swa^2 * 90°

    def rotate_steering_wheel(self, angle):
        pixmap = QtGui.QPixmap(self.steering_wheel_image).scaled(256, 256)
        transform = QtGui.QTransform().rotate(angle)
        pixmap = pixmap.transformed(transform)
        self.steering_wheel.setPixmap(pixmap)

    def get_time(self):
        return round(time.time() * 1000)

    def get_udp_message(self, identifier, data):
        self.latency_one_way_value.setText(str(tdtp_handle.latency / 2))
        self.latency_two_way_value.setText(str(tdtp_handle.latency))
        match identifier:
            case "PACKAGE_LOSS":
                return
            case "IMU_AX":
                self.imu_ax = data
                self.imu_ax_value.setText(str(self.imu_ax))
            case "IMU_AY":
                self.imu_ay = data
                self.imu_ay_value.setText(str(self.imu_ay))
            case "IMU_AZ":
                self.imu_az = data
                self.imu_az_value.setText(str(self.imu_az))
            case "IMU_YAW":
                self.imu_yaw = data
                self.imu_yaw_value.setText(str(self.imu_yaw))
            case "IMU_PITCH":
                self.imu_pitch = data
                self.imu_pitch_value.setText(str(self.imu_pitch))
            case "IMU_ROLL":
                self.imu_roll = data
                self.imu_roll_value.setText(str(self.imu_roll))
            case "BATT_U":
                self.batt_u = data
                self.batt_u_value.setText(str(self.batt_u))
            case _:
                return


if __name__ == "__main__":
    import sys

    app = QtWidgets.QApplication(sys.argv)
    window_title = QtWidgets.QMainWindow()
    ui = Ui_window_title()
    ui.setupUi(window_title)
    window_title.show()
    sys.exit(app.exec())
