from inputs import get_gamepad
import math
import threading

class XboxController(object):
    MAX_TRIG_VAL = math.pow(2, 8)
    MAX_JOY_VAL = math.pow(2, 15)

    def __init__(self):

        self.LeftJoystickY = 0.0
        self.LeftJoystickX = 0.0
        self.RightJoystickY = 0.0
        self.RightJoystickX = 0.0
        self.LeftTrigger = 0.0
        self.RightTrigger = 0.0
        self.LeftBumper = 0.0
        self.RightBumper = 0.0
        self.A = 0.0
        self.X = 0.0
        self.Y = 0.0
        self.B = 0.0
        self.LeftThumb = 0.0
        self.RightThumb = 0.0
        self.Back = 0.0
        self.Start = 0.0
        self.LeftDPad = 0.0
        self.RightDPad = 0.0
        self.UpDPad = 0.0
        self.DownDPad = 0.0

        self._monitor_thread = threading.Thread(target=self._monitor_controller, args=())
        self._monitor_thread.daemon = True
        self._monitor_thread.start()

    def read(self): # return the buttons/triggers that you care about in this methode
        joy_left_x = self.LeftJoystickX
        joy_left_y = self.LeftJoystickY
        joy_right_x = self.RightJoystickX
        joy_right_y = self.RightJoystickY
        joy_left_thumb = self.LeftThumb
        joy_right_thumb = self.RightThumb
        action_a = self.A
        action_b = self.B # b=1, x=2
        action_x = self.X
        action_y = self.Y
        rb = self.RightBumper
        rt = self.RightTrigger
        lb = self.LeftBumper
        lt = self.LeftTrigger
        d_up = self.UpDPad
        d_down = self.DownDPad
        d_left = self.LeftDPad
        d_right = self.RightDPad
        start = self.Start
        back = self.Back
        #return f"Joy-left-X: {joy_left_x}, Joy-left-Y: {joy_left_y}, Joy-left-thumb: {joy_left_thumb}, Joy-right-X: {joy_right_x}, Joy-right-Y: {joy_right_y}, Joy-right-thumb: {joy_right_thumb}, A: {action_a}, X: {action_x}, Y: {action_y}, B: {action_b}, RB: {rb}, RT: {rt}, LB: {lb}, LT: {lt}, d-up: {d_up}, d_left {d_left}, d-down: {d_down}, d-right: {d_right}, Start: {start}, Back: {back}"
        return {
            "A": bool(action_a),
            "X": bool(action_x),
            "Y": bool(action_y),
            "B": bool(action_b),
            "RB": bool(rb),
            "RT": float(rt),
            "LB": bool(lb),
            "LT": float(lt),
            "d-up": bool(d_up),
            "d-left": bool(d_left),
            "d-down": bool(d_down),
            "d-right": bool(d_right),
            "LJoyThumb": bool(joy_left_thumb),
            "RJoyThumb": bool(joy_right_thumb),
            "Start": bool(start),
            "Back": bool(back),
            "LJoyX": float(joy_left_x),
            "LJoyY": float(joy_left_y),
            "RJoyX": float(joy_right_x),
            "RJoyY": float(joy_right_y)
            }

    def _monitor_controller(self):
        while True:
            events = get_gamepad()
            for event in events:
                if event.code == 'ABS_Y':
                    self.LeftJoystickY = event.state / XboxController.MAX_JOY_VAL # normalize between -1 and 1
                elif event.code == 'ABS_X':
                    self.LeftJoystickX = event.state / XboxController.MAX_JOY_VAL # normalize between -1 and 1
                elif event.code == 'ABS_RY':
                    self.RightJoystickY = event.state / XboxController.MAX_JOY_VAL # normalize between -1 and 1
                elif event.code == 'ABS_RX':
                    self.RightJoystickX = event.state / XboxController.MAX_JOY_VAL # normalize between -1 and 1
                elif event.code == 'ABS_Z':
                    self.LeftTrigger = event.state / XboxController.MAX_TRIG_VAL # normalize between 0 and 1
                elif event.code == 'ABS_RZ':
                    self.RightTrigger = event.state / XboxController.MAX_TRIG_VAL # normalize between 0 and 1
                elif event.code == 'BTN_TL':
                    self.LeftBumper = event.state
                elif event.code == 'BTN_TR':
                    self.RightBumper = event.state
                elif event.code == 'BTN_SOUTH':
                    self.A = event.state
                elif event.code == 'BTN_NORTH':
                    self.Y = event.state #previously switched with X
                elif event.code == 'BTN_WEST':
                    self.X = event.state #previously switched with Y
                elif event.code == 'BTN_EAST':
                    self.B = event.state
                elif event.code == 'BTN_THUMBL':
                    self.LeftThumb = event.state
                elif event.code == 'BTN_THUMBR':
                    self.RightThumb = event.state
                elif event.code == 'BTN_START':
                    self.Back = event.state
                elif event.code == 'BTN_SELECT':
                    self.Start = event.state
                elif event.code == 'ABS_HAT0Y':
                    if event.state == -1:
                        self.UpDPad = 1
                    elif event.state == 1:
                        self.DownDPad = 1
                    else:
                        self.UpDPad = 0
                        self.DownDPad = 0
                elif event.code == 'ABS_HAT0X':
                    if event.state == 1:
                        self.RightDPad = 1
                    elif event.state == -1:
                        self.LeftDPad = 1
                    else:
                        self.RightDPad = 0
                        self.LeftDPad = 0

def get_controller_data():
    joy = XboxController()
    while True:
        print(joy.read())

if __name__ == '__main__':
    get_controller_data()