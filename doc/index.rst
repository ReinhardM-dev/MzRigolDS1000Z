.. _RIGOL MSO1000Z/DS1000Z: https://www.rigol.eu/products/oscillosopes/ds1000zds1000z.html
.. _pyvisa: https://pypi.org/project/PyVISA/
.. _VISA: https://en.wikipedia.org/wiki/Virtual_instrument_software_architecture

RigolDS1000Z
===========================
A package which allows to realize the remote control of `RIGOL MSO1000Z/DS1000Z`_
series digital oscilloscopes through the USB or the LAN bus.

The package
 * queries parameters by group, so that all parameters belonging to a group a queried at once
 * implements all relevant groups
 * sets many parameters in one step
 * allows for all types of :WAVeform:DATA? and :DISPlay:DATA? requests
 * has running discover modes for both USB and LAN buses

The software has been developed by using a DS1054Z, Software version: 00.04.05.SP2.
 
Installing
----------

The package is a pure python package.
To work the package requires `pyvisa`_ , a package
implementing the “Virtual Instrument Software Architecture” (`VISA`_)

Download the package using
::

    pip install RigolDS1000Z
    
    
Contents
-----------

.. toctree::
  :maxdepth: 3

  driver
  base
  ds1000

Indices and tables
-----------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

