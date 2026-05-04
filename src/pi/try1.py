import argparse
import sys
import time

from motor import MotorController, find_sabertooth_port
from drive import Drive
from pico import PicoColorReader
from actuators import Actuators

TIMEOUT = 0.1  # keyboard polling timeout


# ----------------------------
# KEYBOARD INPUT
# ----------------------------
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


# ----------------------------
# ARGUMENTS
# ----------------------------
def addArguments(parser):
    parser.add_argument("--mock", action="store_true")
    parser.add_argument("--speed", type=int, default=30)
    parser.add_argument("--port", type=str, default=None)
    parser.add_argument("--list-ports", action="store_true")
    parser.add_argument("--pico-port", type=str, default=None)
    parser.add_argument("--no-pico", action="store_true")
    return parser.parse_args()


# ----------------------------
# MAIN
# ----------------------------
def main():

    parser = argparse.ArgumentParser()
    args = addArguments(parser)

    if args.list_ports:
        import serial.tools.list_ports
        ports = list(serial.tools.list_ports.comports())
        for p in ports:
            print(p.device, p.description)
        return

    # ----------------------------
    # PICO SETUP
    # ----------------------------
    pico = None
    if not args.no_pico:
        try:
            pico = PicoColorReader(port=args.pico_port)
        except Exception as e:
            print("Pico error:", e)
            pico = None

    # ----------------------------
    # MOTOR + DRIVE SETUP
    # ----------------------------
    with MotorController(mock=args.mock, port=args.port) as motor:

        drive = Drive(motor, speed=args.speed)
        act = Actuators()

        # ----------------------------
        # STATE VARIABLES
        # ----------------------------
        brush_on = False
        conveyor_on = False
        last_color = None

        print("\nRobot Ready")
        print("WASD = drive | Z/X = spin | SPACE = stop")
        print("B = brush toggle | C = conveyor toggle")
        print("+/- = speed | Q = quit\n")

        # ----------------------------
        # KEY COMMAND MAP
        # ----------------------------
        commands = {
            "w": drive.forward,
            "s": drive.backward,
            "a": drive.left,
            "d": drive.right,
            "z": drive.spinLeft,
            "x": drive.spinRight,
            " ": drive.stop,
        }

        # ----------------------------
        # RAW MODE (LINUX)
        # ----------------------------
        if sys.platform != "win32":
            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            tty.setraw(fd)

        try:
            moving = False

            while True:

                cmd = getKey()

                # ----------------------------
                # EXIT
                # ----------------------------
                if cmd in ("q", "\x03", "\x1b"):
                    print("\nShutting down...")
                    drive.stop()
                    break

                # ----------------------------
                # SPEED CONTROL
                # ----------------------------
                elif cmd == "+":
                    drive.set_speed(min(Drive.MAX_SPEED, drive.speed + 5))

                elif cmd == "-":
                    drive.set_speed(max(1, drive.speed - 5))

                # ----------------------------
                # TOGGLES
                # ----------------------------
                elif cmd == "b":
                    brush_on = not brush_on
                    print(f"Brush: {'ON' if brush_on else 'OFF'}")

                elif cmd == "c":
                    conveyor_on = not conveyor_on
                    print(f"Conveyor: {'ON' if conveyor_on else 'OFF'}")

                # ----------------------------
                # DRIVE COMMANDS
                # ----------------------------
                elif cmd in commands:
                    commands[cmd]()
                    moving = True

                else:
                    if moving:
                        drive.stop()
                        moving = False

                # ----------------------------
                # ACTUATOR CONTROL LOOP
                # ----------------------------

                # Brush roller (GPIO example pins)
                if brush_on:
                    act.motor(17, 27, 60)
                else:
                    act.motor(17, 27, 0)

                # Conveyor belt
                if conveyor_on:
                    act.motor(22, 23, 60)
                else:
                    act.motor(22, 23, 0)

                # ----------------------------
                # PICO COLOR EVENT TRIGGER
                # ----------------------------
                if pico:
                    color = pico.get_color()

                    if color and color != last_color:
                        print(f"\nColor detected: {color}")

                        # SERVO ACTION
                        servo = act.servo(pin=18, angle=90)
                        time.sleep(0.5)
                        servo.ChangeDutyCycle(0)
                        servo.stop()

                        # STEPPER ACTION (adjust steps later)
                        act.stepper(True, 200)

                        last_color = color

        except KeyboardInterrupt:
            print("\nInterrupted")
            drive.stop()

        finally:
            if sys.platform != "win32":
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
            if pico:
                pico.close()


# ----------------------------
# RUN
# ----------------------------
if __name__ == "__main__":
    main()
    