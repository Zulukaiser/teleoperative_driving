import time
from gpiozero import Servo, DigitalOutputDevice, Buzzer
from identifier_mapping import TDTP_IDENTIFIERS


class Vehicle(object):
    def __init__(self):
        self.indicator_left = 11
        self.indicator_right = 14
        self.high_beam = 15
        self.low_beam = 16
        self.brake_lights = 18
        self.horn = 19
        self.driving = 12
        self.steering = 13

        self.indicator_left_status = False
        self.indicator_right_status = False
        self.high_beam_status = False
        self.low_beam_status = False
        self.brake_lights_status = False
        self.horn_status = False

        self.indicator_left_output = DigitalOutputDevice(pin=self.indicator_left)
        self.indicator_right_output = DigitalOutputDevice(pin=self.indicator_right)
        self.high_beam_output = DigitalOutputDevice(pin=self.high_beam)
        self.low_beam_output = DigitalOutputDevice(pin=self.low_beam)
        self.brake_lights_output = DigitalOutputDevice(pin=self.brake_lights)
        self.horn_output = Buzzer(pin=self.horn)

        self.drive = Servo(self.driving)
        self.steer = Servo(self.steering)

    def control_vehicle(self, control_data):
        identifier = TDTP_IDENTIFIERS[control_data[0]]
        data = control_data[1]
        if identifier == "Lowbeam" and data > 0:
            if not self.low_beam_status:
                self.low_beam_output.on()
                self.low_beam_status = True
            else:
                self.low_beam_output.off()
                self.low_beam_status = False
        if identifier == "Highbeam" and data > 0:
            if not self.high_beam_status:
                self.high_beam_output.on()
                self.high_beam_status = True
            else:
                self.high_beam_output.off()
                self.high_beam_status = False
        if identifier == "Indicator_R" and data > 0:
            if not self.indicator_right_status:
                self.indicator_right_output.blink(
                    on_time=1, off_time=1, n=None, background=True
                )
                self.indicator_right_status = True
            else:
                self.indicator_right_output.off()
                self.indicator_right_status = False
        if identifier == "Indicator_L" and data > 0:
            if not self.indicator_left_status:
                self.indicator_left_output.blink(
                    on_time=1, off_time=1, n=None, background=True
                )
                self.indicator_left_status = True
            else:
                self.indicator_left_output.off()
                self.indicator_left_status = False
        if identifier == "Horn" and data > 0:
            if not self.horn_status:
                self.horn_output.on()
                self.horn_status = True
            else:
                self.horn_output.off()
                self.horn_status = False
        if identifier == "Brake" and data > 0.05:
            self.brake_lights_output.on()
        elif identifier == "Lowbeam" and data <= 0.05:
            self.brake_lights_output.off()

        if identifier == "Gas":
            self.drive.value = data
        if identifier == "SWA":
            self.steer.value = data
