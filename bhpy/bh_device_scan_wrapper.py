import logging
log = logging.getLogger(__name__)

try:
    from ctypes import (c_int16, create_string_buffer, Structure, CDLL, c_char_p, c_uint8,
                        c_void_p, c_char)
    import argparse
    from pathlib import Path
    import re
    import sys
except ModuleNotFoundError as err:
    # Error handling
    log.error(err)
    raise


class HardwareScanResult(Structure):
    _fields_ = [("friendlyName", c_char * 32),
                ("serialNumber", c_char * 32),
                ("firmwareVersion", c_char * 32)]


class HardwareError(IOError):
    pass


class BHDeviceScan:
    version_str = ""
    version_str_buf = create_string_buffer(128)

    def __init__(self, dll_path=None):
        if dll_path is None:
            dll_path = Path(sys.modules["bhpy"].__file__).parent / Path("dll/bh_device_scan.dll")
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

        match = re.match(r"(\d+)\.(\d+)\.(\d+)", self.version_str)
        major = int(match.group(1))
        minor = int(match.group(2))
        patch = int(match.group(3))
        if (major != 1):
            raise RuntimeError("Unable to load DLL: incompatible version. Version is: "
                               f"{major}.{minor}.{patch} Expected >= 1.0.0, < 2")

        self.__bhScanHardware = self.__dll.bh_scan_hardware
        self.__bhScanHardware.argtypes = [c_void_p]
        self.__bhScanHardware.restype = c_int16

    def bh_scan_hardware(self) -> list:
        arg1 = (HardwareScanResult * 32)()
        serial_number = []

        for i in range(32):
            arg1[i].friendlyName = bytes(0)
            arg1[i].serialNumber = bytes(0)
            arg1[i].firmwareVersion = bytes(0)

        ret = self.__bhScanHardware(arg1)
        # Structure objects (arg1) are automatically passed byref

        if ret > 0:
            for i, modul in enumerate(arg1):
                if i < ret:
                    serial_number.append((str(modul.friendlyName)[2:-1],
                                         str(modul.serialNumber)[2:-1],
                                         str(modul.firmwareVersion)[2:-1]))
                else:
                    break
        return serial_number


def main():
    parser = argparse.ArgumentParser(prog="BH Device Scan DLL Wrapper",
                                     description="BH device scanning dll wrapper that provides "
                                     "python bindings to scan the system for all present BH "
                                     "devices, their serial number and firmware version.")
    parser.add_argument('dll_path', nargs='?', default=None)

    args = parser.parse_args()

    bh_scan = BHDeviceScan(args.dll_path)
    print(bh_scan.bh_scan_hardware())
    input("press enter...")


if __name__ == '__main__':
    main()
