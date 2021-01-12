from enum import Enum

import Arduino.BuildArduino as BuildArduino
from VISA.VISA_controller import VisaController


class ArduinoHTRB:
    NAME = "HTRB_test"
    VERSION = "V1.1"

    __ARDUINO_PATH = '.\\HTRB\\'
    __arduino_args = [  # '-v',
        '-W', 'C:\\Program Files (x86)\\Arduino\\hardware\\arduino\\avr\\cores\\arduino',
        '-V', 'C:\\Program Files (x86)\\Arduino\\hardware\\arduino\\avr\\variants',
        '--dude-conf=C:\\Program Files (x86)\\Arduino\\hardware\\tools\\avr\\etc\\avrdude.conf',
        '-l', 'C:\\Program Files (x86)\\Arduino\\hardware\\arduino\\avr\\libraries\\SPI\\src',
        '-l', '.\\HTRB\\MCP23S17',
        '-b', 'uno',
        '-u', '',
        '-d', __ARDUINO_PATH
    ]

    class Device(Enum):
        A1 = "A1"
        A2 = "A2"
        A3 = "A3"
        A4 = "A4"
        A5 = "A5"
        A6 = "A6"
        A7 = "A7"
        A8 = "A8"
        A9 = "A9"
        A10 = "A10"
        A11 = "A11"
        A12 = "A12"
        B1 = "B1"
        B2 = "B2"
        B3 = "B3"
        B4 = "B4"
        B5 = "B5"
        B6 = "B6"
        B7 = "B7"
        B8 = "B8"
        B9 = "B9"
        B10 = "B10"
        B11 = "B11"
        B12 = "B12"

    def __init__(self, instr: VisaController.Instrument):
        self.__device = instr.device

        if instr.idn.name != ArduinoHTRB.NAME:
            raise TypeError("Instrument is not an Arduino !")

        # # Upload
        if instr.idn.ver != ArduinoHTRB.VERSION:
            print(f"{instr.idn.ver} != {ArduinoHTRB.VERSION} !\n Uploading new version...")

            ArduinoHTRB.__arduino_args[-3] = self.__device.resource_info[0].alias
            self.__device.close()

            BuildArduino.main(ArduinoHTRB.__arduino_args)

            self.__device.open()

    def enable(self, device: Device, on: bool) -> float:
        """Launch the enable/disable sequence on the specified board

        :param device: select the board
        :param on: enable (True)/disable (False)

        :return: estimated sequence duration in seconds
        """
        return int(self.__device.query(f":ENAB {device.value},{'1' if on else '0'}"))/1000

    def measure(self, device: Device, on: bool) -> float:
        """Launch the measure+stress/stress only sequence on the specified board

        :param device: select the board
        :param on: measure+stress (True)/stress only (False)

        :return: estimated sequence duration in seconds
        """
        return int(self.__device.query(f":MES {device.value},{'1' if on else '0'}"))/1000

    def relay_on(self, device: Device, on: bool):
        """Activate/deactivate the "on" relay on the specified board
        This method is for debug only and shall not be used in production. Please use 'enable' instead.

        :param device: select the board
        :param on: activate (True)/deactivate (False)
        """
        self.__device.write(f":RELA:ON {device.value},{'1' if on else '0'}")

    def relay_gnd(self, device: Device, on: bool):
        """Activate/deactivate the "gnd(_mes)" relay on the specified board
        This method is for debug only and shall not be used in production. Please use 'enable' or 'measure' instead.

        :param device: select the board
        :param on: activate (True)/deactivate (False)
        """
        self.__device.write(f":RELA:GND {device.value},{'1' if on else '0'}")

    def relay_mes(self, device: Device, on: bool):
        """Activate/deactivate the "mes" relay on the specified board
        This method is for debug only and shall not be used in production. Please use 'enable' or 'measure' instead.

        :param device: select the board
        :param on: activate (True)/deactivate (False)
        """
        self.__device.write(f":RELA:MES {device.value},{'1' if on else '0'}")

    def orange(self, on: bool):
        """Activate/deactivate the orange light

        :param on: activate (True)/deactivate (False)
        """
        self.__device.write(f":LIGH:ORAN {'1' if on else '0'}")

    def red(self, on: bool):
        """Activate/deactivate the red light

        :param on: activate (True)/deactivate (False)
        """
        self.__device.write(f":LIGH:RED {'1' if on else '0'}")
