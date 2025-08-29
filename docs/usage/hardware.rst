Hardware Wrappers
=================

Device Scan (``BHDeviceScan``)
------------------------------
Find connected Becker & Hickl devices and read basic info.

.. code-block:: python

   from bhpy import BHDeviceScan

   scan = BHDeviceScan()
   devices = scan.bh_scan_hardware()
   for name, sn, fw in devices:
       print(name, sn, fw)

TDC/Counter Modules (QC-04/08, PMS-800)
---------------------------------------
The DLL wrappers provide access to configuration and acquisition for TCSPC modules. Typical usage involves:

1. Choosing the right wrapper and configuration (``SpcQcX04``, ``SpcQcX08``, ``Pms800`` and corresponding ``*Conf``).
2. Initializing the DLL and hardware (select card, set enables, configure timing).
3. Starting data collection and fetching rates/data.

High-level API sketch (API subject to device DLL capabilities):

.. code-block:: python

   # Example outline (replace with your module and actual parameters)
   from bhpy import SpcQcX04, SpcQcX04Conf

   conf = SpcQcX04Conf()          # load defaults or from user's app data JSON
   conf.restore_defaults()         # or tweak: conf.threshold = [...]
   conf.write_conf()               # persist

   # Open the DLL wrapper and configure
   # td = SpcQcX04()               # class provided by the DLL wrapper
   # td.channel_enables = [True, True, True, True]
   # td.external_trigger_enable = False
   # td.hardware_countdown_time = 1e6  # ns
   # print(td.rates)               # per-channel rates

Notes
-----
- The required BH DLLs must be available. This package expects them under ``bhpy/dll`` when installed via wheel, or in ``dll/`` next to the package during development.
- Version checks ensure the loaded DLLs match the supported major versions.
- Some operations are device/firmware-dependent; consult BH manuals for exact semantics.

