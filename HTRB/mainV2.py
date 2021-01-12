import pathlib, sys

sys.path.append(str(pathlib.Path('../_libs/').resolve()))

from VISA.VISA_controller import VisaController
from VISA.XR8000 import XR8000
from VISA.PICOAMMETER import PICOAMMETER

from ArduinoHTRB import ArduinoHTRB
from GUI import display_data

import time as tme
import pandas as pd
from collections import namedtuple

# ########## #
# VISA stuff #
# ########## #

#   # VISA controller, only one #   #
vc = VisaController(query='?*::INSTR', verbose=True)
#   # Various devices, as many as needed (but only one object for one real device) #   #
inst = vc.get_instruments_by_name(XR8000.NAME)[0]
xr8000 = XR8000(inst)
inst = vc.get_instruments_by_name(PICOAMMETER.NAME)[0]
pico = PICOAMMETER(inst)
inst = vc.get_instruments_by_name(ArduinoHTRB.NAME)[0]
arduino = ArduinoHTRB(inst)
Diodes = ArduinoHTRB.Device

# ######## #
# Settings #
# ######## #
PATH = pathlib.Path("./csv")

DIODE_LIST = [
    [Diodes.B1, 'D42'],
    [Diodes.B2, 'D67'],
    [Diodes.B3, 'D70'],
    [Diodes.B4, 'D72'],
    [Diodes.B5, 'D74'],
    [Diodes.B6, 'D79'],
    [Diodes.B7, 'D60'],
    [Diodes.B8, 'D66'],
    [Diodes.B9, 'D47'],
    [Diodes.B10, 'D52'],
    [Diodes.B11, 'D58'],
    [Diodes.B12, 'D87']]

DIODE_VOLTAGE = 1200 * .8
DIODE_MAX_CURRENT = 200e-6
DIODE_NORMAL_CURRENT = 100e-6
PROTECTION_RESISTOR = 1e6 / 4
DIODE_VOLTAGE = DIODE_VOLTAGE + DIODE_NORMAL_CURRENT * PROTECTION_RESISTOR
DIODE_CURRENT_COMPLIANCE = 20e-3  # DIODE_MAX_CURRENT * len(DIODE_LIST) + DIODE_VOLTAGE/PROTECTION_RESISTOR

MEASURE_PERIOD = 60  # seconds
RAMP_DURATION = 10  # seconds

print("High Voltage value : ", DIODE_VOLTAGE)
print("Current compliance : ", DIODE_CURRENT_COMPLIANCE)
print("Tripping current : ", DIODE_MAX_CURRENT)

# ##### #
# Setup #
# ##### #

Diode = namedtuple("Diode", ['board', 'name', 'isDead', 'maxCurrent', 'minCurrent', 'lastCurrent', 'cycles'])
COLUMNS = ['Timestamp_abs (s)', 'Timestamp_rel (ms)', 'Current (A)', 'Voltage (estimated) (V)', 'Status', 'Cycles']

DIODES = []
for diode in DIODE_LIST:
    DIODES.append(Diode(*diode, False, -1, 1, 0, 0))

    filepath = PATH / ('diode_' + diode[1] + '.csv')
    header = pd.DataFrame(columns=COLUMNS)
    header.to_csv(filepath, mode='a', index=False, header=True)

# ######## #
# Main App #
# ######## #

#try:
arduino.orange(True)

# ################# #
# Instruments setup #
# ################# #

    #  # Power supply #  #
xr8000.output = False
xr8000.v_source_wizard(DIODE_VOLTAGE, DIODE_CURRENT_COMPLIANCE)

    #  # Picoammeter #  #
pico.zero_check = False
pico.zero_correction = False
pico.arm_count = 1
pico.trig_count = 1

    #  # Boards #  #
for diode in DIODES:
    delay = arduino.enable(diode.board, True)
    tme.sleep(delay + .5)

    # ##### #
    # Start #
    # ##### #
global_over_current = False
xr8000.output_ramp(DIODE_VOLTAGE, RAMP_DURATION)
arduino.red(True)

START_TIMESTAMP = tme.time()

stop = False
while not stop:

    DIODES_TEMP = []
    for diode in DIODES:

        diode_board = diode.board
        diode_name = diode.name

        if diode.isDead:
            tme.sleep(4)
        else:
                # ########### #
                # Acquisition #
                # ########### #

            delay = arduino.measure(diode_board, True)
            tme.sleep(delay + .5)

            data = pico.read()[0]

            delay = arduino.measure(diode_board, False)
            tme.sleep(delay + .5)

                # ########## #
                # Protection #
                # ########## #

            over_current = False
            if data.current > DIODE_MAX_CURRENT:
                over_current = True
                delay = arduino.enable(diode_board, False)
                tme.sleep(delay + .5)

                # ###### #
                # Saving #
                # ###### #

            lastCurrent = data.current
            maxCurrent = max(data.current, diode.maxCurrent)  # Args order matters !
            minCurrent = min(data.current, diode.minCurrent)
            cycles = diode.cycles + 1

            diode_temp = Diode(diode_board, diode_name, over_current, maxCurrent, minCurrent, lastCurrent, cycles)
            DIODES_TEMP.append(diode_temp)

            voltage = DIODE_VOLTAGE - data.current * PROTECTION_RESISTOR
            if (not global_over_current) or over_current:
                print("Pico reading (", diode, ") :", data.current)
                filepath = PATH / ('diode_' + diode_name + '.csv')
                df = pd.DataFrame(columns=COLUMNS,
                                  data=[[round(tme.time()), data.timestamp, data.current, voltage, str(data.status),
                                         diode_temp.cycles]])
                df.to_csv(filepath, mode='a', index=False, header=False)

    DIODES = DIODES_TEMP

        # ########## #
        # Displaying #
        # ########## #

        # Auto scaling
#        top = 0
#        for diode in DIODES:
#            top = max(diode.maxCurrent, top)
#        top = max(round(top * 1e6 / 10 + .5) * 10e-6, 1e-6)

 #       try:
 #           display_data(START_TIMESTAMP, DIODE_VOLTAGE, DIODE_CURRENT_COMPLIANCE,
 #                        xr8000.current, top, PROTECTION_RESISTOR, DIODES)
 #       except Exception as e:
  #          print(e)

        # ######################### #
        # Delay to next measurement #
        # ######################### #

    global_over_current = False
    start = tme.time()
    while ((start + MEASURE_PERIOD) > tme.time()) and not global_over_current:
        if xr8000.current > (DIODE_NORMAL_CURRENT * len([diode for diode in DIODES if not diode.isDead])
                            + DIODE_MAX_CURRENT):
            global_over_current = True
        else:
            tme.sleep(5)

    stop = all([diode.isDead for diode in DIODES])

xr8000.output = False
arduino.red(False)

#except Exception as e:
#    arduino.red(True)
#    arduino.orange(False)
#    print(e)
#    print("IT Service : 0651489404")
#except (KeyboardInterrupt, SystemExit, GeneratorExit) as e:
#    xr8000.output = False
#    arduino.red(True)
#    arduino.orange(False)
#    print(e)
#else:
#    xr8000.output = False
#    arduino.orange(False)
#    arduino.red(False)
