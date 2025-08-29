SPCConnect (SPCM Remote Control)
================================

``BHConnect`` lets you discover and connect to a running SPCM instance that exposes the SPCConnect TCP interface, send commands, and fetch images/traces.

Discovery and Connection
------------------------
.. code-block:: python

   import bhpy as bh

   conn = bh.BHConnect()
   # Option A: mDNS discovery (default instance id=1)
   conn.connect_spcm_instance()
   # Option B: explicit host/port
   # conn.connect_spcm_instance(host="myspcm-host", port=12345)

   print(conn.command("Version:number"))  # e.g. "OK: 2.0.1"

Commands
--------
Commands follow the SPCConnect protocol. ``command()`` returns the payload string (without the leading ``OK:``) or raises on errors.

.. code-block:: python

   # Navigate SPCM UI and set parameters
   conn.command("pressmenu:systemparameter")
   conn.command("setparameter:pixelx,256")
   conn.command("setparameter:pixely,256")

Fetch Images and Traces
-----------------------
Images are streamed over a temporary TCP server created by ``BHConnect`` and are saved to the user BH data directory. Returned values are absolute file paths.

.. code-block:: python

   # First-moment image of current window/cycle
   paths = conn.get_image(window=1, cycle=1, image_type="1stMoment")
   print(paths)  # [".../BH/bhpy/SPCConnect/temp/... .tiff"]

   # Fitted image (requires SPCImage fit config)
   paths = conn.get_image(window=1, image_type="Fit", fit_config=("SingleExp", 1))

   # Decay trace (image decay of trace #1)
   trace = conn.get_trace(trace_number=1)
   print(len(trace), "samples")

Cleanup
-------
.. code-block:: python

   conn.disconnect_spcm_instance()
   # or shutdown the remote SPCM (if allowed)
   # conn.shutdown_spcm_instance()

Notes
-----
- Ensure SPCM is running with SPCConnect enabled, and reachable on the network.
- ``BHConnect`` negotiates a secure session (RSA/AES) and validates the SPCConnect protocol version (2.x).
- Saved files are placed under the user app data directory: ``.../BH/bhpy/SPCConnect``.

