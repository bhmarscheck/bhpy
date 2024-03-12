import logging
log = logging.getLogger(__name__)

try:
  from ctypes import byref, cast, c_int16, create_string_buffer, Structure, CDLL, POINTER, c_char_p, c_uint8, c_uint16, c_uint32, c_bool, c_double, c_int8, c_float, c_void_p, c_uint64, c_int64, Union, LittleEndianStructure, c_char, c_int32
  from pathlib import Path
  import argparse
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
  _fields_ = [("deviceNr", c_uint8),
              ("initialized", c_bool),
              ("serialNrStr", c_char * 12)]

class HardwareError(IOError): #TODO this is meh
  pass

class TdcLiterals:
  DEFAULT_NAMES = Literal["spc_qc_X04", "spc_qc_X08", "pms_800"]

  MARKER = Literal["pixel", "line", "frame", "marker3", 0, 1, 2, 3]
  __markerToInt = {"pixel": 0, "line": 1, "frame": 2, "marker3": 3}

  POLARITIES = Literal["Falling", "Rising"]
  __polaritiesToInt = {"Falling": 0, "Rising": 1}
  __polarities = {"0": "Falling", "1": "Rising"}

class Markers(typing.TypedDict):
  pixel: bool | TdcLiterals.POLARITIES
  line: bool | TdcLiterals.POLARITIES
  frame: bool | TdcLiterals.POLARITIES
  marker3: bool | TdcLiterals.POLARITIES

