import logging
log = logging.getLogger(__name__)

try:
  from ctypes import byref, c_int16, create_string_buffer, Structure, CDLL, POINTER, c_char_p, c_uint8, c_uint16, c_uint32, c_bool, c_double, c_int8, c_float, c_void_p, c_uint64, c_int64, Union, LittleEndianStructure, c_char, c_int32
  from pathlib import Path
  import argparse
  import numpy as np
  import numpy.typing as npt
  import re
  import sys
  import threading
  from typing import Literal
  import winreg
except ModuleNotFoundError as err:
  # Error handling
  log.error(err)
  raise

class ModuleInit(Structure):
  _fields_ = [("deviceNr", c_uint8),
              ("initialized", c_bool),
              ("serialNrStr", c_char * 12)]

class ModuleStatusFlags(LittleEndianStructure):
  _fields_ = [("fifoFull", c_uint8, 1),
              ("fifoEmpty", c_uint8, 1),
              ("waitTrig", c_uint8, 1),
              ("measure", c_uint8, 1),
              ("armed", c_uint8, 1),
              ("colT", c_uint8, 1)]

class ModuleStatus(Union):
    _fields_ = [("b", ModuleStatusFlags),
                ("asByte", c_uint8)]

class HardwareError(IOError):
  pass

class __TdcDllWrapper:
  DEFAULT_NAMES = Literal["spc_qc_X04", "spc_qc_X08", "pms_800"]
  versionStr = ""
  versionStrBuf = create_string_buffer(128)

  def __init__(self, defaultDllName: DEFAULT_NAMES, noOfChannels: int, noOfRateChannels: int | None = None, dllPath: Path | str | None = None):
    self.noOfChannels = noOfChannels
    if noOfRateChannels is None:
      self.noOfRateChannels = noOfChannels
    else:
      self.noOfRateChannels = noOfRateChannels
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

  def abort_data_collection(self):
    self.__abort_data_collection()

  def deinit_data_collection(self):
    self.__deinit_data_collection()

  def deinit_data_collections(self):
    self.__deinit_data_collections()

  def deinit(self):
    return self.__deinit()

  def get_card_focus(self):
    return self.__get_card_focus()

  def get_channel_enable(self, channel: int):
    return self.__get_channel_enable(c_uint8(channel))

  def get_channel_enables(self):
    enableBits = self.__get_channel_enables()
    enables = []
    for i in range(self.noOfChannels):
      enables.append((enableBits & (1 << i)) > 0)
    return enables

  def get_external_trigger_enable(self):
    return self.__get_external_trigger_enable()

  def get_firmware_version(self):
    return self.__get_firmware_version()

  def get_hardware_countdown_enable(self):
    return self.__get_hardware_countdown_enable()

  def get_hardware_countdown_time(self):
    return self.__get_hardware_countdown_time()

  def get_rate(self, channel):
    arg = c_uint8(channel)
    return self.__get_rate(arg)

  def get_rates(self) -> list[int]:
    rates = (c_uint32 * self.noOfRateChannels)()
    self.get_rates(byref(rates))
    return rates[:]

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

  def read_setting(self, settingId):
    if self.dllIsDebugVersion:
      arg1 = c_uint16(settingId)
      return self.__read_setting(arg1)
    else:
      raise RuntimeWarning("read_setting() method is only available in debug version of the dll")

  def reset_registers(self):
    self.__reset_registers()
    return

  def run_data_collection(self, acquisitionTimeMs, timeoutMs):
    arg1 = c_uint32(acquisitionTimeMs)
    arg2 = c_uint32(timeoutMs)
    return self.__run_data_collection(arg1, arg2)

  def set_card_focus(self, focusOnCardNr):
    arg = c_uint8(focusOnCardNr)
    return self.__set_card_focus(arg)

  def set_channel_enable(self, channel, state) -> int:
    arg1 = c_uint8(channel)
    arg2 = c_bool(state)
    return self.__set_channel_enable(arg1, arg2)

  def set_channel_enables(self, states: list[bool]) -> int:
    enablesArg = 0
    for i, enable in zip(range(8), states):
      if enable:
        enablesArg |= (1 << i)
    return self.__set_channel_enables(c_uint8(enablesArg))

  def set_external_trigger_enable(self, state):
    arg1 = c_bool(state)
    return self.__set_external_trigger_enable(arg1)

  def set_hardware_countdown_enable(self, state):
    arg = c_bool(state)
    return self.__set_hardware_countdown_enable(arg)

  def set_hardware_countdown_time(self, nsTime):
    arg = c_double(nsTime)
    ret = self.__set_hardware_countdown_time(arg)
    if ret < 0:
      raise HardwareError(f"DLL call set_hardware_countdown_time() returned with {int(ret)}, more details: {self.logPath}")
    return ret

  def stop_measurement(self):
    return self.__stop_measurement()

  def write_setting(self, settingId, value):
    if self.dllIsDebugVersion:
      arg1 = c_uint16(settingId)
      arg2 = c_uint32(value)
      return self.__write_setting(arg1, arg2)
    else:
      raise RuntimeWarning("write_setting() method is only available in debug version of the dll")

