# MarbleSorter
CSU RamRobotics Club [Spring 2026]

## Setup
```
pip install pyserial
```

Flash `src/pico/code.py` to the Pico before running.

## Running

**Check ports first:**
```
python src/pi/main.py --list-ports
```

**Run with hardware:**
```
python src/pi/main.py --port /dev/ttyUSB0 --pico-port /dev/ttyACM0
```

**Run without Sabertooth (mock drive):**
```
python src/pi/main.py --mock --pico-port /dev/ttyACM0
```

**Run without Pico (no color sensor):**
```
python src/pi/main.py --port /dev/ttyUSB0 --no-pico
```

## Controls
| Key | Action |
|-----|--------|
| W / S | Forward / Backward |
| A / D | Turn Left / Right |
| Z / X | Spin Left / Right |
| Space | Stop |
| B | Toggle brush |
| C | Toggle conveyor |
| + / - | Increase / Decrease speed |
| Q | Quit |

## Sorting
Color detection and sorting run automatically when the Pico is connected. Detected colors print to console as `[Pico] Color: <color> | RGB:(r, g, b)`.