class __TdcDllWrapper:
  versionStr = ""
  versionStrBuf = create_string_buffer(128)

  def __init__(self, defaultDllName: TdcLiterals.DEFAULT_NAMES, noOfChannels: int, noOfInputmodes: int | None = None, noOfRates: int | None = None, dllPath: Path | str | None = None):
    self.noOfChannels = noOfChannels

    if noOfInputmodes is None:
      self.noOfInputmodes = noOfChannels
    else:
      self.noOfInputmodes = noOfInputmodes

    if noOfRates is None:
      self.noOfRates = noOfChannels
    else:
      self.noOfRates = noOfRates

    if dllPath is None:
      dllPath = Path(sys.modules["bhpy"].__file__).parent / Path(f"dll/{defaultDllName}.dll")
    else:
      dllPath = Path(dllPath)
    
    try:
      self.__dll = CDLL(str(dllPath.absolute()))
    except FileNotFoundError as e:
      log.error(e)
      raise

    self.__get_dll_version = self.__dll.get_dll_version
    self.__get_dll_version.argtypes = [c_char_p, c_uint8]
    self.__get_dll_version.restype = c_int16

    self.__get_dll_version(self.versionStrBuf, c_uint8(128))
    self.versionStr = str(self.versionStrBuf.value)[2:-1]

    match = re.match(r"(\d+)\.(\d+)\.(\d+)", self.versionStr)
    major = int(match.group(1))
    minor = int(match.group(2))
    patch = int(match.group(3))
    if (major != 2):
      raise RuntimeError(f"Unable to load DLL: incompatible version. Version is: {major}.{minor}.{patch} Expected >= 2.0.0, < 3")
    
    self.__get_dll_debug = self.__dll.get_dll_debug
    self.__get_dll_debug.restype = c_uint8
    self.dllIsDebugVersion = (self.__get_dll_debug() > 0)

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

    if self.dllIsDebugVersion:
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

    if self.dllIsDebugVersion:
      self.__write_setting = self.__dll.write_setting
      self.__write_setting.argtypes = [c_uint16, c_uint32]
      self.__write_setting.restype = c_uint32

  @property
  def cardFocus(self) -> int:
    return self.__get_card_focus()
  @cardFocus.setter
  def cardFocus(self, cardNumber):
    self.__set_card_focus(c_uint8(cardNumber))
  
  @property
  def channelEnables(self) -> list[bool]:
    enables = self.__get_channel_enables()
    return reversed([True if digit > 0 else False for digit in format(enables, '08b')]) # so first in list end up in leas significant bit
  @channelEnables.setter
  def channelEnables(self, values: list[bool] | tuple[int, bool]):
    if type(values) is list:
      output = 0
      for bit in reversed(values): # so first in list end up in leas significant bit
        output = output * 2 + 1 if bit else output * 2
      self.__set_channel_enables(c_uint8(output)) #TODO check all setters to not use get functions
    else:
      channel, value = values
      self.__set_channel_enable(c_uint8(channel), c_bool(value))
  
  @property
  def externalTriggerEnable(self) -> bool:
    return True if self.__get_external_trigger_enable() > 0 else False # TODO alle enables returns
  @externalTriggerEnable.setter
  def externalTriggerEnable(self, enable: bool):
    self.__set_external_trigger_enable(c_bool(enable)) # TODO raise on error return for all

  @property
  def firmwareVersion(self) -> int:
    return self.__get_firmware_version()
  
  @property
  def hardwareCountdownEnable(self) -> int:
    return self.__get_hardware_countdown_enable()
  @hardwareCountdownEnable.setter
  def hardwareCountdownEnable(self, state):
    self.__set_hardware_countdown_enable(c_bool(state))
  
  @property
  def hardwareCountdownTime(self) -> float:
    return self.__get_hardware_countdown_time()
  @hardwareCountdownTime.setter
  def hardwareCountdownTime(self, nsTime):
    if self.__set_hardware_countdown_time(c_double(nsTime)) < 0:
      raise HardwareError(f"DLL call set_hardware_countdown_time() returned with error, more details: {self.logPath}")
  
  @property
  def rates(self) -> list[int]:
    c_rates = (c_int32 * self.noOfRates)()
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

  def init(self, moduleList: list[int], logPath: str = None, emulateHardware: bool = False) -> int:
    arg1 = (ModuleInit * len(moduleList))()
    self.serialNumber = []

    self.logPath = logPath

    for i in range(len(moduleList)):
      arg1[i].initialized = False
      arg1[i].serialNrStr = bytes(0)
      arg1[i].deviceNr = c_uint8(moduleList[i])

    numberOfHwModules = len(moduleList) if emulateHardware == False else 0

    lpArg = None if logPath is None else logPath.encode('utf-8')
    ret = self.__init(arg1, c_uint8(numberOfHwModules), lpArg)
    # Structure objects (arg1) are automatically passed byref

    for module in arg1:
      self.serialNumber.append(str(module.serialNrStr)[2:-1])
    return ret

  def initialize_data_collection(self, eventSize):
    arg = c_uint64(eventSize)
    self.__initialize_data_collection(byref(arg))
    return arg.value

  def initialize_data_collections(self, eventSize):
    arg = c_uint64(eventSize)
    self.__initialize_data_collections(byref(arg))
    return arg.value

  def _read_setting(self, settingId):#TODO change all deb only to _leading_private style
    if self.dllIsDebugVersion:
      arg1 = c_uint16(settingId)
      return self.__read_setting(arg1)
    else:
      raise RuntimeWarning("_read_setting() method is only available in debug version of the dll")

  def reset_registers(self):
    self.__reset_registers()
    return

  def run_data_collection(self, acquisitionTimeMs, timeoutMs):
    arg1 = c_uint32(acquisitionTimeMs) #TODO remove these extra steps where not needed
    arg2 = c_uint32(timeoutMs)
    return self.__run_data_collection(arg1, arg2)

  def stop_measurement(self):
    return self.__stop_measurement()

  def _write_setting(self, settingId, value):
    if self.dllIsDebugVersion:
      return self.__write_setting(c_uint16(settingId), c_uint32(value))
    else:
      raise RuntimeWarning("_write_setting() method is only available in debug version of the dll")

