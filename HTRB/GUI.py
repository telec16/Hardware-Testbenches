import time
import colorama
from colorama import Fore, Back, Style


def display_data(sts, voltage, compliance, actual, trip_current, resistor, diodes):
    colorama.init(autoreset=True)
    __clear_screen()
    HEIGHT = 15

    total_stress_time = (time.time() - sts) / 3600
    alive = sum([not diode.isDead for diode in diodes])
    total = len(diodes)
    color = Back.GREEN if alive / total > .8 else (Back.YELLOW if alive / total > .4 else Back.RED)

    print(f"Applied voltage    : {Fore.LIGHTRED_EX}{voltage:=+10,.2f}V")
    print(f"Current compliance : {Fore.LIGHTRED_EX}{compliance*1e6:=+10,.2f}µA", end='')
    print(f" - Actual voltage : {Fore.LIGHTRED_EX}{actual}V")
    print(f"Alive              : {Style.BRIGHT+color}{alive:0>2d}/{total:0>2d}")
    print(f"Total stress time  : {Style.BRIGHT+Fore.YELLOW+Back.BLUE}{total_stress_time:0>8,.2f}h")
    __print_scale(trip_current, 1, 6, HEIGHT)

    for diode in diodes:
        col = int(diode.board.value[1:3]) - 1
        row = 1 if diode.board.value[0] == 'A' else 0
        diode_voltage = voltage - diode.lastCurrent * resistor

        __print_diode(diode, trip_current, diode_voltage, x=7, y=6, column=col, row=row, height=HEIGHT, length=9)

    __move_cursor(1, 6 + (HEIGHT + 7) * 2)


def __print_scale(trip_current, x, y, height):
    y += 3
    __move_cursor(x, y)
    print(f"\n{trip_current*1e6:>3.0f}µA")
    y += height-1
    __move_cursor(x, y)
    print(f"\n{(trip_current*1e6)/height:>3.0f}µA")
    y += 1
    __move_cursor(x, y)
    print(f"\n{0:>3.0f}µA")

    y += 7
    __move_cursor(x, y)
    print(f"\n{trip_current*1e6:>3.0f}µA")
    y += height-1
    __move_cursor(x, y)
    print(f"\n{(trip_current*1e6)/height:>3.0f}µA")
    y += 1
    __move_cursor(x, y)
    print(f"\n{0:>3.0f}µA")


def __print_diode(diode, trip_current, voltage, *, x, y, column, row, height, length):
    x = column * length + x
    y = row * (height + 7) + y

    # Draw a box
    __move_cursor(x, y)
    print(f'{Back.WHITE}{" " * (length+1)}')
    for yy in range(y, y + height + 5):
        __move_cursor(x, yy)
        print(Back.WHITE + ' ', end='')
        __move_cursor(x + length, yy)
        print(Back.WHITE + ' ', end='')
    __move_cursor(x, y + height + 5)
    print(f'{Back.WHITE}{" " * (length+1)}')

    # Print the diode name
    back = Back.LIGHTRED_EX if diode.isDead else Back.LIGHTGREEN_EX
    __move_cursor(x + 1, y + 1)
    print(f'{back+Fore.BLACK}{diode.name:^{length-1}}')

    # Print the diode current
    __move_cursor(x + 1, y + 2)
    print(f'{Style.BRIGHT}{diode.lastCurrent*1e6:>{length-3}.2f}µA')

    # Print the diode voltage
    __move_cursor(x + 1, y + 3)
    print(f'{Style.BRIGHT}{voltage:>{length-2}.2f}V')

    # Draw the diode's currents bar chart
    def print_cursor(x, y, val, color, cursor):
        __move_cursor(x, y + val)
        print(f'{color}{cursor}')

    CURSOR_SIZE = int((length - 2) / 3)
    print_cursor(x + 2 + 0 * CURSOR_SIZE, y + 4, __map_clip(diode.minCurrent, 0, trip_current, height, 0),
                 Back.LIGHTCYAN_EX, (" " if diode.minCurrent <= trip_current else "^") * CURSOR_SIZE)
    print_cursor(x + 2 + 1 * CURSOR_SIZE, y + 4, __map_clip(diode.lastCurrent, 0, trip_current, height, 0),
                 Back.GREEN, (" " if diode.lastCurrent <= trip_current else "^") * CURSOR_SIZE)
    print_cursor(x + 2 + 2 * CURSOR_SIZE, y + 4, __map_clip(diode.maxCurrent, 0, trip_current, height, 0),
                 Back.LIGHTRED_EX, (" " if diode.maxCurrent <= trip_current else "^") * CURSOR_SIZE)


