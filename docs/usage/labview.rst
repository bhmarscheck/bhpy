LabVIEW Control (QC008, BDU)
============================

The LabVIEW shims expose simple, command-based control of BH LabVIEW applications.

QC008 (``LVConnectQC008``)
--------------------------
.. code-block:: python

   from bhpy import LVConnectQC008

   qc = LVConnectQC008()  # connects to localhost QC008 app via DLL
   print(qc.dll_version)
   print(qc.firmware_version)

   # Configure and measure
   qc.set_no_of_bins(1024)
   qc.set_resolution(5e-12)
   qc.set_time_range(50e-9)
   qc.set_channel_thresholds([ -50 ] * 8)
   qc.set_collection_time(0.5)     # seconds
   qc.command("StartMeasurement")
   # ... wait or poll qc.measurement_status
   qc.command("StopMeasurement")
   qc.save_sdt("my_measurement")

BDU (``LVConnectBDU``)
----------------------
.. code-block:: python

   from bhpy import LVConnectBDU

   bdu = LVConnectBDU()  # connects to localhost BDU app via DLL
   print(bdu.firmware_version)
   print(bdu.emission)  # True when emission active/possible

   # Generic command access (for commands not yet wrapped):
   # bdu.command('Power', '20')
   # bdu.command('Armed', '1')

Notes
-----
- The respective LabVIEW applications must be running and expose their LVConnect ports.
- Errors from the applications are surfaced as ``ChildProcessError`` with descriptive messages.
- File paths in helpers (e.g., ``save_sdt``) are relative to ``file_saving_path`` (defaults to ``./``).

