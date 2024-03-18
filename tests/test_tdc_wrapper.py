import pytest

import bhpy as bh

class Constants:
  version = [2, 3, 0]

class TestX08:
  def test_init(self):
    cardX08 = bh.SpcQcX08(dllPath="c:/Users/enzo/BH/SPC-QC-104/CVI/Build/spc_qc_X08.dll")
    assert [cardX08.version["major"],cardX08.version["minor"],cardX08.version["patch"]] == Constants.version

    cardX08.init([0], emulateHardware=True)
    assert cardX08.serialNumber[0][:2] == "3R"

    assert cardX08.cardFocus == 0
    cardX08.cardFocus = 1          # In Emulation never more than 1 card
    assert cardX08.cardFocus == 0  # so this need to default to the previous value
    
    assert False not in cardX08.channelEnables
    cardX08.channelEnables = [False,False,False,False, False,False,False,False]
    assert not (True in cardX08.channelEnables)
    for i in range(cardX08.noOfChannels):
      cardX08.channelEnables = (i, True)
      assert True == cardX08.channelEnables[i]
    
    assert False == cardX08.externalTriggerEnable
    cardX08.externalTriggerEnable = True
    assert True == cardX08.externalTriggerEnable

    assert 0 == cardX08.firmwareVersion
    cardX08.reset_registers()
    assert 1 == cardX08.firmwareVersion #this is the same register and therefore in emu will return what was written by reset_registers()

    assert False == cardX08.hardwareCountdownEnable
    cardX08.hardwareCountdownEnable = True
    assert True == cardX08.hardwareCountdownEnable
    
    assert 0.0 == cardX08.hardwareCountdownTime
    cardX08.hardwareCountdownTime = 50.0 #50ns
    assert 100.0 == cardX08.hardwareCountdownTime
    cardX08.hardwareCountdownTime = 200.0
    assert 200.0 == cardX08.hardwareCountdownTime
    cardX08.hardwareCountdownTime = 30_001.0
    assert 30_000.0 == cardX08.hardwareCountdownTime
    cardX08.hardwareCountdownTime = 300_002.0
    assert 300_000.0 == cardX08.hardwareCountdownTime
    cardX08.hardwareCountdownTime = 4_000_003.0
    assert 4_000_000.0 == cardX08.hardwareCountdownTime
    cardX08.hardwareCountdownTime = 1_000_000_004.0
    assert 1_000_000_004.0 == cardX08.hardwareCountdownTime
    cardX08.hardwareCountdownTime = 55_000_000_001.0 #55s
    assert 17_179_869_180.0 == cardX08.hardwareCountdownTime

    assert all(rate == 0 for rate in cardX08.rates)