class __8ChannelDllWrapper(__TdcDllWrapper):
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
    self.__get_input_thresholds.argtypes = [c_uint8]
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

    if self.dllIsDebugVersion:
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
  def polarities(self):
    polarities = self.__get_channel_polarities()
    return reversed([TdcLiterals.__polarities[digit] for digit in format(polarities, '08b')]) # so first in list end up in leas significant bit
  #TODO remove empty lines between property and setter
  @polarities.setter
  def polarities(self, values: list[TdcLiterals.POLARITIES | int] | tuple[int, TdcLiterals.POLARITIES | int]):
    if type(values) is list:
      values = [TdcLiterals.__polaritiesToInt[x] if (type(x) is str and x in typing.get_args(TdcLiterals.POLARITIES)) else x for x in values]
      badArgs = [x for x in values if (x not in typing.get_args(TdcLiterals.POLARITIES))]
      if badArgs:
        raise ValueError(f"{list(dict.fromkeys(badArgs))} not part of {TdcLiterals.POLARITIES}")
      output = 0
      for bit in reversed(values): # so first in list end up in leas significant bit
        output = output * 2 + bit
      valuesArg = c_uint8(output)
      self.__set_channel_polarities(valuesArg)
    else:
      channel, value = values
      if value in typing.get_args(TdcLiterals.POLARITIES):
        if str == type(value):
          value = TdcLiterals.__polaritiesToInt[value]
      else:
        raise ValueError(f"{[value]} not part of {TdcLiterals.POLARITIES}")
      self.__set_channel_polarity(c_uint8(channel), c_uint8(value))
  
  @property
  def inputThresholds(self):
    thresholds = (c_float * self.noOfChannels)()
    self.__get_input_thresholds(cast(thresholds, POINTER(c_float)))
    return thresholds[:]
  @inputThresholds.setter
  def inputThresholds(self, values: list[float] | tuple[int, float]):
    if type(values) is list:
      self.__set_input_thresholds(cast((c_float * self.noOfChannels)(*values), POINTER(c_float)))
    else:
      channel, value = values
      self.__set_input_threshold(c_uint8(channel), c_float(value))

  @property
  def maxTriggerCount(self):
    return self.__get_max_trigger_count()
  
  @maxTriggerCount.setter
  def maxTriggerCount(self, count: int):
    self.__set_max_trigger_count(c_uint32(count))
  
  @property
  def pulsgeneratorEnable(self):
    return self.__get_pulsgenerator_enable()
  
  @pulsgeneratorEnable.setter
  def pulsgeneratorEnable(self, enable: bool):
    self.__set_pulsgenerator_enable(c_bool(enable))
  
  @property
  def triggerCountdownEnable(self):
    return self.__get_trigger_countdown_enable()
  
  @triggerCountdownEnable.setter
  def triggerCountdownEnable(self, enable: bool):
    self.__set_trigger_countdown_enable(c_bool(enable))
  
  def _write_module_type(self, cardNumber: int, typeString: str):
    if self.dllIsDebugVersion:
      self.__write_module_type(c_uint8(cardNumber), c_char_p(typeString.encode()))
    else:
      raise RuntimeWarning("_write_module_type() method is only available in debug version of the dll")
  
  def _write_production_date(self, cardNumber: int, dateString: str):
    if self.dllIsDebugVersion:
      self.__write_production_date(c_uint8(cardNumber), c_char_p(dateString.encode()))
    else:
      raise RuntimeWarning("_write_production_date() method is only available in debug version of the dll")
  
  def _write_serial_number(self, cardNumber: int, serialString: str):
    if self.dllIsDebugVersion:
      self.__write_serial_number(c_uint8(cardNumber), c_char_p(serialString.encode()))
    else:
      raise RuntimeWarning("_write_serial_number() method is only available in debug version of the dll")

