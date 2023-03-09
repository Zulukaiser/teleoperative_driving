# Structure definition for teleoperative driving over udp
import ctypes


class ControlStruct(ctypes.Structure):
    _fields_ = [
        ("LT", ctypes.c_float),
        ("RT", ctypes.c_float),
        ("LJoyX", ctypes.c_float),
        ("LJoyY", ctypes.c_float),
        ("RJoyX", ctypes.c_float),
        ("RJoyY", ctypes.c_float),
        ("packet_number", ctypes.c_int32),
        ("packet_dropped", ctypes.c_int32),
        ("latency_mcs", ctypes.c_int32),
        ("latency_s", ctypes.c_int32)("A", ctypes.c_int32),
        ("X", ctypes.c_int32),
        ("Y", ctypes.c_int32),
        ("B", ctypes.c_int32),
        ("RB", ctypes.c_int32),
        ("LB", ctypes.c_int32),
        ("d_up", ctypes.c_int32),
        ("d_left", ctypes.c_int32),
        ("d_down", ctypes.c_int32),
        ("d_right", ctypes.c_int32),
        ("LJoyThumb", ctypes.c_int32),
        ("RJoyThumb", ctypes.c_int32),
        ("Start", ctypes.c_int32),
        ("Back", ctypes.c_int32),
    ]


class VehicleStruct(ctypes.Structure):
    _fields_ = [
        ("indicator_left", ctypes.c_int32),
        ("indicator_right", ctypes.c_int32),
        ("low_beam", ctypes.c_int32),
        ("high_beam", ctypes.c_int32),
        ("brake_light", ctypes.c_int32),
        ("gear", ctypes.c_int32),
        ("diff_front", ctypes.c_int32),
        ("diff_rear", ctypes.c_int32),
        ("gas", ctypes.c_float),
        ("brake", ctypes.c_float),
        ("steering", ctypes.c_float),
        ("packet_number", ctypes.c_int32),
        ("packet_dropped", ctypes.c_int32),
        ("latency_mcs", ctypes.c_int32),
        ("latency_s", ctypes.c_int32),
    ]