def __move_cursor(x, y):
    y = int(max(1, min(80, y)))
    x = int(max(1, min(120, x)))
    print(f'\x1b[{y:d};{x:d}H', end='')


def __clear_screen(mode=2):
    print(f'\033[{mode:d}J', end='')
    __move_cursor(1,1)


def __map_clip(value, from_min, from_max, to_min, to_max):
    value = max(from_min, min(from_max, value))
    return ((value - from_min) / (from_max - from_min)) * (to_max - to_min) + to_min


if __name__ == "__main__":
    import pathlib, sys

    sys.path.append(str(pathlib.Path('../_libs/').resolve()))
    from ArduinoHTRB import ArduinoHTRB
    from collections import namedtuple

    Diodes = ArduinoHTRB.Device

    DIODE_VOLTAGE = 1200 * .8
    DIODE_MAX_CURRENT = 200e-6
    DIODE_NORMAL_CURRENT = 100e-6
    PROTECTION_RESISTOR = 1e6 / 4
    DIODE_VOLTAGE = DIODE_VOLTAGE + DIODE_NORMAL_CURRENT * PROTECTION_RESISTOR
    DIODE_CURRENT_COMPLIANCE = 20e-3  # DIODE_MAX_CURRENT * len(DIODE_LIST) + DIODE_VOLTAGE/PROTECTION_RESISTOR

    MEASURE_PERIOD = 60  # seconds

    Diode = namedtuple("Diode", ['board', 'name', 'isDead', 'maxCurrent', 'minCurrent', 'lastCurrent', 'cycles'])
    COLUMNS = ['Timestamp_abs (s)', 'Timestamp_rel (ms)', 'Current (A)', 'Voltage (estimated) (V)', 'Status', 'Cycles']

    DIODES = [
        Diode(Diodes.B1, 'D42', True, 10e-6, 1e-6, 5e-6, 0),
        Diode(Diodes.B2, 'D60', False, 18e-6, 5e-6, 5.5e-6, 0),
        Diode(Diodes.B7, 'D74', True, 16e-6, 8e-6, 8.2e-6, 0),
        Diode(Diodes.B8, 'D79', False, 21e-6, 15e-6, 16e-6, 0),
        Diode(Diodes.B9, 'D47', False, 10e-6, 5e-6, 8e-6, 0),
        Diode(Diodes.B10, 'D52', False, 5e-6, 2e-6, 2e-6, 0),
        Diode(Diodes.B3, 'D66', True, 20e-6, 6e-6, 6e-6, 0),
        Diode(Diodes.B4, 'D67', False, 10e-6, 4e-6, 4e-6, 0),
        Diode(Diodes.A5, 'D70', True, 5e-6, 3e-6, 3.3e-6, 0),
        Diode(Diodes.A3, 'D66', False, 20e-6, 6e-6, 6e-6, 0),
        Diode(Diodes.A4, 'D67', False, 10e-6, 4e-6, 4e-6, 0),
        Diode(Diodes.B5, 'D70', True, 5e-6, 3e-6, 3.3e-6, 0),
        Diode(Diodes.B6, 'D72', False, 3e-6, 2e-6, 2e-6, 0),
        Diode(Diodes.A11, 'D58', False, 3e-6, 0e-6, 1e-6, 0),
        Diode(Diodes.A12, 'D87', False, 8e-6, 4e-6, 6e-6, 0)
    ]

    top = 0
    for diode in DIODES:
        top = max(diode.maxCurrent, top)
    top = round(top * 1e6 / 10 + .5) * 10e-6

    display_data(time.time() - 10000000, DIODE_VOLTAGE, DIODE_CURRENT_COMPLIANCE, 1e-3, top, 1e6, DIODES)
