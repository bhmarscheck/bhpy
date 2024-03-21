import logging
log = logging.getLogger(__name__)

try:
    from ctypes import create_string_buffer, CDLL, POINTER, c_char_p, c_float, c_int32
    from pathlib import Path
    import sys
except ModuleNotFoundError as err:
    # Error handling
    log.error(err)
    raise


class LVConnectQC008:
    def __init__(self, dll_path: Path | str | None = None, machine_name: str | None = None,
                 error_string_buffer_len: int = 512, result_string_buffer_len: int = 512):
        if dll_path is None:
            dll_path = Path(sys.modules["bhpy"].__file__).parent / Path("dll/ControlQC008.dll")
        else:
            dll_path = Path(dll_path)

        self.__dll = CDLL(str(dll_path.absolute()))
        self.__Dll_ControlQC008 = self.__dll.Dll_ControlQC008

        self.__Dll_ControlQC008.argtypes = [c_char_p, c_char_p, c_char_p, c_int32, c_char_p,
                                            c_int32, POINTER(c_float), c_int32]
        self.__Dll_ControlQC008.restype = c_int32

        if machine_name is None:
            self.machine_name = "localhost".encode('utf-8')
        else:
            self.machine_name = machine_name.encode('utf-8')

        self.errString = create_string_buffer(error_string_buffer_len)
        self.resultString = create_string_buffer(result_string_buffer_len)
        self.rates = (c_float * 8)()

    def command(self, command: str, command_arg: str, machine_name: str | None = None):
        if machine_name is None:
            machine_name = self.machine_name
        else:
            machine_name = machine_name.encode('utf-8')

        res = self.__Dll_ControlQC008(f"{command} {command_arg}".encode('utf-8'), machine_name,
                                      self.errString, len(self.errString), self.resultString,
                                      len(self.resultString), self.rates, len(self.rates))
        if 0 == res:
            return self.resultString.value.decode().split(" ")[0], list(self.rates)
        else:
            raise ChildProcessError(f"{self.errString.value.decode()} ({res})")

    def get_rates(self, machine_name: str | None = None):
        if machine_name is None:
            machine_name = self.machine_name
        else:
            machine_name = machine_name.encode('utf-8')

        if 0 == self.__Dll_ControlQC008("".encode('utf-8'), machine_name, None, 0, None, 0,
                                        self.rates, 8):
            return list(self.rates)
        else:
            return None


def main():
    import appdirs
    lv_connect_qc008 = LVConnectQC008()
    print(lv_connect_qc008.command("ScrPrt",
                                   f"{appdirs.user_data_dir(appauthor='BH', appname='bhpy')}"
                                   "LVConnectQC008\\temp\\lvtest.png"))
    print(lv_connect_qc008.get_rates())


if __name__ == '__main__':
    main()