class __EventStream32Bit(__TdcDllWrapper):
  def __init__(self, **kwargs):
    super().__init__(**kwargs)
    self.fileName = kwargs["defaultDllName"]
    self.__dll: CDLL = self._TdcDllWrapper__dll

    self.__get_events_from_buffer = self.__dll.get_events_from_buffer
    self.__get_events_from_buffer.argtypes = [POINTER(c_uint32), c_uint32, c_uint8]
    self.__get_events_from_buffer.restype = c_int64

    self.__get_raw_events_from_buffer = self.__dll.get_raw_events_from_buffer
    self.__get_raw_events_from_buffer.argtypes = [POINTER(c_uint32), c_uint32, c_uint8]
    self.__get_raw_events_from_buffer.restype = c_int64

    self.__get_raw_events_from_buffer_to_file = self.__dll.get_raw_events_from_buffer_to_file
    self.__get_raw_events_from_buffer_to_file.argtypes = [c_uint32, c_uint32, c_uint8, c_uint32, c_uint32, c_char_p]
    self.__get_raw_events_from_buffer_to_file.restype = c_int64

  def get_events_from_buffer(self, buffer: npt.NDArray[np.uint32], maxEvents, cardNumber, filterMTOs: bool=False):
    getEvents = self.__get_events_from_buffer if filterMTOs else self.__get_raw_events_from_buffer
    events = getEvents(buffer.ctypes.data, c_uint32(maxEvents), c_uint8(cardNumber))
    return buffer, events

  def get_events_from_buffer_to_file(self, cardNumber: int, dirPath: str, idx: int, minEvents: int, maxEvents: int | None = None, timeoutMs: int = 10_000) -> tuple[str, int]:
    if maxEvents is None:
      maxEvents = minEvents
    events = self.__get_raw_events_from_buffer_to_file(c_uint32(minEvents), c_uint32(maxEvents), c_uint8(cardNumber), c_uint32(idx), c_uint32(timeoutMs), c_char_p(dirPath.encode()))
    return f"{dirPath}/{self.fileName}_record_{idx}.data", events

