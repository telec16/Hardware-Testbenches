import math
from collections import namedtuple
from enum import Enum
from typing import List, Tuple, Callable
import time as tme


class MODEL2410:
    Data = namedtuple('Data', ['voltage', 'current', 'resistance', 'timestamp', 'status'])
    Data.__doc__ = """Store a point of data returned by the picoammeter"""
    Data.voltage.__doc__ += """ : Value in Volts (float)"""
    Data.current.__doc__ += """ : Value in Amps (float)"""
    Data.resistance.__doc__ += """ : Value in Ohms (float)"""
    Data.timestamp.__doc__ += """ : Time since start, in ms (float)"""
    Data.status.__doc__ += """ : Details about the reading (PICOAMMETER.Status)"""

    # ############### #
    # ## SMU enums ## #
    # ############### #

    class Sources(Enum):
        """An enumeration to select in which mode the SMU will be used."""
        VOLTAGE = 'VOLT'
        CURRENT = 'CURR'
        MEMORY = 'MEM'

    class OutputModes(Enum):
        """An enumeration to select the output mode."""
        HIGH_Z = 'HIMP'
        NORMAL = 'NORM'
        ZERO = 'ZERO'
        GUARD = 'GUAR'

    class Keys(Enum):
        """An enumeration that describe all the keys of the instrument."""
        RANGE_UP = "1"
        SOURCE_DOWN = "2"
        LEFT = "3"
        MENU = "4"
        FCTN = "5"
        FILTER = "6"
        SPEED = "7"
        EDIT = "8"
        AUTO = "9"
        RIGHT = "10"
        EXIT = "11"
        V_SOURCE = "12"
        LIMITS = "13"
        STORE = "14"
        V_MEAS = "15"
        TOGGLE = "16"
        RANGE_DOWN = "17"
        ENTER = "18"
        I_SOURCE = "19"
        TRIG = "20"
        RECALL = "21"
        I_MEAS = "22"
        LOCAL = "23"
        ON_OFF = "24"
        SOURCE = "26"
        SWEEP = "27"
        CONFIG = "28"
        OHM = "29"
        REL = "30"
        DIGITS = "31"
        FRONT_REAR = "32"

    class Status(Enum):
        """An enumeration that describe the current status (errors) of the instrument."""
        OVERFLOW = (0, "Over-range during measurement")
        FILTER = (1, "Averaging filter is enabled")
        FRONT_REAR = (2, "FRONT terminals are selected")
        COMPLIANCE = (3, "Currently in real compliance")
        OVP = (4, "Over voltage protection was reached")
        MATHS = (5, "CALC1 is enabled")
        NULL = (6, "Null is enabled")
        LIMITS = (7, "Limit test on CALC2 is enabled")
        LIM_BIT8 = (8, "Provides limit test results (BIT8)")
        LIM_BIT9 = (9, "Provides limit test results (BIT9)")
        AUTO_OHMS = (10, "Auto Ohms is enabled")
        V_MEAS = (11, "V-Measure is enabled")
        I_MEAS = (12, "I-Measure is enabled")
        O_MEAS = (13, "Ω-Measure is enabled")
        V_SOURCE = (14, "V-Source used")
        I_SOURCE = (15, "I-Source used")
        RANGE_COMPLIANCE = (16, "Currently in range compliance")
        OFFSET = (17, "Offset Compensated Ohms is enabled")
        CONTACT = (18, "Contact check failure")
        LIM_BIT19 = (19, "Provides limit test results (BIT19)")
        LIM_BIT20 = (20, "Provides limit test results (BIT20)")
        LIM_BIT21 = (21, "Provides limit test results (BIT21)")
        REMOTE_SENSE = (22, "4-wire remote sense selected")
        PULSE_MODE = (23, "Currently in the Pulse Mode")

    @staticmethod
    # TODO: def __parse_enum(enum: Enum[EnumMember], s: str) -> EnumMember:
    def __parse_enum(enum, s: str):
        """Transform a string to an enum member

        :param enum: the enum class.
        :param s: the enum member value's string.
        :return: the enum member.

        >>>MODEL2410.__parse_enum(MODEL2410.Sources, 'VOLT')
        <Sources.VOLTAGE: 'VOLT'>
        """
        for e in enum:
            if e.value in s:
                return e

        raise KeyError()

    @staticmethod
    def __list_errors(enum, val: int) -> List:
        """Return a list of error enum member, corresponding to the value of val.

        :param enum: the error enum class.
        :param val: the error value from the instrument.
        :return: a list of error enum member.
        """
        return [e for e in enum if ((val >> e.value[0]) & 1) == 1]

    # ############# #
    # ## Methods ## #
    # ############# #

    NAME = "MODEL 2410"

    def __init__(self, instr):
        """Initialize the instrument.
        More than one instrument can be instanced.

        :param instr: the value returned by VisaController.get_instruments_by_name(...).
        :raise TypeError: "Instrument is not a Keithley 2410 !" : specified instrument must be a Keithley 2410.

        >>>from VISA.VISA_controller import VisaController
        ...from VISA.MODEL_2410 import MODEL2410
        ...vc = VisaController()
        ...k2410 = MODEL2410(vc.get_instruments_by_name(MODEL2410.NAME)[0])

        """
        self.__device = instr.device

        if MODEL2410.NAME not in self.__device.query("*IDN?"):
            raise TypeError("Instrument is not a Keithley 2410 !")

    def v_source_wizard(self, volt: float, compliance: float):
        """Automatically configure the instrument in voltage source mode,
        with the specified voltage and current compliance.

        :param volt: Constant voltage
        :param compliance: Current compliance
        """
        self.source = MODEL2410.Sources.VOLTAGE

        self.compliance_current = compliance
        self.sense_current = compliance  # Setting range (auto)

        self.source_voltage_range = volt  # setting range (auto)
        self.source_voltage = volt

    def i_source_wizard(self, amp: float, compliance: float):
        """Automatically configure the instrument in current source mode,
        with the specified current and voltage compliance.

        :param amp: Constant current
        :param compliance: Voltage compliance
        """
        self.source = MODEL2410.Sources.CURRENT

        self.sense_voltage = compliance  # Setting range (auto)
        self.compliance_voltage = compliance

        self.source_current_range = amp  # setting range (auto)
        self.source_current = amp

    def read(self) -> List[Data]:
        """Read a new value from the 2410.

        :return: a list of Data('voltage', 'current', 'resistance', 'timestamp', 'status')
        """
        readings = self.__device.query(":READ?").split(',')  # Split by ','
        readings = [float(x) for x in readings]  # Convert to float
        readings[4::5] = [MODEL2410.__list_errors(MODEL2410.Status, int(x))
                          for x in readings[4::5]]  # Evaluate status bits
        readings = [readings[i:i + 5] for i in range(0, len(readings), 5)]  # Split every 5 items
        data = [MODEL2410.Data(*x) for x in readings]  # Create data list
        return data

    def iv_wizard(self, i_compliance: float, v_start: float = 0, v_stop: float = 0, v_step: float = 1,
                  v_list: List[float] = None, settle_time: float = .05, autoscale: bool = False) -> List[Data]:
        """Create a list of Data points, for each specified voltage (from linear ramp or custom list)

        :param i_compliance: Maximum current
        :param v_start: Start voltage of the ramp (included)
        :param v_stop: End voltage of the ramp (included)
        :param v_step: Step voltage between Start and Stop (can be absolute)
        :param v_list: Custom voltages list that replace v_start, v_stop, and v_step
        :param settle_time: Delay between voltage change and reading
        :param autoscale: If the measure is to low compared to the compliance, adjust the compliance and retry
        :return: a list of Data('voltage', 'current', 'resistance', 'timestamp', 'status')
        """
        self.key_press = MODEL2410.Keys.I_MEAS
        return self.yx_wizard(self.v_source_wizard, i_compliance, v_start, v_stop, v_step,
                              v_list, settle_time, autoscale)

    def vi_wizard(self, v_compliance: float, i_start: float = 0, i_stop: float = 0, i_step: float = 1,
                  i_list: List[float] = None, settle_time: float = .05, autoscale: bool = False) -> List[Data]:
        """Create a list of Data points, for each specified current (from linear ramp or custom list)

        :param v_compliance: Maximum voltage
        :param i_start: Start current of the ramp (included)
        :param i_stop: End current of the ramp (included)
        :param i_step: Step current between Start and Stop (can be absolute)
        :param i_list: Custom currents list that replace i_start, i_stop, and i_step
        :param settle_time: Delay between voltage change and reading
        :param autoscale: If the measure is to low compared to the compliance, adjust the compliance and retry
        :return: a list of Data('voltage', 'current', 'resistance', 'timestamp', 'status')
        """
        self.key_press = MODEL2410.Keys.V_MEAS
        return self.yx_wizard(self.i_source_wizard, v_compliance, i_start, i_stop, i_step,
                              i_list, settle_time, autoscale)

    def yx_wizard(self, x_source_wizard: Callable[[float, float], None], y_compliance: float,
                  x_start: float = 0, x_stop: float = 0, x_step: float = 1, x_list: List[float] = None,
                  settle_time: float = .05, autoscale: bool = False) -> List[Data]:
        """Create a list of Data points, for each specified x (from linear ramp or custom list)

        :param x_source_wizard: Either v_source_wizard or i_source_wizard
        :param y_compliance: Maximum y
        :param x_start: Start x of the ramp (included)
        :param x_stop: End x of the ramp (included)
        :param x_step: Step x between Start and Stop (can be absolute)
        :param x_list: Custom x list that replace i_start, i_stop, and i_step
        :param settle_time: Delay between voltage change and reading
        :param autoscale: If the measure is to low compared to the compliance, adjust the compliance and retry
        :return: a list of Data('voltage', 'current', 'resistance', 'timestamp', 'status')
        """
        self.output = False
        if x_list is None:
            x_step = abs(x_step) if (x_start < x_stop) else -abs(x_step)
            x_list = [x * x_step + x_start for x in range(round((x_stop - x_start) / x_step + .5))]
            if x_list[-1] != x_stop:
                x_list.append(x_stop)
        data = []

        x_source_wizard(0, y_compliance)
        x_source_wizard(x_list[0], y_compliance)
        self.output = True
        for i in x_list:
            reading = None
            comp = y_compliance
            while comp is not None:
                x_source_wizard(i, comp)
                if settle_time > 0:
                    tme.sleep(settle_time)
                reading = self.read()[0]

                # Doing at max two measure per data (only one retry)
                if not autoscale or comp != y_compliance:
                    comp = None
                else:
                    comp = self.__good_reading(x_source_wizard, reading, y_compliance)

            data.append(reading)
        self.output = False
        x_source_wizard(0, y_compliance)

        return data

    @staticmethod
    def __good_reading(x_source_wizard: Callable[[float, float], None], data: Data, compliance: float):
        values = {MODEL2410.v_source_wizard.__name__: data.current,
                  MODEL2410.i_source_wizard.__name__: data.voltage}

        value = abs(values.get(x_source_wizard.__name__) or 0) * 100
        if value < compliance:
            return max(value, 1e-6)
        return None

    def beep(self, freq: float, t: float, wait: bool = False):
        """Produce a sound of the specified frequency and duration. Blocking or non-blocking call."""
        freq = min(max(freq, 65), 2e6)
        t = min(max(t, 0), 7.9)
        self.__device.write(f":SYST:BEEP:STAT 1")
        self.__device.write(f":SYST:BEEP {freq}, {t}")
        if wait:
            tme.sleep(t)

    def melody(self, mel: List[Tuple[float, float]]):
        """Read and play a list of sound."""
        for m in mel:
            self.beep(*m, True)

    # ################ #
    # ## Attributes ## #
    # ################ #

    # ## Global attributes ## #
    @property
    def output(self) -> bool:
        """Unleash the juice !"""
        return self.__device.query(":OUTP:STATE?") == "ON"

    @output.setter
    def output(self, out: bool):
        self.__device.write(f":SYST:BEEP:STAT 0")
        self.__device.write(f":OUTP:STATE {'ON' if out else 'OFF'}")
        self.__device.write(f":SYST:BEEP:STAT 1")

    @property
    def output_mode(self) -> OutputModes:
        """Get/Set the output mode"""
        return MODEL2410.__parse_enum(MODEL2410.OutputModes, self.__device.query(":OUTP:SMOD?"))

    @output_mode.setter
    def output_mode(self, out: OutputModes):
        self.__device.write(f":OUTP:SMOD {out.value}")

    @property
    def key_press(self) -> Keys:
        """Get/Simulate key press."""
        return MODEL2410.__parse_enum(MODEL2410.Keys, self.__device.query(":SYST:KEY?"))

    @key_press.setter
    def key_press(self, key: Keys):
        self.__device.write(f":SYST:KEY {key.value}")

    @property
    def source(self) -> Sources:
        """Get/Set the type of output source"""
        return MODEL2410.__parse_enum(MODEL2410.Sources, self.__device.query(":SOUR:FUNC:MODE?"))

    @source.setter
    def source(self, src: Sources):
        self.__device.write(f":SOUR:FUNC:MODE {src.value}")

    # \/ Upper text \/
    @property
    def text1(self) -> str:
        """Get/Set the custom display text, line 1 (max width of 20 char)."""
        return self.__device.query(":DISP:WIND1:TEXT:DATA?")

    @text1.setter
    def text1(self, txt: str):
        txt = txt[:20] if len(txt) > 20 else txt
        self.__device.write(f':DISP:WIND1:TEXT:DATA "{txt}"')

    @property
    def text1_dis(self) -> bool:
        """Check if displayed/Display the custom display text, line 1."""
        return self.__device.query(":DISP:WIND1:TEXT:STAT?") == "1"

    @text1_dis.setter
    def text1_dis(self, display: bool):
        self.__device.write(f":DISP:WIND1:TEXT:STAT {'1' if display else '0'}")

    # /\ Upper text /\

    # \/ Lower text \/
    @property
    def text2(self) -> str:
        """Get/Set the custom display text, line 2 (max width of 32 char)."""
        return self.__device.query(":DISP:WIND2:TEXT:DATA?")

    @text2.setter
    def text2(self, txt: str):
        txt = txt[:32] if len(txt) > 32 else txt
        self.__device.write(f':DISP:WIND2:TEXT:DATA "{txt}"')

    @property
    def text2_dis(self) -> bool:
        """Check if displayed/Display the custom display text, line 2."""
        return self.__device.query(":DISP:WIND2:TEXT:STAT?") == "1"

    @text2_dis.setter
    def text2_dis(self, display: bool):
        self.__device.write(f":DISP:WIND2:TEXT:STAT {'1' if display else '0'}")

    # /\ Lower text /\

    # ## V-Source attributes ## #
    @property
    def source_voltage(self) -> float:
        """Get/Set source voltage (in V-source mode)."""
        return float(self.__device.query(":SOUR:VOLT?"))

    @source_voltage.setter
    def source_voltage(self, volt: float):
        self.__device.write(f":SOUR:VOLT {volt}")

    @property
    def source_voltage_range(self) -> float:
        """Get/Set source voltage range (in V-source mode)."""
        return float(self.__device.query(":SOUR:VOLT:RANG?"))

    @source_voltage_range.setter
    def source_voltage_range(self, v_range: float):
        self.__device.write(f":SOUR:VOLT:RANG {v_range}")

    @property
    def compliance_current(self) -> float:
        """Get/Set current compliance (in V-source mode)."""
        return float(self.__device.query(":SENS:CURR:PROT?"))

    @compliance_current.setter
    def compliance_current(self, curr: float):
        self.__device.write(f":SENS:CURR:PROT {curr}")

    @property
    def sense_current(self) -> float:
        """Get/Set current compliance range (in V-source mode)."""
        return float(self.__device.query(":SENS:CURR:RANG?"))

    @sense_current.setter
    def sense_current(self, c_range: float):
        self.__device.write(f":SENS:CURR:RANG {c_range}")

    # ## I-Source attributes ## #
    @property
    def source_current(self) -> float:
        """Get/Set source current (in I-source mode)."""
        return float(self.__device.query(":SOUR:CURR?"))

    @source_current.setter
    def source_current(self, curr: float):
        self.__device.write(f":SOUR:CURR {curr}")

    @property
    def source_current_range(self) -> float:
        """Get/Set source current range(in I-source mode)."""
        return float(self.__device.query(":SOUR:CURR:RANG?"))

    @source_current_range.setter
    def source_current_range(self, v_range: float):
        self.__device.write(f":SOUR:CURR:RANG {v_range}")

    @property
    def compliance_voltage(self) -> float:
        """Get/Set voltage compliance (in I-source mode)."""
        return float(self.__device.query(":SENS:VOLT:PROT?"))

    @compliance_voltage.setter
    def compliance_voltage(self, volt: float):
        self.__device.write(f":SENS:VOLT:PROT {volt}")

    @property
    def sense_voltage(self) -> float:
        """Get/Set voltage compliance range (in I-source mode)."""
        return float(self.__device.query(":SENS:VOLT:RANG?"))

    @sense_voltage.setter
    def sense_voltage(self, v_range: float):
        self.__device.write(f":SENS:VOLT:RANG {v_range}")


if __name__ == "__main__":
    from VISA_controller import VisaController
    import time

    vc = VisaController(query='?*::INSTR', verbose=True)
    inst = vc.get_instruments_by_name(MODEL2410.NAME)[0]
    k2410 = MODEL2410(inst)
