import pigpio
import time

SERVO = 12

pi = pigpio.pi()

pi.set_servo_pulsewidth(SERVO, 1000)

time.sleep(1)

pi.set_servo_pulsewidth(SERVO, 2000)

time.sleep(1)

pi.set_servo_pulsewidth(SERVO, 1100)

time.sleep(1)

pi.set_servo_pulsewidth(SERVO, 0)

pi.stop()