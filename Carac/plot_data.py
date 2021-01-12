from copy import deepcopy
from typing import List, Tuple, Dict
from pathlib import Path

import math
from natsort import natsorted
from matplotlib import pyplot as plt
import pandas as pd
import numpy as np


def read_data(path: Path, diodename: str, test: str) -> Tuple[List[str], Dict[str, pd.DataFrame]]:
    full_path = path / diodename / test
    data = {}

    for file in natsorted(full_path.iterdir(), key=lambda x: x.stem):
        data[file.stem] = pd.read_csv(file)
    # Could use that too : data=OrderedDict(natsorted(data.items()))
    columns = list(list(data.values())[0].columns)

    return columns, data


def read_data_rows_as_df(path: Path, diodename: str, test: str) -> Tuple[List[str], List[pd.DataFrame]]:
    full_path = path / diodename / test
    data = []

    df = pd.read_csv(list(full_path.iterdir())[0])
    columns = list(df.columns)
    size = len(df)
    for _ in range(size):
        data.append(pd.DataFrame(columns=df.columns))

    for file in natsorted(full_path.iterdir(), key=lambda x: x.stem):
        df = pd.read_csv(file)
        for i in range(size):
            data[i] = data[i].append(df.loc[i], ignore_index=True)

    return columns, data


def find_column(columns: List[str], key: str) -> str:
    for c in columns:
        if key.lower() in c.lower():
            return c
    return ""


def add_dyn_resistance(data: Dict[str, pd.DataFrame], columns: List[str], name: str="Resistance (ohm)")->List[str]:
    columns.append(name)
    vi = find_column(columns, "volt")
    ci = find_column(columns, "current")

    for df in data.values():
        df[name] = df[vi]/df[ci]

    return columns


def filter_all(data: Dict[str, pd.DataFrame], columns: List[str], name: str, filt):
    name = find_column(columns, name)

    if type(filt) in [int, float]:
        filt = np.ones(filt) / filt
    for df in data.values():
        df[name] = np.convolve(filt, df[name], mode='same')


def align_all(data: Dict[str, pd.DataFrame], columns: List[str]):
    ti = find_column(columns, "time")
    ci = find_column(columns, "current")

    for df in data.values():
        t_step = df[ti][1] - df[ti][0]
        t_max = df.idxmax()[ti]
        c_max = df.idxmax()[ci]

        t_offset = 5 * 10 ** (round(math.log10(df[ti][t_max])) - 1)
        t_offset = t_offset + (t_max / 2 - c_max) * t_step

        df[ti] = [t + t_offset for t in df[ti]]


def plot_all(data: Dict[str, pd.DataFrame], columns: List[str], x: str, y: str, grouped: bool = True, **kwargs):
    x = find_column(columns, x)
    y = find_column(columns, y)

    if grouped:
        fig, ax = plt.subplots()
    else:
        ax = None

    for name, df in data.items():
        df.plot(ax=ax, kind='line', x=x, y=y, label=name, **kwargs)


def plot_dots(ddots: Dict[str, List[Tuple[float, float]]], **kwargs):
    for dots in ddots.values():
        for dot in dots:
            plt.plot(*dot, **kwargs)


def get_bipolar_transition(data: Dict[str, pd.DataFrame], columns: List[str],
                           threshold: float) -> Dict[str, List[Tuple[float, float]]]:
    data = deepcopy(data)
    volt = find_column(columns, "volt")
    current = find_column(columns, "current")

    bt = {}
    for name, df in data.items():
        df["dvolt"] = np.diff(df[volt]) * (df[volt] >= threshold)[:-1]
        df["ddvolt"] = np.diff(np.diff(df[volt])) * (df[volt] >= threshold)[:-2]
        dots = [(df[volt][idx], df[current][idx]) for idx in [np.argmax(df[volt]), np.argmin(df["ddvolt"])]]
        bt[name] = dots

    return bt