class SpcQcX04(__EventStream32Bit):
  def __init__(self, dllPath: Path | str | None = None):
    super().__init__(defaultDllName = "spc_qc_X04", noOfChannels = 4, dllPath = dllPath)
    self.__dll: CDLL = self._EventStream32Bit__dll

    self.__get_CFD_threshold = self.__dll.get_CFD_threshold
    self.__get_CFD_threshold.argtypes = [c_uint8]
    self.__get_CFD_threshold.restype = c_float

    self.__get_CFD_thresholds = self.__dll.get_CFD_thresholds
    self.__get_CFD_thresholds.argtypes = [POINTER(c_float)]
    self.__get_CFD_thresholds.restype = c_int16

    self.__get_CFD_zc = self.__dll.get_CFD_zc
    self.__get_CFD_zc.argtypes = [c_uint8]
    self.__get_CFD_zc.restype = c_float

    self.__get_CFD_zcs = self.__dll.get_CFD_zcs
    self.__get_CFD_zcs.argtypes = [POINTER(c_float)]
    self.__get_CFD_zcs.restype = c_int16

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

    self.__set_CFD_threshold = self.__dll.set_CFD_threshold
    self.__set_CFD_threshold.argtypes = [c_uint8, c_float]
    self.__set_CFD_threshold.restype = c_float

    self.__set_CFD_thresholds = self.__dll.set_CFD_thresholds
    self.__set_CFD_thresholds.argtypes = [POINTER(c_float)]

    self.__set_CFD_zc = self.__dll.set_CFD_zc
    self.__set_CFD_zc.argtypes = [c_uint8, c_float]
    self.__set_CFD_zc.restype = c_float

    self.__set_CFD_zcs = self.__dll.set_CFD_zcs
    self.__set_CFD_zcs.argtypes = [POINTER(c_float)]

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
    self.__set_measurement_configuration.argtypes = [c_uint8, POINTER(c_uint32), POINTER(c_uint32), POINTER(c_uint8)]
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
  def cfdThresholds(self) -> list[float]:
    thresholds = (c_float * self.noOfChannels)()
    self.__get_CFD_thresholds(cast(thresholds, POINTER(c_float)))
    return thresholds[:]
  @cfdThresholds.setter
  def cfdThresholds(self, values: list[float] | tuple[int, float]):
    if type(values) is list:
      self.__set_CFD_thresholds(cast((c_float * self.noOfChannels)(*values), POINTER(c_float)))
    else:
      channel, value = values
      self.__set_CFD_threshold(c_uint8(channel), c_float(value))

  @property
  def cfdZeroCross(self) -> list[float]:
    zeroCrosses = (c_float * self.noOfChannels)()
    self.__get_CFD_zcs(cast(zeroCrosses, POINTER(c_float)))
    return zeroCrosses[:]
  @cfdZeroCross.setter
  def cfdZeroCross(self, values: list[float] | tuple[int, float]):
    if type(values) is list:
      self.__set_CFD_zcs(cast((c_float * self.noOfChannels)(*values), POINTER(c_float)))
    else:
      channel, value = values
      self.__set_CFD_zc(c_uint8(channel), c_float(value))

  @property
  def channelDelays(self) -> list[float]:
    delays = (c_float * self.noOfChannels)()
    self.__get_channel_delays(cast(delays, POINTER(c_float)))
    return delays[:]
  @channelDelays.setter
  def channelDelays(self, values: list[float] | tuple[int, float]):
    if type(values) is list:
      self.__set_channel_delays(cast((c_float * self.noOfChannels)(*values), POINTER(c_float)))
    elif type(values) is tuple:
      channel, value = values
      self.__set_channel_delay(c_uint8(channel), c_float(value))
    else:
      raise ValueError(values)

  @property
  def channelDivider(self):
    return self.__get_channel_divider(c_uint8(3))
  @channelDivider.setter
  def channelDivider(self, divider: int):
    self.__set_channel_divider(c_uint8(3),c_uint8(divider))

  @property
  def ditheringEnable(self):
    return self.__get_dithering_enable()
  @ditheringEnable.setter
  def ditheringEnable(self, enable: bool):
    self.__set_dithering_enable(c_bool(enable))

  @property
  def markerEnables(self) -> Markers:
    enables = self.__get_marker_enables()
    return Markers(pixel = (enables & 0x1) > 0, line = (enables & 0x2) > 0, frame = (enables & 0x4) > 0, marker3 = (enables & 0x8) > 0)
  @markerEnables.setter
  def markerEnables(self, enables: Markers | list[bool, int] | int | tuple[TdcLiterals.MARKER, bool | int]):
    if type(enables) is tuple:
      marker, enable = enables
      if type(marker) is str:
        marker = TdcLiterals.__markerToInt[marker]
      self.__set_marker_enable(c_uint8(marker), c_bool(enable))
      return
    elif type(enables) is int:
      enablesArg = enables
    elif type(enables) is Markers:
      enables = [enables["pixel"], enables["line"], enables["frame"], enables["marker3"]]
    elif type(enables) is not list:
      raise ValueError()
    
    if type(enables) is list:
      enablesArg = 0
      for bit in reversed(enables): # so first in list end up in leas significant bit
        enablesArg = enablesArg * 2 + 1 if bit else enablesArg * 2
    self.__set_marker_enables(c_uint8(enablesArg))

  @property
  def markerPolarities(self):
    polarities = self.__get_marker_polarities()
    return reversed([TdcLiterals.__polarities[digit] for digit in format(polarities, '04b')])
  @markerPolarities.setter
  def markerPolarities(self, polarities: Markers | list[int] | int | tuple[TdcLiterals.MARKER, int]):
    if type(polarities) is tuple:
      marker, polarity = polarities
      if type(marker) is str:
        marker = TdcLiterals.__markerToInt[marker]
      self.__set_marker_polarity(c_uint8(marker), c_bool(polarity))
      return
    elif type(polarities) is int:
      polaritiesArg = polarities
    elif type(polarities) is Markers:
      polarities = [polarities["pixel"], polarities["line"], polarities["frame"], polarities["marker3"]]
    elif type(polarities) is not list:
      raise ValueError()
    
    if type(polarities) is list:
      polaritiesArg = 0
      for bit in reversed(polarities): # so first in list end up in leas significant bit
        polaritiesArg = polaritiesArg * 2 + 1 if bit else polaritiesArg * 2
    self.__set_marker_enables(c_uint8(polaritiesArg))

  @property
  def markerStatus(self):
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
  def moduleStatus(self):
    res = self.__get_module_status()
    status = []
    if res & 0x1:
      status.append("HFF") #Hardware FIFO is full
    if res & 0x2:
      status.append("HFE") #Hardware FIFO is empty
    if res & 0x4:
      status.append("WFT") #Waiting for trigger
    if res & 0x8:
      status.append("MEA") #Module is measuring
    if res & 0x10:
      status.append("ARM") #Module is armed
    if res & 0x20:
      status.append("HCE") #Hardware collection timer is expired
  
  @property
  def hardwareFifoFull(self):
    res = self.__get_module_status()
    return True if (self.__get_module_status() & 0x1) else False
  
  @property
  def hardwareFifoEmpty(self):
    res = self.__get_module_status()
    return True if (self.__get_module_status() & 0x2) else False
  
  @property
  def waitingForTrigger(self):
    res = self.__get_module_status()
    return True if (self.__get_module_status() & 0x4) else False
  
  @property
  def moduleIsMeasuring(self):
    res = self.__get_module_status()
    return True if (self.__get_module_status() & 0x8) else False
  
  @property
  def moduleIsArmed(self):
    res = self.__get_module_status()
    return True if (self.__get_module_status() & 0x10) else False
  
  @property
  def hardwareCollectionTimerExpired(self):
    res = self.__get_module_status()
    return True if (self.__get_module_status() & 0x20) else False

  @property
  def routingCompensation(self):
    return self.__get_routing_compensation()
  @routingCompensation.setter
  def routingCompensation(self, compensationNs: int):
    self.__set_routing_compensation(c_int8(compensationNs))

  @property
  def routingEnables(self):
    enables = self.__get_routing_enables()
    return reversed([True if bit else False for bit in format(enables, '04b')])
  @routingEnables.setter
  def routingEnables(self, enables: list[bool, int] | int | tuple[int, bool | int]):
    if type(enables) is tuple:
      channel, enable = enables
      self.__set_routing_enable(c_uint8(channel), c_bool(enable))
      return
    elif type(enables) is int:
      enablesArg = enables
    elif type(enables) is not list:
      raise ValueError()
    
    if type(enables) is list:
      enablesArg = 0
      for bit in reversed(enables): # so first in list end up in leas significant bit
        enablesArg = enablesArg * 2 + 1 if bit else enablesArg * 2
    self.__set_routing_enables(c_uint8(enablesArg))

  @property
  def triggerPolarity(self) -> TdcLiterals.POLARITIES:
    return "Rising" if self.__get_trigger_polarity() else "Falling"
  @triggerPolarity.setter
  def triggerPolarity(self, polarity: TdcLiterals.POLARITIES | bool | int):
    if type(polarity) is str:
      polarity = TdcLiterals.__polaritiesToInt[polarity]
    self.__set_trigger_polarity(c_bool(polarity))

  def set_measurement_configuration(self, operationMode, timeRange, frontClipping, resolution):
    timeRangeArg = c_uint32(timeRange)
    frontClippingArg = c_uint32(frontClipping)
    resolutionArg = c_uint8(resolution)
    ret = self.__set_measurement_configuration(c_uint8(operationMode), byref(timeRangeArg), byref(frontClippingArg), byref(resolutionArg))
    return ret, timeRangeArg.value, frontClippingArg.value, resolutionArg.value

