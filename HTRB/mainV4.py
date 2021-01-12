import pathlib, sys

sys.path.append(str(pathlib.Path('../_libs/').resolve()))

from VISA.VISA_controller import VisaController
from VISA.PICOAMMETER import PICOAMMETER
from VISA.ArduinoAlim import ArduinoAlim

from ArduinoHTRB import ArduinoHTRB

import time as tme
from datetime import datetime
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
PATH_CARAC = pathlib.Path("./csv_carac")

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

MEASURE_INTER = []
j = 66

for x in range(197):
    #if(x < 10):
        #MEASURE_INTER.append(j)
        #j += 1
    if(x < 17):
        MEASURE_INTER.append(j)
        j += 2
    if(16 < x <= 197):
        MEASURE_INTER.append(j)
        j += 5
indice_carac = 0

list_voltage = []
volt = 0
for i in range(123):
    list_voltage.append(volt)
    volt += 10

print("High Voltage value : ", DIODE_VOLTAGE)
print("Current compliance : ", DIODE_CURRENT_COMPLIANCE)
print("Tripping current : ", DIODE_MAX_CURRENT)

# ##### #
# Setup #
# ##### #

Diode = namedtuple("Diode", ['board', 'name', 'isDead', 'maxCurrent', 'minCurrent', 'lastCurrent', 'cycles'])
COLUMNS = ['Timestamp_abs (s)', 'Timestamp_rel (ms)', 'Current (A)', 'Voltage (estimated) (V)','Voltage (real) (V)', 'Status', 'Cycles']
COLUMNS_CARAC = ['Rel_TimeStamp (s)', 'Voltage (V)', 'Current (A)']

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
    alim.output_relay(False)
    re_enable_alim = False

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
    alim.set_output_voltage(980)
    tme.sleep(2)
    alim.output_relay(True)
    arduino.red(True)

    START_TIMESTAMP = tme.time()

    stop = False
    while not stop:
        
        
        DIODES_TEMP = []
        
        # ################ #
        # Characterization #
        # ################ #
                
        #REL_TIME = tme.time() - START_TIMESTAMP
        if(tme.time() + 66*3600 > START_TIMESTAMP + MEASURE_INTER[indice_carac]*3600): #if time is right
            
            #  # Power Off #  #
            alim.output_relay(False)
            tme.sleep(1)
            alim.set_output_voltage(0)
            tme.sleep(1)
            alim.output_relay(True)
            
            #  # Disable HV on all board #  #
            for diodes in DIODES:
                delay = arduino.enable(diodes.board, False)
                tme.sleep(delay + 0.5)
            
            #  # Pico Param #  #
            pico.auto_range = False
            
            for diodes in DIODES:
                print(f"IdeV en cours sur {diodes.name}")
                pico.range = 2.1e-07
                alim.input_relay(True)
                save_time = tme.time() #  Unique timestamp, simpler. # (tme.time() - START_TIMESTAMP) + 66*3600
                filepath_carac = PATH_CARAC / ('diode_' + diodes.name + '_' + str(round(save_time)) + '.csv')
                header_carac = pd.DataFrame(columns=COLUMNS_CARAC)
                header_carac.to_csv(filepath_carac, mode='a', index=False, header=True)
                
                delay = arduino.enable(diodes.board, True)
                tme.sleep(delay + 0.5)
                
                delay = arduino.measure(diodes.board, True)
                tme.sleep(delay + .5)
                
                
                for voltage in list_voltage:
                    #  # Step voltage from list #  # 
                    alim.manu_rampe_voltage(voltage)
                    tme.sleep(0.1)
                    
                    #  # Read current and voltage #  #
                    volt_carac = alim.voltage()
                    tme.sleep(0.1)
                    data_carac = pico.read()[0]
                    
                    #  # Homemande Auto-range #  #
                    if(data_carac.current == 9.9e+37):
                        if(pico.range == 2.1e-07):
                            pico.range = 0.00002
                        elif(pico.range == 2.1e-5): 
                            pico.range = 0.0002 
                        elif(pico.range == 2.1e-4):
                            pico.range = 0.002
                        #  # Re-read current value due to overflow #  #
                        data_carac = pico.read()[0]
                    
                    #  # Save data in csv #  #
                    df_carac = pd.DataFrame(columns=COLUMNS_CARAC, data=[[round(tme.time()-START_TIMESTAMP) , volt_carac, data_carac.current]])
                    df_carac.to_csv(filepath_carac, mode='a', index=False, header=False)
                    
                
                alim.set_output_voltage(0)
                tme.sleep(4)
                delay = arduino.measure(diodes.board, False)
                tme.sleep(delay + 0.5)
                delay = arduino.enable(diodes.board, False)
                tme.sleep(delay + 0.5)
            
            #  # Enable HV on all boards #  #
            for diodes in DIODES:
                delay = arduino.enable(diodes.board, True)
                tme.sleep(delay + 0.5)
               
            pico.auto_range = True
            indice_carac += 1
            re_enable_alim = True
        
        if(re_enable_alim == True):
            #  # Power On #  #
            alim.output_relay(False)
            tme.sleep(2)
            alim.set_output_voltage(980)
            tme.sleep(2)
            alim.output_relay(True)
            re_enable_alim = False
        
        
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

                diode_voltage = alim.voltage() - data.current * PROTECTION_RESISTOR
                alim_voltage = alim.voltage()
                if (not global_over_current) or over_current:
                    print("Pico reading (", diode, ") :", data.current*1e6 ,"uA ","Actual Voltage = ", alim.voltage(), "V")
                    filepath = PATH / ('diode_' + diode_name + '.csv')
                    df = pd.DataFrame(columns=COLUMNS,
                                      data=[[round(tme.time()), data.timestamp, data.current, diode_voltage, alim_voltage, str(data.status),
                                             diode_temp.cycles]])
                    df.to_csv(filepath, mode='a', index=False, header=False)
                    
                
                
                
        DIODES = DIODES_TEMP
        
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

    alim.input_relay(False)
    arduino.red(False)

except Exception as e:
    arduino.red(True)
    arduino.orange(False)
    print(e)
    print("IT Service : 0651489404")
    print(str(datetime.today()))
except (KeyboardInterrupt, SystemExit, GeneratorExit) as e:
    alim.input_relay(False)
    arduino.red(True)
    arduino.orange(False)
    print(e)
    print(str(datetime.today()))
else:
    alim.input_relay(False)
    arduino.orange(False)
    arduino.red(False)
