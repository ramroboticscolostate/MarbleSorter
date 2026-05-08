import threading

try: 
    import serial  # type: ignore
    import serial.tools.list_ports  # type: ignore
    SERIAL_AVAILABLE = True
except ImportError:
    SERIAL_AVAILABLE = False


def find_pico_port():
    for port in serial.tools.list_ports.comports():
        desc = (port.description or "").lower()
        if any(kw in desc for kw in ["pico", "circuitpython", "micropython", "cdc"]):
            return port.device
    return None


class PicoColorReader:

    def __init__(self, port=None):
        if not SERIAL_AVAILABLE:
            raise RuntimeError("pyserial missing // pip install pyserial")

        resolved_port = port or find_pico_port() or "/dev/ttyACM0"

        try:
            print(f"Connecting to Pico on {resolved_port}...")
            self.ser = serial.Serial(resolved_port, 115200, timeout=1)
            print("Pico connected")
        except serial.SerialException as ex:
            available = [p.device for p in serial.tools.list_ports.comports()]
            raise RuntimeError(
                f"Failed to connect to Pico on {resolved_port}: {ex}\n"
                f"Available ports: {available if available else 'none found'}\n"
                f"Tip: use --pico-port <port> to specify and update manually"
            )

        self.color = None
        self._lock = threading.Lock()
        self._thread = threading.Thread(target=self._read_loop, daemon=True)
        self._thread.start()

    def _read_loop(self):
        while self.ser.is_open:
            try:
                line = self.ser.readline().decode("utf-8", errors="ignore").strip()
                if line.startswith("Color:"):
                    # "Color: Red | RGB:(255, 0, 0)"
                    color_name = line.split(":")[1].split("|")[0].strip()
                    with self._lock:
                        self.color = color_name
                    print(f"\r\n[Pico] {line}", end="\r\n")
            except Exception as e:
                print(f"Error reading from Pico serial port: {e}")
                break

    def refresh(self):
        """Manually trigger a color read (if Pico is set to only send on demand)"""
        if self.ser.is_open:
            self.ser.write(b"\x04")

    def get_color(self):
        with self._lock:
            return self.color

    def close(self):
        if hasattr(self, "ser") and self.ser.is_open:
            self.ser.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
