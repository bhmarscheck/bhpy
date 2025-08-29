bhpy Documentation
===================

Overview
--------
bhpy provides Python bindings and wrappers for Becker & Hickl software and hardware used in time-correlated single photon counting (TCSPC) and related fluorescence lifetime imaging (FLIM) workflows.

- SPCConnect TCP interface: Automate and script SPCM via a secure TCP protocol (class ``bhpy.BHConnect``).
- LabVIEW control shims: Programmatically control BH LabVIEW apps like QC008 and BDU (classes ``bhpy.LVConnectQC008`` and ``bhpy.LVConnectBDU``).
- Hardware wrappers: Scan BH devices and configure/acquire with QC-04/08 and PMS-800 DLLs (``bhpy.BHDeviceScan``, ``bhpy.SpcQcX04``/``SpcQcX08``/``Pms800`` and configs).

Quickstart
----------
Install from PyPI (device drivers/apps must be present on your system):

.. code-block:: console

   pip install bhpy

Basic usage examples are in :doc:`usage/spcconnect`, :doc:`usage/labview`, and :doc:`usage/hardware`.

Contents
--------
.. toctree::
   :maxdepth: 2

   usage/spcconnect
   usage/labview
   usage/hardware
   api/index

Indices and tables
------------------
* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

