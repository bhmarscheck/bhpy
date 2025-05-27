import logging
log = logging.getLogger(__name__)

try:
    from ctypes import (byref, cast, c_int16, create_string_buffer, Structure,
                        CDLL, POINTER, c_char_p, c_uint8, c_uint16, c_uint32,
                        c_bool, c_double, c_int8, c_float, c_uint64, c_int64,
                        c_char, c_int32)
    from pathlib import Path
    import numpy as np
    import numpy.typing as npt
    import re
    import sys
    from typing import Literal
    import typing
except ModuleNotFoundError as err:
    # Error handling
    log.error(err)
    raise


class ModuleInit(Structure):
    _fields_ = [("device_nr", c_uint8),
                ("initialized", c_bool),
                ("serial_nr_str", c_char * 12),
                ("device_type_str", c_char * 32)]


class TdcLiterals:
    DEFAULT_NAMES = Literal["spc_qc_X04", "spc_qc_X08", "pms_800"]

    MARKER = Literal["pixel", "line", "frame", "marker3", 0, 1, 2, 3]
    _marker_to_int = {"pixel": 0, "line": 1, "frame": 2, "marker3": 3}

    POLARITIES = Literal["Falling", "Rising", 0, 1]
    _polarities_to_int = {"Falling": 0, "Rising": 1}
    _polarities = {"0": "Falling", "1": "Rising"}


class Markers(typing.TypedDict):
    pixel: bool | TdcLiterals.POLARITIES = 0
    line: bool | TdcLiterals.POLARITIES = 0
    frame: bool | TdcLiterals.POLARITIES = 0
    marker3: bool | TdcLiterals.POLARITIES = 0


