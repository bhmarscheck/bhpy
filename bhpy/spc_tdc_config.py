import logging
log = logging.getLogger(__name__)

try:
  import appdirs
  import pathlib
  import json
except ModuleNotFoundError as err:
  # Error handling
  log.error(err)

class SpcQcX04Conf():
  default_path = f"{appdirs.user_data_dir(appauthor='BH',appname='SPC-QC-104 GUI')}/SpcQc104Conf.json"

  POSITIVE_EDGE = "͟  |͞   (rising)"
  NEGATIVE_EDGE = "͞  |͟   (falling)"

  POS_NEG_LIST = [POSITIVE_EDGE, NEGATIVE_EDGE]

  DELTA_TIME_MODE = "Δt"

  def __init__(self, configPath: str=default_path) -> None:
    SpcQcX04Conf.default_path = configPath
    self.selectedCard = '1'
    self.restore_defaults()
    self.load_conf(configPath)

  def load_conf(self, confPath = None) -> None:
    if confPath is None:
      confPath = self.default_path
    try:
      with open(confPath, 'r', encoding='utf8') as f:
        jsonConf = json.load(f)
        for name in jsonConf:
          setattr(self, name, jsonConf[name])
    except:
      self.write_conf(confPath)

  def write_conf(self, confPath = None) -> None:
    if confPath is None:
      confPath = self.default_path
    confDict = self.__dict__
    confDict.pop('default_path', None)
    pathlib.Path(confPath).parent.mkdir(parents=True, exist_ok=True)
    with open(confPath, 'w', encoding='utf8') as f:
      json.dump(confDict, f, indent = 2, sort_keys = True, default = str, ensure_ascii=False)

  def restore_config(self) -> None:
    '''Resets the Hardware settings.

    Settings that require little or no changes after initial setup because they are tied to the
    measurement system's components and their assembly, get set to values that are either the
    hardware defaults or good starting point'''
    # Channel wise settings
    self.threshold = [-50.0, -50.0, -50.0, -50.0]
    self.zeroCross = [12.0, 12.0, 12.0, 12.0]
    self.syncEn = [False, False, False, True]
    self.syncDiv = [1, 1, 1, 1]
    self.routingEn = [True, True, True, False]
    self.routingDelay = 0.0

    # Marker wise settings
    self.markerEn = [False, False, False, False]
    self.markerEdge = [self.POSITIVE_EDGE, self.POSITIVE_EDGE, self.POSITIVE_EDGE, self.POSITIVE_EDGE]

    # Other settings
    self.ditheringEn = True
    self.externalTrigEn = False
    self.triggerEdge = self.POSITIVE_EDGE

  def restore_measurement(self) -> None:
    '''Resets the measurement parameters

    Parameters that are related to the individual measurement, that may be changed according to the
    need of the test specimen or the expected/desired experiment results'''
    self.channelDelay = [0., 0., 0., 0.]
    self.timeRangePs = 4_194_573
    self.frontClippingNs = 0
    self.measuringDurationNs = 0
    self.stopOnTime = False
    self.dllAutoStopTimeNs = 0
    self.mode = self.DELTA_TIME_MODE
    self.resolution = 12

  def restore_defaults(self) -> None:
    '''Resets all settings and parameters

    Dispatcher call for all different categories of settings and parameters'''
    self.restore_config()
    self.restore_measurement()
