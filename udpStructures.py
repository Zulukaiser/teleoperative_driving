# Structure definition for teleoperative driving over udp
import ctypes


class ControlStruct(ctypes.Structure):
    _fields_ = [
        ("Gas", ctypes.c_double),
        ("Brake", ctypes.c_double),
        ("SWA", ctypes.c_double),
        ("Lowbeam", ctypes.c_double),
        ("Highbeam", ctypes.c_double),
        ("Horn", ctypes.c_double),
        ("Indicator_L", ctypes.c_double),
        ("Indicator_R", ctypes.c_double),
        ("packet_number", ctypes.c_double),
        ("packet_dropped", ctypes.c_double),
        ("latency_ms", ctypes.c_double),
    ]


class VehicleStruct(ctypes.Structure):
    _fields_ = [
        ("Gas", ctypes.c_double),
        ("Brake", ctypes.c_double),
        ("SWA", ctypes.c_double),
        ("Lowbeam", ctypes.c_double),
        ("Highbeam", ctypes.c_double),
        ("Horn", ctypes.c_double),
        ("Indicator_L", ctypes.c_double),
        ("Indicator_R", ctypes.c_double),
        ("packet_number", ctypes.c_double),
        ("packet_dropped", ctypes.c_double),
        ("latency_ms", ctypes.c_double),
    ]
