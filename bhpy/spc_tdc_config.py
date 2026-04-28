"""Configuration helpers for SPC/TDC modules.

These classes provide simple load/save helpers and reasonable defaults for
different hardware families. They write JSON files to the per-user data
directory so that applications can persist configuration between runs.
"""

import logging
log = logging.getLogger(__name__)

try:
    import appdirs
    from pathlib import Path
    import json
except ModuleNotFoundError as err:
    # Error handling
    log.error(err)
    raise


class Pms800Conf():
    """Default locations and helpers for PMS-800 configuration files."""
    default_path = f"{appdirs.user_data_dir(appauthor='BH', appname='bhpy')}/Pms800/Config.json"
    pass


class SpcQcX08Conf():
    """Default locations and helpers for SPC QC X08 configuration files."""
    default_path = f"{appdirs.user_data_dir(appauthor='BH', appname='bhpy')}/SpcQcX08/Config.json"
    pass


class SpcQcX04Conf():
    """Default locations and helpers for SPC QC X04 configuration files.

    The string constants for edges are kept as-is to match the GUI
    representation expected by external tools.
    """
    default_path = f"{appdirs.user_data_dir(appauthor='BH', appname='bhpy')}/SpcQcX04/Config.json"

    POSITIVE_EDGE = "͟  |͞   (rising)"
    NEGATIVE_EDGE = "͞  |͟   (falling)"

    POS_NEG_LIST = [POSITIVE_EDGE, NEGATIVE_EDGE]

    DELTA_TIME_MODE = "Δt"

    def __init__(self, config_path: str = default_path) -> None:
        """Create a configuration with defaults, then try to load from disk.

        Args:
            config_path: Path to a JSON file to load. If it does not exist,
                it will be created with the default contents.
        """
        SpcQcX04Conf.default_path = config_path
        self.selectedCard = '1'
        self.restore_defaults()
        self.load_conf(config_path)

    def load_conf(self, conf_path=None) -> None:
        """Load configuration from ``conf_path``; write defaults if missing."""
        if conf_path is None:
            conf_path = self.default_path
        try:
            with open(conf_path, 'r', encoding='utf8') as f:
                json_conf = json.load(f)
                for name in json_conf:
                    setattr(self, name, json_conf[name])
        except FileNotFoundError:
            self.write_conf(conf_path)

    def write_conf(self, conf_path=None) -> None:
        """Persist the current configuration to disk as JSON."""
        if conf_path is None:
            conf_path = self.default_path
        conf_dict = self.__dict__
        conf_dict.pop('default_path', None)
        Path(conf_path).parent.mkdir(parents=True, exist_ok=True)
        with open(conf_path, 'w', encoding='utf8') as f:
            json.dump(conf_dict, f, indent=2, sort_keys=True, default=str, ensure_ascii=False)

    def restore_config(self) -> None:
        """Reset hardware-related settings to safe defaults.

        Settings that rarely change after initial setup (e.g. thresholds
        tied to the physical setup) are reset to hardware defaults or good
        starting points.
        """
        # Channel wise settings
        self.threshold = [-50.0, -50.0, -50.0, -50.0]
        self.zeroCross = [12.0, 12.0, 12.0, 12.0]
        self.syncEn = [False, False, False, True]
        self.syncDiv = [1, 1, 1, 1]
        self.routingEn = [True, True, True, False]
        self.routingDelay = 0.0

        # Marker wise settings
        self.markerEn = [False, False, False, False]
        self.markerEdge = [self.POSITIVE_EDGE, self.POSITIVE_EDGE, self.POSITIVE_EDGE,
                           self.POSITIVE_EDGE]

        # Other settings
        self.ditheringEn = True
        self.externalTrigEn = False
        self.triggerEdge = self.POSITIVE_EDGE

    def restore_measurement(self) -> None:
        """Reset measurement parameters to common defaults.

        These values are intended to be tailored for each experiment but are
        useful defaults to start from.
        """
        self.channelDelay = [0., 0., 0., 0.]
        self.timeRangePs = 4_194_573
        self.frontClippingNs = 0
        self.measuringDurationNs = 0
        self.stopOnTime = False
        self.dllAutoStopTimeNs = 0
        self.mode = self.DELTA_TIME_MODE
        self.resolution = 12

    def restore_defaults(self) -> None:
        """Reset all settings and parameters to defaults.

        Convenience dispatcher that calls the config and measurement resetters.
        """
        self.restore_config()
        self.restore_measurement()
