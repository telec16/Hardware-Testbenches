import pathlib, sys

sys.path.append(str(pathlib.Path('../_libs/').resolve()))

from VISA.VISA_controller import VisaController
from VISA.DS4024 import DS4024

from ArduinoCLDBurn import ArduinoCLD
from plot_cld import plot_cld
from save_cld import save_cld

import time as tme

try:
    from getch import getch
except ImportError:
    from msvcrt import getch


# Put all arrays to the size of the smaller one
def resize(*args: list):
    size = min(*[len(arg) for arg in args])
    r_args = [arg[0:size] for arg in args]
    return tuple(r_args)


# ########## #
# VISA stuff #
# ########## #

#   # VISA controller, only one #   #
vc = VisaController(query='?*::INSTR', verbose=True)
#   # Various devices, as many as needed (but only one object for one real device) #   #
inst = vc.get_instruments_by_name(DS4024.NAME)[0]
ds = DS4024(inst)
inst = vc.get_instruments_by_name(ArduinoCLD.NAME)[0]
arduino = ArduinoCLD(inst)

# ######## #
# Main App #
# ######## #
try:
    #   # Default parameters, will be changed in GUI #  #
    path_png = pathlib.Path("./png_graph_gros")
    path_csv = pathlib.Path("./csv_gros")
    
    name="CALY_KE12LS060a_30"
    max_voltage = 4
    max_current = 3
    shunt = 0.0256
    pw = 3e3

    arduino.orange(True)

    # ################# #
    # Instruments setup #
    # ################# #

    #   # Scope channels #  #
    ds.chn_display(ds.Channels.CHANNEL1, True)
    ds.chn_display(ds.Channels.CHANNEL2, True)
    ds.chn_display(ds.Channels.CHANNEL3, False)
    ds.chn_display(ds.Channels.CHANNEL4, False)

    #   # Channels ratio #  #
    ds.set_chn_ratio(ds.Channels.CHANNEL1, ds.Ratios.X10)
    ds.set_chn_ratio(ds.Channels.CHANNEL2, ds.Ratios.X1)

    #   # Time scale #  #
    ds.time_scale = pw / 10e3  # 14 divs on this screen !
    ds.time_offset = (pw / 10e3) * 5

    #   # Channels scale #  #
    ds.set_chn_scale(ds.Channels.CHANNEL1, max_voltage / 6)
    ds.set_chn_scale(ds.Channels.CHANNEL2, (max_current * shunt) / 6)
    ds.set_chn_offset(ds.Channels.CHANNEL1, -max_voltage / 2)
    ds.set_chn_offset(ds.Channels.CHANNEL2, -(max_current * shunt) / 2)

    #   # Trigger #  #
    ds.level = max_voltage / 2
    ds.edge = ds.Slopes.POSITIVE

    # ################# #
    # Start a pulse row #
    # ################# #

    arduino.red(True)
    for i in range(50):


        # ########### #
        # Acquisition #
        # ########### #

        #   # Start scope in SINGLE mode and pulse ! #  #
        ds.running = True
        ds.sweep = ds.Sweeps.SINGLE
        tme.sleep(.5)
        while ds.status != ds.Status.WAIT:
            pass
            
        arduino.long_pulse(pw)

        #   # Wait until acquired #  #
        while not ds.stopped:
            pass

        #   # Retrieve data #  #
        time, volt = ds.get_curve(ds.Channels.CHANNEL1)
        _, current = ds.get_curve(ds.Channels.CHANNEL2, custom_scale=1 / shunt)
        time, volt, current = resize(time, volt, current)

        #   # Check for over current #  #
        
        # ###### #
        # Saving #
        # ###### #

        cld_filename = name + '_' + str(int(i))

        #   # Plotting (and saving to png) #  #
        plot_cld(time, volt, current, cld_filename, time_scale=1e3, max_voltage=max_voltage * 4 / 3,
                 max_current=max_current + 1, show=False, save=True, path=path_png)

        #   # Saving to csv #  #
        save_cld(time, volt, current, cld_filename, path=path_csv)


    #   # End of pulse row, ready to the next one #  #
    arduino.red(False)

except Exception as e:
    arduino.red(False)
    print(e)
finally:
    arduino.orange(False)
    arduino.red(False)
