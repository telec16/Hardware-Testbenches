from typing import List, Tuple
from texttable import Texttable


def diode_map(diodes: List[Tuple], rows: int = 7) -> str:
    diode_list = []
    for _ in range(rows):
        diode_list.append(["", ""])

    for diode in diodes:
        name = diode[1]
        board = diode[0].name

        col = 1 if "A" in board else 0
        row = rows - 1 - int(board[1:])

        diode_list[row][col] = name

    t = Texttable()
    t.add_rows(diode_list)
    t.set_chars(['-', '|', '+', '-'])  # No headers

    return t.draw()
