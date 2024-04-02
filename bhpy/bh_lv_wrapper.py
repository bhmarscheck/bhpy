import logging
log = logging.getLogger(__name__)

try:
    from ctypes import create_string_buffer, CDLL, POINTER, c_char_p, c_float, c_int32, c_uint32
    from pathlib import Path
    from typing import Literal
    import sys
except ModuleNotFoundError as err:
    # Error handling
    log.error(err)
    raise


class LVConnectQC008:
    INSTRUCTIONS = Literal["AutoAdjust", "HideAnalysis", "HideCardSettings", "HideCorrelation",
                           "HideDebugInfo", "HideDeltaT", "HideMCS", "LoadAutoSavedSettings",
                           "RepeatMeasurement", "ScanThreshold", "ShowAnalysis",
                           "ShowCardSettings", "ShowCorrelation", "ShowDebugInfo", "ShowDeltaT",
                           "ShowMCS", "StartMeasurement", "StopMeasurement"]
    MEASUREMENT_STATUS = Literal["repeating", "measuring", "noData", "DataAvailable"]

    def __init__(self, dll_path: Path | str | None = None, machine_name: str | None = None,
                 default_timeout_s: int = 3, error_string_buffer_len: int = 512,
                 result_string_buffer_len: int = 512):
        if dll_path is None:
            dll_path = Path(sys.modules["bhpy"].__file__).parent / Path("dll/ControlQC008.dll")
        else:
            dll_path = Path(dll_path)

        self._file_saving_path = Path("./")

        self.__dll = CDLL(str(dll_path.absolute()))
        self.__Dll_ControlQC008 = self.__dll.Dll_ControlQC008

        self.__Dll_ControlQC008.argtypes = [c_char_p, c_char_p, c_uint32, c_char_p, c_char_p,
                                            POINTER(c_float), c_int32, c_int32, c_int32]
        self.__Dll_ControlQC008.restype = c_int32

        if machine_name is None:
            self.machine_name = "localhost".encode('utf-8')
        else:
            self.machine_name = machine_name.encode('utf-8')

        self.cmd_timeout_s = default_timeout_s
        self.errString = create_string_buffer(error_string_buffer_len)
        self.resultString = create_string_buffer(result_string_buffer_len)
        self._rates = (c_float * 8)()

    def _command(self, command: str, command_arg: str = None,
                 machine_name: str | None = None) -> tuple[str, list[int]]:
        if machine_name is None:
            machine_name = self.machine_name
        else:
            machine_name = machine_name.encode('utf-8')

        if command_arg is None:
            cmd = command
        else:
            cmd = f"{command} {command_arg}"

        res = self.__Dll_ControlQC008(cmd.encode('utf-8'), machine_name, self.cmd_timeout_s,
                                      self.errString, self.resultString, self._rates,
                                      len(self.errString), len(self.resultString),
                                      len(self._rates))
        if 0 == res:
            return self.resultString.value.decode().split(" ")[0], list(self._rates)
        else:
            raise ChildProcessError(f"{self.errString.value.decode()} ({res})")

    def command(self, command: INSTRUCTIONS):
        self._command(command=command)

    @property
    def dll_version(self) -> str:
        return self._command(command="GetDLLversionStr")[0]

    @property
    def firmware_version(self) -> str:
        return self._command(command="GetGAPEvents")[0]

    @property
    def gap_events(self) -> int:
        return int(self._command(command="GetFW-Version")[0])

    @property
    def initialized(self) -> bool:
        return bool(int(self._command(command="Getinitialized")[0]))

    @property
    def measurement_status(self) -> MEASUREMENT_STATUS:
        return self._command(command="GetMeasurementStatus")[0]

    @property
    def rates(self) -> list[int]:
        return [int(x) for x in self._command(command="GetRates")[0].split(',')]

    @property
    def serial_number(self) -> str:
        return self._command(command="GetserialNrStr")[0]

    @property
    def file_saving_path(self) -> Path:
        return self._file_saving_path.absolute()

    @file_saving_path.setter
    def file_saving_path(self, path: str | Path):
        self._file_saving_path = Path(path)

    def bool_cmd(self, cmd: str, boolean: bool):
        self._command(cmd, f"{1 if boolean else 0}")

    def set_count(self, enable: bool = True):
        self.bool_cmd("count", enable)

    def disable_sync_filter(self, disable: bool = True):
        self.bool_cmd("DisableSyncFilter", disable)

    def set_external(self, enable: bool = True):
        self.bool_cmd("external", enable)

    def set_x_axis_in_bins(self, enable: bool = True):
        self.bool_cmd("X-AxisInBins", enable)

    def set_mcs_ref(self, channel: int, enable: bool):
        self._command("MCSRef", f"{channel},{1 if enable else 0}")

    def set_correlation_ref(self, channel_a: int, channel_b: int):
        self._command("CorrelationRef", f"{channel_a},{channel_b}")

    def set_delta_t_ref(self, channel_a: int, channel_b: int):
        self._command("DeltaTRef", f"{channel_a},{channel_b}")

    def save_raw(self, file_name):
        self._command("SaveRAW", f"{self.file_saving_path}/{file_name}.bin")

    def load_settings(self, file_name):
        self._command("LoadSettings", f"{self.file_saving_path}/{file_name}.cfg")

    def save_settings(self, file_name):
        self._command("SaveSettings", f"{self.file_saving_path}/{file_name}.cfg")

    def load_graph(self, file_name):
        self._command("LoadGraph", f"{self.file_saving_path}/{file_name}.cvs")

    def save_analysis(self, file_name):
        self._command("SaveAnalysis", f"{self.file_saving_path}/{file_name}.cvs")

    def save_graph(self, file_name):
        self._command("SaveGraph", f"{self.file_saving_path}/{file_name}.cvs")

    def save_time_line(self, file_name):
        self._command("SaveTimeLine", f"{self.file_saving_path}/{file_name}.cvs")

    def screen_print(self, file_name):
        self._command("ScrPrt", f"{self.file_saving_path}/{file_name}.png")

    def load_sdt(self, file_name):
        self._command("LoadSDT", f"{self.file_saving_path}/{file_name}.sdt")

    def save_sdt(self, file_name):
        self._command("SaveSDT", f"{self.file_saving_path}/{file_name}.sdt")

    def set_max_count(self, count: int):
        self._command("maxCount", f"{count}")

    def set_no_of_bins(self, bins: int):
        self._command("NoOfBins", f"{bins}")

    def set_channel_thresholds(self, threshold_mv: list[int]):
        self._command("ChThresh", f"{threshold_mv[0]},{threshold_mv[1]},{threshold_mv[2]},"
                      f"{threshold_mv[3]},{threshold_mv[4]},{threshold_mv[5]},{threshold_mv[6]},"
                      f"{threshold_mv[7]}")

    def set_start_delay(self, delay_ns: int):
        self._command("StartDelay", f"{delay_ns}")

    def set_channel_delays(self, delays_ns: list[int]):
        self._command("ChDelays", f"{delays_ns[0]},{delays_ns[1]},{delays_ns[2]},{delays_ns[3]},"
                      f"{delays_ns[4]},{delays_ns[5]},{delays_ns[6]},{delays_ns[7]}")

    def set_channel_polarities(self, polarities: list[int]):
        polarities = [max(min(x, 1), 0) for x in polarities]
        self._command("Polarity", f"{polarities[0]}{polarities[1]}{polarities[2]}{polarities[3]}"
                      f"{polarities[4]}{polarities[5]}{polarities[6]}{polarities[7]}")

    def set_puls_gen_enables(self, enables: list[int]):
        enables = [max(min(x, 1), 0) for x in enables]
        self._command("PulseGenerator", f"{enables[0]}{enables[1]}{enables[2]}{enables[3]}"
                      f"{enables[4]}{enables[5]}{enables[6]}{enables[7]}")

    def set_collection_time(self, time_s: float):
        time_s = max(min(time_s, 4.0e6), 100.0e-9)
        self._command("CollectionTime", f"{time_s:.9E}")

    def set_correlation_time(self, time_s: float):
        self._command("CorrelationT", f"{time_s:.9E}")

    def set_resolution(self, resolution_s: float):
        self._command("Resolution", f"{resolution_s:.9E}")

    def set_time_range(self, range_s: float):
        self._command("TimeRange", f"{range_s:.9E}")
