from ctypes import create_string_buffer, CDLL, POINTER, c_char_p, c_float, c_int32

class LVConnectQC008Wrapper:
  def __init__(self, machineName: str | None = None, errorStringBufferLen: int = 512, resultStringBufferLen: int = 512):
    self.__dll = CDLL("f:/bh/SOFTWARE/BH-LabVIEW/BH-QC008/ControlQC008/ControlQC008.dll")
    self.__Dll_ControlQC008 = self.__dll.Dll_ControlQC008

    #JobCommand[], machineName[], ErrString[], ErrString_len, Result[], Result_len, Rates[], Rates_len
    self.__Dll_ControlQC008.argtypes = [c_char_p, c_char_p, c_char_p, c_int32, c_char_p, c_int32, POINTER(c_float), c_int32]
    self.__Dll_ControlQC008.restype = c_int32
    
    if machineName is None:
      self.machineName = "localhost".encode('utf-8')
    else:
      self.machineName = machineName.encode('utf-8')
    
    self.errString = create_string_buffer(errorStringBufferLen)
    self.resultString = create_string_buffer(resultStringBufferLen)
    self.rates = (c_float * 8)()

  def command(self, command: str, commandArg: str, machineName: str | None = None):
    if machineName is None:
      machineName = self.machineName
    else:
      machineName = machineName.encode('utf-8')

    res = self.__Dll_ControlQC008(f"{command} {commandArg}".encode('utf-8'), machineName, self.errString, len(self.errString), self.resultString, len(self.resultString), self.rates, len(self.rates))
    if 0 == res:
      return self.resultString.value.decode().split(" ")[0], list(self.rates)
    else:
      raise ChildProcessError(f"{self.errString.value.decode()} ({res})")
  
  def get_rates(self, machineName: str | None = None):
    if machineName is None:
      machineName = self.machineName
    else:
      machineName = machineName.encode('utf-8')
    
    if 0 == self.__Dll_ControlQC008("".encode('utf-8'), machineName, None, 0, None, 0, self.rates, 8):
      return list(self.rates)
    else:
      return None

def main():
  lVConnectQC008 = LVConnectQC008Wrapper()
  print(lVConnectQC008.command("ScrPrt", "c:\\Users\\enzo\\Desktop\\lvtest.png"))
  print(lVConnectQC008.get_rates())

if __name__ == '__main__':
  main()