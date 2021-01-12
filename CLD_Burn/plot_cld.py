import math
from matplotlib import pyplot as plt
from pathlib import Path


def plot_cld(time: list, voltage: list, current: list, filename: str = 'graph', *,
             time_scale: float = 1, max_voltage: float = 100, max_current: float = 10,
             show: bool = True, save: bool = False, show_png: bool = False, path: Path = None):
    if show_png:
        raise NotImplementedError

    fig, (ax1, ax2) = plt.subplots(2, 1)

    time = [t*time_scale for t in time]
    
    ax1.plot(time, voltage)
    ax1.set_title(filename, fontsize=10)
    # ax1.set_title('Voltage over time')
    ax1.set_xlabel('Time (us)', fontsize=14)
    ax1.set_ylabel('Voltage (V)', fontsize=14)
    ax1.set_ylim(0,max_voltage)
    ax1.tick_params('x', labelsize=12)
    ax1.tick_params('y', labelsize=12)
    ax1.grid(True)

    ax2.plot(time, current)
    # ax2.set_title('Current over time')
    ax2.set_xlabel('Time (us)', fontsize=14)
    ax2.set_ylabel('Current (A)', fontsize=14)
    ax2.set_ylim(0,max_current)
    ax2.tick_params('x', labelsize=12)
    ax2.tick_params('y', labelsize=12)
    ax2.grid(True)

    # fig.suptitle(filename, fontsize='18')
    fig.tight_layout()

    if show:
        plt.show()
    if save:
        if path is None:
            path = Path("./")
        path.resolve()
        if not path.is_dir():
            path.mkdir()
        full_path = (path / (filename+".png"))

        plt.savefig(full_path, dpi=120, bbox_inches="tight")

    plt.close()


if __name__ == "__main__":
    t = list(range(10))
    c = [math.sin(i * 6 / 10) for i in t]
    v = [math.cos(i * 6 / 10) for i in t]

    plot_cld(t, v, c, 'CLD', time_scale=1e6, max_voltage=800, max_current=10, show=False, save=True)
