from string import Template
import csv

from typing import List
import pathlib
from VISA.MODEL_2410 import MODEL2410


def diode_save(columns: List, rows: List, path: pathlib.Path, save_params, test_datas):
    """Save a list of rows to a csv, automatically named.

    :param columns: list of columns names
    :param rows: the list of rows to be saved
    :param path: Path to the csv folder
    :param save_params: dirname and filename template
    :param test_datas: values of the test (used for saving/naming)
    """
    # ###### #
    # Saving #
    # ###### #

    filename = Template(save_params.filename).safe_substitute(test_datas._asdict())
    full_path = path / test_datas.name / save_params.dirname / filename

    with open(str(full_path.resolve()), 'w', newline='') as csv_file:
        writer = csv.writer(csv_file, dialect='excel', delimiter=',')
        writer.writerow(columns)
        writer.writerows(rows)


def diode_iv_and_save(k2410: MODEL2410, test_params, columns: List, path: pathlib.Path, save_params, test_datas,
                      autoscale=False):
    """Perform an IV characterization using the 2410's wizard and then save it

    :param k2410: MODEL2410 instrument
    :param test_params: parameters of the IV characterization
    :param columns: list of columns names
    :param path: Path to the csv folder
    :param save_params: dirname and filename template
    :param test_datas: values of the test (used for saving/naming)
    :param autoscale: If the measure is to low compared to the compliance, adjust the compliance and retry
    """
    # ########### #
    # Acquisition #
    # ########### #
    data = k2410.iv_wizard(test_params.current_compliance, 0, -test_params.max_voltage, test_params.step_voltage,
                           autoscale=autoscale)

    # ###### #
    # Saving #
    # ###### #
    rows = [[d.timestamp, -d.current, -d.voltage] for d in data]
    diode_save(columns, rows, path, save_params, test_datas)


def diode_vi_and_save(k2410: MODEL2410, test_params, columns: List, path: pathlib.Path, save_params, test_datas,
                      autoscale=False):
    """Perform a VI characterization using the 2410's wizard and then save it

    :param k2410: MODEL2410 instrument
    :param test_params: parameters of the VI characterization
    :param columns: list of columns names
    :param path: Path to the csv folder
    :param save_params: dirname and filename template
    :param test_datas: values of the test (used for saving/naming)
    :param autoscale: If the measure is to low compared to the compliance, adjust the compliance and retry
    """
    # ########### #
    # Acquisition #
    # ########### #

    data = k2410.vi_wizard(test_params.voltage_compliance, 0, -test_params.max_current, test_params.step_current,
                           autoscale=autoscale)

    # ###### #
    # Saving #
    # ###### #
    rows = [[d.timestamp, -d.current, -d.voltage] for d in data]
    diode_save(columns, rows, path, save_params, test_datas)
