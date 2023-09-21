import time
from gpiozero import Servo, DigitalOutputDevice, Buzzer
from gpiozero.pins.pigpio import PiGPIOFactory
from identifier_mapping import TDTP_IDENTIFIERS

class Vehicle(object):
    """A controller class for the Traxxas TRX4 Model
    
    This class contains Raspberry Pi Pin mapping and functions to control
    the Traxxas TRX4 Model via a Raspberry Pi. Steering and driving functionality
    is given as well as a self made lighting assembly with an additional horn.
    """
    def __init__(self):
        self.pin_factory = PiGPIOFactory()
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
        self.prev_indicator_left_status = False
        self.indicator_right_status = False
        self.prev_indicator_right_status = False
        self.high_beam_status = False
        self.prev_high_beam_status = False
        self.low_beam_status = False
        self.prev_low_beam_status = False
        self.brake_lights_status = False
        self.horn_status = False

        self.indicator_left_output = DigitalOutputDevice(pin=self.indicator_left, pin_factory=self.pin_factory)
        self.indicator_right_output = DigitalOutputDevice(pin=self.indicator_right, pin_factory=self.pin_factory)
        self.high_beam_output = DigitalOutputDevice(pin=self.high_beam, pin_factory=self.pin_factory)
        self.low_beam_output = DigitalOutputDevice(pin=self.low_beam, pin_factory=self.pin_factory)
        self.brake_lights_output = DigitalOutputDevice(pin=self.brake_lights, pin_factory=self.pin_factory)
        self.day_light_output = DigitalOutputDevice(pin=self.day_light, pin_factory=self.pin_factory)
        self.horn_output = Buzzer(pin=self.horn, pin_factory=self.pin_factory)

        self.drive = Servo(self.driving, pin_factory=self.pin_factory)
        self.steer = Servo(self.steering, pin_factory=self.pin_factory)

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
        if identifier == "Lowbeam":
            if data > 0 and not self.prev_low_beam_status:
                if not self.low_beam_status:
                    self.low_beam_output.on()
                    self.low_beam_status = True
                else:
                    self.low_beam_output.off()
                    self.low_beam_status = False
            self.prev_low_beam_status = data
        if identifier == "Highbeam":
            if data > 0 and not self.prev_high_beam_status:
                if not self.high_beam_status:
                    self.high_beam_output.on()
                    self.high_beam_status = True
                else:
                    self.high_beam_output.off()
                    self.high_beam_status = False
            self.prev_high_beam_status = data
        if identifier == "Indicator_R":
            if data > 0 and not self.prev_indicator_right_status:
                if not self.indicator_right_status:
                    self.indicator_right_output.on()
                    self.indicator_right_status = True
                else:
                    self.indicator_right_output.off()
                    self.indicator_right_status = False
            self.prev_indicator_right_status = data
        if identifier == "Indicator_L":
            if data > 0 and not self.prev_indicator_left_status:
                if not self.indicator_left_status:
                    self.indicator_left_output.on()
                    self.indicator_left_status = True
                else:
                    self.indicator_left_output.off()
                    self.indicator_left_status = False
            self.prev_indicator_left_status = data
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