class __TdcDllWrapper:
    version_str = ""
    version_str_buf = create_string_buffer(128)

    def __init__(self, default_dll_name: TdcLiterals.DEFAULT_NAMES, no_of_channels: int,
                 no_of_inputmodes: int | None = None, no_of_rates: int | None = None,
                 dll_path: Path | str | None = None):
        self.no_of_channels = no_of_channels

        if no_of_inputmodes is None:
            self.no_of_inputmodes = no_of_channels
        else:
            self.no_of_inputmodes = no_of_inputmodes

        if no_of_rates is None:
            self.no_of_rates = no_of_channels
        else:
            self.no_of_rates = no_of_rates

        if dll_path is None:
            dll_path = (Path(sys.modules["bhpy"].__file__).parent.parent.absolute()
                        / Path(f"dll/{default_dll_name}.dll"))
        else:
            dll_path = Path(dll_path)

        try:
            self.__dll = CDLL(str(dll_path.absolute()))
        except FileNotFoundError as e:
            log.error(e)
            raise

        self.__get_dll_version = self.__dll.get_dll_version
        self.__get_dll_version.argtypes = [c_char_p, c_uint8]
        self.__get_dll_version.restype = c_int16

        self.__get_dll_version(self.version_str_buf, c_uint8(128))
        self.version_str = str(self.version_str_buf.value)[2:-1]

        match = re.match(r"(\d+)\.(\d+)\.(\d+)\+([0-9a-fA-F]+)", self.version_str)
        self.version = {"major": int(match.group(1)), "minor": int(match.group(2)),
                        "patch": int(match.group(3)), "commit_iD": match.group(4)}
        if (self.version["major"] != 4):
            raise RuntimeError(f"Unable to load DLL: incompatible version. Version is: "
                               f"{self.version['major']}.{self.version['minor']}."
                               f"{self.version['patch']} Expected >= 4.0.0, < 5")

        self.__get_dll_debug = self.__dll.get_dll_debug
        self.__get_dll_debug.restype = c_uint8
        self.dll_is_debug_version = (self.__get_dll_debug() > 0)

        self.__abort_data_collection = self.__dll.abort_data_collection

        self.__deinit_data_collection = self.__dll.deinit_data_collection

        self.__deinit_data_collections = self.__dll.deinit_data_collections

        self.__deinit = self.__dll.deinit
        self.__deinit.restype = c_uint8

        self.__get_card_focus = self.__dll.get_card_focus
        self.__get_card_focus.restype = c_uint8

        self.__get_channel_enable = self.__dll.get_channel_enable
        self.__get_channel_enable.argtypes = [c_uint8]
        self.__get_channel_enable.restype = c_int8

        self.__get_channel_enables = self.__dll.get_channel_enables
        self.__get_channel_enables.restype = c_uint8

        self.__get_external_trigger_enable = self.__dll.get_external_trigger_enable
        self.__get_external_trigger_enable.restype = c_uint8

        self.__get_firmware_version = self.__dll.get_firmware_version
        self.__get_firmware_version.restype = c_uint16

        self.__get_hardware_countdown_enable = self.__dll.get_hardware_countdown_enable
        self.__get_hardware_countdown_enable.restype = c_uint8

        self.__get_hardware_countdown_time = self.__dll.get_hardware_countdown_time
        self.__get_hardware_countdown_time.restype = c_double

        self.__get_rate = self.__dll.get_rate
        self.__get_rate.argtypes = [c_uint8]
        self.__get_rate.restype = c_int32

        self.__get_rates = self.__dll.get_rates
        self.__get_rates.argtypes = [POINTER(c_int32)]

        self.__init = self.__dll.init
        self.__init.argtypes = [POINTER(ModuleInit), c_uint8, c_char_p]
        self.__init.restype = c_int16

        self.__initialize_data_collection = self.__dll.initialize_data_collection
        self.__initialize_data_collection.argtypes = [POINTER(c_uint64)]
        self.__initialize_data_collection.restype = c_int16

        self.__initialize_data_collections = self.__dll.initialize_data_collections
        self.__initialize_data_collections.argtypes = [POINTER(c_uint64)]
        self.__initialize_data_collections.restype = c_int16

        if self.dll_is_debug_version:
            self.__read_setting = self.__dll.read_setting
            self.__read_setting.argtypes = [c_uint16]
            self.__read_setting.restype = c_uint32

        self.__reset_registers = self.__dll.reset_registers

        self.__run_data_collection = self.__dll.run_data_collection
        self.__run_data_collection.argtypes = [c_uint32, c_uint32]
        self.__run_data_collection.restype = c_int16

        self.__set_card_focus = self.__dll.set_card_focus
        self.__set_card_focus.argtypes = [c_uint8]
        self.__set_card_focus.restype = c_uint8

        self.__set_channel_enable = self.__dll.set_channel_enable
        self.__set_channel_enable.argtypes = [c_uint8, c_bool]
        self.__set_channel_enable.restype = c_int16

        self.__set_channel_enables = self.__dll.set_channel_enables
        self.__set_channel_enables.argtypes = [c_uint8]
        self.__set_channel_enables.restype = c_int16

        self.__set_external_trigger_enable = self.__dll.set_external_trigger_enable
        self.__set_external_trigger_enable.argtypes = [c_bool]
        self.__set_external_trigger_enable.restype = c_int16

        self.__set_hardware_countdown_enable = self.__dll.set_hardware_countdown_enable
        self.__set_hardware_countdown_enable.argtypes = [c_bool]
        self.__set_hardware_countdown_enable.restype = c_int16

        self.__set_hardware_countdown_time = self.__dll.set_hardware_countdown_time
        self.__set_hardware_countdown_time.argtypes = [c_double]
        self.__set_hardware_countdown_time.restype = c_double

        self.__stop_measurement = self.__dll.stop_measurement
        self.__stop_measurement.restype = c_int16

        if self.dll_is_debug_version:
            self.__write_setting = self.__dll.write_setting
            self.__write_setting.argtypes = [c_uint16, c_uint32]
            self.__write_setting.restype = c_uint32

    @property
    def card_focus(self) -> int:
        return self.__get_card_focus()

    @card_focus.setter
    def card_focus(self, card_number):
        self.__set_card_focus(c_uint8(card_number))

    @property
    def channel_enables(self) -> list[bool]:
        enables = self.__get_channel_enables()
        # so first in list end up in leas significant bit
        return list(reversed([bool(int(digit)) for digit in format(enables,
                                                                   f'0{self.no_of_channels}b')]))

    @channel_enables.setter
    def channel_enables(self, values: list[bool] | int | tuple[int, bool]):
        output = 0
        if type(values) is tuple:
            channel, value = values
            self.__set_channel_enable(c_uint8(channel), c_bool(value))
            return
        elif type(values) is list:
            for bit in reversed(values):  # so first in list end up in leas significant bit
                output = output * 2 + 1 if bit else output * 2
        else:
            output = values
        self.__set_channel_enables(c_uint8(output))  # TODO check setters for using get functions

    @property
    def external_trigger_enable(self) -> bool:
        return bool(self.__get_external_trigger_enable())  # TODO alle enables returns

    @external_trigger_enable.setter
    def external_trigger_enable(self, enable: bool):
        self.__set_external_trigger_enable(c_bool(enable))  # TODO raise on error return for all

    @property
    def firmware_version(self) -> int:
        return self.__get_firmware_version()

    @property
    def hardware_countdown_enable(self) -> bool:
        return bool(self.__get_hardware_countdown_enable())

    @hardware_countdown_enable.setter
    def hardware_countdown_enable(self, state):
        self.__set_hardware_countdown_enable(c_bool(state))

    @property
    def hardware_countdown_time(self) -> float:
        return self.__get_hardware_countdown_time()

    @hardware_countdown_time.setter
    def hardware_countdown_time(self, ns_time):
        if self.__set_hardware_countdown_time(c_double(ns_time)) < 0:
            raise RuntimeError("DLL call set_hardware_countdown_time() returned with error, more "
                               f"details: {self.log_path}")

    @property
    def rates(self) -> list[int]:
        c_rates = (c_int32 * self.no_of_rates)()
        self.__get_rates(cast(c_rates, POINTER(c_int32)))
        return c_rates[:]

    def abort_data_collection(self):
        self.__abort_data_collection()

    def deinit_data_collection(self):
        self.__deinit_data_collection()

    def deinit_data_collections(self):
        self.__deinit_data_collections()

    def deinit(self):
        return self.__deinit()

    def get_rate(self, channel) -> int:
        return self.__get_rate(c_uint8(channel))

    def init(self, module_list: list[int], log_path: str = None,
             emulate_hardware: bool = False) -> int:
        arg1 = (ModuleInit * len(module_list))()
        self.serial_number = []

        self.log_path = log_path

        for i in range(len(module_list)):
            arg1[i].initialized = False
            arg1[i].serial_nr_str = bytes(0)
            arg1[i].device_nr = c_uint8(module_list[i])

        number_of_hw_modules = len(module_list) if emulate_hardware is False else 0

        lp_arg = None if log_path is None else log_path.encode('utf-8')
        ret = self.__init(arg1, c_uint8(number_of_hw_modules), lp_arg)
        # Structure objects (arg1) are automatically passed byref

        for module in arg1:
            self.serial_number.append(str(module.serial_nr_str)[2:-1])
        return ret

    def initialize_data_collection(self, event_size):
        arg = c_uint64(event_size)
        self.__initialize_data_collection(byref(arg))
        return arg.value

    def initialize_data_collections(self, event_size):
        arg = c_uint64(event_size)
        self.__initialize_data_collections(byref(arg))
        return arg.value

    def _read_setting(self, setting_id):  # TODO change all deb only to _leading_private style
        if self.dll_is_debug_version:
            arg1 = c_uint16(setting_id)
            return self.__read_setting(arg1)
        else:
            raise RuntimeWarning("_read_setting() method is only available in debug version of the"
                                 " dll")

    def reset_registers(self):
        self.__reset_registers()
        return

    def run_data_collection(self, acquisition_time_ms, timeout_ms):
        arg1 = c_uint32(acquisition_time_ms)  # TODO remove these extra steps where not needed
        arg2 = c_uint32(timeout_ms)
        return self.__run_data_collection(arg1, arg2)

    def stop_measurement(self):
        return self.__stop_measurement()

    def _write_setting(self, setting_id, value):
        if self.dll_is_debug_version:
            return self.__write_setting(c_uint16(setting_id), c_uint32(value))
        else:
            raise RuntimeWarning("_write_setting() method is only available in debug version of "
                                 "the dll")


