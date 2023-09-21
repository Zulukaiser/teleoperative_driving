import pygame
import threading

pygame.init()

clock = pygame.time.Clock()


class ControlInput:
    def __init__(self):
        self.done = False
        self.joystick = None
        self.joysticks = {}
        self.joy = None
        self.gas = 0
        self.brake = 0
        self.swa = 0
        self.lowbeam = 0
        self.highbeam = 0
        self.horn = 0
        self.indicator_l = 0
        self.indicator_r = 0

        self._monitor_thread = threading.Thread(
            target=self._monitor_controller, args=()
        )
        self._monitor_thread.daemon = True
        self._monitor_thread.start()

    def read(self):
        gas = self.gas
        brake = self.brake
        swa = self.swa
        lowbeam = self.lowbeam
        highbeam = self.highbeam
        horn = self.horn
        indicator_l = self.indicator_l
        indicator_r = self.indicator_r

        return {
            "Gas": float(gas),
            "Brake": float(brake),
            "SWA": float(swa),
            "Lowbeam": bool(lowbeam),
            "Highbeam": bool(highbeam),
            "Horn": bool(horn),
            "Indicator_L": bool(indicator_l),
            "Indicator_R": bool(indicator_r),
        }

    def _monitor_controller(self):
        self.done = False
        pedals = pygame.joystick.Joystick(2)
        wheel = pygame.joystick.Joystick(0)
        while not self.done:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.done = True

                if event.type == pygame.JOYBUTTONDOWN:
                    if event.button == 0:
                        self.joystick = self.joysticks[event.instance_id]

                if event.type == pygame.JOYBUTTONUP:
                    del self.joysticks[event.instance_id]

                if event.type == pygame.JOYDEVICEADDED:
                    self.joy = pygame.joystick.Joystick(event.device_index)
                    self.joysticks[self.joy.get_instance_id()] = self.joy

                if event.type == pygame.JOYDEVICEREMOVED:
                    del self.joysticks[event.instance_id]

                self.gas = (pedals.get_axis(0) + 1) / 2
                self.brake = (pedals.get_axis(1) + 1) / 2

                self.swa = wheel.get_axis(0)
                self.lowbeam = wheel.get_button(7)
                self.highbeam = wheel.get_button(11)
                self.horn = wheel.get_button(2)
                self.indicator_l = wheel.get_button(60)
                self.indicator_r = wheel.get_button(61)

                clock.tick(400)

    def stop(self):
        self.done = True
