import pathlib, sys

sys.path.append(str(pathlib.Path('../_libs/').resolve()))

from VISA.VISA_controller import VisaController
from VISA.MODEL_2410 import MODEL2410
from VISA.PICOAMMETER import PICOAMMETER

from ArduinoHTRB import ArduinoHTRB

import time as tme
import pandas as pd

# ########## #
# VISA stuff #
# ########## #

#   # VISA controller, only one #   #
vc = VisaController(query='?*::INSTR', verbose=True)
#   # Various devices, as many as needed (but only one object for one real device) #   #
#inst = vc.get_instruments_by_name(MODEL2410.NAME)[0]
#k2410 = MODEL2410(inst)
inst = vc.get_instruments_by_name(PICOAMMETER.NAME)[0]
pico = PICOAMMETER(inst)
inst = vc.get_instruments_by_name(ArduinoHTRB.NAME)[0]
arduino = ArduinoHTRB(inst)
Diodes = ArduinoHTRB.Device

# ######## #
# Main App #
# ######## #
try:
    PATH = pathlib.Path("./csv")
    
    DIODE_LIST = [
    Diodes.B1,
    Diodes.B2,
    Diodes.B3,
    Diodes.B4,
    Diodes.B5,
    Diodes.B6,
    Diodes.B7,
    Diodes.B8,
    Diodes.B9,
    Diodes.B10,
    Diodes.B11,
    Diodes.B12]
    
    CYCLES = {}
    for diode in DIODE_LIST:
        CYCLES[diode] = 0
    
    DIODE_VOLTAGE = 1200 * .8
    DIODE_MAX_CURRENT = 200e-6
    DIODE_NORMAL_CURRENT = 100e-6
    PROTECTION_RESISTOR = 1e6/4
    DIODE_VOLTAGE = DIODE_VOLTAGE + DIODE_NORMAL_CURRENT*PROTECTION_RESISTOR
    DIODE_CURRENT_COMPLIANCE = 20e-3#DIODE_MAX_CURRENT * len(DIODE_LIST) + DIODE_VOLTAGE/PROTECTION_RESISTOR
    
    MEASURE_PERIOD = 60 #seconds
    
    COLUMNS = ['Timestamp_abs (s)', 'Timestamp_rel (ms)', 'Current (A)', 'Voltage (estimated) (V)', 'Status', 'Cycles']
    
    print("High Voltage value : ", DIODE_VOLTAGE)
    print("Current compliance : ", DIODE_CURRENT_COMPLIANCE)
    print("Tripping current : ", DIODE_MAX_CURRENT)

    arduino.orange(True)
    # k2410.melody([(440, .5), (300, .25), (350, .25), (440, .5), (500, .75)])

    # ################# #
    # Instruments setup #
    # ################# #

    #   # 2410 in v-source mode, output mode ZERO #  #
    # k2410.melody([(440, .25), (500, .5)])
    #k2410.v_source_wizard(DIODE_VOLTAGE, DIODE_CURRENT_COMPLIANCE)
    #k2410.output_mode = k2410.OutputModes.ZERO
    #k2410.text1_dis = False
    #k2410.text2_dis = False

    #   # Picoammeter #  #
    pico.zero_check = False
    pico.zero_correction = False
    pico.arm_count = 1
    pico.trig_count = 1

    #   # Boards #  #
    for diode in DIODE_LIST:
        delay = arduino.enable(diode, True)
        tme.sleep(delay + .5)

    # ###### #
    # Saving #
    # ###### #

    for diode in DIODE_LIST:
        filepath = PATH / ('diode_' + diode.value + '.csv')
        header = pd.DataFrame(columns=COLUMNS)
        header.to_csv(filepath, mode='a', index=False, header=True)

    # ##### #
    # Start #
    # ##### #
    global_over_current = False
    #k2410.output = True
    arduino.red(True)
    #k2410.key_press = k2410.Keys.I_MEAS
    #k2410.key_press = k2410.Keys.LOCAL

    stop = False
    while not stop:

        for diode in DIODE_LIST:

            # ########### #
            # Acquisition #
            # ########### #

            #k2410.beep(880, .2)
            #k2410.key_press = k2410.Keys.LOCAL

            delay = arduino.measure(diode, True)
            tme.sleep(delay + .5)

            data = pico.read()[0]

            delay = arduino.measure(diode, False)
            tme.sleep(delay + .5)
            
            CYCLES[diode] += 1
            
            print("Pico reading (",diode,") :", data)
            
            # ########## #
            # Protection #
            # ########## #
            
            over_current = False
            if data.current > DIODE_MAX_CURRENT:
                over_current = True
                delay = arduino.enable(diode, False)
                tme.sleep(delay + .5)
                #k2410.beep(220, 1)

            # ###### #
            # Saving #
            # ###### #
            
            voltage = DIODE_VOLTAGE - data.current*PROTECTION_RESISTOR
            if (not global_over_current) or over_current:
                filepath = PATH / ('diode_' + diode.value + '.csv')
                df = pd.DataFrame(columns=COLUMNS,
                                  data=[[round(tme.time()), data.timestamp, data.current, voltage, str(data.status), CYCLES[diode]]])
                df.to_csv(filepath, mode='a', index=False, header=False)

            if over_current:
                DIODE_LIST.remove(diode)

        # ######################### #
        # Delay to next measurement #
        # ######################### #

        tme.sleep(MEASURE_PERIOD)
        global_over_current = False
        #start = tme.time()
        #data = None
        #while ((start + MEASURE_PERIOD) > tme.time()) and not global_over_current:
        #    data = k2410.read()
        #    print("2410 reading : ", data[0].current)
        #    if data[0].current > (DIODE_NORMAL_CURRENT * len(DIODE_LIST) + DIODE_MAX_CURRENT):
        #        #k2410.beep(220, .4)
        #        k2410.key_press = k2410.Keys.LOCAL
        #        global_over_current = True
        #    else:
        #        tme.sleep(5)
        
        stop = len(DIODE_LIST) == 0

    #k2410.output = False
    arduino.red(False)

except Exception as e:
    #k2410.output = False
    arduino.red(True)
    arduino.orange(False)
    print(e)
    
    print("IT Service : 0651489404")
    while True:
        #k2410.beep(330, .5)
        tme.sleep(1)
        #k2410.beep(220, 1)
        tme.sleep(1)
    
else:
    #k2410.output = False
    arduino.orange(False)
    arduino.red(False)