class __8ChannelDllWrapper(__TdcDllWrapper):  # noqa
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.__dll: CDLL = self._TdcDllWrapper__dll

        self.__get_channel_inputmode = self.__dll.get_channel_inputmode
        self.__get_channel_inputmode.argtypes = [c_uint8]
        self.__get_channel_inputmode.restype = c_int8

        self.__get_channel_inputmodes = self.__dll.get_channel_inputmodes
        self.__get_channel_inputmodes.argtypes = [POINTER(c_uint8)]

        self.__get_channel_polarities = self.__dll.get_channel_polarities
        self.__get_channel_polarities.restype = c_uint8

        self.__get_channel_polarity = self.__dll.get_channel_polarity
        self.__get_channel_polarity.argtypes = [c_uint8]
        self.__get_channel_polarity.restype = c_int8

        self.__get_input_threshold = self.__dll.get_input_threshold
        self.__get_input_threshold.argtypes = [c_uint8]
        self.__get_input_threshold.restype = c_float

        self.__get_input_thresholds = self.__dll.get_input_thresholds
        self.__get_input_thresholds.argtypes = [POINTER(c_float)]
        self.__get_input_thresholds.restype = c_int16

        self.__get_max_trigger_count = self.__dll.get_max_trigger_count
        self.__get_max_trigger_count.restype = c_uint32

        self.__get_pulsgenerator_enable = self.__dll.get_pulsgenerator_enable
        self.__get_pulsgenerator_enable.restype = c_uint8

        self.__get_trigger_countdown_enable = self.__dll.get_trigger_countdown_enable
        self.__get_trigger_countdown_enable.restype = c_uint8

        self.__set_channel_inputmode = self.__dll.set_channel_inputmode
        self.__set_channel_inputmode.argtypes = [c_uint8, c_uint8]
        self.__set_channel_inputmode.restype = c_int16

        self.__set_channel_inputmodes = self.__dll.set_channel_inputmodes
        self.__set_channel_inputmodes.argtypes = [POINTER(c_uint8)]
        self.__set_channel_inputmodes.restype = c_int16

        self.__set_channel_polarities = self.__dll.set_channel_polarities
        self.__set_channel_polarities.argtypes = [c_uint8]
        self.__set_channel_polarities.restype = c_int16

        self.__set_channel_polarity = self.__dll.set_channel_polarity
        self.__set_channel_polarity.argtypes = [c_uint8, c_bool]
        self.__set_channel_polarity.restype = c_int16

        self.__set_input_threshold = self.__dll.set_input_threshold
        self.__set_input_threshold.argtypes = [c_uint8, c_float]
        self.__set_input_threshold.restype = c_float

        self.__set_input_thresholds = self.__dll.set_input_thresholds
        self.__set_input_thresholds.argtypes = [POINTER(c_float)]

        self.__set_max_trigger_count = self.__dll.set_max_trigger_count
        self.__set_max_trigger_count.argtypes = [c_uint32]
        self.__set_max_trigger_count.restype = c_int64

        self.__set_pulsgenerator_enable = self.__dll.set_pulsgenerator_enable
        self.__set_pulsgenerator_enable.argtypes = [c_bool]
        self.__set_pulsgenerator_enable.restype = c_int16

        self.__set_trigger_countdown_enable = self.__dll.set_trigger_countdown_enable
        self.__set_trigger_countdown_enable.argtypes = [c_bool]
        self.__set_trigger_countdown_enable.restype = c_int16

        if self.dll_is_debug_version:
            self.__write_module_type = self.__dll.write_module_type
            self.__write_module_type.argtypes = [c_uint8, c_char_p]
            self.__write_module_type.restype = c_int16

            self.__write_production_date = self.__dll.write_production_date
            self.__write_production_date.argtypes = [c_uint8, c_char_p]
            self.__write_production_date.restype = c_int16

            self.__write_serial_number = self.__dll.write_serial_number
            self.__write_serial_number.argtypes = [c_uint8, c_char_p]
            self.__write_serial_number.restype = c_int16

    @property
    def channel_polarities(self):
        polarities = self.__get_channel_polarities()
        # so first in list end up in leas significant bit
        return list(reversed([TdcLiterals._polarities[digit] for digit in
                              format(polarities, f'0{self.no_of_channels}b')]))

    @channel_polarities.setter
    def channel_polarities(self, values: list[TdcLiterals.POLARITIES | int]
                           | tuple[int, TdcLiterals.POLARITIES | int]):
        if type(values) is tuple:
            channel, value = values
            if value in typing.get_args(TdcLiterals.POLARITIES):
                if type(value) is str:
                    value = TdcLiterals._polarities_to_int[value]
            else:
                raise ValueError(f"{[value]} not part of {TdcLiterals.POLARITIES}")
            self.__set_channel_polarity(c_uint8(channel), c_uint8(value))
            return
        elif type(values) is int:
            values_arg = values
        elif type(values) is list:
            values = [TdcLiterals._polarities_to_int[x]
                      if (type(x) is str and x in typing.get_args(TdcLiterals.POLARITIES))
                      else x for x in values]
            bad_args = [x for x in values if (x not in typing.get_args(TdcLiterals.POLARITIES))]
            if bad_args:
                raise ValueError(f"{list(dict.fromkeys(bad_args))} not part of "
                                 f"{TdcLiterals.POLARITIES}")
            output = 0
            for bit in reversed(values):  # so first in list end up in leas significant bit
                output = output * 2 + bit
            values_arg = output
        else:
            raise ValueError()
        self.__set_channel_polarities(c_uint8(values_arg))

    @property
    def input_thresholds(self):
        thresholds = (c_float * self.no_of_channels)()
        self.__get_input_thresholds(cast(thresholds, POINTER(c_float)))
        return [x if x >= -500 else None for x in thresholds[:]]

    @input_thresholds.setter
    def input_thresholds(self, values: list[float] | tuple[int, float]):
        if type(values) is list:
            self.__set_input_thresholds(cast((c_float * self.no_of_channels)(*values),
                                             POINTER(c_float)))
        else:
            channel, value = values
            self.__set_input_threshold(c_uint8(channel), c_float(value))

    @property
    def max_trigger_count(self):
        return self.__get_max_trigger_count()

    @max_trigger_count.setter
    def max_trigger_count(self, count: int):
        count = max(0, min((4294967295), count))  # 2**32
        self.__set_max_trigger_count(c_uint32(count))

    @property
    def pulsgenerator_enable(self):
        return bool(self.__get_pulsgenerator_enable())

    @pulsgenerator_enable.setter
    def pulsgenerator_enable(self, enable: bool):
        self.__set_pulsgenerator_enable(c_bool(enable))

    @property
    def trigger_countdown_enable(self):
        return bool(self.__get_trigger_countdown_enable())

    @trigger_countdown_enable.setter
    def trigger_countdown_enable(self, enable: bool):
        self.__set_trigger_countdown_enable(c_bool(enable))

    def _write_module_type(self, card_number: int, type_string: str):
        if self.dll_is_debug_version:
            self.__write_module_type(c_uint8(card_number), c_char_p(type_string.encode()))
        else:
            raise RuntimeWarning("_write_module_type() method is only available in debug version "
                                 "of the dll")

    def _write_production_date(self, card_number: int, date_string: str):
        if self.dll_is_debug_version:
            self.__write_production_date(c_uint8(card_number), c_char_p(date_string.encode()))
        else:
            raise RuntimeWarning("_write_production_date() method is only available in debug "
                                 "version of the dll")

    def _write_serial_number(self, card_number: int, serial_string: str):
        if self.dll_is_debug_version:
            self.__write_serial_number(c_uint8(card_number), c_char_p(serial_string.encode()))
        else:
            raise RuntimeWarning("_write_serial_number() method is only available in debug version"
                                 " of the dll")


