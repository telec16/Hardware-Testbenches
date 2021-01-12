import Arduino.BuildArduino as BuildArduino
from VISA.VISA_controller import VisaController


class ArduinoAlim:
    NAME = "Alim0_1500V"
    VERSION = "v2.0"

    __ARDUINO_PATH = '.\\Alim\\'
    __arduino_args = [  # '-v',
        '-W', 'C:\\Program Files\\Arduino\\hardware\\arduino\\avr\\cores\\arduino',
        '-V', 'C:\\Program Files\\Arduino\\hardware\\arduino\\avr\\variants',
        '--dude-conf=C:\\Program Files\\Arduino\\hardware\\tools\\avr\\etc\\avrdude.conf',
        '-l', 'C:\\Program Files\\Arduino\\hardware\\arduino\\avr\\libraries\\SPI\\src',
        '-l', '.\\Alim\\MCP4922',
        '-b', 'uno',
        '-u', '',
        '-d', __ARDUINO_PATH
    ]
    
    def __init__(self, instr: VisaController.Instrument):
        self.__device = instr.device

        if instr.idn.name != ArduinoAlim.NAME:
            raise TypeError("Instrument is not an Arduino !")

        # # Upload
        if instr.idn.ver != ArduinoAlim.VERSION:
            print(f"{instr.idn.ver} != {ArduinoAlim.VERSION} !\n Uploading new version...")

            ArduinoAlim.__arduino_args[-3] = self.__device.resource_info[0].alias
            self.__device.close()

            BuildArduino.main(ArduinoAlim.__arduino_args)

            self.__device.open()
            
    def set_output_voltage(self, HV_voltage):
        self.__device.write(f":VOLT:OUT,{HV_voltage}")
       
    def rampe_voltage(self, final_voltage, nb_step, step_time):
        self.__device.write(f":VOLT:RAMPE:AUTO,{final_voltage};{nb_step}/{step_time}")
       
    def output_relay(self, ON):
        self.__device.write(f":RELA:OUT {'1' if ON else '0'}")
        
    def manu_rampe_voltage(self, HV_step):
        self.__device.write(f":VOLT:RAMPE:MANU,{HV_step}")
        
    def input_relay(self, ON):
        self.__device.write(f":RELA:IN {'1' if ON else '0'}")
    
    def voltage(self):
        try:
            return int(self.__device.query(":MEAS:VOLT?"))
        except Exception as e:
            return -1
        
    def close(self):
        self.__device.close()
        