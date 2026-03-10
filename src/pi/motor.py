
import time
    
try:
    import serial
    SERIAL_AVAILABLE = True
except ImportError:
    SERIAL_AVAILABLE = False


class MotorController:

    def __init__(self, mock =False):

        self.mock = mock
        if self.mock:
            print("MotorController running in MOCK mode")
        else:
            if not SERIAL_AVAILABLE:
                raise RuntimeError("Pyserial missing // pip install pyserial")
            try:
                print("Connecting to Sabertooth...")
                self.ser = serial.Serial("/dev/serial0", 9600, timeout=1)
                time.sleep(2)
                print("Connection Success")
            except serial.SerialException as ex:
                raise RuntimeError(f"Failed connection to Sabertooth: {ex}")

    def drive(self, left, right):

        if self.mock:
            print(f"DRIVE left={left} right={right}")
            return
       
        left = max(-63, min(63, left))
        right = max(-63, min(63, right))

        m1 = 64 + left
        m2 = 192 + right

        self.ser.write(bytes([m1, m2]))

    def stop(self):

        self.drive(0, 0)

    def close(self):

        self.stop()
        if not self.mock and hasattr(self, "ser") and self.ser.is_open:
            self.ser.close()
            print("Serial Connection closed")

    def __enter__(self):

        return self
    
    def __exit__(self, excType, excVal, excTb):

        self.close()
    