class __EventStream32Bit(__TdcDllWrapper):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.file_name = kwargs["default_dll_name"]
        self.__dll: CDLL = self._TdcDllWrapper__dll

        self.__get_raw_events_from_buffer = self.__dll.get_raw_events_from_buffer
        self.__get_raw_events_from_buffer.argtypes = [POINTER(c_uint32), c_uint32, c_uint8]
        self.__get_raw_events_from_buffer.restype = c_int64

        self.__get_raw_events_from_buffer_to_file = self.__dll.get_raw_events_from_buffer_to_file
        self.__get_raw_events_from_buffer_to_file.argtypes = [c_uint32, c_uint32, c_uint8,
                                                              c_uint32, c_uint32, c_char_p]
        self.__get_raw_events_from_buffer_to_file.restype = c_int64

    def get_events_from_buffer_to_file(self, card_number: int, dir_path: str, idx: int,
                                       min_events: int, max_events: int | None = None,
                                       timeout_ms: int = 10_000) -> tuple[str, int]:
        if max_events is None:
            max_events = min_events
        events = self.__get_raw_events_from_buffer_to_file(c_uint32(min_events),
                                                           c_uint32(max_events),
                                                           c_uint8(card_number),
                                                           c_uint32(idx),
                                                           c_uint32(timeout_ms),
                                                           c_char_p(dir_path.encode()))
        return f"{dir_path}/{self.file_name}_record_{idx}.data", events


