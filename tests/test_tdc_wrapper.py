import pytest
import bhpy as bh
import subprocess

skip_test = True

''' Comment out the next line to skip tests during test development '''
# skip_test = False

skip_x04 = False
skip_x08 = False
skip_pms = False
skip_pep_check = False


if skip_test:
    ''' Comment out the test groups that are not to be skipped '''
    # skip_x04 = True
    skip_x08 = True
    skip_pms = True
    skip_pep_check = True


class Constants:
    version = [2, 3, 0]


@pytest.mark.skipif(skip_x08, reason="Test development")
class Test_X08:  # noqa
    card_x08 = bh.SpcQcX08(dll_path="c:/Users/enzo/BH/SPC-QC-104/CVI/Build/spc_qc_X08.dll")

    def test_init_x08(self):
        assert [self.card_x08.version["major"], self.card_x08.version["minor"],
                self.card_x08.version["patch"]] == Constants.version

        self.card_x08.init([0], emulate_hardware=True)
        assert self.card_x08.serial_number[0][:2] == "3R"

        assert self.card_x08.card_focus == 0
        self.card_x08.card_focus = 1          # In Emulation never more than 1 card
        assert self.card_x08.card_focus == 0  # so this need to default to the previous value

    def test_channel_enables(self):
        assert False not in self.card_x08.channel_enables
        self.card_x08.channel_enables = [False, False, False, False, False, False, False, False]
        assert not (True in self.card_x08.channel_enables)
        for i in range(self.card_x08.no_of_channels):
            self.card_x08.channel_enables = (i, True)
            assert self.card_x08.channel_enables[i]

    def test_external_trigger_enable(self):
        assert self.card_x08.external_trigger_enable is False
        self.card_x08.external_trigger_enable = True
        assert self.card_x08.external_trigger_enable

    def test_firmware_version(self):
        assert 0 == self.card_x08.firmware_version
        self.card_x08.reset_registers()
        ''' this is the same register and therefore in emu will return
        what was written by reset_registers() '''
        assert 1 == self.card_x08.firmware_version

    def test_hardware_countdown(self):
        assert self.card_x08.hardware_countdown_enable is False
        self.card_x08.hardware_countdown_enable = True
        assert self.card_x08.hardware_countdown_enable

        assert 0.0 == self.card_x08.hardware_countdown_time
        self.card_x08.hardware_countdown_time = 50.0  # 50ns
        assert 100.0 == self.card_x08.hardware_countdown_time
        self.card_x08.hardware_countdown_time = 200.0
        assert 200.0 == self.card_x08.hardware_countdown_time
        self.card_x08.hardware_countdown_time = 30_001.0
        assert 30_000.0 == self.card_x08.hardware_countdown_time
        self.card_x08.hardware_countdown_time = 300_002.0
        assert 300_000.0 == self.card_x08.hardware_countdown_time
        self.card_x08.hardware_countdown_time = 4_000_003.0
        assert 4_000_000.0 == self.card_x08.hardware_countdown_time
        self.card_x08.hardware_countdown_time = 1_000_000_004.0
        assert 1_000_000_004.0 == self.card_x08.hardware_countdown_time
        self.card_x08.hardware_countdown_time = 55_000_000_001.0  # 55s
        assert 17_179_869_180.0 == self.card_x08.hardware_countdown_time

    def test_rates(self):
        assert all(rate == 0 for rate in self.card_x08.rates)


