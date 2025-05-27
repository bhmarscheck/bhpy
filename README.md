# bhpy

Python API for Becker&Hickl software products, data acquisition and data handling

To install this module on your system, you can use pip: 

    pip install bhpy

or

    python3 -m pip install bhpy

To access bhpy and its components import it into your Python code like this:

    import bhpy as bh

## SPCConnect

[SPCConnect](https://www.becker-hickl.com/products/spcconnect) is a command based TCP interface for [SPCM](https://www.becker-hickl.com/products/spcm-data-acquisition-software) that allows programmatic access to SPCM's user interface. It can be used to automate measurements, create measurement feedback loops, integrate SPCM's functionality into your software or add other functionality to SPCM. Many parameters can be accessed through the interface directly, others can be set through predefined setups and will be added over time (requests can be submitted via the [bug tracker](https://github.com/bhmarscheck/bhpy/issues)). SPCConnect can also facilitate automated data analysis through SPCM as well as GPU accelerated fluorescence decay analysis with [SPCImage](https://www.becker-hickl.com/products/spcimage) by fitting the data with single-, double- and triple exponential decay models.

## BH LabView Connect

Remote control interface for Becker&Hickl's LabView software products. Command based interface that allows programmatic access to their user interfaces, similar to SPCConnect. Currently supported LabView applications (requests can be submitted via the [bug tracker](https://github.com/bhmarscheck/bhpy/issues)):
- [BH-QC008](https://www.becker-hickl.com/products/bh-qc008/)
- [BDU](https://www.becker-hickl.com/products/bdu-sm-series)

## BH Hardware

Python wrapper for Becker&Hickl hardware control.

### BH Device Scan

BH device scanning dll wrapper that provides Python bindings to scan the system for all present Becker&Hickl devices, their serial number and firmware version.

### Hardware Dll

Dll wrapper for hardware configuration and data acquisition compatible with:
- [SPC-QC-104](https://www.becker-hickl.com/products/spc-qc-104)/[004](https://www.becker-hickl.com/products/spc-qc-004)
- [SPC-QC-108](https://www.becker-hickl.com/products/spc-qc-108-tcspc-module)/[008](https://www.becker-hickl.com/products/spc-qc-008-tcspc-module)
- [PMS-800](https://www.becker-hickl.com/products/pms-800)