class __8ChannelDllWrapper(__TdcDllWrapper):
  def __init__(self, **kwargs):
    super().__init__(**kwargs)

    self.__get_channel_inputmode = self.__dll.get_channel_inputmode
    self.__get_channel_inputmode.argtypes = [c_uint8]
    self.__get_channel_inputmode.restype = c_int8













class SpcQcX04(__TdcDllWrapper):
  def __init__(self, dllPath: Path | str | None = None):
    super().__init__(defaultDllName = "spc_qc_X04", noOfChannels = 4, dllPath = dllPath)

class SpcQcX08(__8ChannelDllWrapper):
  def __init__(self, dllPath: Path | str | None = None):
    super().__init__(defaultDllName = "spc_qc_X08", noOfChannels = 8, dllPath = dllPath)

class Pms800(__8ChannelDllWrapper):
  def __init__(self, dllPath: Path | str | None = None):
    super().__init__(defaultDllName = "pms_800", noOfChannels = 8, noOfRateChannels = 5, dllPath = dllPath)

class SpcQcDllWrapper:
  versionStr = ""
  versionStrBuf = create_string_buffer(128)

  def __init__(self, dllPath = None):
    if dllPath is None:
      spcmPath = winreg.QueryValueEx(winreg.OpenKey(winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER), 'SOFTWARE\\BH\\SPCM'), "FilePath")[0]
      dllPath = Path(spcmPath).parent / "DLL/spc_qc_X04.dll"
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
    
    self.__abort_data_collection = self.__dll.abort_data_collection

    self.__deinit_data_collection = self.__dll.deinit_data_collection

    self.__deinit_data_collections = self.__dll.deinit_data_collections

    self.__deinit = self.__dll.deinit
    self.__deinit.restype = c_uint8

    self.__get_events_from_buffer = self.__dll.get_events_from_buffer
    self.__get_events_from_buffer.argtypes = [c_void_p, c_uint32, c_uint8]
    self.__get_events_from_buffer.restype = c_int64

    self.__get_firmware_version = self.__dll.get_firmware_version
    self.__get_firmware_version.restype = c_uint16

    self.__get_marker_enables = self.__dll.get_marker_enables
    self.__get_marker_enables.restype = c_uint8

    self.__get_marker_polarities = self.__dll.get_marker_polarities
    self.__get_marker_polarities.restype = c_uint8

    self.__get_marker_status = self.__dll.get_marker_status
    self.__get_marker_status.restype = c_uint8

    self.__get_module_status = self.__dll.get_module_status
    self.__get_module_status.restype = c_uint8

    self.__get_rates = self.__dll.get_rates
    self.__get_rates.argtypes = [c_uint8]
    self.__get_rates.restype = c_int32

    self.__get_raw_events_from_buffer = self.__dll.get_raw_events_from_buffer
    self.__get_raw_events_from_buffer.argtypes = [c_void_p, c_uint32, c_uint8]
    self.__get_raw_events_from_buffer.restype = c_int64

    self.__get_routing_enables = self.__dll.get_routing_enables
    self.__get_routing_enables.restype = c_uint8

    self.__init = self.__dll.init
    self.__init.argtypes = [POINTER(ModuleInit), c_uint8, c_char_p]
    self.__init.restype = c_int16

    self.__initialize_data_collection = self.__dll.initialize_data_collection
    self.__initialize_data_collection.argtypes = [POINTER(c_uint64)]
    self.__initialize_data_collection.restype = c_int16

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

    self.__set_CFD_threshold = self.__dll.set_CFD_threshold
    self.__set_CFD_threshold.argtypes = [c_uint8, c_float]
    self.__set_CFD_threshold.restype = c_float

    self.__set_CFD_zc = self.__dll.set_CFD_zc
    self.__set_CFD_zc.argtypes = [c_uint8, c_float]
    self.__set_CFD_zc.restype = c_float

    self.__set_channel_delay = self.__dll.set_channel_delay
    self.__set_channel_delay.argtypes = [c_uint8, c_float]
    self.__set_channel_delay.restype = c_float

    self.__set_channel_divider = self.__dll.set_channel_divider
    self.__set_channel_divider.argtypes = [c_uint8, c_uint8]
    self.__set_channel_divider.restype = c_int16

    self.__set_dithering_enable = self.__dll.set_dithering_enable
    self.__set_dithering_enable.argtypes = [c_bool]
    self.__set_dithering_enable.restype = c_int16

    self.__set_external_trigger_enable = self.__dll.set_external_trigger_enable
    self.__set_external_trigger_enable.argtypes = [c_bool]
    self.__set_external_trigger_enable.restype = c_int16

    self.__set_hardware_countdown_enable = self.__dll.set_hardware_countdown_enable
    self.__set_hardware_countdown_enable.argtypes = [c_bool]
    self.__set_hardware_countdown_enable.restype = c_int16

    self.__set_hardware_countdown_time = self.__dll.set_hardware_countdown_time
    self.__set_hardware_countdown_time.argtypes = [c_double]
    self.__set_hardware_countdown_time.restype = c_double

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
    self.__set_measurement_configuration.argtypes = [c_uint8, POINTER(c_uint32),POINTER(c_uint32),POINTER(c_uint8)]
    self.__set_measurement_configuration.restype = c_int16

    self.__set_routing_enable = self.__dll.set_routing_enable
    self.__set_routing_enable.argtypes = [c_uint8, c_bool]
    self.__set_routing_enable.restype = c_int16

    self.__set_routing_enables = self.__dll.set_routing_enables
    self.__set_routing_enables.argtypes = [c_uint8]
    self.__set_routing_enables.restype = c_int16

    self.__set_routing_compensation = self.__dll.set_routing_compensation
    self.__set_routing_compensation.argtypes = [c_int8]
    self.__set_routing_compensation.restype = c_int16

    self.__set_trigger_polarity = self.__dll.set_trigger_polarity
    self.__set_trigger_polarity.argtypes = [c_bool]
    self.__set_trigger_polarity.restype = c_int16

    self.__stop_measurement = self.__dll.stop_measurement
    self.__stop_measurement.restype = c_int16

    self.__write_setting = self.__dll.write_setting
    self.__write_setting.argtypes = [c_uint16, c_uint32]
    self.__write_setting.restype = c_uint32

  def abort_data_collection(self):
    self.__abort_data_collection()

  def deinit_data_collection(self):
    self.__deinit_data_collection()

  def deinit_data_collections(self):
    self.__deinit_data_collections()

  def deinit(self):
    return self.__deinit()

  def get_events_from_buffer(self, buffer: npt.NDArray[np.uint32], maxEvents, cardNumber, filterMTOs: bool=False):
    getEvents = self.__get_events_from_buffer if filterMTOs else self.__get_raw_events_from_buffer
    arg2 = c_uint32(maxEvents)
    arg3 = c_uint8(cardNumber)
    events = getEvents(buffer.ctypes.data, arg2, arg3)
    return buffer, events

  def get_events_from_buffer_to_file(self, cardNumber, filePath, threadEvent: threading.Event, filterMTOs: bool=False):
    getEvents = self.__get_events_from_buffer if filterMTOs else self.__get_raw_events_from_buffer
    Path(filePath).parent.mkdir(parents=True, exist_ok=True)
    with open(filePath, 'wb') as file:
      buffer_size = 8388607
      buffer = np.array([0]*int(buffer_size), dtype=np.uint32) # 1GiB
      arg2 = c_uint32(buffer_size)#0x7F_FFFF)#4000_0000)
      arg3 = c_uint8(cardNumber)

      while not threadEvent.isSet():
        events = getEvents(buffer.ctypes.data, buffer_size, arg3)
        if events > 0:
          file.write(buffer[:int(events)])

      events = getEvents(buffer.ctypes.data, c_uint32(0), arg3)
      while events > 0:
        events = getEvents(buffer.ctypes.data, arg2, arg3)
        if events > 0:
          file.write(buffer[:int(events)])

  def get_firmware_version(self):
    return self.__get_firmware_version()

  def get_marker_enables(self):
    markerEnables = self.__get_marker_enables()
    return [(markerEnables & 0x1), (markerEnables & 0x2), (markerEnables & 0x4), (markerEnables & 0x8)]

  def get_marker_polarities(self):
    markerPolarities = self.__get_marker_polarities()
    return [(markerPolarities & 0x1), (markerPolarities & 0x2), (markerPolarities & 0x4), (markerPolarities & 0x8)]

  def get_marker_status(self):
    markers = self.__get_marker_status()
    return [(markers & 0x1), (markers & 0x2), (markers & 0x4), (markers & 0x8)]

  def get_module_status(self) -> dict:
    ms = ModuleStatus()
    ms.asBytes = self.__get_module_status()
    return dict((field, getattr(ms.b, field)) for field, _ in ms.b._fields_)

  def get_rates(self, channel):
    arg = c_uint8(channel)
    return self.__get_rates(arg)

  def get_routing_enables(self):
    routingEnables = self.__get_routing_enables()
    return [(routingEnables & 0x1), (routingEnables & 0x2), (routingEnables & 0x4), (routingEnables & 0x8)]

  def init(self, moduleList: list[int], logPath: str=None, emulateHardware: bool=False) -> int:
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

  def read_setting(self, settingId):
    arg1 = c_uint16(settingId)
    return self.__read_setting(arg1)

  def reset_registers(self):
    self.__reset_registers()
    return

  def run_data_collection(self, acquisitionTimeMs, timeoutMs):
    arg1 = c_uint32(acquisitionTimeMs)
    arg2 = c_uint32(timeoutMs)
    return self.__run_data_collection(arg1, arg2)

  def set_card_focus(self, focusOnCardNr):
    arg = c_uint8(focusOnCardNr)
    return self.__set_card_focus(arg)

  def set_cfd_threshold(self, channel, threshold) -> float:
    arg1 = c_uint8(channel)
    arg2 = c_float(threshold)
    return self.__set_CFD_threshold(arg1, arg2)

  def set_cfd_zero_cross(self, channel, zeroCross) -> float:
    arg1 = c_uint8(channel)
    arg2 = c_float(zeroCross)
    return self.__set_CFD_zc(arg1, arg2)

  def set_channel_delay(self, channel, nsDelay) -> float:
    arg1 = c_uint8(channel)
    arg2 = c_float(nsDelay)
    return self.__set_channel_delay(arg1, arg2)

  def set_channel_divider(self, channel, divider: int) -> int:
    arg1 = c_uint8(int(channel))
    arg2 = c_uint8(divider)
    return self.__set_channel_divider(arg1, arg2)

  def set_dithering_enable(self, state):
    arg1 = c_bool(state)
    return self.__set_dithering_enable(arg1)

  def set_external_trigger_enable(self, state):
    arg1 = c_bool(state)
    return self.__set_external_trigger_enable(arg1)

  def set_hardware_countdown_enable(self, state):
    arg = c_bool(state)
    return self.__set_hardware_countdown_enable(arg)

  def set_hardware_countdown_time(self, nsTime):
    arg = c_double(nsTime)
    ret = self.__set_hardware_countdown_time(arg)
    if ret < 0:
      raise HardwareError(f"DLL call set_hardware_countdown_time() returned with {int(ret)}, more details: {self.logPath}")
    return ret

  def set_marker_enable(self, marker, state):
    arg1 = c_uint8(marker)
    arg2 = c_bool(state)
    return self.__set_marker_enable(arg1, arg2)

  def set_marker_enables(self, states):
    combinedStates = 0
    if type(states) == type(list):
      for i, state in enumerate(states):
        if state:
          combinedStates |= (1 << i)
      combinedStates &= 0xFF
    else:
      combinedStates = (states & 0xFF)
    arg = c_uint8(combinedStates)
    return self.__set_marker_enables(arg)

  def set_marker_polarities(self, polarities):
    combinedPolarities = 0
    if type(polarities) == type(list):
      for i, polarity in enumerate(polarities):
        if polarity:
          combinedPolarities |= (1 << i)
      combinedPolarities &= 0xFF
    else:
      combinedPolarities = (polarities & 0xFF)
    arg = c_uint8(combinedPolarities)
    return self.__set_marker_polarities(arg)

  def set_marker_polarity(self, marker, polarity):
    arg1 = c_uint8(marker)
    arg2 = c_bool(polarity)
    return self.__set_marker_polarity(arg1, arg2)

  def set_measurement_configuration(self, operationMode, timeRange, frontClipping, resolution):
    arg1 = c_uint8(operationMode)
    arg2 = c_uint32(timeRange)
    arg3 = c_uint32(frontClipping)
    arg4 = c_uint8(resolution)
    ret = self.__set_measurement_configuration(arg1, byref(arg2), byref(arg3), byref(arg4))
    return ret, arg2.value, arg3.value, arg4.value

  def set_routing_enable(self, channel, state):
    arg1 = c_uint8(channel)
    arg2 = c_bool(state)
    return self.__set_routing_enable(arg1, arg2)

  def set_routing_enables(self, states):
    combinedStates = 0
    if type(states) == type(list):
      for i, state in enumerate(states):
        if state:
          combinedStates |= (1 << i)
      combinedStates &= 0xFF
    else:
      combinedStates = (states & 0xFF)
    arg = c_uint8(combinedStates)
    return self.__set_routing_enables(arg)

  def set_routing_compensation(self, delay):
    arg = c_int8(delay)
    return self.__set_routing_compensation(arg)

  def set_trigger_polarity(self, polarity):
    arg1 = c_bool(polarity)
    return self.__set_trigger_polarity(arg1)

  def stop_measurement(self):
    return self.__stop_measurement()

  def write_setting(self, settingId, value):
    arg1 = c_uint16(settingId)
    arg2 = c_uint32(value)
    return self.__write_setting(arg1, arg2)

def main():
  import bhpy
  parser = argparse.ArgumentParser(prog="SPC-QC-X04 DLL Wrapper", description="SPC-QC-X04 dll wrapper that provides python bindings to use Becker&Hickls' SPC-QC-X04 hardware through the dll")
  parser.add_argument('dll_path', nargs='?', default=None)

  args = parser.parse_args()

  spcQcX04 = SpcQcX04(args.dll_path)
  print(spcQcX04.versionStr)
  spcQcX04.init([0], emulateHardware=True)
  print(spcQcX04.serialNumber)
  print(f"Dll debuggable: {spcQcX04.dllIsDebugVersion}")
  input("press enter...")

if __name__ == '__main__':
  main()