import RPi.GPIO as GPIO # type: ignore
import time

GPIO.setmode(GPIO.BCM)
motor_pin = 12
GPIO.setup(motor_pin, GPIO.OUT)

pwm = GPIO.PWM(motor_pin, 1000)  # 1kHz frequency
pwm.start(0)  # Start with 0% duty cycle

try:
    while True:
        print("Ramp up duty cycle from 0% to 100%")
        for duty in range(0, 101, 5):
            pwm.ChangeDutyCycle(duty)
            time.sleep(0.1)
        print("Ramp down duty cycle from 100% to 0%")
        for duty in range(100, -1, -5):
            pwm.ChangeDutyCycle(duty)
            time.sleep(0.1)
except KeyboardInterrupt:
    print("Motor test stopped")
    pwm.stop()
    GPIO.cleanup()