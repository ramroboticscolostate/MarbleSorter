import argparse
import sys
from motor import MotorController, find_sabertooth_port
from drive import Drive

if sys.platform == "win32":
    import msvcrt
    def getKey():
        key = msvcrt.getwch()
        if key in ("\x00", "\xe0"):
            msvcrt.getwch()
            return ""
        return key
else:
    import tty, termios
    def getKey():
        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            return sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)


def main():

    parser = argparse.ArgumentParser(description="Robot keyboard controller")
    parser.add_argument("--mock", action="store_true", help="Run in mock mode (no hardware)")
    parser.add_argument("--speed", type=int, default=30, help="Drive speed 1-63 (default: 30)")
    parser.add_argument("--port", type=str, default=None, help="Serial port (e.g. /dev/ttyUSB0, COM3)")
    parser.add_argument("--list-ports", action="store_true", help="List available serial ports and exit")
    args = parser.parse_args()

    if args.list_ports:
        try:
            import serial.tools.list_ports
            ports = list(serial.tools.list_ports.comports())
            if ports:
                print("Available serial ports:")
                for p in ports:
                    print(f"  {p.device}: {p.description}")
                detected = find_sabertooth_port()
                if detected:
                    print(f"\nAuto-detect would pick: {detected}")
            else:
                print("No serial ports found")
        except ImportError:
            print("pyserial not installed // pip install pyserial")
        return

    with MotorController(mock=args.mock, port=args.port) as motor:
        drive = Drive(motor, speed=args.speed)

        commands = {
            "w": drive.forward,
            "s": drive.backward,
            "a": drive.left,
            "d": drive.right,
            " ": drive.stop,
        }

        print("Robot ready")
        print("Movement: w s a d | space = stop | +/- = speed | q = quit")
        print(f"Speed: {drive.speed}")

        try:
            while True:
                cmd = getKey()

                if cmd in ("q", "\x03", "\x1b"):
                    print("\nQuitting...")
                    drive.stop()
                    break
                elif cmd == "+":
                    drive.setSpeed(min(Drive.MAX_SPEED, drive.speed + 5))
                elif cmd == "-":
                    drive.setSpeed(max(1, drive.speed - 5))
                elif cmd in commands:
                    commands[cmd]()
                else:
                    #unknown commands  will be treated as stop
                    drive.stop()

        except KeyboardInterrupt:
            print("\nInterrupted")
            drive.stop()


if __name__ == "__main__":
    main()
