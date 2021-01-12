import pathlib, sys

sys.path.append(str(pathlib.Path('../_libs/').resolve()))

from VISA.VISA_controller import VisaController
from VISA.DS4024 import DS4024
from VISA.MODEL_2410 import MODEL2410

from ArduinoCLDBurn import ArduinoCLD
from Gui_CLD import NextCldDialog, StartCldDialog
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
inst = vc.get_instruments_by_name(MODEL2410.NAME)[0]
k2410 = MODEL2410(inst)
inst = vc.get_instruments_by_name(ArduinoCLD.NAME)[0]
arduino = ArduinoCLD(inst)

# ######## #
# Main App #
# ######## #
try:
    #   # Default parameters, will be changed in GUI #  #
    path_png = pathlib.Path("./png_graph")
    path_csv = pathlib.Path("./csv")

    cld_info = dict(name="CALY_KE12LSB200-bonded_",
                    implanted=True,
                    size=6,
                    csv=True,
                    png=True,
                    show=False)

    parameters = dict(voltage=50,
                      max_current=20,
                      shunt=0.025600,
                      pw=[10, 30, 50, 70, 100, 120, 150, 200, 250, 300, 400, 500, 700, 1000, 1500, 2000, 3000, 5000,
                          10000])
    parameters = StartCldDialog.new_dialog_with_results(**parameters)  # Dialog box to change parameters
    if parameters is None:
        exit()

    arduino.orange(True)
    # k2410.melody([(440, .5), (300, .25), (350, .25), (440, .5), (500, .75)])

    stop = False
    while not stop:

        cld_info = NextCldDialog.new_dialog_with_results(**cld_info)  # Dialog box to change CLD
        if cld_info is None:
            break
        cld_base_filename = cld_info["name"] + '_' + \
                            'LCH' + str(cld_info['size']) + '_' + \
                            ('Imp' if cld_info["implanted"] else 'Noimp') + '_' + \
                            '25C' + '_' + \
                            str(int(parameters["voltage"])) + '_' + \
                            'square'

        print(f"### Base filename : {cld_base_filename} ###")

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

        #   # 2410 in v-source mode, output mode ZERO #  #
        # k2410.melody([(440, .25), (500, .5)])
        k2410.v_source_wizard(parameters["voltage"], 10e-3)
        k2410.output_mode = k2410.OutputModes.ZERO
        k2410.text1_dis = False

        # ################# #
        # Start a pulse row #
        # ################# #

        k2410.output = True
        arduino.red(True)
        k2410.key_press = k2410.Keys.V_MEAS
        k2410.key_press = k2410.Keys.LOCAL
        tme.sleep(parameters["voltage"] / 100 + 1)
        for pw in parameters["pw"]:

            # ################# #
            # Instruments setup #
            # ################# #

            #   # Time scale #  #
            ds.time_scale = pw / 10e6  # 14 divs on this screen !
            ds.time_offset = (pw / 10e6) * 5

            #   # Channels scale #  #
            ds.set_chn_scale(ds.Channels.CHANNEL1, parameters["voltage"] / 6)
            ds.set_chn_scale(ds.Channels.CHANNEL2, (parameters["max_current"] * parameters["shunt"]) / 6)
            ds.set_chn_offset(ds.Channels.CHANNEL1, -parameters["voltage"] / 2)
            ds.set_chn_offset(ds.Channels.CHANNEL2, -(parameters["max_current"] * parameters["shunt"]) / 2)

            #   # Trigger #  #
            ds.level = parameters["voltage"] / 2
            ds.edge = ds.Slopes.POSITIVE

            # ########### #
            # Acquisition #
            # ########### #

            #   # Start scope in SINGLE mode and pulse ! #  #
            k2410.beep(880, .2)
            ds.running = True
            ds.sweep = ds.Sweeps.SINGLE
            tme.sleep(.5)
            k2410.key_press = k2410.Keys.LOCAL
            print(arduino.pulse(pw))

            #   # Wait until acquired #  #
            while not ds.stopped:
                pass

            #   # Retrieve data #  #
            time, volt = ds.get_curve(ds.Channels.CHANNEL1)
            _, current = ds.get_curve(ds.Channels.CHANNEL2, custom_scale=1 / parameters["shunt"])
            time, volt, current = resize(time, volt, current)

            #   # Check for over current #  #
            surge_current = max(current)
            nominal_current = current[int(len(current) / 2)]
            over_current = surge_current > parameters["max_current"]
            if over_current:
                print("OVER CURRENT !")
                k2410.text1 = f"{'The CLD burned !':^20}"
                k2410.text1_dis = True
                k2410.output = False
                k2410.melody([(392, .250), (262, .500)])
                # k2410.melody([(300, .75), (2e6, .25), (375, .5), (2e6, .25), (350, .25), (325, .25), (2e6, .25), (340, .25), (310, .25),(2e6, .25), (340, .25), (310, .5)])

            # ###### #
            # Saving #
            # ###### #

            cld_filename = cld_base_filename + '_' + \
                           str(int(pw)) + 'us' + '_' + \
                           str(int(round(surge_current))) + 'A' + '-' + \
                           str(int(round(nominal_current))) + 'A' + \
                           ('_BURNED' if over_current else '')

            #   # Plotting (and saving to png) #  #
            plot_cld(time, volt, current, cld_filename, time_scale=1e6, max_voltage=parameters["voltage"] * 4 / 3,
                     max_current=parameters["max_current"] + 1, show=cld_info["show"], save=cld_info["png"],
                     path=path_png)

            #   # Saving to csv #  #
            if cld_info["csv"]:
                save_cld(time, volt, current, cld_filename, path=path_csv)

            if over_current:
                break

        #   # End of pulse row, ready to the next one #  #
        k2410.output = False
        arduino.red(False)

except Exception as e:
    k2410.output = False
    arduino.red(False)
    print(e)
finally:
    k2410.output = False
    arduino.orange(False)
    arduino.red(False)