class SpcQcX04(__EventStream32Bit):
    def __init__(self, dll_path: Path | str | None = None):
        super().__init__(default_dll_name="spc_qc_x04", no_of_channels=4, dll_path=dll_path)
        self.__dll: CDLL = self._EventStream32Bit__dll

        self.__get_events_from_buffer = self.__dll.get_events_from_buffer
        self.__get_events_from_buffer.argtypes = [POINTER(c_uint32), c_uint32, c_uint8]
        self.__get_events_from_buffer.restype = c_int64

        self.__get_cFD_threshold = self.__dll.get_CFD_threshold
        self.__get_cFD_threshold.argtypes = [c_uint8]
        self.__get_cFD_threshold.restype = c_float

        self.__get_cFD_thresholds = self.__dll.get_CFD_thresholds
        self.__get_cFD_thresholds.argtypes = [POINTER(c_float)]
        self.__get_cFD_thresholds.restype = c_int16

        self.__get_cFD_zc = self.__dll.get_CFD_zc
        self.__get_cFD_zc.argtypes = [c_uint8]
        self.__get_cFD_zc.restype = c_float

        self.__get_cFD_zcs = self.__dll.get_CFD_zcs
        self.__get_cFD_zcs.argtypes = [POINTER(c_float)]
        self.__get_cFD_zcs.restype = c_int16

        self.__get_channel_delay = self.__dll.get_channel_delay
        self.__get_channel_delay.argtypes = [c_uint8]
        self.__get_channel_delay.restype = c_float

        self.__get_channel_delays = self.__dll.get_channel_delays
        self.__get_channel_delays.argtypes = [POINTER(c_float)]

        self.__get_channel_divider = self.__dll.get_channel_divider
        self.__get_channel_divider.argtypes = [c_uint8]
        self.__get_channel_divider.restype = c_int8

        self.__get_dithering_enable = self.__dll.get_dithering_enable
        self.__get_dithering_enable.restype = c_uint8

        self.__get_marker_enable = self.__dll.get_marker_enable
        self.__get_marker_enable.argtypes = [c_uint8]
        self.__get_marker_enable.restype = c_int16

        self.__get_marker_enables = self.__dll.get_marker_enables
        self.__get_marker_enables.restype = c_uint8

        self.__get_marker_polarities = self.__dll.get_marker_polarities
        self.__get_marker_polarities.restype = c_uint8

        self.__get_marker_polarity = self.__dll.get_marker_polarity
        self.__get_marker_polarity.argtypes = [c_uint8]
        self.__get_marker_polarity.restype = c_int8

        self.__get_marker_status = self.__dll.get_marker_status
        self.__get_marker_status.restype = c_uint8

        self.__get_module_status = self.__dll.get_module_status
        self.__get_module_status.restype = c_uint8

        self.__get_routing_compensation = self.__dll.get_routing_compensation
        self.__get_routing_compensation.restype = c_int16

        self.__get_routing_enable = self.__dll.get_routing_enable
        self.__get_routing_enable.argtypes = [c_uint8]
        self.__get_routing_enable.restype = c_int8

        self.__get_routing_enables = self.__dll.get_routing_enables
        self.__get_routing_enables.restype = c_uint8

        self.__get_trigger_polarity = self.__dll.get_trigger_polarity
        self.__get_trigger_polarity.restype = c_uint8

        self.__set_cFD_threshold = self.__dll.set_CFD_threshold
        self.__set_cFD_threshold.argtypes = [c_uint8, c_float]
        self.__set_cFD_threshold.restype = c_float

        self.__set_cFD_thresholds = self.__dll.set_CFD_thresholds
        self.__set_cFD_thresholds.argtypes = [POINTER(c_float)]

        self.__set_cFD_zc = self.__dll.set_CFD_zc
        self.__set_cFD_zc.argtypes = [c_uint8, c_float]
        self.__set_cFD_zc.restype = c_float

        self.__set_cFD_zcs = self.__dll.set_CFD_zcs
        self.__set_cFD_zcs.argtypes = [POINTER(c_float)]

        self.__set_channel_delay = self.__dll.set_channel_delay
        self.__set_channel_delay.argtypes = [c_uint8, c_float]
        self.__set_channel_delay.restype = c_float

        self.__set_channel_delays = self.__dll.set_channel_delays
        self.__set_channel_delays.argtypes = [POINTER(c_float)]
        self.__set_channel_delays.restype = c_uint16

        self.__set_channel_divider = self.__dll.set_channel_divider
        self.__set_channel_divider.argtypes = [c_uint8, c_uint8]
        self.__set_channel_divider.restype = c_int16

        self.__set_dithering_enable = self.__dll.set_dithering_enable
        self.__set_dithering_enable.argtypes = [c_bool]
        self.__set_dithering_enable.restype = c_int16

        self.__set_marker_enable = self.__dll.set_marker_enable
        self.__set_marker_enable.argtypes = [c_uint8, c_bool]
        self.__set_marker_enable.restype = c_int16

        self.__set_marker_enables = self.__dll.set_marker_enables
        self.__set_marker_enables.argtypes = [c_uint8]
        self.__set_marker_enables.restype = c_int16

        self.__set_marker_polarities = self.__dll.set_marker_polarities
        self.__set_marker_polarities.argtypes = [c_uint8]
        self.__set_marker_polarities.restype = c_int16

        self.__set_marker_polarity = self.__dll.set_marker_polarity
        self.__set_marker_polarity.argtypes = [c_uint8, c_bool]
        self.__set_marker_polarity.restype = c_int16

        self.__set_measurement_configuration = self.__dll.set_measurement_configuration
        self.__set_measurement_configuration.argtypes = [c_uint8, POINTER(c_uint32),
                                                         POINTER(c_uint32), POINTER(c_uint8)]
        self.__set_measurement_configuration.restype = c_int16

        self.__set_routing_compensation = self.__dll.set_routing_compensation
        self.__set_routing_compensation.argtypes = [c_int8]
        self.__set_routing_compensation.restype = c_int16

        self.__set_routing_enable = self.__dll.set_routing_enable
        self.__set_routing_enable.argtypes = [c_uint8, c_bool]
        self.__set_routing_enable.restype = c_int16

        self.__set_routing_enables = self.__dll.set_routing_enables
        self.__set_routing_enables.argtypes = [c_uint8]
        self.__set_routing_enables.restype = c_int16

        self.__set_trigger_polarity = self.__dll.set_trigger_polarity
        self.__set_trigger_polarity.argtypes = [c_bool]
        self.__set_trigger_polarity.restype = c_int16

    @property
    def cfd_thresholds(self) -> list[float]:
        thresholds = (c_float * self.no_of_channels)()
        self.__get_cFD_thresholds(cast(thresholds, POINTER(c_float)))
        return [x if x >= -500 else None for x in thresholds[:]]

    @cfd_thresholds.setter
    def cfd_thresholds(self, values: list[float] | tuple[int, float]):
        if type(values) is list:
            thresholds = (c_float * self.no_of_channels)(*values)
            self.__set_cFD_thresholds(cast(thresholds, POINTER(c_float)))
        else:
            channel, value = values
            self.__set_cFD_threshold(c_uint8(channel), c_float(value))

    @property
    def cfd_zero_cross(self) -> list[float]:
        zero_crosses = (c_float * self.no_of_channels)()
        self.__get_cFD_zcs(cast(zero_crosses, POINTER(c_float)))
        return [x if x >= -96 else None for x in zero_crosses[:]]

    @cfd_zero_cross.setter
    def cfd_zero_cross(self, values: list[float] | tuple[int, float]):
        if type(values) is list:
            zero_crosses = (c_float * self.no_of_channels)(*values)
            self.__set_cFD_zcs(cast(zero_crosses, POINTER(c_float)))
        else:
            channel, value = values
            self.__set_cFD_zc(c_uint8(channel), c_float(value))

    @property
    def channel_delays(self) -> list[float]:
        delays = (c_float * self.no_of_channels)()
        self.__get_channel_delays(cast(delays, POINTER(c_float)))
        return delays[:]

    @channel_delays.setter
    def channel_delays(self, values: list[float] | tuple[int, float]):
        if type(values) is list:
            self.__set_channel_delays(cast((c_float * self.no_of_channels)(*values),
                                           POINTER(c_float)))
        elif type(values) is tuple:
            channel, value = values
            self.__set_channel_delay(c_uint8(channel), c_float(value))
        else:
            raise ValueError(values)

    @property
    def channel_divider(self):
        return self.__get_channel_divider(c_uint8(3))

    @channel_divider.setter
    def channel_divider(self, divider: int):
        self.__set_channel_divider(c_uint8(3), c_uint8(divider))

    @property
    def dithering_enable(self):
        return bool(self.__get_dithering_enable())

    @dithering_enable.setter
    def dithering_enable(self, enable: bool):
        self.__set_dithering_enable(c_bool(enable))

    @property
    def marker_enables(self) -> Markers:
        enables = self.__get_marker_enables()
        return Markers(pixel=(enables & 0x1) > 0, line=(enables & 0x2) > 0,
                       frame=(enables & 0x4) > 0, marker3=(enables & 0x8) > 0)

    @marker_enables.setter  # TODO add bool to turn all on/off
    def marker_enables(self, enables:
                       Markers | list[bool, int] | int
                       | tuple[TdcLiterals.MARKER | int, bool | int]):
        if type(enables) is tuple:
            marker, enable = enables
            if type(marker) is str:
                marker = TdcLiterals._marker_to_int[marker]
            self.__set_marker_enable(c_uint8(marker), c_bool(enable))
            return
        elif type(enables) is int:
            enables_arg = enables
        elif type(enables) is dict:
            enables = [enables["pixel"], enables["line"], enables["frame"], enables["marker3"]]
        elif type(enables) is not list:
            raise ValueError("marker_enables excepts the following types: bhpy.Markers | list[bool"
                             ", int] | int | tuple[Tdc_literals.MARKER, bool | int]")

        if type(enables) is list:
            enables_arg = 0
            for bit in reversed(enables):  # so first in list end up in leas significant bit
                enables_arg = enables_arg * 2 + 1 if bit else enables_arg * 2
        self.__set_marker_enables(c_uint8(enables_arg))

    @property
    def marker_polarities(self):
        polarities = format(self.__get_marker_polarities(), f'0{self.no_of_channels}b')
        return Markers(pixel=TdcLiterals._polarities[polarities[3]],
                       line=TdcLiterals._polarities[polarities[2]],
                       frame=TdcLiterals._polarities[polarities[1]],
                       marker3=TdcLiterals._polarities[polarities[0]])

    @marker_polarities.setter
    def marker_polarities(self,
                          polarities: Markers | list[int] | int
                          | tuple[TdcLiterals.MARKER | int, TdcLiterals.POLARITIES | int]):
        if type(polarities) is tuple:
            marker, polarity = polarities
            if type(marker) is str:
                marker = TdcLiterals._marker_to_int[marker]
            if type(polarity) is str:
                polarity = TdcLiterals._polarities_to_int[polarity]
            self.__set_marker_polarity(c_uint8(marker), c_bool(polarity))
            return
        elif type(polarities) is int:
            polarities_arg = polarities
        elif type(polarities) is dict:
            polarities = [polarities["pixel"], polarities["line"], polarities["frame"],
                          polarities["marker3"]]
        elif type(polarities) is not list:
            raise ValueError()

        if type(polarities) is list:
            for i, item in enumerate(polarities):
                if type(item) is str:
                    polarities[i] = TdcLiterals._polarities_to_int[item]
            polarities_arg = 0
            for bit in reversed(polarities):  # so first in list end up in leas significant bit
                polarities_arg = polarities_arg * 2 + 1 if bit else polarities_arg * 2
        self.__set_marker_polarities(c_uint8(polarities_arg))

    @property
    def marker_status(self):
        res = self.__get_marker_status()
        status = []
        if res & 0x1:
            status.append("pixel")
        if res & 0x2:
            status.append("line")
        if res & 0x4:
            status.append("frame")
        if res & 0x8:
            status.append("marker3")
        return status

    @property
    def module_status(self):
        res = self.__get_module_status()
        status = []
        if res & 0x1:
            status.append("HFF")  # Hardware FIFO is full
        if res & 0x2:
            status.append("HFE")  # Hardware FIFO is empty
        if res & 0x4:
            status.append("WFT")  # Waiting for trigger
        if res & 0x8:
            status.append("MEA")  # Module is measuring
        if res & 0x10:
            status.append("ARM")  # Module is armed
        if res & 0x20:
            status.append("HCE")  # Hardware collection timer is expired
        return status

    @property
    def hardware_fifo_full(self):
        return True if (self.__get_module_status() & 0x1) else False

    @property
    def hardware_fifo_empty(self):
        return True if (self.__get_module_status() & 0x2) else False

    @property
    def waiting_for_trigger(self):
        return True if (self.__get_module_status() & 0x4) else False

    @property
    def module_is_measuring(self):
        return True if (self.__get_module_status() & 0x8) else False

    @property
    def module_is_armed(self):
        return True if (self.__get_module_status() & 0x10) else False

    @property
    def hardware_collection_timer_expired(self):
        return True if (self.__get_module_status() & 0x20) else False

    @property
    def routing_compensation(self):
        return self.__get_routing_compensation()

    @routing_compensation.setter
    def routing_compensation(self, compensation_ns: int):
        compensation_ns = max(min(compensation_ns, 65), -57)
        self.__set_routing_compensation(c_int8(compensation_ns))

    @property
    def routing_enables(self):
        enables = self.__get_routing_enables()
        return list(reversed([bool(int(bit)) for bit in format(enables,
                                                               f'0{self.no_of_channels}b')]))

    @routing_enables.setter
    def routing_enables(self, enables: list[bool, int] | int | tuple[int, bool | int]):
        if type(enables) is tuple:
            channel, enable = enables
            self.__set_routing_enable(c_uint8(channel), c_bool(enable))
            return
        elif type(enables) is int:
            enables_arg = enables
        elif type(enables) is not list:
            raise ValueError()

        if type(enables) is list:
            enables_arg = 0
            for bit in reversed(enables):  # so first in list end up in leas significant bit
                enables_arg = enables_arg * 2 + 1 if bit else enables_arg * 2
        self.__set_routing_enables(c_uint8(enables_arg))

    @property
    def trigger_polarity(self) -> TdcLiterals.POLARITIES:
        return "Rising" if self.__get_trigger_polarity() else "Falling"

    @trigger_polarity.setter
    def trigger_polarity(self, polarity: TdcLiterals.POLARITIES | bool | int):
        if type(polarity) is str:
            polarity = TdcLiterals._polarities_to_int[polarity]
        self.__set_trigger_polarity(c_bool(polarity))

    def set_measurement_configuration(self, operation_mode, time_range, front_clipping,
                                      resolution):
        time_range_arg = c_uint32(time_range)
        front_clipping_arg = c_uint32(front_clipping)
        resolution_arg = c_uint8(resolution)
        ret = self.__set_measurement_configuration(c_uint8(operation_mode),
                                                   byref(time_range_arg),
                                                   byref(front_clipping_arg),
                                                   byref(resolution_arg))
        return ret, time_range_arg.value, front_clipping_arg.value, resolution_arg.value

    def get_events_from_buffer(self, buffer: npt.NDArray[np.uint32], max_events, card_number,
                               filter_mtos: bool = False):
        get_events = (self.__get_events_from_buffer if filter_mtos
                      else self.__get_raw_events_from_buffer)
        events = get_events(buffer.ctypes.data, c_uint32(max_events), c_uint8(card_number))
        return buffer, events