class SpcQcX08(__8ChannelDllWrapper):
  INPUT_MODES = Literal["Input", "Calibration Input", 0, 2]
  input_modes = {"Input": 0, "Calibration Input": 2}
  modes_input = {0: "Input", 2: "Calibration Input"}
  def __init__(self, dllPath: Path | str | None = None):
    super().__init__(defaultDllName = "spc_qc_X08", noOfChannels = 8, dllPath = dllPath)
    self.__dll: CDLL = self._8ChannelDllWrapper__dll

    self.__auto_calibration = self.__dll.auto_calibration

    if self.dllIsDebugVersion:
      self.__get_cal_reg = self.__dll.get_cal_reg
      self.__get_cal_reg.restype = c_uint32

    self.__get_raw_event_triplets_from_buffer_to_file = self.__dll.get_raw_event_triplets_from_buffer_to_file
    self.__get_raw_event_triplets_from_buffer_to_file.argtypes = [c_uint32, c_uint32, c_uint8, c_uint32, c_uint32, c_char_p]
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
  def _calReg(self):
    if self.dllIsDebugVersion:
      return self.__get_cal_reg()
    else:
      raise RuntimeWarning("_calReg() method is only available in debug version of the dll")

  @property
  def inputmodes(self):
    inputmodes = (c_uint8 * self.noOfChannels)()
    self._8ChannelDllWrapper__get_channel_inputmodes(cast(inputmodes, POINTER(c_uint8)))
    return [self.modes_input[x] for x in inputmodes]

  @inputmodes.setter
  def inputmodes(self, values: list[INPUT_MODES] | list[int] | tuple[int, INPUT_MODES | int]):
    if type(values) is list:
      values = [self.input_modes[x] if (type(x) is str and x in typing.get_args(self.INPUT_MODES)) else x for x in values][:self.noOfInputmodes]
      badArgs = [x for x in values if (x not in typing.get_args(self.INPUT_MODES))]
      if badArgs:
        raise ValueError(f"{list(dict.fromkeys(badArgs))} not part of {self.INPUT_MODES}")
      valuesArg = (c_uint8 * self.noOfChannels)(*values)
      self._8ChannelDllWrapper__set_channel_inputmodes(valuesArg)
    elif type(values) is tuple:
      channel, value = values
      if value in typing.get_args(self.INPUT_MODES):
        if str == type(value):
          value = self.input_modes[value]
      else:
        raise ValueError(f"{[value]} not part of {self.INPUT_MODES}")
      self._8ChannelDllWrapper__set_channel_inputmode(c_uint8(channel), c_uint8(value))
    else:
      raise ValueError("values must be of one of the following types: list[INPUT_MODES], list[int], tuple[int, INPUT_MODES], tuple[int, int]", values)#TODO  also raise all others with proper message TODO check what the default text from python is when passing wrong types to functions

  @property
  def syncChannel(self):
    return self.__get_sync_channel()
  @syncChannel.setter
  def syncChannel(self, channel):
    self.__set_sync_channel(c_int8(channel))

  def get_event_triplets_from_buffer(self, buffer: npt.NDArray[np.uint32], cardNumber: int, maxEventTriplets: int | None = None) -> tuple[npt.NDArray[np.uint32], int]:
    if maxEventTriplets is None:
      maxEventTriplets = buffer.size
    events = self.__get_raw_event_triplets_from_buffer(buffer.ctypes.data, c_uint32(maxEventTriplets), c_uint8(cardNumber))
    return buffer, events

  def get_event_triplets_from_buffer_to_file(self, cardNumber: int, dirPath: str, idx: int, minEventTriplets: int, maxEventTriplets: int | None = None, timeoutMs: int = 10_000) -> tuple[str, int]:
    if maxEventTriplets is None:
      maxEventTriplets = minEventTriplets
    events = self.__get_raw_event_triplets_from_buffer_to_file(c_uint32(minEventTriplets), c_uint32(maxEventTriplets), c_uint8(cardNumber), c_uint32(idx), c_uint32(timeoutMs), c_char_p(dirPath.encode()))
    return f"{dirPath}/SPC_QC_X08_record_{idx}.data", events

