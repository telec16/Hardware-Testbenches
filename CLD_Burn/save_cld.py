import math
from pathlib import Path
import csv


def save_cld(time: list, voltage: list, current: list, filename: str = 'graph', *,
             path: Path = None, delimiter: str = ","):
    if path is None:
        path = Path("./")
    path.resolve()
    if not path.is_dir():
        path.mkdir()
    full_path = (path / (filename+".csv"))

    rows = [[time[i], voltage[i], current[i]] for i in range(len(time))]

    with open(str(full_path.resolve()), 'w', newline='') as csv_file:
        writer = csv.writer(csv_file, dialect='excel', delimiter=delimiter)
        writer.writerow(["Time", "Voltage", "Current"])
        writer.writerow(["s", "V", "A"])
        writer.writerows(rows)


if __name__ == "__main__":
    t = list(range(10))
    c = [math.sin(i * 6 / 10) for i in t]
    v = [math.cos(i * 6 / 10) for i in t]

    save_cld(t, v, c, 'CLD', path=Path("./csv"), delimiter=",")
