import argparse
import sys
import time
import threading

import RPi.GPIO as GPIO

from motor import MotorController, find_sabertooth_port
from drive import Drive
from pico import PicoColorReader, find_pico_port

TIMEOUT = 0.1  # seconds — auto-stop if no key held within this window


# =========================================================
# GPIO SETUP
# =========================================================
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# ---- Motor driver pins (brush + conveyor) ----
BRUSH_IN1 = 12
BRUSH_IN2 = 27

CONV_IN1 = 18
CONV_IN2 = 23

# ---- Stepper ----
STEP_PIN = 6
DIR_PIN = 5

# ---- Servo ----
SERVO_PIN = 4

GPIO.setup([BRUSH_IN1, BRUSH_IN2, CONV_IN1, CONV_IN2], GPIO.OUT)
GPIO.setup(STEP_PIN, GPIO.OUT)
GPIO.setup(DIR_PIN, GPIO.OUT)
GPIO.setup(SERVO_PIN, GPIO.OUT)


# =========================================================
# PWM SETUP (PERSISTENT)
# =========================================================
brush_pwm = GPIO.PWM(BRUSH_IN1, 1000)
conv_pwm  = GPIO.PWM(CONV_IN1,  1000)
servo_pwm = GPIO.PWM(SERVO_PIN,   50)

brush_pwm.start(0)
conv_pwm.start(0)
servo_pwm.start(0)


# =========================================================
# STEPPER FUNCTION
# =========================================================
def stepper(steps, direction=True, delay=0.001):
    GPIO.output(DIR_PIN, direction)
    for _ in range(steps):
        GPIO.output(STEP_PIN, True)
        time.sleep(delay)
        GPIO.output(STEP_PIN, False)
        time.sleep(delay)


# =========================================================
# KEY INPUT
# =========================================================
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


# =========================================================
# LIST PORTS
# =========================================================
def list_ports():
    try:
        import serial.tools.list_ports  # type: ignore
        ports = list(serial.tools.list_ports.comports())
        if ports:
            print("Available serial ports:")
            for p in ports:
                print(f"  {p.device}: {p.description}")
            sabertooth = find_sabertooth_port()
            print(f"\nSabertooth auto-detect would pick: {sabertooth or 'none found'}")
            pico = find_pico_port()
            print(f"Pico auto-detect would pick:       {pico or 'none found'}")
        else:
            print("No serial ports found")
    except ImportError:
        print("pyserial not installed // pip install pyserial")


# =========================================================
# MAIN
# =========================================================
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

        brush_on  = False
        conveyor_on = False
        last_color  = None
        sorting     = False

        print("Robot ready")
        print("Hold w/a/s/d to move, z/x to spin | B brush | C conveyor | +/- speed | q = quit")
        print(f"Speed: {drive.speed}")

        if sys.platform != "win32":
            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            tty.setraw(fd)

        try:
            moving = False
            while True:
                cmd = getKey()

                # ---------------- EXIT ----------------
                if cmd in ("q", "\x03", "\x1b"):
                    print("\nQuitting...")
                    drive.stop()
                    break

                # ---------------- SPEED ----------------
                elif cmd == "+":
                    drive.set_speed(min(Drive.MAX_SPEED, drive.speed + 5))
                elif cmd == "-":
                    drive.set_speed(max(1, drive.speed - 5))

                # ---------------- DRIVE ----------------
                elif cmd in commands:
                    commands[cmd]()
                    moving = True

                # ---------------- TOGGLES ----------------
                elif cmd == "b":
                    brush_on = not brush_on
                    print("Brush:", brush_on)
                elif cmd == "c":
                    conveyor_on = not conveyor_on
                    print("Conveyor:", conveyor_on)

                # ---------------- AUTO-STOP ----------------
                else:
                    if moving:
                        drive.stop()
                        moving = False

                # ---------------- BRUSH CONTROL ----------------
                if brush_on:
                    GPIO.output(BRUSH_IN2, GPIO.LOW)
                    brush_pwm.ChangeDutyCycle(70)
                else:
                    brush_pwm.ChangeDutyCycle(0)

                # ---------------- CONVEYOR CONTROL ----------------
                if conveyor_on:
                    GPIO.output(CONV_IN2, GPIO.LOW)
                    conv_pwm.ChangeDutyCycle(70)
                else:
                    conv_pwm.ChangeDutyCycle(0)

                # ---------------- PICO COLOR EVENT ----------------
                if pico:
                    color = pico.get_color()

                    if color and color != last_color and not sorting:
                        print("Color detected:", color)
                        last_color = color
                        sorting = True

                        def do_sort():
                            nonlocal last_color, sorting
                            servo_pwm.ChangeDutyCycle(7)  # ~90°
                            time.sleep(0.5)
                            servo_pwm.ChangeDutyCycle(0)
                            stepper(200, True)
                            last_color = None
                            sorting = False

                        threading.Thread(target=do_sort, daemon=True).start()

        except KeyboardInterrupt:
            print("\nInterrupted")
            drive.stop()
        finally:
            brush_pwm.stop()
            conv_pwm.stop()
            servo_pwm.stop()
            GPIO.cleanup()
            if sys.platform != "win32":
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
            if pico:
                pico.close()


# =========================================================
def addArguments(parser):
    parser.add_argument("--mock",       action="store_true", help="Run in mock mode (no hardware)")
    parser.add_argument("--speed",      type=int, default=30, help="Drive speed 1-63 (default: 30)")
    parser.add_argument("--port",       type=str, default=None, help="Serial port for Sabertooth (e.g. /dev/ttyUSB0, COM3)")
    parser.add_argument("--pico-port",  type=str, default=None, help="Serial port for the Pico (e.g. /dev/ttyACM0, COM4)")
    parser.add_argument("--no-pico",    action="store_true", help="Disable Pico color reader")
    parser.add_argument("--list-ports", action="store_true", help="List available serial ports and exit")
    return parser.parse_args()


if __name__ == "__main__":
    main()