class Pms800(__8ChannelDllWrapper, __EventStream32Bit):
  INPUT_MODES = Literal["Input", "Gated Input", "Calibration Input", 0, 1, 2]
  input_modes = {"Input": 0, "Gated Input": 1, "Calibration Input": 2}
  modes_input = {0: "Input", 1: "Gated Input", 2: "Calibration Input"}
  def __init__(self, dllPath: Path | str | None = None):
    super().__init__(defaultDllName = "pms_800", noOfChannels = 8, noOfInputmodes = 4, noOfRates = 5, dllPath = dllPath)
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
    self.__set_measurement_configuration.argtypes = [c_uint8, POINTER(c_uint32), POINTER(c_uint32), POINTER(c_uint8), POINTER(c_uint32)]
    self.__set_measurement_configuration.restype = c_int16

  @property
  def eventCountThresholds(self):
    eventCountThresholdsArg = (c_uint8 * self.noOfInputmodes)()
    self.__get_event_count_thresholds(cast(eventCountThresholdsArg, POINTER(c_uint8)))
    return eventCountThresholdsArg[:]
  @eventCountThresholds.setter
  def eventCountThresholds(self, values: list[int] | tuple[int, int]):
    if type(values) is list:
      valuesArg = (c_uint8 * self.noOfInputmodes)(*values)
      self.__set_event_count_thresholds(cast(valuesArg, POINTER(c_uint8)))
    else:
      channel, value = values
      self.__set_event_count_threshold(c_uint8(channel), c_uint8(value))

  @property
  def inputmodes(self):
    inputmodes = (c_uint8 * self.noOfInputmodes)() #TODO add arg to var name 
    self._8ChannelDllWrapper__get_channel_inputmodes(cast(inputmodes, POINTER(c_uint8)))
    return [self.modes_input[x] for x in inputmodes]
  @inputmodes.setter
  def inputmodes(self, values: list[INPUT_MODES] | list[int] | tuple[int, INPUT_MODES | int]):
    #TODO remove all prints
    if type(values) is list:
      values = [self.input_modes[x] if (type(x) is str and x in typing.get_args(self.INPUT_MODES)) else x for x in values][:self.noOfInputmodes]
      badArgs = [x for x in values if (x not in typing.get_args(self.INPUT_MODES))]
      if badArgs:
        raise ValueError(f"{list(dict.fromkeys(badArgs))} not part of {self.INPUT_MODES}")
      valuesArg = (c_uint8 * self.noOfInputmodes)(*values)
      self._8ChannelDllWrapper__set_channel_inputmodes(valuesArg) #TODO check for proper arg passing cast(valuesArg, POINTER(c_uint8))
    else:
      channel, value = values
      if value in typing.get_args(self.INPUT_MODES):
        if str == type(value):
          value = self.input_modes[value]
      else:
        raise ValueError(f"{[value]} not part of {self.INPUT_MODES}")
      self._8ChannelDllWrapper__set_channel_inputmode(c_uint8(channel), c_uint8(value))

  def set_measurement_configuration(self, operationMode, timeRange, frontClipping, resolution, binSize):
    timeRangeArg = c_uint32(timeRange)
    frontClippingArg = c_uint32(frontClipping)
    resolutionArg = c_uint8(resolution)
    binSizeArg = c_uint32(binSize)
    ret = self.__set_measurement_configuration(c_uint8(operationMode), byref(timeRangeArg), byref(frontClippingArg), byref(resolutionArg), byref(binSizeArg))
    return ret, timeRangeArg.value, frontClippingArg.value, resolutionArg.value, binSizeArg.value