class SpcQcX08(__8ChannelDllWrapper):
    INPUT_MODES = Literal["Input", "Calibration Input", 0, 2]
    input_modes = {"Input": 0, "Calibration Input": 2}
    modes_input = {0: "Input", 2: "Calibration Input"}

    def __init__(self, dll_path: Path | str | None = None):
        super().__init__(default_dll_name="spc_qc_x08", no_of_channels=8, dll_path=dll_path)
        self.__dll: CDLL = self._8ChannelDllWrapper__dll

        self.__auto_calibration = self.__dll.auto_calibration

        if self.dll_is_debug_version:
            self.__get_cal_reg = self.__dll.get_cal_reg
            self.__get_cal_reg.restype = c_uint32

        self.__get_raw_event_triplets_from_buffer_to_file = (
            self.__dll.get_raw_event_triplets_from_buffer_to_file)
        self.__get_raw_event_triplets_from_buffer_to_file.argtypes = [c_uint32, c_uint32, c_uint8,
                                                                      c_uint32, c_uint32, c_char_p]
        self.__get_raw_event_triplets_from_buffer_to_file.restype = c_int64

        self.__get_raw_event_triplets_from_buffer = self.__dll.get_raw_event_triplets_from_buffer
        self.__get_raw_event_triplets_from_buffer.argtypes = [POINTER(c_uint64), c_uint32, c_uint8]
        self.__get_raw_event_triplets_from_buffer.restype = c_int64

        self.__get_sync_channel = self.__dll.get_sync_channel
        self.__get_sync_channel.restype = c_int8

        self.__set_sync_channel = self.__dll.set_sync_channel
        self.__set_sync_channel.argtypes = [c_int8]
        self.__set_sync_channel.restype = c_int16

    @property
    def _cal_reg(self):
        if self.dll_is_debug_version:
            return self.__get_cal_reg()
        else:
            raise RuntimeWarning("_cal_reg() method is only available in debug version of the dll")

    @property
    def inputmodes(self):
        inputmodes = (c_uint8 * self.no_of_channels)()
        self._8ChannelDllWrapper__get_channel_inputmodes(cast(inputmodes, POINTER(c_uint8)))
        return [self.modes_input[x] for x in inputmodes]

    @inputmodes.setter
    def inputmodes(self, values: list[INPUT_MODES | int] | tuple[int, INPUT_MODES | int]):
        if type(values) is list:
            values = [
                self.input_modes[x] if (type(x) is str and x in typing.get_args(self.INPUT_MODES))
                else x for x in values][:self.no_of_inputmodes]
            bad_args = [x for x in values if (x not in typing.get_args(self.INPUT_MODES))]
            if bad_args:
                raise ValueError(f"{list(dict.fromkeys(bad_args))} not part of {self.INPUT_MODES}")
            values_arg = (c_uint8 * self.no_of_channels)(*values)
            self._8ChannelDllWrapper__set_channel_inputmodes(values_arg)
        elif type(values) is tuple:
            channel, value = values
            if value in typing.get_args(self.INPUT_MODES):
                if str == type(value):
                    value = self.input_modes[value]
            else:
                raise ValueError(f"{[value]} not part of {self.INPUT_MODES}")
            self._8ChannelDllWrapper__set_channel_inputmode(c_uint8(channel), c_uint8(value))
        else:
            raise ValueError("values must be of one of the following types: list[INPUT_MODES], "
                             "list[int], tuple[int, INPUT_MODES], tuple[int, int]", values)
        # TODO  also raise all others with proper message
        # TODO check what the default text from python is when passing wrong types to functions

    @property
    def sync_channel(self):
        return self.__get_sync_channel()

    @sync_channel.setter
    def sync_channel(self, channel):
        if channel < -1 or channel >= 8:
            raise ValueError("Sync channel must be either -1(all) or 0 through 7")
        self.__set_sync_channel(c_int8(channel))

    def get_event_triplets_from_buffer(self, buffer: npt.NDArray[np.uint32], card_number: int,
                                       max_event_triplets: int | None = None
                                       ) -> tuple[npt.NDArray[np.uint32], int]:
        if max_event_triplets is None:
            max_event_triplets = buffer.size
        events = self.__get_raw_event_triplets_from_buffer(buffer.ctypes.data,
                                                           c_uint32(max_event_triplets),
                                                           c_uint8(card_number))
        return buffer, events

    def get_event_triplets_from_buffer_to_file(self, card_number: int, dir_path: str, idx: int,
                                               min_event_triplets: int,
                                               max_event_triplets: int | None = None,
                                               timeout_ms: int = 10_000) -> tuple[str, int]:
        if max_event_triplets is None:
            max_event_triplets = min_event_triplets
        events = self.__get_raw_event_triplets_from_buffer_to_file(c_uint32(min_event_triplets),
                                                                   c_uint32(max_event_triplets),
                                                                   c_uint8(card_number),
                                                                   c_uint32(idx),
                                                                   c_uint32(timeout_ms),
                                                                   c_char_p(dir_path.encode()))
        return f"{dir_path}/SPC_QC_X08_record_{idx}.data", events


