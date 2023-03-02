import RPi.GPIO as GPIO
import time

class Vehicle(object):
    
    def __init__(self):
        self.indicator_left = 11
        self.indicator_right = 13
        self.high_beam = 15
        self.low_beam = 16
        self.brake_lights = 18
        self.driving = 12
        self.steering = 32
        self.gearbox = 33

        GPIO.setmode(GPIO.BOARD)

        GPIO.setup(self.indicator_left, GPIO.OUT)
        GPIO.setup(self.indicator_right, GPIO.OUT)
        GPIO.setup(self.high_lights, GPIO.OUT)
        GPIO.setup(self.low_lights, GPIO.OUT)
        GPIO.setup(self.brake_lights, GPIO.OUT)
        GPIO.setup(self.driving, GPIO.OUT)
        GPIO.setup(self.steering, GPIO.OUT)
        GPIO.setup(self.gearbox, GPIO.OUT)
        
        self.drive = GPIO.PWM(self.driving, 100)
        self.steer = GPIO.PWM(self.steering, 100)
        self.gear = GPIO.PWM(self.gearbox, 100)

    def control_lights(self, vehicle_data, control_data):
        if control_data.X:
            if not vehicle_data.low_beam:
                GPIO.output(self.low_beam, True)
                vehicle_data.low_beam = True
            else:
                GPIO.output(self.low_beam, False)
                vehicle_data.low_beam = False
        if control_data.Y:
            if not vehicle_data.high_beam:
                GPIO.output(self.high_beam, True)
                vehicle_data.high_beam = True
            else:
                GPIO.output(self.high_beam, False)
                vehicle_data.high_beam = False
        if control_data.RB:
            if not vehicle_data.indicator_right:
                GPIO.output(self.indicator_right, True)
                vehicle_data.indicator_right = True
            else:
                GPIO.output(self.indicator_right, False)
                vehicle_data.indicator_right = False
        if control_data.LB:
            if not vehicle_data.indicator_left:
                GPIO.output(self.indicator_left, True)
                vehicle_data.indicator_left = True
            else:
                GPIO.output(self.indicator_left, False)
                vehicle_data.indicator_left = False
        if control_data.LT > 0.05:
            GPIO.output(self.brake_lights, True)
        elif control_data.LT <= 0.05:
            GPIO.output(self.brake_lights, False)

        return vehicle_data

    def control_steering(self, duty_cycle):
        self.steer.start(int(duty_cycle*100.0))

    def control_vehicle(self, gas, brake):
        # check documentation for brake implementation
        self.drive.start(int(gas*100.0))

    def control_shift(self, gear_up, gear_down):
        # Check documentation for gearbox implementation
        pass