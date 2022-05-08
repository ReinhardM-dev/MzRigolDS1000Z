from typing import Optional, List, Dict, Tuple, Any
import re, string, time

import pyvisa
import driver

class DigitalOscilloscopeBase(driver.Instrument):
 """Base class of Rigol digital oscilloscopes of the types DSnnnn and MSOnnnn providing:
 
:param resourceName: USB or GPIB INSTR resource
:param openTimeout_msec: Time delay on opening
:param resourceManager: VISA Resource Manager (DEF: use ``DigitalOscilloscopeBase.resourceManager``)
 
.. csv-table:: DigitalOscilloscopeBase implementation
 :header: "Item", "Description"
 :widths: 30, 70
   
 *:ACQuire*, Parameters of the digital electronics
 *:CHANnel*, Vertical axis parameters of the analog channels
 *:DISPlay*, Display parameters and data
 *:TIMebase*, Parameters to handle the horizontal timebase mode
 *:TRIGger*, Parameters to handle the trigger system 
 *:WAVeform*, Parameters to handle waveform settings and data
 
.. note::
 The software has been developed by using a DS1054Z, Software: 00.04.05.SP2.
 Several product properties are not available through the remote interface and were derived from model name:
  
 * pointsPerTimeDivision
 * bandwidth_MHz
 * numberOfDecoders
 * numberOfDigitalChannels
 
.. note::

  According to Rigol's documentation, these methods run on all series DS1000Z/MSO1000Z oscilloscopes.
  Although not tested, they are expected to run on following series: 
  
  * DS2000A/MSO2000A
  * MSO5000
  * DS7000/MSO7000
  * DS70000
  
  The compatibility can be tested at best by using the test environment found on `RigolDS1000Z`_
  
.. _RigolDS1000Z: https://github.com/ReinhardM-dev/RigolDS1000Z
  """
 resourceManager = pyvisa.ResourceManager()
 def __init__(self, resourceName : str, openTimeout_msec : int = 0,  
                           resourceManager : Optional[pyvisa.ResourceManager] = None, 
                           parent = None) -> None:
  super(DigitalOscilloscopeBase, self).__init__(resourceName, openTimeout_msec, resourceManager)
  self.chunk_size = 250000 # ensure that a RIGOL :WAV:DATA? chunk is read in 1 step
  modelMatch = re.fullmatch('(DS[1-9]|MSO[1-9])([0-9][0-9])([1-9])([^1-9]+)', self._idnDict['model'], flags = re.I)
  assert modelMatch is not None
  matchGroups = modelMatch.groups()
  self._idnDict['series'] = '{}000{}'.format(matchGroups[0].upper(), matchGroups[3].upper())
  self._idnDict['bandwidth_MHz'] = 10*int(matchGroups[1])
  if self._idnDict['series'].upper().endswith('PLUS') or self._idnDict['series'].upper().startswith('MSO'):
   self._idnDict['digitalChannels'] = 16
  else:
   self._idnDict['digitalChannels'] = 0
  if re.match('(DS|MSO)1', self._idnDict['series']) is not None:
   self._idnDict['decoders'] = 2
  else:
   self._idnDict['decoders'] = 0
  self._idnDict['channels'] = int(self.query(':SYST:RAM?'))
  self._idnDict['numberOfTimeDivisions'] = int(self.query(':SYST:GAM?'))
  wfSettings = self.getWAVSettings()
  self._idnDict['pointsPerTimeDivision'] = wfSettings[':WAV:POINts?']//self._idnDict['numberOfTimeDivisions']

 @property
 def numberOfAnalogChannels(self) -> int:
  ":returns: Number of channels"
  return self._idnDict['channels']
  
 @property
 def numberOfDigitalChannels(self) -> int:
  ":returns: Number of digital channels"
  return self._idnDict['digitalChannels']
  
 @property
 def numberOfReferenceChannels(self) -> int:
  ":returns: Number of reference channels"
  return 10

 @property
 def numberOfDecoders(self) -> int:
  ":returns: Number of decoder units"
  return self._idnDict['decoders']

 @property
 def numberOfTimeDivisions(self) -> int:
  ":returns: Number of time divisions on screen"
  return self._idnDict['numberOfTimeDivisions']

 @property
 def pointsPerTimeDivision(self) -> int:
  ":returns: points per time division"
  return self._idnDict['pointsPerTimeDivision']

 @property
 def bandwidth_MHz(self) -> int:
  ":returns: Bandwidth in MHz"
  return self._idnDict['bandwidth_MHz']
  
 @property
 def minRiseTime_nsec(self) -> int:
  ":returns: Minimum rise time that can be resolved"
  return 350.0/self._idnDict['bandwidth_MHz']
  
 @property
 def triggerStatus(self) -> str:
  ":returns: Trigger status (TD|WAIT|RUN|AUTO|STOP)"
  return self.query(':TRIG:STAT?')

 def setAutoscale(self) -> None:
  "Equivalent to pressing the AUTO key at the front panel"
  self.write(':AUT')

 def setClEar(self) -> None:
  "Clear all the waveforms on the screen"
  self.write(':CLE')

 def setRUN(self) -> None:
  "Moves the oscilloscope into RUN mode"
  self.write(':RUN')
  time.sleep(0.1)

 def setSTOP(self) -> None:
  """Moves the oscilloscope into STOP mode

.. note::
 The :ACQuire:MDEPth command is not available in STOP mode
  """
  self.write(':STOP')
  time.sleep(0.1)

 def setSINGle(self) -> None:
  "Moves the oscilloscope into :TRIGger:SWEep:SINGle mode"
  self.write(':SING')
  time.sleep(0.1)

 def setTFORce(self) -> None:
  "Forces triggering of the oscilloscope"
  self.write(':TFOR')
  time.sleep(0.1)
  
 def setSettings(self, settingsDict : Dict[str, Any]) -> None:
  """Uses any dictionary created by a getXXXSettings or any part or combinations of them
to set variables on a Rigol oscilloscope. The keys of the dictionary are only written, if

 * the key begins with a colon (:)
 * does not end with a question mark (?)
  
  :param settingsDict: dictionary dictionary
  """
  for _key, value in settingsDict.items():
   if _key.startswith(':') and not _key.endswith('?') and value is not None:
    key = ''
    for c in _key:
     if c not in string.ascii_lowercase:
      key += c
    if isinstance(value, bool):
     value = int(value)
    if isinstance(value, float):
     value = '{:e}'.format(value)
    command = '{} {}'.format(key, value)
    self.write(command)
   
 def getACQSettings(self) -> Dict[str, Any]:
  """The acquire settings describe the features of the digital electronics.
For the :ACQuire command, it returns the following settings:

.. csv-table:: ACQ Settings
 :header: "Key", "Range", "Description"
 :widths: 30, 30, 50
   
 *:ACQuire:AVERages*, int, Number of averages (2 ... 1024)
 *:ACQuire:MDEPth*, AUTO|int, Memory depth (dep: number of enabled channels)
 *:ACQuire:SRATe?*, float, Sample rate in Hz
 *:ACQuire:TYPE*, NORM|AVER|PEAK|HRES, Acquisition mode
 *MDEPthPerTimeDivision?*, int, :ACQuire:MDEPth in one Timebase unit (div)
 
All parameters ending with a ? are readonly, the others are RW.

:returns: Dict[key, value]
  """
  acqSettingsDict = dict()
  acqSettingsDict[':ACQuire:AVERages'] = int(self.query(':ACQ:AVER?'))
  acqSettingsDict[':ACQuire:MDEPth'] = self.query(':ACQ:MDEP?')
  if acqSettingsDict[':ACQuire:MDEPth'] != 'AUTO':
   acqSettingsDict[':ACQuire:MDEPth'] = int(acqSettingsDict[':ACQuire:MDEPth'])
  acqSettingsDict[':ACQuire:SRATe?'] = float(self.query(':ACQ:SRAT?'))
  acqSettingsDict[':ACQuire:TYPE'] = self.query(':ACQ:TYPE?')
  acqSettingsDict['MDEPthPerTimeDivision?'] = int(acqSettingsDict[':ACQuire:SRATe?']  * float(self.query(':TIM:SCAL?')))
  if acqSettingsDict[':ACQuire:MDEPth'] == 'AUTO':
   points = (acqSettingsDict['MDEPthPerTimeDivision?']  * self.numberOfTimeDivisions) 
  else:
   points = acqSettingsDict[':ACQuire:MDEPth']
  acqSettingsDict['SamplingTime?'] =  points * acqSettingsDict[':ACQuire:SRATe?']
  return acqSettingsDict

 def getCHANSettings(self, n : int) -> Dict[str, Any]:
  """For the :CHANnel command, it returns the following settings:

.. csv-table:: CHAN Settings
 :header: "Key", "Range", "Description"
 :widths: 30, 30, 50
   
 *:CHAN<n>:BWLimit*, OFF|20M, Bandwidth limit
 *:CHAN<n>:COUPling*, AC|DC|GND, Coupling mode
 *:CHAN<n>:DISPlay*, 0|1, Channel status query
 *:CHAN<n>:INVert*, 0|1, Inverted display mode status query
 *:CHAN<n>:OFFSet*, float, vertical offset (in *Units*)
 *:CHAN<n>:RANGe*, float, vertical range (in *Units*)
 *:CHAN<n>:SCALe*, float, vertical scale (in *Units*)
 *:CHAN<n>:TCAL*, float, calibration time (in s)
 *:CHAN<n>:UNITs*, VOLT|WATT|AMP|UNKN, amplitude display unit
 *:CHAN<n>:VERNier*, 0|1, Fine adjustment of the vertical scale
 
All parameters are RW.

:param n: analog channel to be queried

:returns: Dict[key, value]
  """
  assert n in range(1, self.numberOfAnalogChannels+1)
  key = lambda _key, channel = n: ':CHAN{}:{}'.format(channel, _key)
  chSettingsDict = dict()
  chSettingsDict[key('BWLimit')] = self.query(key('BWL?'))
  chSettingsDict[key('COUPling')] = self.query(key('COUP?'))
  chSettingsDict[key('DISPlay')] = int(self.query(key('DISP?')))
  chSettingsDict[key('INVert')] = int(self.query(key('INV?')))
  chSettingsDict[key('OFFSet')] = float(self.query(key('OFFS?')))
  chSettingsDict[key('PROBe')] = float(self.query(key('PROB?')))
  try:
   chSettingsDict[key('RANGe')] = float(self.query(key('RANG?')))
  except:
   pass
  chSettingsDict[key('SCALe')] = float(self.query(key('SCAL?')))
  chSettingsDict[key('TCAL')] = float(self.query(key('TCAL?')))
  chSettingsDict[key('UNITs')] = self.query(key('UNIT?'))
  chSettingsDict[key('VERNier')] = int(self.query(key('VERN?')))
  return chSettingsDict

 def getDISPSettings(self) -> Dict[str, Any]:
  """For the :DISPlay command, it returns the following settings:

:returns: Dict[key, value]

.. csv-table:: DISP Settings
 :header: "Key", "Range", "Description"
 :widths: 30, 30, 50
   
 *:DISPlay:TYPE*, VECT|DOTS, Display style (line or dots)
 *:DISPlay:GRADing:TIME*, MIN|0.1|0.2|0.5|1|5|10|INFinite, Persistence time in seconds
 *:DISPlay:GRID*, FULL|HALF|NONE, Grid type 
 *:DISPlay:GBRightness*, 0 ... 100, Grid brightness in % 
 *:DISPlay:WBRightness*, 0 ... 100, Waveform brightness in % 
 
All parameters are RW.
  """
  dispSettingsDict = dict()
  dispSettingsDict[':DISPlay:TYPE'] = self.query(':DISP:TYPE?')
  dispSettingsDict[':DISPlay:GRADing:TIME'] = self.query(':DISP:GRAD:TIME?')
  dispSettingsDict[':DISPlay:GRID'] = self.query(':DISP:GRID?')
  dispSettingsDict[':DISPlay:GBRightness'] = int(self.query(':DISP:GBR?'))
  dispSettingsDict[':DISPlay:WBRightness'] = int(self.query(':DISP:WBR?'))
  return dispSettingsDict

 def getDISPData(self, color : bool = True, invert : bool = False, fmt : str = 'BMP') -> bytearray:
  """Returns :DISP:DATA? result, i.e. a screenshot of the oscilloscope.

:param color: return a colored screenshot 
:param invert: return a inverted screenshot 
:param fmt: format of the image data (BMP|PNG|TIFF), JPEG is buggy

:returns: binary data

.. code-block:: python3
 :caption: Display of a screenshot using the PIL package

  import io
  from RigolDS1000Z import DigitalOscilloscopeBase
  from PIL import Image

  dev = DigitalOscilloscopeBase(<resourceName>)
  fmt = 'BMP'
  fp = io.BytesIO(dev.getDISPData(fmt = fmt))
  img = Image.open(fp, mode = "r", formats = [fmt])
  img.show()
  """
  assert fmt in ['BMP', 'PNG', 'TIFF']
  toOnOff = lambda bv:  ['OFF', 'ON'][int(bv)]
  if fmt == 'BMP':
   if color:
    fmt = 'BMP24'
   else:
    fmt = 'BMP8'
  try:
   return bytearray(self.query_binary_values(':DISP:DATA? {},{},{}'.format(toOnOff(color), toOnOff(invert), fmt),  datatype = 'B'))
  except:
   return bytearray(self.query_binary_values(':DISP:DATA?',  datatype = 'B'))

 def getTRIGSettings(self, mode : Optional[str] = None ) -> Dict[str, Any]:
  """For the :TRIGger command, it returns the following settings:

:param mode: trigger mode
:returns: Dict[key, value]

.. csv-table:: Global Trigger Parameter
 :header: "Key", "Range", "Description"
 :widths: 30, 30, 50
 
 *:TRIG:COUPling*, AC|DC|LFR|HFR, trigger coupling type
 *:TRIG:HOLDoff*, float, trigger holdoff time
 *:TRIG:MODE*, PATT|see below, Trigger type
 *:TRIG:NREJect*, 0|1, status of noise rejection
 *:TRIG:POSition?*, -2|-1|posint, waveform trigger position
 *:TRIG:STATus?*, TD|WAIT|RUN|AUTO|STOP, trigger status
 *:TRIG:SWEep*, AUTO|NORM|SING, trigger sweep mode

.. csv-table:: Trigger Modes
 :header: "Key", "Opt", "Description"
 :widths: 30, 10, 50
   
 *:TRIG:DEL*, X, Delay between edges of 2 signals trigger
 *:TRIG:DUR*,, Pulse train duration trigger
 *:TRIG:EDGE*,, Edge trigger
 *:TRIG:IIC*, X, I2C bus trigger
 *:TRIG:NEDG*, X, Nth edge trigger after an idle time
 *:TRIG:PULS*,, Pulse width trigger
 *:TRIG:RS232*, X, RS232 bus trigger
 *:TRIG:RUNT*, X, Runt pulse trigger
 *:TRIG:SHOL*, X, Setup/hold time trigger
 *:TRIG:SLOP*,, Edge slope trigger
 *:TRIG:SPI*, X, SPI bus trigger
 *:TRIG:TIM*, X, Minimum pulse width (timeout) trigger
 *:TRIG:VID*,, Video trigger
 *:TRIG:WIND*, X, Covered window trigger

.. csv-table:: Trigger Mode Parameters
 :header: "Key", "Range", "Description"
 :widths: 30, 30,50

 *:TRIG:<m>:ADDRess*, int, address in I2C trigger
 *:TRIG:<m>:AWIDth*, 7|8|10, address bits for *ADDRess*
 *:TRIG:<m>:BAUD|BUSer*, str, Baud rate in RS232 trigger
 *:TRIG:<m>:CHAN<n>*, D<n>, AC
 *:TRIG:<m>:DIRection*, READ|WRIT|RWR, Direction in I2C trigger
 *:TRIG:<m>:EDGE*, int, Number of edges in Nth edge trigger
 *:TRIG:<m>:[HS]TIMe*, float, Hold/Setup time in SHOLd trigger
 *:TRIG:<m>:IDLE*, float, idle time
 *:TRIG:<m>:[ABCDS]?LEVel*, float, trigger level
 *:TRIG:<m>:LINE*, int, line number in video trigger
 *:TRIG:<m>:MODE*, POS|NEG, Polarity in video trigger
 *:TRIG:<m>:PARity*, EVEN|ODD|NONE, Parity setting in RS232 trigger
 *:TRIG:<m>:PATTern*, H| L, Pattern in SHOLd trigger
 *:TRIG:<m>:POLarity*, ODD|EVEN|LINE|ALIN|POS|NEG, Polarity in video trigger
 *:TRIG:<m>:S[AB]*, CHAN<n>, Source channel
 *:TRIG:<m>:SCL*, CHAN<n>|D<n>, SCL in I2C trigger
 *:TRIG:<m>:SDA*, CHAN<n>|D<n>, SDA in I2C trigger
 *:TRIG:<m>:SLOP[eAB]*, POS|NEG|RFAL, Edge type
 *:TRIG:<m>:SOURce*, CHAN<n>|D<n>|AC, Trigger source
 *:TRIG:<m>:STANdard*, PALS|NTSC|480P|576P, video standard
 *:TRIG:<m>:STOP*, 1|2, number of stop bits in RS232 trigger
 *:TRIG:<m>:TIME*, float, Time in SLOPe trigger (see *WHEN*)
 *:TRIG:<m>:TIMeout*, float, Timeout time
 *:TRIG:<m>:TLOWer*, float, Lower limit of time delay
 *:TRIG:<m>:TUPPer*, float, Lower limit of time delay
 *:TRIG:<m>:TYPe*, str, Context dependent (see DELay|DURATion|SHold)
 *:TRIG:<m>:WHEN*, str, Context dependent (see DURATion|IIC| PULSe|RS232|SLOPe|SPI)
 *:TRIG:<m>:[LU]?WIDTh*, float, Pulse width
 *:TRIG:<m>:WINDow*, TA|TB|TAB, vertical window type
 *:TRIG:<m>:WLOWer*, float, Lower limit of pulse with
 *:TRIG:<m>:WUPPer*, float, Upper limit of pulse with

All parameters ending with a ? as well as those of the trigger modes are readonly, the others are RW.
  """
  key = lambda _key, mode = mode: ':TRIG:{}:{}'.format(mode, _key)
  allModes = ['EDGE', 'PULS', 'SLOP', 'VID', 'DURAT', 'TIM', 'RUNT', 'WIND', 'DEL', 'SHOL',  'NEDG', 'RS232', 'IIC', 'SPI']
  triggerDict = dict()
  if mode is None:
   mode = self.query(':TRIG:MODE?')
  else: 
   mode = mode.upper()
   assert mode in allModes, '{}.getTriggerSettings: Mode {} not installed.'.format(self.__class__.__name__, mode)
  triggerDict[':TRIG:COUPling?'] = self.query(':TRIG:COUP?')
  triggerDict[':TRIG:HOLDoff?'] = float(self.query(':TRIG:HOLD?'))
  triggerDict[':TRIG:MODE?'] = mode
  triggerDict[':TRIG:NREJect?'] = int(self.query(':TRIG:NREJ?'))
  try:
   triggerDict[':TRIG:POSition?'] = int(self.query(':TRIG:POS?'))
  except:
   pass
  triggerDict[':TRIG:STATus?'] = self.query(':TRIG:STAT?')
  triggerDict['SWEep'] = self.query(':TRIG:SWE?')
  try:
   if mode in ['EDGE', 'PULS', 'SLOP', 'VID', 'DURAT', 'TIM', 'RUNT', 'WIND', 'NEDG', 'RS232']:
    triggerDict[key('SOURce')] =  self.query(key('SOUR?'))
   if mode in ['EDGE', 'TIM', 'WIND', 'SHOL', 'NEDG']:
    triggerDict[key('SLOPe?')] =  self.query(key('SLOP?'))
   if mode in ['EDGE', 'PULS', 'VID', 'NEDG', 'RS232']:
    triggerDict[key('LEVel?')] =  float(self.query(key('LEV?')))
   if mode in  ['PULS', 'SLOP', 'DURAT', 'RUNT', 'RS232', 'IIC', 'SPI']:
    triggerDict[key('WHEN?')] =  self.query(key('WHEN?'))
   if mode in  ['PULS', 'RS232', 'SPI']:
    triggerDict[key('WIDTh?')] =  float(self.query(key('WIDT?')))
   if mode in  ['PULS']:
    triggerDict[key('UWIDth?')] =  float(self.query(key('UWID?')))
    triggerDict[key('LWIDth?')] =  float(self.query(key('LWID?')))
   if mode in  ['SLOP', 'TIM', 'WIND']:
    triggerDict[key('TIME?')] =  float(self.query(key('TIME?')))
   if mode in  ['SLOP', 'DURAT', 'DEL']:
    triggerDict[key('TUPPer?')] =  float(self.query(key('TUPP?')))
    triggerDict[key('TLOWer?')] =  float(self.query(key('TLOW?')))
   if mode in  ['SLOP']:
    triggerDict[key('WINDow?')] =  self.query(key('WIND?'))
   if mode in  ['SLOP', 'RUNT', 'WIND']:
    triggerDict[key('ALEVel?')] =  float(self.query(key('ALEV?')))
    triggerDict[key('BLEVel?')] =  float(self.query(key('BLEV?')))
   if mode in  ['VID', 'RUNT']:
    triggerDict[key('POLarity?')] =  self.query(key('POL?'))
   if mode in  ['VID', 'SPI']:
    triggerDict[key('MODE?')] =  self.query(key('MODE?'))
   if mode in  ['VID']:
    triggerDict[key('LINE?')] =  int(self.query(key('LINE?')))
    triggerDict[key('STANdard?')] =  self.query(key('STAN?'))
   if mode in  ['SHOL']:
    triggerDict[key('PATTern?')] =  self.query(key('PATT?'))
   if mode in  ['DURAT', 'DEL', 'SHOL']:
    triggerDict[key('TYPe?')] =  self.query(key('TYP?'))
   if mode in  ['RUNT']:
    triggerDict[key('WUPPer?')] =  float(self.query(key('WUPP?')))
    triggerDict[key('WLOWer?')] =  float(self.query(key('WLOW?')))
   if mode in  ['WIND']:
    triggerDict[key('POSition?')] =  self.query(key('POS?'))
   if mode in  ['DEL']:
    triggerDict[key('SA?')] =  self.query(key('SA?'))
    triggerDict[key('SLOPA?')] =  self.query(key('SLOPA?'))
    triggerDict[key('SB?')] =  self.query(key('SB?'))
    triggerDict[key('SLOPB?')] =  self.query(key('SLOPB?'))
   if mode in  ['SHOL']:
    triggerDict[key('CSrc?')] =  self.query(key('CS?'))
    triggerDict[key('DSrc?')] =  self.query(key('CS?'))
    triggerDict[key('STIMe?')] =  float(self.query(key('STIM?')))
    triggerDict[key('HTIMe?')] =  float(self.query(key('HTIM?')))
   if mode in  ['NEDG']:
    triggerDict[key('IDLE?')] =  float(self.query(key('IDLE?')))
    triggerDict[key('EDGE?')] =  int(self.query(key('EDGE?')))
   if mode in  ['RS232', 'IIC', 'SPI']:
    triggerDict[key('DATA?')] =  self.query(key('DATA?'))
   if mode in  ['RS232']:
    triggerDict[key('PARity?')] =  self.query(key('PAR?'))
    triggerDict[key('STOP?')] =  self.query(key('STOP?'))
    triggerDict[key('BAUD?')] =  self.query(key('BAUD?'))
    triggerDict[key('BUSer?')] =  self.query(key('BUS?'))
   if mode in  ['IIC', 'SPI']:
    triggerDict[key('SCL?')] =  self.query(key('SCL?'))
    triggerDict[key('SDA?')] =  self.query(key('SDA?'))
    triggerDict[key('CLEVel?')] =  float(self.query(key('CLEV?')))
    triggerDict[key('DLEVel?')] =  float(self.query(key('DLEV?')))
   if mode in  ['IIC']:
    triggerDict[key('AWIDth?')] =  int(self.query(key('AWID?')))
    triggerDict[key('ADDRess?')] =  int(self.query(key('ADDR?')))
    triggerDict[key('DIRection?')] =  self.query(key('DIR?'))
   if mode in  ['SPI']:
    triggerDict[key('TIMeout?')] =  float(self.query(key('TIM?')))
    triggerDict[key('SLEVel?')] =  float(self.query(key('SLEV?')))
  except driver.RigolError:
   raise driver.RigolError('{}.getTriggerSettings: Mode {} not installed.'.format(self.__class__.__name__, mode))
  return triggerDict

 def getTIMSettings(self):
  """For the :TIMebase command, it returns the following settings:

.. csv-table:: TIM Settings
 :header: "Key", "Range", "Description"
 :widths: 30, 30, 50

  *:TIM:MODE*, MAIN|XY|ROLL, Mode of the horizontal axis
  *:TIM:DELay:ENABle*, 0|1, Status of the delayed sweep  
  *:TIM:DELay:OFFSet*, float, Delayed timebase offset (only for :TIM:DELay:ENABle mode) 
  *:TIM:OFFSet*, float, Timebase offset (not for XY and :TIM:DELay:ENABle mode)
  *:TIM:SCALe*, float, Timebase scale (not for XY and :TIM:DELay:ENABle mode)  
  *TIM:TL*, float, Time at the left edge of the screen (not for XY and :TIM:DELay:ENABle mode)  
  *TIM:TR*, float, Time at the right edge of the screen (not for XY and :TIM:DELay:ENABle mode)  
  
All parameters are RW.

:returns: Dict[key, value]
  """
  timSettingsDict = dict()
  timSettingsDict[':TIM:MODE'] = self.query(':TIM:MODE?')
  timSettingsDict[':TIM:DELay:ENABle'] = int(self.query(':TIM:DEL:ENAB?'))
  if timSettingsDict[':TIM:DELay:ENABle'] == 1:
   timSettingsDict[':TIM:DELay:OFFSet'] = float(self.query(':TIM:DEL:OFFS?'))
  else:
   timSettingsDict[':TIM:OFFSet'] = float(self.query(':TIM:OFFS?'))
   timSettingsDict[':TIM:SCALe'] = float(self.query(':TIM:SCAL?'))
   timSettingsDict['TIM:TL?'] = timSettingsDict[':TIM:OFFSet']
   timSettingsDict['TIM:TR?'] = timSettingsDict['TIM:TL?'] + timSettingsDict[':TIM:SCALe'] * self.numberOfTimeDivisions
  return timSettingsDict

 def getWAVSettings(self):
  """For the :WAVeform command, it returns the following settings:

.. csv-table:: WAV Settings
 :header: "Key", "Range", "Description"
 :widths: 30, 30, 50

  *:WAV:SOURce*,CHAN<n>|D<n>|MATH, Waveform source
  *:WAV:MODE*, NORMal|MAXimum|RAW, Waveform mode
  *:WAV:FORMat*, WORD|BYTE|ASCii, Waveform format
  *:WAV:STARt?*, int, First point of the waveform (starting from 1)
  *:WAV:STOP?*, int, Last point of the waveform (starting from 1)
  *:WAV:XINCrement?*, float, time difference between two neighboring points
  *:WAV:XORigin?*, float, time of origin (always 0)
  *:WAV:XREFerence?*, float, first point on the screen (always 0)
  *:WAV:YINCrement?*, float, waveform amplitude increment in amplitude units
  *:WAV:YORigin?*, int, waveform amplitude origin relative to YREFerence in YINCrement
  *:WAV:YREFerence?*, int, waveform amplitude reference in YINCrement
  *:WAV:PRE:Points?*, int, waveform amplitude reference in YINCrement
  
All parameters ending with a ? are readonly, the others are RW.

.. note:: 
 When the oscillosope is in :RUN status, all modes behave like :WAV:MODE == NORMal

:returns: Dict[key, value]
  """
  wfSettingsDict = dict()
  wfSettingsDict[':WAV:SOURce'] = self.query(':WAV:SOUR?')
  wfSettingsList = self.query(':WAV:PRE?').split(',')
  wfSettingsDict[':WAV:STARt?'] = int(self.query(':WAV:STAR?'))
  wfSettingsDict[':WAV:STOP?'] = int(self.query(':WAV:STOP?'))
  wfSettingsDict[':WAV:FORMat'] = ['BYTE', 'WORD', 'ASCii'][int(wfSettingsList[0])]
  wfSettingsDict[':WAV:MODE'] = ['NORMal', 'MAXimum', 'RAW'][int(wfSettingsList[1])]
  wfSettingsDict[':WAV:POINts?'] = int(wfSettingsList[2])
  wfSettingsDict[':WAV:XINcrement?'] = float(wfSettingsList[4])
  wfSettingsDict[':WAV:XORigin?'] = float(wfSettingsList[5])
  wfSettingsDict[':WAV:XREFerence?'] = float(wfSettingsList[6])
  wfSettingsDict[':WAV:YINcrement?'] = float(wfSettingsList[7])
  wfSettingsDict[':WAV:YORigin?'] = int(wfSettingsList[8])
  wfSettingsDict[':WAV:YREFerence?'] = int(wfSettingsList[9])
  return wfSettingsDict

 def getWAVData(self, SOURce : str, MODE : str = 'MAX', FORMat : str = 'BYTE', showHiddenData : bool = True) -> List[float]:
  """Return :WAV:DATA 

:param SOURce: Waveform source (CHAN<n>|D<n>|MATH)
:param MODE: Waveform mode (NORM|MAX|RAW)
:param FORMat: Waveform format (WORD|BYTE|ASC)
:param reScale: Rescale Y axis 
:param showHiddenData: Show also hidden data (if Oscilloscope is in :STOP state)

:returns: Dict[key, value]

.. code-block:: python3
 :caption: Display of a waveform using the matplotlib package

  from RigolDS1000Z import DigitalOscilloscopeBase
  import matplotlib.pyplot as plt

  dev = DigitalOscilloscopeBase(<resourceName>)
  chData = dev.getWAVData('CHAN1'.format(channel), showHiddenData = False)
  timSettings = dev.getTIMSettings()
  tData = numpy.linspace(timSettings['TIM:TL?'], timSettings['TIM:TR?'], num = len(chData))
  plt.plot(tData, chData)
  plt.show()
  """
  def setParam(cmd : str, value : str) -> None:
   try:
    self.write('{} {}'.format(cmd, value))
   except driver.RigolError:
    assert False, "Improper parameter {} = {}".format(cmd, value)
    
  def getDataBatch(wfFORMat : str, start : int, stop : int, offsetIncr : Optional[Tuple[int, float]] = None) -> List[float]:
   self.write(':WAV:STARt {}'.format(start))
   self.write(':WAV:STOP {}'.format(stop))
   if wfFORMat == 'BYTE':
    assert offsetIncr is not None
    offset, incr = offsetIncr
    wfData = self.query_binary_values(':WAV:DATA?', datatype = "B", container = list, delay_msec = 100, chunk_size = 20*1024)
    for n, value in enumerate(wfData):
     wfData[n] = (wfData[n] - offset)*incr
   else:
    wfData = self.query_ascii_values(':WAV:DATA?', converter = "f", container = list, delay_msec = 100)
   return wfData
   
  SOURce = SOURce.upper() 
  if SOURce == 'MATH':
   assert self.query(':MATH:DISP?') == '1', "SOURce == MATH not displayed"
   channel = -1
   srcType = 2
  else:
   match = re.fullmatch('D([1-9][0-9])', SOURce)
   if match is not None:
    channel = int(match.groups()[0])
    assert int(match.groups()[0]) <= self.numberOfDigitalChannels, "Improper parameter SOURCe = D{}".format(channel)
    srcType = 1
   else:
    match = re.fullmatch('CHAN([1-9])', SOURce)
    assert match is not None and int(match.groups()[0]) <= self.numberOfAnalogChannels, "Improper parameter SOURCe = {}".format(SOURce)
    channel = int(match.groups()[0])
    assert self.query(':CHAN{}:DISP?'.format(channel)) == '1', "SOURce == CHAN{} not displayed".format(channel)
    srcType = 0

  setParam(':WAV:SOUR', SOURce)
  MODE = MODE.upper()
  assert MODE in ['NORM', 'MAX', 'RAW'] and (srcType != 2 or MODE == 'NORM'), "Improper parameter MODE = {}".format(MODE)
  if self.triggerStatus == 'STOP':
   if MODE == 'MAX':
    MODE = 'RAW'
   else:
    assert MODE == 'RAW', "Improper parameter MODE = {} in :STOP state".format(MODE)
  else:
   if MODE == 'MAX':
    MODE = 'NORM'
   else:
    assert MODE == 'NORM', "Improper parameter MODE = {} in :RUN state".format(MODE)
  setParam(':WAV:MODE', MODE)
  if FORMat is not None:
   FORMat = FORMat.upper()
   assert FORMat in ['WORD', 'BYTE', 'ASC'] and (srcType != 1 or FORMat == 'BYTE'), "Improper parameter FORMat = {}".format(FORMat)
   setParam(':WAV:FORM', FORMat)

  acqSettings = self.getACQSettings()
  wfSettings = self.getWAVSettings()
  mDepth = wfSettings[':WAV:POINts?']
  assert mDepth > 0, "Too many sampling points {}".format(acqSettings[':ACQuire:MDEPth'])
  wfIncrement = wfSettings[':WAV:YINcrement?']
  wfOffset = wfSettings[':WAV:YREFerence?'] + wfSettings[':WAV:YORigin?']

  if wfSettings[':WAV:FORMat'] == 'WORD':
   wfFORMat = 'BYTE'
  else:
   wfFORMat = wfSettings[':WAV:FORMat']
  if wfFORMat == 'BYTE':
   maxPointsPerBatch = 250000
  else:
   maxPointsPerBatch = 15625

  if wfSettings[':WAV:MODE'] == 'NORM':
   mDepth = self.numberOfTimeDivisions * self.pointsPerTimeDivision
  
  start = 0
  end = mDepth
  if ( not showHiddenData) \
       and (MODE =='RAW') \
        and (acqSettings['MDEPthPerTimeDivision?'] * self.numberOfTimeDivisions < mDepth):
    start = (mDepth - acqSettings['MDEPthPerTimeDivision?'] * self.numberOfTimeDivisions) // 2
    end = mDepth - start
   
  wfData = list()
  while start + maxPointsPerBatch < end:
   wfData += getDataBatch(wfFORMat, start + 1, start + maxPointsPerBatch, (wfOffset, wfIncrement))
   start += maxPointsPerBatch

  if start + 1 < end:
   wfData += getDataBatch(wfFORMat, start + 1, end, (wfOffset, wfIncrement))

  self.write(':WAV:STARt 1')
  self.write(':WAV:STOP {}'.format(self.numberOfTimeDivisions * self.pointsPerTimeDivision))

  return wfData

 @staticmethod
 def getTimeUnitAndScale(tSpan : float) -> Tuple[float, str]:
  tUnit = 's'
  if tSpan < 1.E-6:
   tScale = 1.E9
   tUnit = 'ns'
  elif tSpan < 1.E-3:
   tScale = 1.E6
   tUnit = 'us'
  elif tSpan < 1:
   tScale = 1.E3
   tUnit = 'ms'
  else:
   tScale = 1 
  return (tScale, tUnit)
