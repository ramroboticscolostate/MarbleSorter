from gpiozero import Servo
import time

# Connect the servo signal wire to a PWM-capable GPIO pin.
# Change this pin number to match your wiring.
SERVO_PIN = 4

servo = Servo(SERVO_PIN)

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
        time.sleep(1)

        print("Sweeping servo smoothly...")
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