class TestX04:
  def test_init(self):
    cardX04 = bh.SpcQcX04("c:/Users/enzo/BH/SPC-QC-104/CVI/Build/spc_qc_X04.dll")
    assert [cardX04.version["major"], cardX04.version["minor"], cardX04.version["patch"]] == Constants.version

    cardX04.init([0], emulateHardware=True)
    assert cardX04.serialNumber[0][:2] == "3T"

    assert cardX04.cardFocus == 0
    cardX04.cardFocus = 1          # In Emulation never more than 1 card
    assert cardX04.cardFocus == 0  # so this need to default to the previous value

    assert True not in cardX04.channelEnables
    cardX04.channelEnables = [True,True,True,True]
    assert not (False in cardX04.channelEnables)
    for i in range(4):
      cardX04.channelEnables = (i, False)
      assert False == cardX04.channelEnables[i]
    
    assert False == cardX04.externalTriggerEnable
    cardX04.externalTriggerEnable = True
    assert True == cardX04.externalTriggerEnable

    assert 0 == cardX04.firmwareVersion
    cardX04.reset_registers()
    assert 1 == cardX04.firmwareVersion #this is the same register and therefore in emu will return what was written by reset_registers()

    assert False == cardX04.hardwareCountdownEnable
    cardX04.hardwareCountdownEnable = True
    assert True == cardX04.hardwareCountdownEnable
    
    assert 0.0 == cardX04.hardwareCountdownTime
    cardX04.hardwareCountdownTime = 50.0 #50ns
    assert 100.0 == cardX04.hardwareCountdownTime
    cardX04.hardwareCountdownTime = 220.0 #220ns
    assert 200.0 == cardX04.hardwareCountdownTime
    cardX04.hardwareCountdownTime = 221_000.0 #220us
    assert 220_000.0 == cardX04.hardwareCountdownTime
    cardX04.hardwareCountdownTime = 13_330_000.0 #13.33ms
    assert 13_300_000.0 == cardX04.hardwareCountdownTime
    cardX04.hardwareCountdownTime = 1_444_000_000.0 #1.441s
    assert 1_445_000_000.0 == cardX04.hardwareCountdownTime
    cardX04.hardwareCountdownTime = 55_000_000_000.0 #55s
    assert 50_000_000_000.0 == cardX04.hardwareCountdownTime

    assert all(rate == 0 for rate in cardX04.rates)

    assert cardX04.initialize_data_collection(1) == 128
    cardX04.deinit_data_collection()
    assert cardX04.initialize_data_collection(128*5000 + 1) == 128*5000
    cardX04.deinit_data_collection()
    assert cardX04.initialize_data_collection((128//4)*10_007) == (128//4)*10_007
    cardX04.deinit_data_collection()


class TestPms:
  def test_init(self):
    cardPms = bh.Pms800("c:/Users/enzo/BH/SPC-QC-104/CVI/Build/pms_800.dll")
    assert [cardPms.version["major"],cardPms.version["minor"],cardPms.version["patch"]] == Constants.version

    cardPms.init([0], emulateHardware=True)
    assert cardPms.serialNumber[0][:2] == "3S"

    assert cardPms.cardFocus == 0
    cardPms.cardFocus = 1          # In Emulation never more than 1 card
    assert cardPms.cardFocus == 0  # so this need to default to the previous value

    assert True not in cardPms.channelEnables
    cardPms.channelEnables = [True,True,True,True,True,True,True,True]
    assert not (False in cardPms.channelEnables)
    for i in range(cardPms.noOfChannels):
      cardPms.channelEnables = (i, False)
      assert False == cardPms.channelEnables[i]
    
    assert False == cardPms.externalTriggerEnable
    cardPms.externalTriggerEnable = True
    assert True == cardPms.externalTriggerEnable

    assert 0 == cardPms.firmwareVersion
    cardPms.reset_registers()
    assert 1 == cardPms.firmwareVersion #this is the same register and therefore in emu will return what was written by reset_registers()

    assert False == cardPms.hardwareCountdownEnable
    cardPms.hardwareCountdownEnable = True
    assert True == cardPms.hardwareCountdownEnable
    
    assert 0.0 == cardPms.hardwareCountdownTime
    cardPms.hardwareCountdownTime = 50.0 #50ns
    assert 100.0 == cardPms.hardwareCountdownTime
    cardPms.hardwareCountdownTime = 200.0
    assert 200.0 == cardPms.hardwareCountdownTime
    cardPms.hardwareCountdownTime = 30_001.0
    assert 30_000.0 == cardPms.hardwareCountdownTime
    cardPms.hardwareCountdownTime = 300_002.0
    assert 300_000.0 == cardPms.hardwareCountdownTime
    cardPms.hardwareCountdownTime = 4_000_003.0
    assert 4_000_000.0 == cardPms.hardwareCountdownTime
    cardPms.hardwareCountdownTime = 1_000_000_004.0
    assert 1_000_000_004.0 == cardPms.hardwareCountdownTime
    cardPms.hardwareCountdownTime = 55_000_000_001.0 #55s
    assert 17_179_869_180.0 == cardPms.hardwareCountdownTime

    assert all(rate == 0 for rate in cardPms.rates)