def main():
  import bhpy
  parser = argparse.ArgumentParser(prog="SPC-QC-X04 DLL Wrapper", description="SPC-QC-X04 dll wrapper that provides python bindings to use Becker&Hickls' SPC-QC-X04 hardware through the dll")
  parser.add_argument('dll_path', nargs='?', default=None)

  args = parser.parse_args()

  spcQcX04s = [SpcQcX08(args.dll_path),Pms800(args.dll_path),SpcQcX04(args.dll_path)]
  
  for spcQcX04 in spcQcX04s:
    print(spcQcX04.versionStr)
    spcQcX04.init([0], emulateHardware=True)
    print(spcQcX04.serialNumber)
    print(f"Dll debuggable: {spcQcX04.dllIsDebugVersion}\n")
    if hasattr(spcQcX04, "inputmodes"):
      print(spcQcX04.inputmodes)
      spcQcX04.inputmodes = [0,2,2,0,2,2,2,2]
      print(spcQcX04.inputmodes)
      spcQcX04.inputmodes = ["Input","Input","Input","Calibration Input","Calibration Input","Calibration Input"]
      print(spcQcX04.inputmodes)
      spcQcX04.inputmodes = ["Input","Input","Calibration Input",2,2,2,"Input",2]
      print(spcQcX04.inputmodes)
      spcQcX04.inputmodes = (0, 2)
      print(spcQcX04.inputmodes)
      spcQcX04.inputmodes = (0, "Input")
      print(spcQcX04.inputmodes)
    print("\n")

  input("press enter...\n\n")

if __name__ == '__main__':
  main()