USE_MOCK = True

if not USE_MOCK:
    import serial
    import time


class MotorController:

    def __init__(self):
        if USE_MOCK:
            print("MotorController running in MOCK mode")
        else:
            print("Connecting to Sabertooth...")
            self.ser = serial.Serial("/dev/serial0", 9600)
            time.sleep(2)
            print("Connected")

    def drive(self, left, right):
        if USE_MOCK:
            print(f"DRIVE left={left} right={right}")
        else:
            left = max(-63, min(63, left))
            right = max(-63, min(63, right))

            m1 = 64 + left
            m2 = 192 + right

            self.ser.write(bytes([m1]))
            self.ser.write(bytes([m2]))

    def stop(self):
        self.drive(0, 0)