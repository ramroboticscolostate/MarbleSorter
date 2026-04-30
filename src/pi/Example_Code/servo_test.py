from gpiozero import Servo
import time

# Connect the servo signal wire to a PWM-capable GPIO pin.
# Change this pin number to match your wiring.
SERVO_PIN = 4

# Some servos need a wider pulse range than the default.
# Adjust min_pulse_width and max_pulse_width if your servo still
# does not reach its full mechanical travel.
servo = Servo(SERVO_PIN, min_pulse_width=0.0005, max_pulse_width=0.0025)

try:
    while True:
        print("Moving servo to minimum position...")
        servo.min()
        time.sleep(1)

        print("Moving servo to center position...")
        servo.mid()
        time.sleep(1)

        print("Moving servo to maximum position...")
        servo.max()
        time.sleep(3)

        print("Swegiteping servo smoothly...")
        for position in [i / 10 for i in range(-10, 11)]:
            servo.value = position
            time.sleep(0.05)

        for position in [i / 10 for i in range(10, -11, -1)]:
            servo.value = position
            time.sleep(0.05)

        print("Servo sweep cycle complete. Press Ctrl+C to stop.")

except KeyboardInterrupt:
    servo.detach()
    print("Servo test stopped")
