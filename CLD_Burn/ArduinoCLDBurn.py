import Arduino.BuildArduino as BuildArduino
from VISA.VISA_controller import VisaController


class ArduinoCLD:
    NAME = "CLD_burning"
    VERSION = "V1.6"

    __ARDUINO_PATH = '.\\burn_CLD_burn\\'
    # __arduino_args = [  # '-v',
    #     '-W', 'C:\\Program Files (x86)\\Arduino\\hardware\\arduino\\avr\\cores\\arduino',
    #     '-V', 'C:\\Program Files (x86)\\Arduino\\hardware\\arduino\\avr\\variants',
    #     '--dude-conf=C:\\Program Files (x86)\\Arduino\\hardware\\tools\\avr\\etc\\avrdude.conf',
    #     '-b', 'uno',
    #     '-u', '',
    #     '-d', __ARDUINO_PATH
    # ]
    __arduino_args = [  # '-v',
        '-W', 'C:\\Program Files\\Arduino\\hardware\\arduino\\avr\\cores\\arduino',
        '-V', 'C:\\Program Files\\Arduino\\hardware\\arduino\\avr\\variants',
        '--dude-conf=C:\\Program Files\\Arduino\\hardware\\tools\\avr\\etc\\avrdude.conf',
        '-b', 'uno',
        '-u', '',
        '-d', __ARDUINO_PATH
    ]

    def __init__(self, instr: VisaController.Instrument):
        self.__device = instr.device

        if instr.idn.name != ArduinoCLD.NAME:
            raise TypeError("Instrument is not an Arduino !")

        # # Upload
        if instr.idn.ver != ArduinoCLD.VERSION:
            print(f"{instr.idn.ver} != {ArduinoCLD.VERSION} !\n Uploading new version...")

            ArduinoCLD.__arduino_args[-3] = self.__device.resource_info[0].alias
            self.__device.close()

            BuildArduino.main(ArduinoCLD.__arduino_args)

            self.__device.open()

    def pulse(self, width: float) -> str:
        return self.__device.query(f":PULS {width}")
        
    def long_pulse(self, width: float):
        self.__device.write(f":LPUL {width}")

    def orange(self, on: bool):
        self.__device.write(f":LIGH:ORAN {'1' if on else '0'}")

    def red(self, on: bool):
        self.__device.write(f":LIGH:RED {'1' if on else '0'}")
