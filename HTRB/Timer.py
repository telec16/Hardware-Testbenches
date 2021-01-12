from datetime import datetime
import time as tme
import colorama
from colorama import Fore, Back, Style

charset = [
    "  ████████  ",
    "██        ██",
    "██      ████",
    "██  ████  ██",
    "████      ██",
    "██        ██",
    "  ████████  ",
    "      ██    ",
    "    ████    ",
    "  ██  ██    ",
    "      ██    ",
    "      ██    ",
    "      ██    ",
    "  ██████████",
    "  ████████  ",
    "██        ██",
    "          ██",
    "      ████  ",
    "  ████      ",
    "██          ",
    "████████████",
    "  ████████  ",
    "██        ██",
    "          ██",
    "    ██████  ",
    "          ██",
    "██        ██",
    "  ████████  ",
    "        ██  ",
    "      ████  ",
    "    ██  ██  ",
    "  ██    ██  ",
    "████████████",
    "        ██",
    "        ██",
    "████████████",
    "██          ",
    "████████    ",
    "        ██  ",
    "          ██",
    "██      ██  ",
    "  ██████    ",
    "    ██████  ",
    "  ██        ",
    "██          ",
    "██████████  ",
    "██        ██",
    "██        ██",
    "  ████████  ",
    "████████████",
    "██        ██",
    "        ██  ",
    "      ██    ",
    "    ██      ",
    "    ██      ",
    "    ██      ",
    "  ████████  ",
    "██        ██",
    "██        ██",
    "  ████████  ",
    "██        ██",
    "██        ██",
    "  ████████  ",
    "  ████████  ",
    "██        ██",
    "██        ██",
    "  ██████████",
    "          ██",
    "        ██  ",
    "  ██████    ",
    "██          ",
    "██          ",
    "██  ██████  ",
    "████      ██",
    "██        ██",
    "██        ██",
    "██        ██",
    "            ",
    "            ",
    "            ",
    "            ",
    "            ",
    "    ████    ",
    "    ████    ",
]


def __move_cursor(x, y):
    y = int(max(1, min(80, y)))
    x = int(max(1, min(120, x)))
    print(f'\x1b[{y:d};{x:d}H', end='')


def __clear_screen(mode=1):
    print(f'\033[{mode:d}J', end='')


def __print_char(x, y, c, color, charset):
    for i in range(7):
        __move_cursor(x, y + i)
        print(color + charset[c * 7 + i])


def print_time(time: str, charset):
    x = 3
    y = 2
    time = time.split(".")
    digits_set = [[int(d) for d in t if d.isdigit()] for t in time if len(t) is not 0]

    for digit in digits_set[0]:
        __print_char(x, y, digit, Fore.LIGHTRED_EX, charset)
        x += len(charset[0]) + 2
    if len(digits_set) >= 2:
        __print_char(x, y, 11, Fore.LIGHTRED_EX, charset)
        x += len(charset[0]) + 2
        for digit in digits_set[1]:
            __print_char(x, y, digit, Fore.LIGHTRED_EX, charset)
            x += len(charset[0]) + 2
    __print_char(x + 2, y, 10, Fore.LIGHTRED_EX, charset)


if __name__ == "__main__":
    END_TEXT = list("Yay ! It's finished ! \o/ -o- \o/ -o- \o/" + " " * (7 * 7 * 2))
    colorama.init()

    start = datetime(2019, 7, 25, 10, 20, 0)

    # Stop time then restart time (year, month, day, hour, minute, second)
    gaps = [(datetime(2019, 7, 28, 4, 20, 0), datetime(2019, 7, 29, 10, 45, 0)), 
            (datetime(2019, 8, 11, 21, 5, 0), datetime(2019, 8, 12, 8, 17, 0)), 
            (datetime(2019, 8, 12, 8, 44, 0), datetime(2019, 8, 12, 9, 19, 0))]
            #(datetime(2019, 1, 27, 9, 30, 0), datetime(2019, 1, 31, 14, 30, 0))]

    stop_time = 0
    for gap in gaps:
        stop_time += (gap[1] - gap[0]).total_seconds() / 3600

    while True:
        time = (datetime.today() - start).total_seconds() / 3600 - stop_time

        __clear_screen()
        print_time(f"{time:0>7.2f}", charset)

        __move_cursor(3, 10)
        print(f"{Fore.WHITE}{'█'*(7 * 7 * 2)}")
        __move_cursor(3, 10)
        for i in range(7 * 7 * 2):
            __move_cursor(3+i, 10)
            print(f"{Fore.CYAN}█" if (time < 1000) else f"{Fore.LIGHTRED_EX+Back.LIGHTWHITE_EX}{END_TEXT[i]}")
            tme.sleep(1 * 60 / (7 * 7 * 2))
        print(Style.RESET_ALL)

