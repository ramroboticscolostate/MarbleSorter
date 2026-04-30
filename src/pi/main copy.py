import argparse
import sys
import time
from motor import MotorController, find_sabertooth_port
from drive import Drive
from pico import PicoColorReader
from actuators import Actuators

TIMEOUT = 0.1  # seconds — auto-stop if no key held within this window

if sys.platform == "win32":
    import msvcrt
    def getKey():
        end = time.time() + TIMEOUT
        while time.time() < end:
            if msvcrt.kbhit():
                key = msvcrt.getwch()
                if key in ("\x00", "\xe0"):
                    msvcrt.getwch()
                    return ""
                return key
            time.sleep(0.005)
        return None
else:
    import tty, termios, select
    def getKey():
        rlist, _, _ = select.select([sys.stdin], [], [], TIMEOUT)
        if rlist:
            return sys.stdin.read(1)
        return None


def list_ports():
    try:
        import serial.tools.list_ports   # type: ignore
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


def main():

    parser = argparse.ArgumentParser(description="Robot keyboard controller")

    args = addArguments(parser)

    if args.list_ports:
        list_ports()
        return

    pico = None
    if not args.no_pico:
        try:
            pico = PicoColorReader(port=args.pico_port)
        except RuntimeError as e:
            print(f"ERROR: could not connect to Pico: {e}")
            print("Continuing without color reading. Use --no-pico to suppress this.")

    with MotorController(mock=args.mock, port=args.port) as motor:
        drive = Drive(motor, speed=args.speed)

        commands = {
            "w": drive.forward,
            "s": drive.backward,
            "a": drive.left,
            "d": drive.right,
            "z": drive.spinLeft,
            "x": drive.spinRight,
            " ": drive.stop,
        }

        

        print("Robot ready")
        print("Hold w/a/s/d to move, z/x to spin | release to stop | +/- = speed | q = quit")
        print(f"Speed: {drive.speed}")

        if sys.platform != "win32":
            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            tty.setraw(fd)

        try:
            moving = False
            while True:
                cmd = getKey()

                if cmd in ("q", "\x03", "\x1b"):
                    print("\nQuitting...")
                    drive.stop()
                    break
                elif cmd == "+":
                    drive.set_speed(min(Drive.MAX_SPEED, drive.speed + 5))
                elif cmd == "-":
                    drive.set_speed(max(1, drive.speed - 5))
                elif cmd in commands:
                    commands[cmd]()
                    moving = True
                else:
                    if moving:
                        drive.stop()
                        moving = False

        except KeyboardInterrupt:
            print("\nInterrupted")
            drive.stop()
        finally:
            if sys.platform != "win32":
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
            if pico:
                pico.close()

# FOR DEBUGGING IN CMD PROMPT python main.py --ARGUMENT
def addArguments(parser):
    parser.add_argument("--mock", action="store_true", help="Run in mock mode (no hardware)")
    parser.add_argument("--speed", type=int, default=30, help="Drive speed 1-63 (default: 30)")
    parser.add_argument("--port", type=str, default=None, help="Serial port (e.g. /dev/ttyUSB0, COM3)")
    # WHen linking port this can help troubleshoot sabertooth conn. CHECK LINE 33 MOTOR.py if continous no connection
    parser.add_argument("--list-ports", action="store_true", help="List available serial ports and exit")
    parser.add_argument("--pico-port", type=str, default=None, help="Serial port for the Pico (e.g. /dev/ttyACM0, COM4)")
    parser.add_argument("--no-pico", action="store_true", help="Disable Pico color reader")
    return parser.parse_args()



if __name__ == "__main__":
    main()
