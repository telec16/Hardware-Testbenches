import pathlib, sys

sys.path.append(str(pathlib.Path('../_libs/').resolve()))

from VISA.VISA_controller import VisaController
from VISA.PICOAMMETER import PICOAMMETER
from VISA.ArduinoAlim import ArduinoAlim

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
#inst = vc.get_instruments_by_name(XR8000.NAME)[0]
#xr8000 = XR8000(inst)
inst = vc.get_instruments_by_name(ArduinoAlim.NAME)[0]
alim = ArduinoAlim(inst)
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
    [Diodes.B1, 'B1_87'],
    [Diodes.B2, 'B2_78'],
    [Diodes.B3, 'B3_75'],
    [Diodes.B4, 'B4_51'],
    [Diodes.B5, 'B5_55'],
    [Diodes.B6, 'B6_76'],
    [Diodes.B7, 'B7_28'],
    [Diodes.B8, 'B8_57'],
    [Diodes.B9, 'B9_23'],
    [Diodes.B10, 'B10_47'],
    [Diodes.B11, 'B11_25'],
    [Diodes.B12, 'B12_15']]


DIODE_VOLTAGE = 1200 * 0.8
DIODE_MAX_CURRENT = 200e-6
DIODE_NORMAL_CURRENT = 100e-6
PROTECTION_RESISTOR = 1e6 / 4
DIODE_VOLTAGE = DIODE_VOLTAGE + DIODE_NORMAL_CURRENT * PROTECTION_RESISTOR
DIODE_CURRENT_COMPLIANCE = 20e-3  # DIODE_MAX_CURRENT * len(DIODE_LIST) + DIODE_VOLTAGE/PROTECTION_RESISTOR

MEASURE_PERIOD = 60  # seconds


print("High Voltage value : ", DIODE_VOLTAGE)
print("Current compliance : ", DIODE_CURRENT_COMPLIANCE)
print("Tripping current : ", DIODE_MAX_CURRENT)

# ##### #
# Setup #
# ##### #

Diode = namedtuple("Diode", ['board', 'name', 'isDead', 'maxCurrent', 'minCurrent', 'lastCurrent', 'cycles'])
COLUMNS = ['Timestamp_abs (s)', 'Timestamp_rel (ms)', 'Current (A)', 'Voltage (estimated) (V)','Voltage (real) (V)', 'Status', 'Cycles']

DIODES = []
for diode in DIODE_LIST:
    DIODES.append(Diode(*diode, False, -1, 1, 0, 0))

    filepath = PATH / ('diode_' + diode[1] + '.csv')
    header = pd.DataFrame(columns=COLUMNS)
    header.to_csv(filepath, mode='a', index=False, header=True)
    

# ######## #
# Main App #
# ######## #

try:
    arduino.orange(True)

    # ################# #
    # Instruments setup #
    # ################# #

    #  # Power supply #  #
    #xr8000.output = False
    alim.output_relay(False)
    #xr8000.v_source_wizard(DIODE_VOLTAGE, DIODE_CURRENT_COMPLIANCE)

    #  # Picoammeter #  #
    pico.zero_check = False
    pico.zero_correction = False
    pico.arm_count = 1
    pico.trig_count = 1
    pico.auto_range = True

    #  # Boards #  #
    for diode in DIODES:
        delay = arduino.enable(diode.board, True)
        tme.sleep(delay + .5)

    # ##### #
    # Start #
    # ##### #
    global_over_current = False
    #xr8000.output_ramp(DIODE_VOLTAGE, RAMP_DURATION)
    alim.set_output_voltage(980)
    tme.sleep(2)
    alim.output_relay(True)
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

                voltage = alim.voltage() - data.current * PROTECTION_RESISTOR
                tension = alim.voltage()
                if (not global_over_current) or over_current:
                    print("Pico reading (", diode, ") :", data.current*1e6 ,"uA ","Actual Voltage = ", alim.voltage(), "V")
                    filepath = PATH / ('diode_' + diode_name + '.csv')
                    df = pd.DataFrame(columns=COLUMNS,
                                      data=[[round(tme.time()), data.timestamp, data.current, voltage,tension, str(data.status),
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


#        try:
#            display_data(START_TIMESTAMP, DIODE_VOLTAGE, DIODE_CURRENT_COMPLIANCE,
#                         alim.voltage(), top, PROTECTION_RESISTOR, DIODES) #xr8000.current
#        except Exception as e:
#            print(e)

        # ######################### #
        # Delay to next measurement #
        # ######################### #

        global_over_current = False
        start = tme.time()
        compliance_detection = alim.voltage()
        while ((start + MEASURE_PERIOD) > tme.time()) and not global_over_current:
            if compliance_detection < DIODE_VOLTAGE * 0.8 :
                global_over_current = True
            else:
                tme.sleep(5)

        stop = all([diode.isDead for diode in DIODES])

    #xr8000.output = False
    alim.input_relay(False)
    arduino.red(False)

except Exception as e:
    arduino.red(True)
    arduino.orange(False)
    print(e)
    print("IT Service : 0651489404")
except (KeyboardInterrupt, SystemExit, GeneratorExit) as e:
    #xr8000.output = False
    alim.input_relay(False)
    arduino.red(True)
    arduino.orange(False)
    print(e)
else:
    #xr8000.output = False
    alim.input_relay(False)
    arduino.orange(False)
    arduino.red(False)
