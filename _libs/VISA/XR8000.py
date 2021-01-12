class XR8000:
    # ############# #
    # ## Methods ## #
    # ############# #

    NAME = "XR8000-0.25"

    def __init__(self, instr):
        """Initialize the instrument.
        More than one instrument can be instanced.

        :param instr: the value returned by VisaController.get_instruments_by_name(...).
        :raise TypeError: "Instrument is not a XR8000 !" : specified instrument must be a Magna-Power XR8000.

        >>>from VISA.VISA_controller import VisaController
        ...from VISA.XR8000 import XR8000
        ...vc = VisaController()
        ...xr8000 = XR8000(vc.get_instruments_by_name(XR8000.NAME)[0])

        """
        self.__device = instr.device

        if XR8000.NAME not in self.__device.query("*IDN?"):
            raise TypeError("Instrument is not a XR8000 !")

    def v_source_wizard(self, volt: float, compliance: float):
        """Automatically configure the instrument in voltage source mode,
        with the specified voltage and current compliance.

        :param volt: Constant voltage
        :param compliance: Current compliance
        """
        self.voltage = volt
        self.current = compliance

        self.voltage_protection = volt * 1.1
        self.current_protection = compliance * 1.1

    def output_ramp(self, final_voltage: float, ramp_duration: float, step_time: float = 1):
        """Cancel the overshoot by slowly ramping up the voltage.

        :param final_voltage:
        :param ramp_duration:
        """
        import time

        step_volt = final_voltage / (ramp_duration / step_time)

        volt = 0
        self.voltage = 0
        self.output = True
        time.sleep(1)

        while volt < final_voltage:
            volt += step_volt
            self.voltage = volt
            time.sleep(step_time)

        self.voltage = final_voltage

    # ################ #
    # ## Attributes ## #
    # ################ #

    # ## Global attributes ## #
    @property
    def output(self) -> bool:
        """Unleash the juice !"""
        return self.__device.query("OUTP?") == "1"

    @output.setter
    def output(self, out: bool):
        self.__device.write(f"OUTP:{'START' if out else 'STOP'}")

    @property
    def voltage(self) -> float:
        """Measure/Set voltage"""
        return float(self.__device.query("MEAS:VOLT?"))

    @voltage.setter
    def voltage(self, volt: float):
        self.__device.write(f"VOLT {volt}")

    @property
    def current(self) -> float:
        """Measure/Set current"""
        return float(self.__device.query("MEAS:CURR?"))

    @current.setter
    def current(self, curr: float):
        self.__device.write(f"CURR {curr}")

    @property
    def voltage_protection(self) -> float:
        """Get/Set over voltage protection"""
        return float(self.__device.query("VOLT:PROT?"))

    @voltage_protection.setter
    def voltage_protection(self, volt: float):
        self.__device.write(f"VOLT:PROT {volt}")

    @property
    def current_protection(self) -> float:
        """Get/Set over current protection"""
        return float(self.__device.query("CURR:PROT?"))

    @current_protection.setter
    def current_protection(self, curr: float):
        self.__device.write(f"CURR:PROT {curr}")

    @property
    def disable_front_panel(self) -> bool:
        """Check if disabled/Disable front panel buttons"""
        return self.__device.query("CONT:INT?") == "0"

    @disable_front_panel.setter
    def disable_front_panel(self, disable: bool):
        self.__device.write(f"CONT:INT {0 if disable else 1}")


if __name__ == "__main__":
    from VISA_controller import VisaController
    import time

    vc = VisaController(query='?*::INSTR', verbose=True)
    inst = vc.get_instruments_by_name(XR8000.NAME)[0]
    grosse_berta = XR8000(inst)
