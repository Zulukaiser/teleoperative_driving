import RPi.GPIO as GPIO
import time

class vehicle(object):
    
    def __init__(self):
        self.blinker_left = 11
        self.blinker_right = 13
        self.flash_lights = 15
        self.driving_lights = 16
        self.brake_lights = 18
        self.driving = 12
        self.steering = 32
        self.gearbox = 33

        GPIO.setmode(GPIO.BOARD)

        GPIO.setup(self.blinker_left, GPIO.OUT)
        GPIO.setup(self.blinker_right, GPIO.OUT)
        GPIO.setup(self.flash_lights, GPIO.OUT)
        GPIO.setup(self.driving_lights, GPIO.OUT)
        GPIO.setup(self.brake_lights, GPIO.OUT)
        GPIO.setup(self.driving, GPIO.OUT)
        GPIO.setup(self.steering, GPIO.OUT)
        GPIO.setup(self.gearbox, GPIO.OUT)
        
        self.drive = GPIO.PWM(self.driving, 100)
        self.steer = GPIO.PWM(self.steering, 100)
        self.gear = GPIO.PWM(self.gearbox, 100)

    def control_lights(self, data: dict):
        for light in data:
            state = light['state']
            pin = light['pin']
            if state and pin and light not in ['blinker_left', 'blinker_right']:
                GPIO.output(pin, False)
                light['state'] = False
            elif not state and pin and light not in ['blinker_left', 'blinker_right']:
                GPIO.output(pin, True)
                light['state'] = True
            elif state and pin:
                GPIO.output(pin, False)
                light['state'] = False
                time.sleep(1)
            elif not state and pin:
                GPIO.output(pin, True)
                light['state'] = True
                time.sleep(1)
            else:
                GPIO.output(pin, False)
                light['state'] = True
        return data

    def control_steering(self, duty_cycle):
        self.steer.start(duty_cycle)

    def control_vehicle(self, gas, brake):
        self.drive.start(int(gas*100.0))

    def control_shift(self, gear_up, gear_down):
        # Check documentation for gearbox in vehicle
        pass