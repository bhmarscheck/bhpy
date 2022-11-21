import logging
log = logging.getLogger(__name__)

try:
  import pathlib
  import json
except ModuleNotFoundError as err:
  # Error handling
  log.error(err)

class SpcQc104Conf():
  default_path = f"{pathlib.Path.home().drive}/BHdata/pbPy/SpcQc104Conf.json"
  positiveEdge = "\u035F  |\u035E   (rising)"
  negativeEdge = "\u035E  |\u035F   (falling)"
  posNegList = [positiveEdge, negativeEdge]
  def __init__(self, configPath: str=default_path) -> None:
    self.default_path = configPath
    self.selectedCard = '1'
    self.restore_defaults()
    self.load_conf(configPath)

  def load_conf(self, confPath = None) -> None:
    if confPath is None:
      confPath = self.default_path
    try:
      with open(confPath,"r") as f:
        jsonConf = json.load(f)
        for name in jsonConf:
          setattr(self, name, jsonConf[name])
    except:
      self.write_conf(confPath)

  def write_conf(self, confPath = None) -> None:
    if confPath is None:
      confPath = self.default_path
    with open(confPath,"w") as f:
      json.dump(self.__dict__, f, indent = 2, sort_keys = True, default = str)

  def restore_config(self) -> None:
    '''Resets the Hardware settings.

    Settings that require little or no changes after initial setup because they
    are tied to the measurement system's components and their assembly, get set
    to values that are either the hardware defaults or good starting point'''
    # Channel wise settings
    self.threshold = [-50.0, -50.0, -50.0, -50.0]
    self.zeroCross = [12.0, 12.0, 12.0, 12.0]
    self.syncEn = [False, False, False, True]
    self.syncDiv = [1, 1, 1, 1]
    self.routingEn = [True, True, True, False]
    self.routingDelay = 0.0

    # Marker wise settings
    self.markerEn = [False, False, False, False]
    self.markerEdge = [SpcQc104Conf.positiveEdge, SpcQc104Conf.positiveEdge,\
      SpcQc104Conf.positiveEdge, SpcQc104Conf.positiveEdge]

    # Other settings
    self.ditheringEn = True
    self.externalTrigEn = False
    self.triggerEdge = SpcQc104Conf.positiveEdge

  def restore_measurement(self) -> None:
    '''Resets the measurement parameters

    Parameters that are related to the individual measurement, that may be
    changed according to the need of the test specimen or the expected/desired
    experiment results'''
    self.channelDelay = [0., 0., 0., 0.]
    self.timeRange = 4_194_573
    self.frontClipping = 0

  def restore_defaults(self) -> None:
    '''Resets all settings and parameters

    Dispatcher call for all different categories of settings and parameters'''
    self.restore_config()
    self.restore_measurement()
