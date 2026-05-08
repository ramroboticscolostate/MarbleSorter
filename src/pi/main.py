import argparse
import sys
import time
import threading

import RPi.GPIO as GPIO # type: ignore

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
step = 0
stepperOfset = 0

def stepper(steps, direction=True, delay=0.001):
    global step

    GPIO.output(DIR_PIN, direction)
    for _ in range(steps):
        step += 1 if direction else -1
        GPIO.output(STEP_PIN, True)
        time.sleep(delay)
        GPIO.output(STEP_PIN, False)
        time.sleep(delay)

    return step

def setStepperOfset(pin):
    global stepperOfset
    GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

    steps = 0
    value = GPIO.input(pin)
    while value == 0:
        stepper(1, True)
        value = GPIO.input(pin)
        steps += 1

    stepperOfset = steps
    return stepperOfset

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

        brush_on       = False
        brush_speed    = 70
        conveyor_on    = False
        conveyor_speed = 70
        last_color     = None
        sorting        = False
        servo_testing  = False

        print("Robot ready")
        print("Hold w/a/s/d to move, z/x to spin | B brush | [ ] brush speed | C conveyor | , . conveyor speed | +/- drive speed | V servo test | q = quit")
        print(f"Drive speed: {drive.speed} | Brush speed: {brush_speed} | Conveyor speed: {conveyor_speed}")

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

                # ---------------- STEPPER ----------------

                # elif cmd == "o":
                #     print("Calibrating stepper offset...", end="\r\n")
                #     offset = setStepperOfset(STEP_PIN)
                #     print(f"Stepper offset set to {offset} steps", end="\r\n")

                elif cmd == "r":
                    print("Rotating stepper 90°...", end="\r\n")
                    stepper(200*4, True)  # Adjust steps for 90° based on your hardware
                    print("Rotation complete.", end="\r\n")

                # ---------------- PICO ----------------
                elif cmd == "p" and pico:
                    color = pico.get_color()
                    print(f"Pico color: {color}", end="\r\n")
                elif cmd == "l" and pico:
                    pico.refresh()
                    print("Requested Pico color refresh", end="\r\n")

                # ---------------- SERVO TEST ----------------
                elif cmd == "0":
                    servo_pwm.ChangeDutyCycle(2.5)
                    time.sleep(.1)
                elif cmd == "1":
                    servo_pwm.ChangeDutyCycle(10)
                    time.sleep(.1)
                elif cmd == "2":
                    servo_pwm.ChangeDutyCycle(12.5)
                    time.sleep(.1)

                    # if not servo_testing and not sorting:
                    #     servo_testing = True
                    #     print("Servo test starting...", end="\r\n")

                    #     def run_servo_test():
                    #         nonlocal servo_testing
                    #         # min → mid → max
                    #         servo_pwm.ChangeDutyCycle(2.5)
                    #         time.sleep(1)
                    #         servo_pwm.ChangeDutyCycle(7.5)
                    #         time.sleep(1)
                    #         servo_pwm.ChangeDutyCycle(12.5)
                    #         time.sleep(3)
                    #         # sweep min → max
                    #         for v in [2.5 + (i / 10) * 10 for i in range(0, 21)]:
                    #             servo_pwm.ChangeDutyCycle(v)
                    #             time.sleep(0.05)
                    #         # sweep max → min
                    #         for v in [12.5 - (i / 10) * 10 for i in range(0, 21)]:
                    #             servo_pwm.ChangeDutyCycle(v)
                    #             time.sleep(0.05)
                    #         servo_pwm.ChangeDutyCycle(0)
                    #         print("Servo test complete.", end="\r\n")
                    #         servo_testing = False

                    #     threading.Thread(target=run_servo_test, daemon=True).start()

                # ---------------- TOGGLES ----------------
                elif cmd == "b":
                    brush_on = not brush_on
                    print(f"Brush: {'on' if brush_on else 'off'} | Speed: {brush_speed}", end="\r\n")
                elif cmd == "]":
                    brush_speed = min(100, brush_speed + 10)
                    print(f"Brush speed: {brush_speed}", end="\r\n")
                elif cmd == "[":
                    brush_speed = max(10, brush_speed - 10)
                    print(f"Brush speed: {brush_speed}", end="\r\n")
                elif cmd == "c":
                    conveyor_on = not conveyor_on
                    print(f"Conveyor: {'on' if conveyor_on else 'off'} | Speed: {conveyor_speed}", end="\r\n")
                elif cmd == ".":
                    conveyor_speed = min(100, conveyor_speed + 10)
                    print(f"Conveyor speed: {conveyor_speed}", end="\r\n")
                elif cmd == ",":
                    conveyor_speed = max(10, conveyor_speed - 10)
                    print(f"Conveyor speed: {conveyor_speed}", end="\r\n")

                # ---------------- AUTO-STOP ----------------
                else:
                    if moving:
                        drive.stop()
                        moving = False

                # ---------------- BRUSH CONTROL ----------------
                if brush_on:
                    GPIO.output(BRUSH_IN2, GPIO.LOW)
                    brush_pwm.ChangeDutyCycle(brush_speed)
                else:
                    brush_pwm.ChangeDutyCycle(0)

                # ---------------- CONVEYOR CONTROL ----------------
                if conveyor_on:
                    GPIO.output(CONV_IN2, GPIO.LOW)
                    conv_pwm.ChangeDutyCycle(conveyor_speed)
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