@pytest.mark.skipif(skip_x04, reason="Test Development")
class Test_X04:  # noqa
    card_x04 = bh.SpcQcX04("c:/Users/enzo/BH/SPC-QC-104/CVI/Build/spc_qc_X04.dll")

    def test_init_x04(self):
        assert [self.card_x04.version["major"], self.card_x04.version["minor"],
                self.card_x04.version["patch"]] == Constants.version

        self.card_x04.init([0], emulate_hardware=True)
        assert self.card_x04.serial_number[0][:2] == "3T"

        assert self.card_x04.card_focus == 0
        self.card_x04.card_focus = 1          # In Emulation never more than 1 card
        assert self.card_x04.card_focus == 0  # so this need to default to the previous value

    @pytest.mark.skipif(skip_test, reason="Test Development")
    def test_channel_enables(self):
        assert True not in self.card_x04.channel_enables
        self.card_x04.channel_enables = [True, True, True, True]
        assert not (False in self.card_x04.channel_enables)
        for i in range(4):
            self.card_x04.channel_enables = (i, False)
            assert self.card_x04.channel_enables[i] is False

    @pytest.mark.skipif(skip_test, reason="Test Development")
    def test_external_trigger_enable(self):
        assert self.card_x04.external_trigger_enable is False
        self.card_x04.external_trigger_enable = True
        assert self.card_x04.external_trigger_enable

    @pytest.mark.skipif(skip_test, reason="Test Development")
    def test_firmware_version(self):
        assert 0 == self.card_x04.firmware_version
        self.card_x04.reset_registers()
        ''' this is the same register and therefore in emu will return
        what was written by reset_registers() '''
        assert 1 == self.card_x04.firmware_version

    @pytest.mark.skipif(skip_test, reason="Test Development")
    def test_hardware_countdown(self):
        assert self.card_x04.hardware_countdown_enable is False
        self.card_x04.hardware_countdown_enable = True
        assert self.card_x04.hardware_countdown_enable

        assert 0.0 == self.card_x04.hardware_countdown_time
        self.card_x04.hardware_countdown_time = 50.0  # 50ns
        assert 100.0 == self.card_x04.hardware_countdown_time
        self.card_x04.hardware_countdown_time = 220.0  # 220ns
        assert 200.0 == self.card_x04.hardware_countdown_time
        self.card_x04.hardware_countdown_time = 221_000.0  # 220us
        assert 220_000.0 == self.card_x04.hardware_countdown_time
        self.card_x04.hardware_countdown_time = 13_330_000.0  # 13.33ms
        assert 13_300_000.0 == self.card_x04.hardware_countdown_time
        self.card_x04.hardware_countdown_time = 1_444_000_000.0  # 1.441s
        assert 1_445_000_000.0 == self.card_x04.hardware_countdown_time
        self.card_x04.hardware_countdown_time = 55_000_000_000.0  # 55s
        assert 50_000_000_000.0 == self.card_x04.hardware_countdown_time

    @pytest.mark.skipif(skip_test, reason="Test Development")
    def test_rates(self):
        assert all(rate == 0 for rate in self.card_x04.rates)

    @pytest.mark.skipif(skip_test, reason="Test Development")
    def test_initialize_data_collection(self):
        assert self.card_x04.initialize_data_collection(1) == 128
        self.card_x04.deinit_data_collection()
        assert self.card_x04.initialize_data_collection(128*5000 + 1) == 128*5000
        self.card_x04.deinit_data_collection()
        assert self.card_x04.initialize_data_collection((128//4)*10_007) == (128//4)*10_007
        self.card_x04.deinit_data_collection()

    @pytest.mark.skipif(skip_test, reason="Test Development")
    def test_cfd_thresholds(self):
        assert all(threshold is None for threshold in self.card_x04.cfd_thresholds)
        self.card_x04.cfd_thresholds = [0.1, 1.0, 10.0, 100.0]
        assert all(threshold == 0.0 for threshold in self.card_x04.cfd_thresholds)
        self.card_x04.cfd_thresholds = [0.0, 0.0, 0.0, 0.0]
        assert all(threshold == 0.0 for threshold in self.card_x04.cfd_thresholds)
        self.card_x04.cfd_thresholds = [-500.0, -5_000.0, -50_000.0, -500_000.0]
        assert all(threshold == -498.046875 for threshold in self.card_x04.cfd_thresholds)
        for i in range(4):
            self.card_x04.cfd_thresholds = (i, -2.0)
            assert self.card_x04.cfd_thresholds[i] == -1.953125

    @pytest.mark.skipif(skip_test, reason="Test Development")
    def test_cfd_zero_cross(self):
        assert all(zero_cross is None for zero_cross in self.card_x04.cfd_zero_cross)
        self.card_x04.cfd_zero_cross = [96.0, 960.0, 9_600.0, 96_000.0]
        assert all(zero_cross == 96.0 for zero_cross in self.card_x04.cfd_zero_cross)
        self.card_x04.cfd_zero_cross = [0.0, 0.0, 0.0, 0.0]
        assert all(zero_cross == 0.0 for zero_cross in self.card_x04.cfd_zero_cross)
        self.card_x04.cfd_zero_cross = [-96.0, -960.0, -9_600.0, -96_000.0]
        assert all(zero_cross == -95.25 for zero_cross in self.card_x04.cfd_zero_cross)
        for i in range(4):
            self.card_x04.cfd_zero_cross = (i, -.8)
            assert self.card_x04.cfd_zero_cross[i] == -0.75
            self.card_x04.cfd_zero_cross = (i, .5)
            assert self.card_x04.cfd_zero_cross[i] == 0.75

    @pytest.mark.skipif(skip_test, reason="Test Development")
    def test_channel_delays(self):
        assert all(delay == 0.0 for delay in self.card_x04.channel_delays)
        self.card_x04.channel_delays = [-0.1, -1.0, -10.0, -100.0]
        assert all(delay == 0.0 for delay in self.card_x04.channel_delays)
        self.card_x04.channel_delays = [0.0, 0.0, 0.0, 0.0]
        assert all(delay == 0.0 for delay in self.card_x04.channel_delays)
        self.card_x04.channel_delays = [129.0, 129.1, 1290.0, 12900.0]
        assert self.card_x04.channel_delays[0] == pytest.approx(4000/31)
        assert all(delay == pytest.approx(4000/31) for delay in self.card_x04.channel_delays)
        for i in range(4):
            self.card_x04.channel_delays = (i, 17.0)
            assert self.card_x04.channel_delays[i] == pytest.approx((11000/651))

    @pytest.mark.skipif(skip_test, reason="Test Development")
    def test_channel_divider(self):
        assert self.card_x04.channel_divider == 0
        self.card_x04.channel_divider = 0
        assert self.card_x04.channel_divider == 1
        for i in range(1, 8):
            self.card_x04.channel_divider = i
            assert self.card_x04.channel_divider == i
        self.card_x04.channel_divider = 8
        assert self.card_x04.channel_divider == 7

    @pytest.mark.skipif(skip_test, reason="Test Development")
    def test_dithering_enable(self):
        assert self.card_x04.dithering_enable == 0
        self.card_x04.dithering_enable = True
        assert self.card_x04.dithering_enable
        self.card_x04.dithering_enable = False
        assert self.card_x04.dithering_enable is False

    def test_marker_enables(self):
        assert all(enable is False for enable in self.card_x04.marker_enables.values())
        self.card_x04.marker_enables = [True, 1, False, 0]
        assert [True, True, False, False] == list(self.card_x04.marker_enables.values())
        self.card_x04.marker_enables = 0b1100
        assert [False, False, True, True] == list(self.card_x04.marker_enables.values())
        with pytest.raises(KeyError):
            self.card_x04.marker_enables = bh.Markers(pixel=True, line=False, frame=True)
        with pytest.raises(ValueError):
            self.card_x04.marker_enables = True  # not yet supported
        self.card_x04.marker_enables = bh.Markers(pixel=True, line=False, frame=True,
                                                  marker3=False)
        marker = self.card_x04.marker_enables
        assert marker["pixel"]
        assert marker["line"] is False
        assert marker["frame"]
        assert marker["marker3"] is False
        self.card_x04.marker_enables = 0
        assert all(enable is False for enable in self.card_x04.marker_enables.values())
        markers = bh.Markers(pixel=False, line=False, frame=False, marker3=False)
        for i, name in enumerate(markers):
            self.card_x04.marker_enables = (i, True)
            assert self.card_x04.marker_enables[name]
            self.card_x04.marker_enables = (name, True)
            assert self.card_x04.marker_enables[name]
            self.card_x04.marker_enables = 1 << i
            assert self.card_x04.marker_enables[name]
    
    def test_hierweiter(self):
        assert "weiter mit den restilchen" == "properties der x04"


@pytest.mark.skipif(skip_pms, reason="Test Development")
class Test_Pms:  # noqa
    card_pms = bh.Pms800("c:/Users/enzo/BH/SPC-QC-104/CVI/Build/pms_800.dll")

    def test_init_pms(self):
        assert [self.card_pms.version["major"], self.card_pms.version["minor"],
                self.card_pms.version["patch"]] == Constants.version

        self.card_pms.init([0], emulate_hardware=True)
        assert self.card_pms.serial_number[0][:2] == "3S"

        assert self.card_pms.card_focus == 0
        self.card_pms.card_focus = 1          # In Emulation never more than 1 card
        assert self.card_pms.card_focus == 0  # so this need to default to the previous value

    def test_channel_enables(self):
        assert True not in self.card_pms.channel_enables
        self.card_pms.channel_enables = [True, True, True, True, True, True, True, True]
        assert not (False in self.card_pms.channel_enables)
        for i in range(self.card_pms.no_of_channels):
            self.card_pms.channel_enables = (i, False)
            assert self.card_pms.channel_enables[i] is False

    def test_external_trigger_enable(self):
        assert self.card_pms.external_trigger_enable is False
        self.card_pms.external_trigger_enable = True
        assert self.card_pms.external_trigger_enable

    def test_firmware_version(self):
        assert 0 == self.card_pms.firmware_version
        self.card_pms.reset_registers()
        '''  this is the same register and therefore in emu will return
        what was written by reset_registers() '''
        assert 1 == self.card_pms.firmware_version

    def test_hardware_countdown(self):
        assert self.card_pms.hardware_countdown_enable is False
        self.card_pms.hardware_countdown_enable = True
        assert self.card_pms.hardware_countdown_enable

        assert 0.0 == self.card_pms.hardware_countdown_time
        self.card_pms.hardware_countdown_time = 50.0  # 50ns
        assert 100.0 == self.card_pms.hardware_countdown_time
        self.card_pms.hardware_countdown_time = 200.0
        assert 200.0 == self.card_pms.hardware_countdown_time
        self.card_pms.hardware_countdown_time = 30_001.0
        assert 30_000.0 == self.card_pms.hardware_countdown_time
        self.card_pms.hardware_countdown_time = 300_002.0
        assert 300_000.0 == self.card_pms.hardware_countdown_time
        self.card_pms.hardware_countdown_time = 4_000_003.0
        assert 4_000_000.0 == self.card_pms.hardware_countdown_time
        self.card_pms.hardware_countdown_time = 1_000_000_004.0
        assert 1_000_000_004.0 == self.card_pms.hardware_countdown_time
        self.card_pms.hardware_countdown_time = 55_000_000_001.0  # 55s
        assert 17_179_869_180.0 == self.card_pms.hardware_countdown_time

    def test_rates(self):
        assert all(rate == 0 for rate in self.card_pms.rates)


@pytest.mark.skipif(skip_pep_check, reason="Test Development")
class Test_PEP8:  # noqa
    def test_pep8conform(self):
        pep_check = "File was not read!!!"
        process = subprocess.Popen("C:/Users/enzo/BH/bhpy/tests/pep_check.bat", text=True,
                                   shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        assert '' == stderr
        with open(stdout.rstrip(), "r") as f:
            pep_check = f.read()
            pep_check = pep_check.replace('\r\n', '')
        assert pep_check == ''
