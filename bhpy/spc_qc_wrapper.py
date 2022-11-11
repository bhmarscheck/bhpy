import logging
log = logging.getLogger(__name__)

try:
  import pathlib
  import argparse
  from ctypes import byref, c_int16, addressof, create_string_buffer, Structure, CDLL, POINTER, c_char_p,\
    c_uint8, c_uint16, c_uint32, c_bool, c_double, c_int8, c_int32, c_float, c_void_p, c_uint64, c_int64
except ModuleNotFoundError as err:
  # Error handling
  log.error(err)

class ModuleInit(Structure):
  _fields_ = [("deviceNr", c_uint8), ("serialNrStr", c_char_p)]

class SpcQcDllWrapper:
  versionStr = ""
  versionStrBuf = create_string_buffer(128)

  def __init__(self, filename):
    self.dll = CDLL(filename)

    self.__get_version = self.dll.get_version
    self.__get_version.restype = c_int16

    self.__init = self.dll.init
    self.__init.restype = c_int16
    self.__init.argtypes = [POINTER(ModuleInit), c_uint8, c_char_p]

    self.deinit = self.dll.deinit
    self.deinit.restype = c_int16

    self.__set_card_focus = self.dll.set_card_focus
    self.__set_card_focus.restype = c_int16
    self.__set_card_focus.argtypes = [c_uint8]

    self.__write_setting = self.dll.write_setting
    self.__write_setting.restype = c_uint32
    self.__write_setting.argtypes = [c_uint16, c_uint32]

    self.__read_setting = self.dll.read_setting
    self.__read_setting.restype = c_uint32
    self.__read_setting.argtypes = [c_uint16]

    self.set_DAC_value = self.dll.set_DAC_value
    self.set_DAC_value.restype = c_int16
    self.set_DAC_value.argtypes = [c_int16, c_uint8]

    self.get_firmware_version = self.dll.get_firmware_version
    self.get_firmware_version.restype = c_uint16

    self.__reset_registers = self.dll.reset_registers
    self.__reset_registers.restype = c_uint16

    self.get_rates = self.dll.get_rates
    self.get_rates.argtypes = [c_uint8]
    self.get_rates.restype = c_uint32

    self.__set_lower_limit = self.dll.set_lower_limit
    self.__set_lower_limit.argtype = c_uint16
    self.__set_lower_limit.restype = c_int16

    self.get_marker_status = self.dll.get_marker_status
    self.get_marker_status.argtype = c_uint8
    self.get_marker_status.restype = c_int8

    self.__set_external_trigger_use = self.dll.set_external_trigger_use
    self.__set_external_trigger_use.argtype = c_bool
    self.__set_external_trigger_use.restype = c_int8

    self.__set_trigger_edge = self.dll.set_trigger_edge
    self.__set_trigger_edge.argtype = c_uint8
    self.__set_trigger_edge.restype = c_int8

    self.__set_routing_delay = self.dll.set_routing_delay
    self.__set_routing_delay.argtype = c_int8
    self.__set_routing_delay.restype = c_int8

    self.__set_routing_enable = self.dll.set_routing_enable
    self.__set_routing_enable.argtypes = [c_uint8, c_bool]
    self.__set_routing_enable.restype = c_int8

    self.set_stop_on_timer = self.dll.set_stop_on_timer
    self.set_stop_on_timer.argtype = c_bool
    self.set_stop_on_timer.restype = c_int8

    self.__set_marker_edge = self.dll.set_marker_polarity
    self.__set_marker_edge.argtypes = [c_uint8, c_uint8]
    self.__set_marker_edge.restype = c_int8

    self.get_module_status = self.dll.get_module_status
    self.get_module_status.restype = c_uint8

    self.__set_dt_mode = self.dll.set_dt_mode
    self.__set_dt_mode.argtype = c_bool
    self.__set_dt_mode.restype = c_int8

    self.start_measurement = self.dll.start_measurement
    self.start_measurement.restype = c_int8

    self.stop_measurement = self.dll.stop_measurement
    self.stop_measurement.restype = c_int8

    self.set_timer_duration = self.dll.set_timer_duration
    self.set_timer_duration.argtype = c_double
    self.set_timer_duration.restype = c_double

    self.__set_time_range = self.dll.set_time_range
    self.__set_time_range.argtype = c_uint32
    self.__set_time_range.restype = c_int32

    self.__set_marker_enable = self.dll.set_marker_enable
    self.__set_marker_enable.argtypes = [c_uint8, c_bool]
    self.__set_marker_enable.restype = c_int8

    self.__set_sync_divider = self.dll.set_sync_divider
    self.__set_sync_divider.argtypes = [c_uint8, c_uint8]
    self.__set_sync_divider.restype = c_int8

    self.__set_sync_enable = self.dll.set_sync_enable
    self.__set_sync_enable.argtypes = [c_uint8, c_bool]
    self.__set_sync_enable.restype = c_int8

    self.__set_dithering_enable = self.dll.set_dithering_enable
    self.__set_dithering_enable.argtype = c_bool
    self.__set_dithering_enable.restype = c_int8

    self.set_channel_delay = self.dll.set_channel_delay
    self.set_channel_delay.argtypes = [c_uint8, c_float]
    self.set_channel_delay.restype = c_float

    self.__set_CFD_threshold = self.dll.set_CFD_threshold
    self.__set_CFD_threshold.argtypes = [c_uint8, c_float]
    self.__set_CFD_threshold.restype = c_float

    self.__set_CFD_zc = self.dll.set_CFD_zc
    self.__set_CFD_zc.argtypes = [c_uint8, c_float]
    self.__set_CFD_zc.restype = c_float

    self.initialise_data_collection = self.dll.initialise_data_collection
    self.initialise_data_collection.argtype = c_uint64
    self.initialise_data_collection.restype = c_int16

    self.run_data_collection = self.dll.run_data_collection
    self.run_data_collection.argtype = c_uint32
    self.run_data_collection.restype = c_int16

    self.get_raw_events_from_buffer = self.dll.get_raw_events_from_buffer
    self.get_raw_events_from_buffer.argtypes = [c_void_p, c_uint32]
    self.get_raw_events_from_buffer.restype = c_int64

    self.deinit_data_collection = self.dll.deinit_data_collection

    self.stop_data_collection = self.dll.stop_data_collection
    self.__get_version(byref(self.versionStrBuf))
    self.versionStr = str(self.versionStrBuf.value)[2:-1]

  def init(self, moduleList: list[int], logPath: str) -> int:
    arg1 = (ModuleInit * len(moduleList))()
    self.serialNumber = []
    serialNumber = []

    for i in range(len(moduleList)):
      serialNumber.append(create_string_buffer(16))
      arg1[i].serialNrStr = addressof(serialNumber[-1])
      arg1[i].deviceNr = c_uint8(moduleList[i])

    res = c_int16(self.__init(arg1, c_uint8(len(moduleList)), logPath.encode('utf-8')))

    for serStr in serialNumber:
      self.serialNumber.append(str(serStr.value)[2:-1])
    return res.value

  def set_dt_mode(self, enable):
    arg = c_bool(enable)
    ret = c_int8(self.__set_dt_mode(arg))
    return ret.value

  def set_time_range(self, timeRange):
    arg = c_uint32(timeRange)
    res = c_int32(self.__set_time_range(arg))
    return res.value

  def set_lower_limit(self, frontClipping):
    arg = c_uint16(frontClipping)
    res = c_int16(self.__set_lower_limit(arg))
    return res.value

  def set_cfd_zero_cross(self, channel, zeroCross) -> float:
    arg1 = c_uint8(channel)
    arg2 = c_float(zeroCross)
    res = c_float(self.__set_CFD_zc(arg1, arg2))
    return res.value

  def set_cfd_threshold(self, channel, threshold) -> float:
    arg1 = c_uint8(channel)
    arg2 = c_float(threshold)
    res = c_float(self.__set_CFD_threshold(arg1, arg2))
    return res.value

  def set_card_focus(self, focusOnCardNr):
    arg = c_uint8(focusOnCardNr)
    res = c_int16(self.__set_card_focus(arg))
    return res.value

  def set_routing_delay(self, delay):
    arg = c_int8(delay)
    res = c_int8(self.__set_routing_delay(arg))
    return res.value

  def set_routing_enable(self, channel, state):
    arg1 = c_uint8(channel)
    arg2 = c_bool(state)
    res = c_int8(self.__set_routing_enable(arg1, arg2))
    return res.value

  def set_sync_enable(self, channel, state):
    arg1 = c_uint8(channel)
    arg2 = c_bool(state)
    res = c_int8(self.__set_sync_enable(arg1, arg2))
    return res.value

  def set_sync_divider(self, channel, divider: int) -> int:
    arg1 = c_uint8(int(channel))
    arg2 = c_uint8(divider)
    res = c_int8(self.__set_sync_divider(arg1, arg2))
    return res.value

  def set_marker_enable(self, marker, state):
    arg1 = c_uint8(marker)
    arg2 = c_bool(state)
    res = c_int8(self.__set_marker_enable(arg1, arg2))
    return res.value

  def set_marker_edge(self, marker, edge):
    arg1 = c_uint8(marker)
    arg2 = c_uint8(edge)
    res = c_int8(self.__set_marker_edge(arg1, arg2))
    return res.value

  def set_dithering_enable(self, state):
    arg1 = c_bool(state)
    res = c_int8(self.__set_dithering_enable(arg1))
    return res.value

  def set_external_trigger_use(self, state):
    arg1 = c_bool(state)
    res = c_int8(self.__set_external_trigger_use(arg1))
    return res.value

  def set_trigger_edge(self, edge):
    arg1 = c_uint8(edge)
    res = c_int8(self.__set_trigger_edge(arg1))
    return res.value

  def reset_registers(self):
    res = c_int16(self.__reset_registers())
    return res.value

  def read_setting(self, settingId):
    arg1 = c_uint16(settingId)
    res = c_uint32(self.__read_setting(arg1))
    return res.value

  def write_setting(self, settingId, value):
    arg1 = c_uint16(settingId)
    arg2 = c_uint32(value)
    res = c_uint32(self.__write_setting(arg1, arg2))
    return res.value

def main():
  home_drive = pathlib.Path.home().drive
  parser = argparse.ArgumentParser(prog="bhPy", description="SPC-QC-104 dll wrapper that provides python bindings to use Becker&Hickls' SPC-QC-104 hardware through the dll")
  parser.add_argument('dll_path', nargs='?', default=f'{home_drive}/Program Files (x86)/BH/SPCM/spc_qc_104.dll')

  args = parser.parse_args()

  dll_path = pathlib.Path(args.dll_path)
  
  print(dll_path)

  if not dll_path.exists:
    dll_path = pathlib.Path(f"{home_drive}/Program Files/BH/SPCM/spc_qc_104.dll")
    if not dll_path.exists:
      print(".../spc_qc_104.dll was neither found at default location nor at the specified path")
      exit()

  spcQcDll = SpcQcDllWrapper(str(dll_path))
  print(spcQcDll.versionStr)

if __name__ == '__main__':
  main()