def get_crossing(data: Dict[str, pd.DataFrame], columns: List[str],
                 threshold: float, accuracy: float) -> Dict[str, List[Tuple[float, float]]]:
    data = deepcopy(data)
    volt = find_column(columns, "volt")
    current = find_column(columns, "current")

    crs = {}
    for name, df in data.items():
        dots = []
        lc = list(df[current])
        lv = list(df[volt])

        cut = list(df[volt] >= threshold)
        try:
            start_idx = cut.index(True)
            stop_idx = cut[::-1].index(True)
        except ValueError:
            pass
        else:
            (start_idx, stop_idx) = align_base(lc, start_idx, stop_idx, accuracy)

            idx = 0
            spot = 0
            for k in range(round((stop_idx - start_idx) / 2 + .5)):
                v1 = lv[start_idx + k]
                v2 = lv[stop_idx - k]
                diff = abs((v1 - v2) / v1)
                if diff < accuracy:
                    if spot == 0:
                        idx = k
                        spot = 1
                    if diff < accuracy / 2:
                        spot = 2
                else:
                    if spot == 2:
                        a1 = (lc[start_idx + k] - lc[start_idx + idx]) / (lv[start_idx + k] - lv[start_idx + idx])
                        a2 = (lc[stop_idx - k] - lc[stop_idx - idx]) / (lv[stop_idx - k] - lv[stop_idx - idx])
                        b1 = lc[start_idx + idx] - a1 * lv[start_idx + idx]
                        b2 = lc[stop_idx - idx] - a2 * lv[stop_idx - idx]
                        v = (b2 - b1) / (a1 - a2)
                        c = a1 * v + b1
                        dots.append((v, c))
                    spot = 0

        crs[name] = dots

    return crs


def align_base(l: List[float], start_idx: int, stop_idx: int, accuracy=0.05) -> Tuple[int, int]:
    m = max(l[start_idx], l[-stop_idx - 1])
    d = -1 if l[start_idx] == m else 1

    ldiff = 1
    lk = 0
    for k, v in enumerate(l[start_idx:-stop_idx][::d]):
        diff = abs((m - v) / m)
        if diff < accuracy:
            if ldiff < diff:
                break
            ldiff = diff
            lk = k

    if d == -1:
        return start_idx, len(l) - stop_idx - 1 - lk
    else:
        return start_idx + lk, len(l) - stop_idx - 1


if __name__ == "__main__":
    import time


    def gaussian(x, mu, sig):
        return np.exp(-np.power(x - mu, 2.) / (2 * np.power(sig, 2.)))


    DIODENAME = "KE12DJ08L_D1"

    start = time.time()
    c, d = read_data(Path("./csv"), DIODENAME, "Surge")
    print("time:", time.time() - start)

    start = time.time()
    # align_all(d, c)
    t = np.linspace(-3, 3, 200)
    f = gaussian(t, 0, 1)
    f = f / sum(f)
    f = np.ones(75) / 75
    filter_all(d, c, "volt", f)
    f = np.ones(75) / 75
    filter_all(d, c, "curr", f)
    bt = get_bipolar_transition(d, c, 2)
    crs = get_crossing(d, c, 2, 0.05)
    c = add_dyn_resistance(d, c)
    print("time:", time.time() - start)

    start = time.time()
    plot_all(d, c, "time", "volt")
    plot_all(d, c, "time", "curr")
    plot_all(d, c, "time", "res", True, ylim=(0, 500e-3))
    plot_all(d, c, "volt", "res", True, ylim=(0, 500e-3))
    # plot_all(d, c, "volt", "curr", grouped=False)
    plot_all(d, c, "volt", "curr", grouped=True)
    plot_dots(bt, marker='x')
    plot_dots(crs, marker='+')
    print("time:", time.time() - start)

    c, d = read_data(Path("./csv"), DIODENAME, "Direct")
    # plot_all(d, c, "volt", "curr")
    plot_all(d, c, "volt", "curr", True, logy=True)

    c, d = read_data(Path("./csv"), DIODENAME, "Reverse")
    # plot_all(d, c, "volt", "curr")
    d = {k: df.abs() for k, df in d.items()}
    plot_all(d, c, "volt", "curr", True, logy=True)

    plt.show()
