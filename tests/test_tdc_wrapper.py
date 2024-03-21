import pytest
import bhpy as bh

skipTest = True

skipTest = False
skipX04 = False
skipX08 = False
skipPms = False

if (skipTest):
  #skipX04 = True
  skipX08 = True
  skipPms = True

class Constants:
  version = [2, 3, 0]

@pytest.mark.skipif(skipX08, reason="Test development")
class TestX08:
  cardX08 = bh.SpcQcX08(dllPath="c:/Users/enzo/BH/SPC-QC-104/CVI/Build/spc_qc_X08.dll")
  def test_initX08(self):
    assert [self.cardX08.version["major"],self.cardX08.version["minor"],self.cardX08.version["patch"]] == Constants.version

    self.cardX08.init([0], emulateHardware=True)
    assert self.cardX08.serialNumber[0][:2] == "3R"

    assert self.cardX08.cardFocus == 0
    self.cardX08.cardFocus = 1          # In Emulation never more than 1 card
    assert self.cardX08.cardFocus == 0  # so this need to default to the previous value

  def test_channelEnables(self):
    assert False not in self.cardX08.channelEnables
    self.cardX08.channelEnables = [False,False,False,False, False,False,False,False]
    assert not (True in self.cardX08.channelEnables)
    for i in range(self.cardX08.noOfChannels):
      self.cardX08.channelEnables = (i, True)
      assert True == self.cardX08.channelEnables[i]

  def test_externalTriggerEnable(self):
    assert False == self.cardX08.externalTriggerEnable
    self.cardX08.externalTriggerEnable = True
    assert True == self.cardX08.externalTriggerEnable

  def test_firmwareVersion(self):
    assert 0 == self.cardX08.firmwareVersion
    self.cardX08.reset_registers()
    assert 1 == self.cardX08.firmwareVersion #this is the same register and therefore in emu will return what was written by reset_registers()

  def test_hardwareCountdown(self):
    assert False == self.cardX08.hardwareCountdownEnable
    self.cardX08.hardwareCountdownEnable = True
    assert True == self.cardX08.hardwareCountdownEnable
    
    assert 0.0 == self.cardX08.hardwareCountdownTime
    self.cardX08.hardwareCountdownTime = 50.0 #50ns
    assert 100.0 == self.cardX08.hardwareCountdownTime
    self.cardX08.hardwareCountdownTime = 200.0
    assert 200.0 == self.cardX08.hardwareCountdownTime
    self.cardX08.hardwareCountdownTime = 30_001.0
    assert 30_000.0 == self.cardX08.hardwareCountdownTime
    self.cardX08.hardwareCountdownTime = 300_002.0
    assert 300_000.0 == self.cardX08.hardwareCountdownTime
    self.cardX08.hardwareCountdownTime = 4_000_003.0
    assert 4_000_000.0 == self.cardX08.hardwareCountdownTime
    self.cardX08.hardwareCountdownTime = 1_000_000_004.0
    assert 1_000_000_004.0 == self.cardX08.hardwareCountdownTime
    self.cardX08.hardwareCountdownTime = 55_000_000_001.0 #55s
    assert 17_179_869_180.0 == self.cardX08.hardwareCountdownTime

  def test_rates(self):
    assert all(rate == 0 for rate in self.cardX08.rates)

