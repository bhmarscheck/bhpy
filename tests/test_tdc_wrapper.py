import pytest

import bhpy as bh

class TestX04:
  def test_init(self):
    card = bh.SpcQcX04()
    assert card.versionStr.split('+',1)[0] == "2.3.0"

    card.init([0], emulateHardware=True)
    assert card.serialNumber[0][:2] == "3T"

class TestX08:
  def test_init(self):
    card = bh.SpcQcX08()
    assert card.versionStr.split('+',1)[0] == "2.3.0"

    card.init([0], emulateHardware=True)
    assert card.serialNumber[0][:2] == "3R"

class TestPms:
  def test_init(self):
    card = bh.SpcQcX08()
    assert card.versionStr.split('+',1)[0] == "2.3.0"

    card.init([0], emulateHardware=True)
    assert card.serialNumber[0][:2] == "3S"