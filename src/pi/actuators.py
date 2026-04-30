import time
import RPi.GPIO as GPIO   # type: ignore

# Use BCM pin numbering
GPIO.setmode(GPIO.BCM)

DIR_PIN = 5   # D5 = BCM 5
STEP_PIN = 6  # D6 = BCM 6
PWM_FREQUENCY = 1000

stepperOfset = 0
step = 0

microMode = 16
steps = 200 * microMode


class actuators:

    def __init__(self, DIR):
        GPIO.setup(DIR_PIN, GPIO.OUT)
        GPIO.setup(STEP_PIN, GPIO.OUT)


    def stepper(self, direction, steps):
        GPIO.output(DIR_PIN, direction)
        global step
        for i in range(steps):
            GPIO.output(STEP_PIN, True)
            time.sleep(0.001)
            GPIO.output(STEP_PIN, False)
            time.sleep(0.001)
            step += 1 if direction == True else -1

    def setStepperOfset(self, pin):
        global stepperOfset
        GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

        steps = 0
        value = GPIO.input(pin)
        while value == 0:
            self.stepper(True, 1)
            value = GPIO.input(pin)
            steps += 1

        stepperOfset = steps
        return stepperOfset

    def stepAng(self, direction, angle):
        self.stepper(direction, steps // (360 // angle))

    def motor(self, in1_pin, in2_pin, speed):
        """Drive a DRV8871 single-channel H-bridge with two inputs.

        The DRV8871 accepts PWM on one input while the other input is held low.
        For forward motion, PWM is applied to IN1 and IN2 is low.
        For reverse, PWM is applied to IN2 and IN1 is low.

        Args:
            in1_pin: BCM pin connected to DRV8871 IN1.
            in2_pin: BCM pin connected to DRV8871 IN2.
            speed: from -100 to 100. Positive = forward, negative = reverse.

        Returns:
            A GPIO.PWM instance for the active pin, or None if speed == 0.
        """
        speed = max(-100, min(100, speed))
        GPIO.setup(in1_pin, GPIO.OUT)
        GPIO.setup(in2_pin, GPIO.OUT)

        if speed == 0:
            GPIO.output(in1_pin, GPIO.LOW)
            GPIO.output(in2_pin, GPIO.LOW)
            return None

        active_pin = in1_pin if speed > 0 else in2_pin
        inactive_pin = in2_pin if speed > 0 else in1_pin
        duty_cycle = abs(speed)

        GPIO.output(inactive_pin, GPIO.LOW)
        pwm = GPIO.PWM(active_pin, PWM_FREQUENCY)
        pwm.start(duty_cycle)
        return pwm


    def stop_pwm(self, pwm):
        """Stop the running PWM motor cleanly."""
        pwm.ChangeDutyCycle(0)
        pwm.stop()

    def servo(self, pin, angle):
        angle = max(0, min(180, angle))
        # Servo PWM: 50Hz, duty cycle 2.5% to 12.5% for 0-180 degrees
        duty_cycle = 2.5 + (angle / 180.0) * 10.0

        GPIO.setup(pin, GPIO.OUT)
        pwm = GPIO.PWM(pin, 50)  # 50Hz for servos
        pwm.start(duty_cycle)
        return pwm


    