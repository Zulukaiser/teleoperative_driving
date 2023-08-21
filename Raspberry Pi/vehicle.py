import time
from gpiozero import Servo, DigitalOutputDevice, Buzzer
from identifier_mapping import TDTP_IDENTIFIERS


class Vehicle(object):
    """A controller class for the Traxxas TRX4 Model
    
    This class contains Raspberry Pi Pin mapping and functions to control
    the Traxxas TRX4 Model via a Raspberry Pi. Steering and driving functionality
    is given as well as a self made lighting assembly with an additional horn.
    """
    def __init__(self):
        self.indicator_left = 23
        self.indicator_right = 24
        self.day_light = 25
        self.high_beam = 7
        self.low_beam = 8
        self.brake_lights = 1
        self.horn = 4
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
        self.day_light_output = DigitalOutputDevice(pin=self.day_light)
        self.horn_output = Buzzer(pin=self.horn)

        self.drive = Servo(self.driving)
        self.steer = Servo(self.steering)

    def control_vehicle(self, control_data: tuple) -> None:
        """Function for controlling the TRX4's lighting system, steering, driving and the horn.

        Model control with control_data as instructions of what functionality and what values
        
        Parameters:
        -----------
        control_data : tuple()
            A tuple that contains the identifier (int), data (any), package_id (int) and timestamp (int)
        
        return: None
        """
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
        elif identifier == "Brake" and data <= 0.05:
            self.brake_lights_output.off()

        if identifier == "Gas":
            self.drive.value = data
        if identifier == "SWA":
            self.steer.value = data
