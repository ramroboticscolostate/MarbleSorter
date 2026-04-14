import time

try:
    import serial
    import serial.tools.list_ports
    SERIAL_AVAILABLE = True
except ImportError:
    SERIAL_AVAILABLE = False


def find_sabertooth_port():
    """Scan serial ports and return the best candidate for the Sabertooth."""
    ports = serial.tools.list_ports.comports()
    for port in ports:
        desc = (port.description or "").lower()
        if any(kw in desc for kw in ["usb", "uart", "serial", "sabertooth"]):
            return port.device
    return None


class MotorController:

    def __init__(self, mock=False, port=None):

        self.mock = mock

        if self.mock:
            print("MotorController running in MOCK mode")
        else:
            if not SERIAL_AVAILABLE:
                raise RuntimeError("Pyserial missing // pip install pyserial")

            resolved_port = port or find_sabertooth_port() or "/dev/serial0"

            try:
                print(f"Connecting to Sabertooth on {resolved_port}...")
                self.ser = serial.Serial(resolved_port, 9600, timeout=1)
                time.sleep(2)
                print("Connection Success")
            except serial.SerialException as ex:
                available = [p.device for p in serial.tools.list_ports.comports()]
                raise RuntimeError(
                    f"Failed to connect on {resolved_port}: {ex}\n"
                    f"Available ports: {available if available else 'none found'}\n"
                    f"Tip: run with --list-ports to see all ports, then use --port <port>"
                )

    def drive(self, left, right):

        # Clamp first so mock and real behave the same
        left = max(-63, min(63, left))
        right = max(-63, min(63, right))

        if self.mock:
            print(f"MOCK drive: left={left}, right={right}", end="\r\n")
            return

        m1 = 64 + left
        m2 = 192 + right

        self.ser.write(bytes([m1, m2]))

    def stop(self):

        self.drive(0, 0)

    def close(self):

        self.stop()
        if not self.mock and hasattr(self, "ser") and self.ser.is_open:
            self.ser.close()
            print("Serial connection closed")

    def __enter__(self):

        return self

    def __exit__(self, excType, excVal, excTb):

        self.close()