class Pms800(__8ChannelDllWrapper, __EventStream32Bit):
    INPUT_MODES = Literal["Input", "Gated Input", "Calibration Input", 0, 1, 2]
    input_modes = {"Input": 0, "Gated Input": 1, "Calibration Input": 2}
    modes_input = {0: "Input", 1: "Gated Input", 2: "Calibration Input"}

    def __init__(self, dll_path: Path | str | None = None):
        super().__init__(default_dll_name="pms_800", no_of_channels=8, no_of_inputmodes=4,
                         no_of_rates=5, dll_path=dll_path)
        self.__dll: CDLL = self._8ChannelDllWrapper__dll

        self.__get_event_count_threshold = self.__dll.get_event_count_threshold
        self.__get_event_count_threshold.argtypes = [c_uint8]
        self.__get_event_count_threshold.restype = c_int16

        self.__get_event_count_thresholds = self.__dll.get_event_count_thresholds
        self.__get_event_count_thresholds.argtypes = [POINTER(c_uint8)]

        self.__set_event_count_threshold = self.__dll.set_event_count_threshold
        self.__set_event_count_threshold.argtypes = [c_uint8, c_uint8]
        self.__set_event_count_threshold.restype = c_int16

        self.__set_event_count_thresholds = self.__dll.set_event_count_thresholds
        self.__set_event_count_thresholds.argtypes = [POINTER(c_uint8)]
        self.__set_event_count_thresholds.restype = c_int16

        self.__set_measurement_configuration = self.__dll.set_measurement_configuration
        self.__set_measurement_configuration.argtypes = [c_uint8, POINTER(c_uint32),
                                                         POINTER(c_uint32), POINTER(c_uint8),
                                                         POINTER(c_uint32)]
        self.__set_measurement_configuration.restype = c_int16

    @property
    def event_count_thresholds(self):
        event_count_thresholds_arg = (c_uint8 * self.no_of_inputmodes)()
        self.__get_event_count_thresholds(cast(event_count_thresholds_arg, POINTER(c_uint8)))
        return event_count_thresholds_arg[:]

    @event_count_thresholds.setter
    def event_count_thresholds(self, values: list[int] | tuple[int, int]):
        if type(values) is list:
            values = [max(1, min(127, x)) for x in values]
            values_arg = (c_uint8 * self.no_of_inputmodes)(*values)
            self.__set_event_count_thresholds(cast(values_arg, POINTER(c_uint8)))
        else:
            channel, value = values
            value = max(1, min(127, value))
            result = self.__set_event_count_threshold(c_uint8(channel), c_uint8(value))
            if result == -1:
                raise ValueError(f"Channel({channel}) out of range [0-3]")
            elif result == -2:
                raise RuntimeError("Hardware register could not be set")

    @property
    def inputmodes(self):
        inputmodes = (c_uint8 * self.no_of_inputmodes)()  # TODO add arg to var name
        self._8ChannelDllWrapper__get_channel_inputmodes(cast(inputmodes, POINTER(c_uint8)))
        return [self.modes_input[x] for x in inputmodes]

    @inputmodes.setter
    def inputmodes(self, values: list[INPUT_MODES] | list[int] | tuple[int, INPUT_MODES | int]):
        # TODO remove all prints
        if type(values) is list:
            values = (
                [self.input_modes[x] if (type(x) is str and x in typing.get_args(self.INPUT_MODES))
                 else x for x in values][:self.no_of_inputmodes])
            bad_args = [x for x in values if (x not in typing.get_args(self.INPUT_MODES))]
            if bad_args:
                raise ValueError(f"{list(dict.fromkeys(bad_args))} not part of "
                                 f"{self.INPUT_MODES}")
            values_arg = (c_uint8 * self.no_of_inputmodes)(*values)
            self._8ChannelDllWrapper__set_channel_inputmodes(values_arg)
# TODO check for proper arg passing cast(values_arg, POINTER(c_uint8))
        else:
            channel, value = values
            if value in typing.get_args(self.INPUT_MODES):
                if str == type(value):
                    value = self.input_modes[value]
            else:
                raise ValueError(f"{[value]} not part of {self.INPUT_MODES}")
            self._8ChannelDllWrapper__set_channel_inputmode(c_uint8(channel), c_uint8(value))

    def set_measurement_configuration(self, operation_mode, time_range, front_clipping, resolution,
                                      bin_size):
        time_range_arg = c_uint32(time_range)
        front_clipping_arg = c_uint32(front_clipping)
        resolution_arg = c_uint8(resolution)
        bin_size_arg = c_uint32(bin_size)
        ret = self.__set_measurement_configuration(c_uint8(operation_mode), byref(time_range_arg),
                                                   byref(front_clipping_arg),
                                                   byref(resolution_arg), byref(bin_size_arg))
        return (ret, time_range_arg.value, front_clipping_arg.value, resolution_arg.value,
                bin_size_arg.value)
