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
        ("latency_s", ctypes.c_int32)
        ("A", ctypes.c_bool),
        ("X", ctypes.c_bool),
        ("Y", ctypes.c_bool),
        ("B", ctypes.c_bool),
        ("RB", ctypes.c_bool),
        ("LB", ctypes.c_bool),
        ("d-up", ctypes.c_bool),
        ("d-left", ctypes.c_bool),
        ("d-down", ctypes.c_bool),
        ("d-right", ctypes.c_bool),
        ("LJoyThumb", ctypes.c_bool),
        ("RJoyThumb", ctypes.c_bool),
        ("Start", ctypes.c_bool),
        ("Back", ctypes.c_bool),
                ]

class VehicleStruct(ctypes.Structure):
    _fields_ = [
        ("indicator_left", ctypes.c_bool),
        ("indicator_right", ctypes.c_bool),
        ("low_beam", ctypes.c_bool),
        ("high_beam", ctypes.c_bool),
        ("brake_light", ctypes.c_bool),
        ("gear", ctypes.c_bool),
        ("diff_front", ctypes.c_bool),
        ("diff_rear", ctypes.c_bool),
        ("gas", ctypes.c_float),
        ("brake", ctypes.c_float),
        ("steering", ctypes.c_float),
        ("packet_number", ctypes.c_int32),
        ("packet_dropped", ctypes.c_int32),
        ("latency_mcs", ctypes.c_int32),
        ("latency_s", ctypes.c_int32)
    ]