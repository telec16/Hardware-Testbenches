from enum import Enum
from typing import TypeVar, List, Tuple
import time as tme

import visa


class DS4024:
    # ################# #
    # ## Scope enums ## #
    # ################# #

    EnumMember = TypeVar('EnumMember')

    class Sources(Enum):
        """An enumeration to select the used source for the trigger. Do not mix up with Channels."""
        CHANNEL1 = 'CHAN1'
        CHANNEL2 = 'CHAN2'
        CHANNEL3 = 'CHAN3'
        CHANNEL4 = 'CHAN4'
        EXTERNAL = 'EXT'
        EXTERNAL5 = 'EXT5'
        AC_LINE = 'ACL'

    class Slopes(Enum):
        """An enumeration to select the triggering edge."""
        POSITIVE = 'POS'
        NEGATIVE = 'NEG'
        EITHER = 'RFAL'

    class Couplings(Enum):
        """An enumeration to select the coupling of the trigger (or a channel)."""
        DC = 'DC'
        AC = 'AC'
        LF_REJECT = 'LFR'
        HF_REJECT = 'HFR'

    class Sweeps(Enum):
        """An enumeration to select the trigger mode."""
        AUTO = 'AUTO'
        NORMAL = 'NORM'
        SINGLE = 'SING'

    class Status(Enum):
        """An enumeration that describe the current state of the scope's trigger."""
        RUN = 'RUN'
        STOP = 'STOP'
        TRIGGERED = 'TD'
        WAIT = 'WAIT'
        AUTO = 'AUTO'

    class Channels(Enum):
        """An enumeration for each channel of the scope"""
        CHANNEL1 = 'CHAN1'
        CHANNEL2 = 'CHAN2'
        CHANNEL3 = 'CHAN3'
        CHANNEL4 = 'CHAN4'

    class Ratios(Enum):
        """An enumeration to select the channel probe ratio."""
        X001 = '0.01'
        X002 = '0.02'
        X005 = '0.05'
        X01 = '0.1'
        X02 = '0.2'
        X05 = '0.5'
        X1 = '1'
        X2 = '2'
        X5 = '5'
        X10 = '10'
        X20 = '20'
        X50 = '50'
        X100 = '100'
        X200 = '200'
        X500 = '500'
        X1000 = '1000'

    class Errors(Enum):
        """An enumeration that describe the current status (errors) of the scope."""
        ERROR_SYSTEM_VOLTAGE = (0, "System voltage error")
        ERROR_ANA_VOL = (1, "Analog voltage error")
        ERROR_STORAGE_VOL = (2, "Storage voltage error")
        ERROR_DIG_CORE_VOL = (3, "Digital core voltage error")
        ERROR_DIG_PER_VOL = (4, "Digital PER voltage error")
        ERROR_BATT = (8, "Battery error")
        ERROR_FAN1 = (9, "FAN1 error")
        ERROR_FAN2 = (10, "FAN2 error")
        ERROR_TEMPE1 = (12, "Temperature 1 error")
        ERROR_TEMPE2 = (13, "Temperature 2 error")
        ERROR_TMO = (16, "Timeout error")

    @staticmethod
    # TODO: def __parse_enum(enum: Enum[EnumMember], s: str) -> EnumMember:
    def __parse_enum(enum, s: str):
        """Transform a string to an enum member

        :param enum: the enum class.
        :param s: the enum member value's string.
        :return: the enum member.

        >>>DS4024.__parse_enum(DS4024.Status, 'RUN')
        <Status.RUN: 'RUN'>
        """
        for e in enum:
            if e.value in s:
                return e

        raise KeyError()

    @staticmethod
    def __list_errors(enum, val: int) -> List:
        """Return a list of error enum member, corresponding to the value of val.

        :param enum: the error enum class.
        :param val: the error value from the scope.
        :return: a list of error enum member.
        """
        return [e for e in enum if ((val >> e.value[0]) & 1) == 1]

    # ############# #
    # ## Methods ## #
    # ############# #

    NAME = "DS4024"

    def __init__(self, instr):
        """Initialize the instrument.
        More than one instrument can be instanced.

        :param instr: the value returned by VisaController.get_instruments_by_name(...).
        :raise TypeError: "Instrument is not a DS4024 !" : specified instrument must be a DS4024.

        >>>from VISA.VISA_controller import VisaController
        ...from VISA.DS4024 import DS4024
        ...vc = VisaController()
        ...ds = DS4024(vc.get_instruments_by_name(DS4024.NAME)[0])

        """
        self.__device = instr.device

        if DS4024.NAME not in self.__device.query("*IDN?"):
            raise TypeError("Instrument is not a DS4024 !")

    def get_curve(self, chn: Channels, tmo: int = 5, custom_scale: float = 1) -> Tuple[List[float], List[float]]:
        """Retrieve waveform data.
        This method will start an acquisition of the current waveform,
        and wait until all data is gathered or after the specified timeout.
        A scaling can be applied to the y values.
        This will leave the scope in a stopped state.

        :param chn: the channel to retrieve.
        :param tmo: timeout until abort waiting and start gathering data.
        :param custom_scale: a scale that is applied to the y value.
        :return: (relative time (seconds), y values (in units, like volts or amps)).
        """
        self.__device.write(":STOP")  # This is needed
        m_dep = int(self.__device.query(":ACQ:MDEP?"))

        # Initializing data retrieving
        self.__device.write(f":WAV:SOUR {chn.value}")
        self.__device.write(":WAV:MODE RAW")
        self.__device.write(":WAV:FORM BYTE")
        self.__device.write(f":WAV:POIN {m_dep}")
        self.__device.write(":WAV:RES")
        # Begin
        self.__device.write(":WAV:BEG")

        # Wait until ready
        # TODO: Make it works for 100k+ depth
        tries = 0
        m_depl = -1
        ready, m_dep = self.reading_status
        while not ready:
            tme.sleep(.5)

            ready, m_dep = self.reading_status

            tries = tries + 1 if (m_dep == m_depl) else 0

            ready |= (tries > tmo)
            m_depl = m_dep

        # Retrieve data
        try:
            data = self.__device.query_binary_values(":WAV:DATA?", is_big_endian=False, datatype='B')
        except visa.VisaIOError as e:
            print(e)
            return [], []
        m_dep = len(data)

        # End
        self.__device.write(":WAV:END")

        # Y scaling values
        scale = float(self.__device.query(':WAV:YINC?'))
        ref = float(self.__device.query(':WAV:YREF?'))
        offset = float(self.__device.query(':WAV:YOR?'))
        inv = -1 if self.is_chn_invert(chn) else +1

        # Read the doc ! (p. 251 of the programming manual)
        scaled_data = [(inv * (d - ref) * scale - offset) * custom_scale for d in data]

        # X scaling values
        # TODO: Full implementation
        scale = float(self.__device.query(':WAV:XINC?'))
        ref = float(self.__device.query(':WAV:XREF?'))
        offset = float(self.__device.query(':WAV:XOR?'))
        off = float(self.__device.query(':TIM:OFFS?'))

        # Once again, read the doc
        scaled_time = [(t - m_dep / 2) * scale + off for t in range(m_dep)]

        return scaled_time, scaled_data

    def chn_display(self, chn: Channels, dis: bool):
        """Display or not the specified channel."""
        self.__device.write(f":{chn.value}:DISP {1 if dis else 0}")

    def is_chn_display(self, chn: Channels) -> bool:
        """Check if specified channel is displayed or not."""
        return int(self.__device.query(f":{chn.value}:DISP?")) == 1

    def chn_invert(self, chn: Channels, inv: bool):
        """Invert or not the specified channel."""
        self.__device.write(f":{chn.value}:INV {1 if inv else 0}")

    def is_chn_invert(self, chn: Channels) -> bool:
        """Check if specified channel is inverted or not."""
        return int(self.__device.query(f":{chn.value}:INV?")) == 1

    def set_chn_scale(self, chn: Channels, scale: float):
        """Set the y scale of the specified channel."""
        self.__device.write(f":{chn.value}:SCAL {scale}")

    def get_chn_scale(self, chn: Channels) -> float:
        """Get the y scale of the specified channel."""
        return float(self.__device.query(f":{chn.value}:SCAL?"))

    def set_chn_offset(self, chn: Channels, offset: float):
        """Set the y offset of the specified channel."""
        self.__device.write(f":{chn.value}:OFFS {offset}")

    def get_chn_offset(self, chn: Channels) -> float:
        """Get the y offset of the specified channel."""
        return float(self.__device.query(f":{chn.value}:OFFS?"))

    def set_chn_ratio(self, chn: Channels, ratio: Ratios):
        """Set the ratio of the specified channel's probe."""
        self.__device.write(f":{chn.value}:PROB {ratio.value}")

    def get_chn_ratio(self, chn: Channels) -> Ratios:
        """Get the ratio of the specified channel's probe."""
        return DS4024.__parse_enum(DS4024.Ratios, self.__device.query(f":{chn.value}:PROB?"))

    # ################ #
    # ## Attributes ## #
    # ################ #

    # ## Global attributes ## #
    @property
    def running(self) -> bool:
        """Check/Set scope state ('RUN'/'STOP')."""
        return self.status == DS4024.Status.RUN

    @running.setter
    def running(self, run: bool):
        """Set the scope to 'RUN' or 'STOP'."""
        self.__device.write(f":{DS4024.Status.RUN.value if run else DS4024.Status.STOP.value}")

    @property
    def stopped(self) -> bool:
        """Check/Set scope state ('STOP'/'RUN')."""
        return self.status == DS4024.Status.STOP

    @stopped.setter
    def stopped(self, stop: bool):
        """Set the scope to 'STOP' or 'RUN'."""
        self.__device.write(f":{DS4024.Status.RUN.value if not stop else DS4024.Status.STOP.value}")

    @property
    def reading_status(self) -> Tuple[bool, int]:
        """Get the status of the started acquisition.

        :return: (ready state, current size of the buffered data).
        """
        status = self.__device.query(":WAV:STAT?").split(',')

        ready = 'IDLE' in status[0]
        m_dep = int(status[1])

        return ready, m_dep

    # ## Time attributes ## #
    # Time scale
    @property
    def time_scale(self) -> float:
        """Get/Set the main timebase scale."""
        return float(self.__device.query(":TIM:SCAL?"))

    @time_scale.setter
    def time_scale(self, value: float):
        self.__device.write(f":TIM:SCAL {value}")

    # Time offset
    @property
    def time_offset(self) -> float:
        """Get/Set the main timebase offset."""
        return float(self.__device.query(":TIM:OFFS?"))

    @time_offset.setter
    def time_offset(self, value: float):
        self.__device.write(f":TIM:OFFS {value}")

    # ## Trigger attributes ## #
    # Coupling
    @property
    def coupling(self) -> Couplings:
        """Get/Set the trigger coupling method."""
        return DS4024.__parse_enum(DS4024.Couplings, self.__device.query(":TRIG:COUP?"))

    @coupling.setter
    def coupling(self, cp: Couplings):
        self.__device.write(f":TRIG:COUP {cp.value}")

    # Status
    @property
    def status(self) -> Status:
        """Get the trigger status of the scope."""
        return DS4024.__parse_enum(DS4024.Status, self.__device.query(":TRIG:STAT?"))

    # Sweep
    @property
    def sweep(self) -> Sweeps:
        """Get/Set the trigger mode."""
        return DS4024.__parse_enum(DS4024.Sweeps, self.__device.query(":TRIG:SWE?"))

    @sweep.setter
    def sweep(self, swp: Sweeps):
        self.__device.write(f":TRIG:SWE {swp.value}")

    # Level
    @property
    def level(self) -> float:
        """Get/Set the trigger level."""
        return float(self.__device.query(":TRIG:EDG:LEV?"))

    @level.setter
    def level(self, value: float):
        self.__device.write(f":TRIG:EDG:LEV {value}")

    # Source
    @property
    def source(self) -> Sources:
        """Get/Set the trigger source."""
        return DS4024.__parse_enum(DS4024.Sources, self.__device.query(":TRIG:EDG:SOUR?"))

    @source.setter
    def source(self, src: Sources):
        self.__device.write(f":TRIG:EDG:SOUR {src.value}")

    # Edge
    @property
    def edge(self) -> Slopes:
        """Get/Set the trigger edge."""
        return DS4024.__parse_enum(DS4024.Slopes, self.__device.query(":TRIG:EDG:SLOP?"))

    @edge.setter
    def edge(self, slp: Slopes):
        self.__device.write(f":TRIG:EDG:SLOP {slp.value}")

    # ############ #
    # ## ERRORS ## #
    # ############ #
    @property
    def errors(self):
        """Get a list of the scope errors."""
        err = int(self.__device.query('*TST?'))

        return DS4024.__list_errors(DS4024.Errors, err)


if __name__ == "__main__":
    from VISA_controller import VisaController
    import time

    vc = VisaController(query='TCPIP[0-9]*::192.168.0.[0-9]*::inst[0-9]*::INSTR', verbose=True)
    inst = vc.get_instruments_by_name('DS4024')[0]
    ds = DS4024(inst)

    tss = [1e-2, 1e-3, 5e-3, 1e-4, 5e-4, 1e-5]
    while True:
        for ts in tss:
            ds.time_scale = ts
            time.sleep(1)
            print(ds.errors)
