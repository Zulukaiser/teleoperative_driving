import smbus2
import time
import threading

class IMU(object):
    def __init__(self):
        self.ADDRESS = 0x1D
        self.bus = smbus2.SMBus(1)
        self.xAccl = 0
        self.yAccl = 0
        self.zAccl = 0

    def _monitor_data(self):
        self.bus.write_byte_data(self.ADDRESS, 0x2A, 0x00)
        self.bus.write_byte_data(self.ADDRESS, 0x2A, 0x01)
        self.bus.write_byte_data(self.ADDRESS, 0x0E, 0x01)
        data = self.bus.read_i2c_block_data(self.ADDRESS, 0x00, 7)
        self.xAccl = (data[1] * 256 + data[2]) / 16
        if self.xAccl > 2047:
            self.xAccl -= 4096
        self.yAccl = (data[3] * 256 + data[4]) / 16
        if self.yAccl > 2047:
            self.yAccl -= 4096
        self.zAccl = (data[5] * 256 + data[6]) / 16
        if self.zAccl > 2047:
            self.zAccl -= 4096

        self.xAccl /= 1000
        self.yAccl /= 1000
        self.yAccl *= -1
        self.zAccl /= 1000
        self.zAccl *= -1
        time.sleep(0.2)

    def get_acceleration(self) -> dict:
        self._monitor_data()
        return {"IMU_AX": self.xAccl, "IMU_AY": self.yAccl, "IMU_AZ": self.zAccl}
    
if __name__ == "__main__":
    acc = IMU()
    while True:
        print(acc.get_acceleration())
        time.sleep(1)