@pytest.mark.skipif(skipX04, reason = "Test Development")
class TestX04:
  cardX04 = bh.SpcQcX04("c:/Users/enzo/BH/SPC-QC-104/CVI/Build/spc_qc_X04.dll")
  def test_initX04(self):
    assert [self.cardX04.version["major"], self.cardX04.version["minor"], self.cardX04.version["patch"]] == Constants.version

    self.cardX04.init([0], emulateHardware=True)
    assert self.cardX04.serialNumber[0][:2] == "3T"

    assert self.cardX04.cardFocus == 0
    self.cardX04.cardFocus = 1          # In Emulation never more than 1 card
    assert self.cardX04.cardFocus == 0  # so this need to default to the previous value

  @pytest.mark.skipif(skipTest, reason = "Test Development")
  def test_channelEnables(self):
    assert True not in self.cardX04.channelEnables
    self.cardX04.channelEnables = [True,True,True,True]
    assert not (False in self.cardX04.channelEnables)
    for i in range(4):
      self.cardX04.channelEnables = (i, False)
      assert False == self.cardX04.channelEnables[i]

  @pytest.mark.skipif(skipTest, reason = "Test Development")
  def test_externalTriggerEnable(self):
    assert False == self.cardX04.externalTriggerEnable
    self.cardX04.externalTriggerEnable = True
    assert True == self.cardX04.externalTriggerEnable

  @pytest.mark.skipif(skipTest, reason = "Test Development")
  def test_firmwareVersion(self):
    assert 0 == self.cardX04.firmwareVersion
    self.cardX04.reset_registers()
    assert 1 == self.cardX04.firmwareVersion #this is the same register and therefore in emu will return what was written by reset_registers()

  @pytest.mark.skipif(skipTest, reason = "Test Development")
  def test_hardwareCountdown(self):
    assert False == self.cardX04.hardwareCountdownEnable
    self.cardX04.hardwareCountdownEnable = True
    assert True == self.cardX04.hardwareCountdownEnable

    assert 0.0 == self.cardX04.hardwareCountdownTime
    self.cardX04.hardwareCountdownTime = 50.0 #50ns
    assert 100.0 == self.cardX04.hardwareCountdownTime
    self.cardX04.hardwareCountdownTime = 220.0 #220ns
    assert 200.0 == self.cardX04.hardwareCountdownTime
    self.cardX04.hardwareCountdownTime = 221_000.0 #220us
    assert 220_000.0 == self.cardX04.hardwareCountdownTime
    self.cardX04.hardwareCountdownTime = 13_330_000.0 #13.33ms
    assert 13_300_000.0 == self.cardX04.hardwareCountdownTime
    self.cardX04.hardwareCountdownTime = 1_444_000_000.0 #1.441s
    assert 1_445_000_000.0 == self.cardX04.hardwareCountdownTime
    self.cardX04.hardwareCountdownTime = 55_000_000_000.0 #55s
    assert 50_000_000_000.0 == self.cardX04.hardwareCountdownTime

  @pytest.mark.skipif(skipTest, reason = "Test Development")
  def test_rates(self):
    assert all(rate == 0 for rate in self.cardX04.rates)

  @pytest.mark.skipif(skipTest, reason = "Test Development")
  def test_initialize_data_collection(self):
    assert self.cardX04.initialize_data_collection(1) == 128
    self.cardX04.deinit_data_collection()
    assert self.cardX04.initialize_data_collection(128*5000 + 1) == 128*5000
    self.cardX04.deinit_data_collection()
    assert self.cardX04.initialize_data_collection((128//4)*10_007) == (128//4)*10_007
    self.cardX04.deinit_data_collection()

  @pytest.mark.skipif(skipTest, reason = "Test Development")
  def test_cfdThresholds(self):
    assert all(threshold == None for threshold in self.cardX04.cfdThresholds)
    self.cardX04.cfdThresholds = [0.1, 1.0, 10.0, 100.0]
    assert all(threshold == 0.0 for threshold in self.cardX04.cfdThresholds)
    self.cardX04.cfdThresholds = [0.0, 0.0, 0.0, 0.0]
    assert all(threshold == 0.0 for threshold in self.cardX04.cfdThresholds)
    self.cardX04.cfdThresholds = [-500.0, -5_000.0, -50_000.0, -500_000.0]
    assert all(threshold == -498.046875 for threshold in self.cardX04.cfdThresholds)
    for i in range(4):
      self.cardX04.cfdThresholds = (i, -2.0)
      assert self.cardX04.cfdThresholds[i] == -1.953125

  @pytest.mark.skipif(skipTest, reason = "Test Development")
  def test_cfdZeroCross(self):
    assert all(zeroCross == None for zeroCross in self.cardX04.cfdZeroCross)
    self.cardX04.cfdZeroCross = [96.0, 960.0, 9_600.0, 96_000.0]
    assert all(zeroCross == 96.0 for zeroCross in self.cardX04.cfdZeroCross)
    self.cardX04.cfdZeroCross = [0.0, 0.0, 0.0, 0.0]
    assert all(zeroCross == 0.0 for zeroCross in self.cardX04.cfdZeroCross)
    self.cardX04.cfdZeroCross = [-96.0, -960.0, -9_600.0, -96_000.0]
    assert all(zeroCross == -95.25 for zeroCross in self.cardX04.cfdZeroCross)
    for i in range(4):
      self.cardX04.cfdZeroCross = (i, -.8)
      assert self.cardX04.cfdZeroCross[i] == -0.75
      self.cardX04.cfdZeroCross = (i, .5)
      assert self.cardX04.cfdZeroCross[i] == 0.75

  @pytest.mark.skipif(skipTest, reason = "Test Development")
  def test_channelDelays(self):
    assert all(delay == 0.0 for delay in self.cardX04.channelDelays)
    self.cardX04.channelDelays = [-0.1, -1.0, -10.0, -100.0]
    assert all(delay == 0.0 for delay in self.cardX04.channelDelays)
    self.cardX04.channelDelays = [0.0, 0.0, 0.0, 0.0]
    assert all(delay == 0.0 for delay in self.cardX04.channelDelays)
    self.cardX04.channelDelays = [129.0, 129.1, 1290.0, 12900.0]
    assert self.cardX04.channelDelays[0] == pytest.approx(4000/31)
    assert all(delay == pytest.approx(4000/31) for delay in self.cardX04.channelDelays)
    for i in range(4):
      self.cardX04.channelDelays = (i, 17.0)
      assert self.cardX04.channelDelays[i] == pytest.approx((11000/651))

  @pytest.mark.skipif(skipTest, reason = "Test Development")
  def test_channelDivider(self):
    assert self.cardX04.channelDivider == 0
    self.cardX04.channelDivider = 0
    assert self.cardX04.channelDivider == 1
    for i in range(1, 8):
      self.cardX04.channelDivider = i
      assert self.cardX04.channelDivider == i
    self.cardX04.channelDivider = 8
    assert self.cardX04.channelDivider == 7

  @pytest.mark.skipif(skipTest, reason = "Test Development")
  def test_ditheringEnable(self):
    assert self.cardX04.ditheringEnable == 0
    self.cardX04.ditheringEnable = True
    assert self.cardX04.ditheringEnable == True
    self.cardX04.ditheringEnable = False
    assert self.cardX04.ditheringEnable == False

  def test_markerEnables(self):
    assert all(enable == False for enable in self.cardX04.markerEnables.values())
    self.cardX04.markerEnables = [True, 1, False, 0]
    assert [True, True, False, False] == list(self.cardX04.markerEnables.values())
    self.cardX04.markerEnables = 0b1100
    assert [False, False, True, True] == list(self.cardX04.markerEnables.values())
    with pytest.raises(KeyError) as e_info:
      self.cardX04.markerEnables = bh.Markers(pixel = True, line = False, frame = True)
    with pytest.raises(ValueError) as e_info:
      self.cardX04.markerEnables = True #not yet supported
    self.cardX04.markerEnables = bh.Markers(pixel = True, line = False, frame = True, marker3 = False)
    marker = self.cardX04.markerEnables
    assert True == marker["pixel"]
    assert False == marker["line"]
    assert True == marker["frame"]
    assert False == marker["marker3"]
    self.cardX04.markerEnables = 0
    assert all(enable == False for enable in self.cardX04.markerEnables.values())
    markers = bh.Markers(pixel = False, line = False, frame = False, marker3 = False)
    for i, name in enumerate(markers):
      self.cardX04.markerEnables = (i, True)
      assert self.cardX04.markerEnables[name] == True
      self.cardX04.markerEnables = (name, True)
      assert self.cardX04.markerEnables[name] == True
      self.cardX04.markerEnables = 1<<i
      assert self.cardX04.markerEnables[name] == True


@pytest.mark.skipif(skipPms, reason = "Test Development")
class TestPms:
  cardPms = bh.Pms800("c:/Users/enzo/BH/SPC-QC-104/CVI/Build/pms_800.dll")
  def test_initPms(self):
    assert [self.cardPms.version["major"],self.cardPms.version["minor"],self.cardPms.version["patch"]] == Constants.version

    self.cardPms.init([0], emulateHardware=True)
    assert self.cardPms.serialNumber[0][:2] == "3S"

    assert self.cardPms.cardFocus == 0
    self.cardPms.cardFocus = 1          # In Emulation never more than 1 card
    assert self.cardPms.cardFocus == 0  # so this need to default to the previous value

  def test_channelEnables(self):
    assert True not in self.cardPms.channelEnables
    self.cardPms.channelEnables = [True,True,True,True,True,True,True,True]
    assert not (False in self.cardPms.channelEnables)
    for i in range(self.cardPms.noOfChannels):
      self.cardPms.channelEnables = (i, False)
      assert False == self.cardPms.channelEnables[i]
    
  def test_externalTriggerEnable(self):
    assert False == self.cardPms.externalTriggerEnable
    self.cardPms.externalTriggerEnable = True
    assert True == self.cardPms.externalTriggerEnable

  def test_firmwareVersion(self):
    assert 0 == self.cardPms.firmwareVersion
    self.cardPms.reset_registers()
    assert 1 == self.cardPms.firmwareVersion #this is the same register and therefore in emu will return what was written by reset_registers()
    
  def test_hardwareCountdown(self):
    assert False == self.cardPms.hardwareCountdownEnable
    self.cardPms.hardwareCountdownEnable = True
    assert True == self.cardPms.hardwareCountdownEnable
    
    assert 0.0 == self.cardPms.hardwareCountdownTime
    self.cardPms.hardwareCountdownTime = 50.0 #50ns
    assert 100.0 == self.cardPms.hardwareCountdownTime
    self.cardPms.hardwareCountdownTime = 200.0
    assert 200.0 == self.cardPms.hardwareCountdownTime
    self.cardPms.hardwareCountdownTime = 30_001.0
    assert 30_000.0 == self.cardPms.hardwareCountdownTime
    self.cardPms.hardwareCountdownTime = 300_002.0
    assert 300_000.0 == self.cardPms.hardwareCountdownTime
    self.cardPms.hardwareCountdownTime = 4_000_003.0
    assert 4_000_000.0 == self.cardPms.hardwareCountdownTime
    self.cardPms.hardwareCountdownTime = 1_000_000_004.0
    assert 1_000_000_004.0 == self.cardPms.hardwareCountdownTime
    self.cardPms.hardwareCountdownTime = 55_000_000_001.0 #55s
    assert 17_179_869_180.0 == self.cardPms.hardwareCountdownTime

  def test_rates(self):
    assert all(rate == 0 for rate in self.cardPms.rates)