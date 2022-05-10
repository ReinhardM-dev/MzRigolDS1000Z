from typing import Optional, List, Dict, Any
import re, string
import pyvisa

import base

class DS1000Z(base.DigitalOscilloscopeBase):
 """.. _RigolDS1000Z: https://github.com/ReinhardM-dev/RigolDS1000Z

Class of enhanced Rigol DS1000Z and MSO DS1000Z operations:

:param resourceName: USB or GPIB INSTR resource
:param openTimeout_msec: Time delay on opening
:param resourceManager: VISA Resource Manager (DEF: use ``DigitalOscilloscopeBase.resourceManager``)

.. csv-table:: DS1000Z implementation
 :header: "Item", "Description"
 :widths: 30, 70
   
 *:CURSor*, Measurements using horizontal and vertical cursors
 *:DECoder*, Analysis of buses (replaced by *:BUS* in modern devices)
 *:MASK*, Analysis by pass/fail Tests
 *:MATH*, Mathematical operations on waveforms
 *:MEASure*, Automatic measurement of waveform parameters
 *:REFerence*, Use of reference waveforms for comparison
 
.. note::

  According to Rigol's documentation, these methods run on all series DS1000Z/MSO1000Z oscilloscopes.
  The commands are partly available with a modified syntax in the following series: 
  
  * DS2000A/MSO2000A
  * MSO5000
  * DS7000/MSO7000
  * DS70000
  
  For example, the :DECoder group has be replaced by the :BUS group. 
  The compatibility can be tested at best by using the test environment found on `RigolDS1000Z`_
  """
 resourceManager = pyvisa.ResourceManager()
 def __init__(self, resourceName : str, openTimeout_msec : int = 0,  
                            resourceManager : Optional[pyvisa.ResourceManager] = None, 
                            parent = None) -> None:
  super(DS1000Z, self).__init__(resourceName, openTimeout_msec, resourceManager)

 def getMEASItem1Source(self, source : str, items : Optional[List[str]] = None, clearOnDevice : bool = False) -> Dict[str, Optional[float]]:
  """Perform measurements using the :MEAS:ITEM command with 1 source

:param source: source channel (CHAN<n>|D<n>|MATH)
:param items: list of items (see below) to be queried
:param clearOnDevice: clear values on the device
:returns: Dict[key, value]

.. note::
 Digital source can only D<n> limited to items marked in column "D" of the table

.. csv-table:: MEAS:ITEM items
 :header: "Key", "D", "Description"
 :widths: 30, 10, 70
   
 *FREQuency*,	Y, 1/PERiod
 *FTIMe*,,	Time span between upper and lower threshold (falling edge)	
 *MARea*,,	Integral over the waveform on the screen difference from middle point 
 *MPARea*,	MArea over the 1. period
 *NDUTy*,	Y, NWIDth / PERiod
 *NEDGes*,, Number of falling edges (from above upper threshold to below lower threshold)
 *NPULses*,, Number of negative pulses of the waveform (voltage below lower threshold)	
 *NSLEWrate*,,	(VLOWer - VUPper) / FTIMe
 *NWIDth*,	Y,	Time span between the middle points of a falling or a rising edge (negative width)
 *OVERshoot*,, VMAX - VTOP	
 *PDUTy*,	Y, PWIDth / PERiod
 *PEDGes*,, Number of rising edges (from below lower threshold to above upper threshold)	
 *PERiod*,	Y, PWIDth + NWIDth
 *PPULses*,, Number of positive pulses of the waveform (voltage above upper threshold)		
 *PREShoot*,, VBASe - VMIN
 *PSLEWrate*,,	(VUPper - VLOWer) / RTIMe
 *PVRMS*,, Root mean square voltage over the 1. period SUM_i(V(i)^2)/points 
 *PWIDth*,	Y,	Time span between the middle points of a rising or a falling edge (positive width)
 *RTIMe*,,	Time span between lower and upper threshold (rising edge)
 *TVMAX*,, Time corresponding to VMAX
 *TVMIN*,, Time corresponding to VMIN	
 *VAMP*,, VTOP - VBASe
 *VARIance*,, Voltage variance over the whole waveform SUM_i((VAMP(i) - VAVG)^2)/periods
 *VAVG*,, Average voltage over the whole waveform
 *VBASe*,, Voltage value from the flat base of the waveform
 *VLOWer*,, Lower threshold voltage	
 *VMAX*,, Maximum voltage 
 *VMID*,, Middle point voltage (VTOP + VBASe)/2	
 *VMIN*,, Minimum voltage 
 *VPP*,, VMAX -VMIN	
 *VRMS*,, PVRMS over the full waveform
 *VTOP*,, Voltage value from the flat top of the waveform	
 *VUPper*,, Upper threshold voltage
  """
  digitalItems = ['FREQuency', 'NDUTy', 'NWIDth', 'PDUTy', 'PERiod', 'PWIDth']
  noDigitalItems = ['VMAX','VMIN','VPP','VTOP','VBASe','VAMP','VAVG',' VRMS',
                          'OVERshoot','PREShoot','MARea','MPARea', 'RTIMe', 'FTIMe', 
                          'TVMAX', 'TVMIN', 'PSLEWrate', 'NSLEWrate', 'VUPper', 'VMID', 'VLOWer', 
                          'VARIance', 'PVRMS', 'PPULses', 'NPULses', 'PEDGes', 'NEDGes'] 
  allItems = digitalItems + noDigitalItems
  if items is not None:
   for item in items:
    assert item in allItems, 'Illegal item {}'.format(item)
  match = re.fullmatch('D([1-9][0-9])', source)
  if match is not None:
   n = int(match.groups()[0])
   assert n <= self.numberOfDigitalChannels, "Non existing digital channel {}".format(source)
   if items is not None:
    for item in items:
     assert item in digitalItems, 'Illegal item {} for digtal channels'.format(item)
   else:
    items = digitalItems
  else: 
   match = re.fullmatch('CHAN([1-9])', source)
   if match is not None:
    n = int(match.groups()[0])
    assert n <= self.numberOfAnalogChannels, "Non existing analog channel {}".format(source)
   elif source != 'MATH':
    assert False, "Illegal source string {}".format(source) 
   if items is None:
    items = allItems

  measDict = dict()
  for item in items:
   sValue = self.query(':MEAS:ITEM? {},{}'.format(item.rstrip(string.ascii_lowercase), source))
   if len(sValue) == 0 or sValue == 'measure error!':
    sValue = 9.9e37
   try: 
    value = float(sValue)
   except:
    value = 9.9e37
   if value > 1e37:
    measDict[item] = None
   else:
    measDict[item] = value
  
  if clearOnDevice or len(items) > 5:
   try:    
    self.write(':MEAS:CLE ALL')
   except:
    pass
 
  return measDict
  
 def getMEASItem2Source(self, source1 : str, source2 : str, items : Optional[List[str]] = None, clearOnDevice : bool = False) -> Dict[str, Optional[float]]:
  """Perform measurements using the :MEAS:ITEM command with 2 sources

:param source1: source channel (CHAN<n>|D<n>|MATH)
:param source2: source channel (CHAN<n>|D<n>|MATH)
:param items: list of items (see below) to be queried
:param clearOnDevice: clear values on the device
:returns: Dict[key, value]

.. csv-table:: MEAS:ITEM items
 :header: "Key", "Description"
 :widths: 30, 70
   
 *RDELay*,	Time difference between rising edges
 *FDELay*,	Time difference between falling edges
 *RPHase*,	Phase difference between rising edges
 *FPHase*,	Phase difference between falling edges
  """
  allItems = ['RDELay', 'FDELay', 'RPHase', 'FPHase']
  if items is not None:
   for item in items:
    assert item in allItems, 'Illegal item {}'.format(item)
  else:
   items = allItems
  for source in [source1, source2]:
   match = re.fullmatch('D([1-9][0-9])', source)
   if match is not None:
    n = int(match.groups()[0])
    assert n <= self.numberOfDigitalChannels, "Non existing digital channel {}".format(source)
   else: 
    match = re.fullmatch('CHAN([1-9])', source)
    if match is not None:
     n = int(match.groups()[0])
     assert n <= self.numberOfAnalogChannels, "Non existing analog channel {}".format(source)
    elif source != 'MATH':
     assert False, "Illegal source string {}".format(source) 

  measDict = dict()
  for item in items:
   sValue = self.query(':MEAS:ITEM? {},{},{}'.format(item.rstrip(string.ascii_lowercase), source1, source2))
   if len(sValue) == 0 or sValue == 'measure error!':
    sValue = 9.9e37
   try: 
    value = float(sValue)
   except:
    value = 9.9e37
   if value > 1e37:
    measDict[item] = None
   else:
    measDict[item] = value
  
  if clearOnDevice or len(items) > 5:    
   try:    
    self.write(':MEAS:CLE ALL')
   except:
    pass
 
  return measDict

 def getMEASThresholdSettings(self) -> Dict[str, float]:
  """Perform measurements using the :MEAS:SET: command with 1 source

.. csv-table:: MEAS:ITEM items
 :header: "Key", "Description"
 :widths: 30, 70
   
 *:MEASure:SETup:MAX*,	Relative upper threshold VMAX = VBAse + th * VAMP
 *:MEASure:SETup:MID*,	Mid point VMID = VBAse + tm * VAMP
 *:MEASure:SETup:MIN*,	Relative lower threshold VMIN = VBAse + th * VAMP

:returns: Dict[key, value]
  """
  measThDict = dict()
  measThDict[':MEASure:SETup:MAX'] = self.query(':MEAS:SET:MAX?')
  measThDict[':MEASure:SETup:MID'] = self.query(':MEAS:SET:MID?')
  measThDict[':MEASure:SETup:MIN'] = self.query(':MEAS:SET:MIN?')

  return measThDict

 def getCURSSettings(self) -> Dict[str, Any]:
  """For the :CURSor command, it returns the following settings:

:returns: Dict[key, value]

.. csv-table:: CURSor Modes
 :header: "Key", "Description"
 :widths: 30, 10, 50
   
 *:CURS:MAN*, Manually defined cursor
 *:CURS:TRAC*, Tracking cursor defined x-value with tracking y-value
 *:CURS:AUTO*, Automatic cursor defined by a :MEAS:ITEM
 *:CURS:XY*, XY cursor, available only :TIMebase:MODE == XY mode
 *:CURS:OFF*, No cursor enabled

.. csv-table:: Trigger Mode Parameters
 :header: "Key", "Type", "Description"
 :widths: 30, 30,50

 *:CURS:<m>:AX*, int, Horizontal position of cursor A on screen (RO for AUTO mode)
 *:CURS:<m>:BX*, int, Horizontal position of cursor B on screen (RO for AUTO mode)
 *:CURS:<m>:AY*, int, Vertical position of cursor A on screen (RO for TRAC and AUTO modes)
 *:CURS:<m>:BY*, int, Vertical position of cursor B on screen (RO for TRAC and AUTO modes)
 *:CURS:<m>:AXValue?*, float, Value at AX
 *:CURS:<m>:BXValue?*, float, Value at BX
 *:CURS:<m>:AYValue?*, float, Value at AY
 *:CURS:<m>:AYValue?*, float, Value at BY
 *:CURS:<m>:XDelta*, float, AXValue - BXValue
 *:CURS:<m>:YDelta*, float, AYValue - BYValue
 *:CURS:<m>:IXDelta*, float, 1/(AXValue - BXValue)
 *:CURS:MAN:SOURce*, str, Source Channel (OFF|CHAN1|CHAN2|CHAN3|CHAN4|MATH)
 *:CURS:MAN:TYPE[12]*, str, Type of cursor (x|y)
 *:CURS:MAN:TUnit*, str, Unit of x-values (S|HZ|DEGRee|PERCent)
 *:CURS:MAN:VUnit*, str, Unit of y-values (DEGRee|PERCent)
 *:CURS:MAN:VUnit*, str, Unit of y-values (DEGRee|PERCent)
 *:CURS:TRAC:SOURce[12]*, str, Source Channel (OFF|CHAN1|CHAN2|CHAN3|CHAN4|MATH)
 *:CURS:AUTO:ITEM*, str, Item defining the cursors (see :MEAS:ITEM)

All parameters ending with a ? are readonly, the others are RW.
  """
  mode = self.query(':CURS:MODE?')
  cursorDict = dict()
  cursorDict[':CURS:MODE'] = mode
  if mode == 'OFF':
   return cursorDict
  key = lambda _key, mode = mode: ':CURS:{}:{}'.format(mode, _key)
  # allModes = ['MAN', 'TRAC', 'AUTO', 'XY']
  for param in ['AX', 'BX', 'AY', 'BY']:
   qParam = '{}?'.format(param)
   if mode == 'AUTO' or (mode == 'TRAC' and param.endswith('Y')):
    cursorDict[key(qParam)] =  int(self.query(key(qParam)))
   else:
    cursorDict[key(param)] =  self.query(key(qParam))
  for param in ['AXValue', 'BXValue', 'AYValue', 'BYValue']:
   qParam = '{}?'.format(param)
   cursorDict[key(qParam)] =  float(self.query(key(qParam)))
  if mode in ['MAN', 'TRAC']:
   for param in ['XDELta', 'YDELta', 'IXDELta']:
    qParam = '{}?'.format(param)
    cursorDict[key(qParam)] = float(self.query(key(qParam)))
  if mode == 'MAN':
   for param in ['TYPE', 'SOURce', 'TUNit', 'VUNit']:
    qParam = '{}?'.format(param)
    cursorDict[key(param)] =  self.query(key(qParam))
  if mode == 'TRAC':
   for param in ['SOURce1', 'SOURce2']:
    qParam = '{}?'.format(param)
    cursorDict[key(param)] =  self.query(key(qParam))
  if mode == 'AUTO':
   cursorDict[key('ITEM')] =  self.query(key('ITEM?'))

  return cursorDict

 def getMATHSettings(self) -> Dict[str, Optional[Any]]:
  """For the :MATH command, it returns the following settings:

:returns: Dict[key, value]

.. csv-table:: :MATH items
 :header: "Key", "Range", "Description"
 :widths: 30, 30, 70
   
 *:MATH:SOURce[12]*,	CHAN<n>|FX, Source for algebraic operation/functional operation
 *:MATH:LSOURce[12]*,	CHAN<n>|D<n>, Source for logic operation
 *:MATH:OPTion:FX:SOURce[12]*,	CHAN<n>, Source for inner layer algebraic operation
 *:MATH:FFT:SOURce*,	CHAN<n>, Source for Fast Fourier Transform
 *:MATH:DISPlay*,	0|1, Math operation display status
 *:MATH:OPERator*,	str, Algebraic or functional operator
 *:MATH:OPTion:FX:OPERator*,	str, Algebraic operator for inner layer algebraic operation
 *:MATH:SCALe*,	float, Vertical scale of the operation result
 *:MATH:OFFSet*,	float, Vertical offset of the operation result
 *:MATH:INVert*,	0|1, Inverted display mode
 *:MATH:FILTer:TYPE*,	str, Filter operation (LPASs|HPASs|BPASs|BSTOP)
 *:MATH:FILTer:W[12]*,	float, Cutoff frequency of the filter
 *:MATH:OPTion:STARt*,	int, First point on screen
 *:MATH:OPTion:END*,	int, Last point on screen
 *:MATH:OPTion:SENSitivity*,	float, Sensitivity for logic operations
 *:MATH:OPTion:DIStance*,	float, Smoothing window width for differentiation (*DIFF*)
 *:MATH:OPTion:ASCale*,	0|1, Auto scale setting for vertical axis
 *:MATH:OPTion:THReshold[12]*,	float, Threshold for logic operations
 *:MATH:OPTion:SENSitivity*,	float, Sensitivity of the logic operations
 *:MATH:FFT:WINDow*,	str, Digital window for FFT (RECT|BLAC|HANN|HAMM|FLAT|TRI)
 *:MATH:FFT:SPLit*,	0|1, Half-screen display mode for FFT
 *:MATH:FFT:UNIT*,	VRMS|DB, Unit for FFT result
 *:MATH:FFT:HSCale*,	float, Horizontal scale for the FFT
 *:MATH:FFT:HCENter*,	float, Center frequency for the FFT
 *:MATH:FFT:MODE*,	TRAC|MEM, Data source of the FFT (Memory or display)

.. csv-table:: :MATH operators
 :header: "Class", "Members"
 :widths: 30, 70
   
 *Algebraic Operators*,	ADD|SUBTract|MULTiply|DIVision
 *Functional Operators*,	INTG|DIFF|SQRT|LOG|LN|EXP|ABS
 *Logic Operators*,	AND|OR|XOR|NOT
 *Filters*,	LPASs|HPASs|BPASs|BSTOP
 *FFT*,	Fast Fourier Transform
  """
  mathDict = dict()
  mathDict[':MATH:SOURce1'] = self.query(':MATH:SOUR1?')
  mathDict[':MATH:SOURce2'] = self.query(':MATH:SOUR2?')
  mathDict[':MATH:LSOURce1'] = self.query(':MATH:LSOUR1?')
  mathDict[':MATH:LSOURce2'] = self.query(':MATH:LSOUR2?')
  mathDict[':MATH:OPTion:FX:SOURce1'] = self.query(':MATH:OPT:FX:SOUR1?')
  mathDict[':MATH:OPTion:FX:SOURce2'] = self.query(':MATH:OPT:FX:SOUR2?')
  mathDict[':MATH:DISPlay'] = self.query(':MATH:DISP?')
  mathDict[':MATH:OPERator'] = self.query(':MATH:OPER?')
  mathDict[':MATH:OPTion:FX:OPERator'] = self.query(':MATH:OPT:FX:OPER?')
  mathDict[':MATH:SCALe'] = self.query(':MATH:SCAL?')
  mathDict[':MATH:OFFSet'] = self.query(':MATH:OFFS?')
  mathDict[':MATH:INVert'] = self.query(':MATH:INV?')
  mathDict[':MATH:OPTion:STARt'] = self.query(':MATH:OPT:STAR?')
  mathDict[':MATH:OPTion:END'] = self.query(':MATH:OPT:END?')
  mathDict[':MATH:OPTion:SENSitivity'] = self.query(':MATH:OPT:SENS?')
  mathDict[':MATH:OPTion:DIStance'] = self.query(':MATH:OPT:DIST?')
  mathDict[':MATH:OPTion:ASCale'] = self.query(':MATH:OPT:ASC?')
  mathDict[':MATH:OPTion:THReshold1'] = self.query(':MATH:OPT:THR1?')
  mathDict[':MATH:OPTion:THReshold2'] = self.query(':MATH:OPT:THR2?')
  mathDict[':MATH:FILTer:TYPE'] = self.query(':MATH:FILT:TYPE?')
  mathDict[':MATH:FILTer:W1'] = self.query(':MATH:FILT:W1?')
  mathDict[':MATH:FILTer:W2'] = self.query(':MATH:FILT:W2?')
  mathDict[':MATH:FFT:SOURce'] = self.query(':MATH:FFT:SOUR?')
  mathDict[':MATH:FFT:WINDow'] = self.query(':MATH:FFT:WIND?')
  mathDict[':MATH:FFT:SPLit'] = self.query(':MATH:FFT:SPL?')
  mathDict[':MATH:FFT:UNIT'] = self.query(':MATH:FFT:UNIT?')
  mathDict[':MATH:FFT:HSCale'] = self.query(':MATH:FFT:HSC?')
  mathDict[':MATH:FFT:HCENter'] = self.query(':MATH:FFT:HCEN?')
  mathDict[':MATH:FFT:MODE'] = self.query(':MATH:FFT:MODE?')
  return mathDict

 def getREFSettings(self, n : int) -> Dict[str, Optional[Any]]:
  """For the :REFerence command, it returns the following settings:

:param n: reference channel to be queried
:returns: Dict[key, value]

.. note::
 There is no (documented) way to read the reference waveforms

.. csv-table:: REF Settings
 :header: "Key", "Range", "Description"
 :widths: 30, 30, 50
   
 *:REF:DISPlay*, 0|1, Display all reference channels
 *:REF<n>:ENABle*, 0|1, Enable reference channel
 *:REF<n>:SOURce*, CHAN<n>|D<n>, Source for reference channel
 *:REF<n>:VSCale*, float, Vertical scale for reference channel
 *:REF<n>:VOFFset*, float, Vertical offset for reference channel
 *:REF<n>:COLor*, GRAY|GREE|LBL|MAG|ORAN, Color of the reference channel (LBL == light blue)
 
All parameters are RW.
  """
  assert n in range(1, self.numberOfReferenceChannels+1)
  key = lambda _key, channel = n: ':REF{}:{}'.format(channel, _key)
  refSettingsDict = dict()
  refSettingsDict[':REF:DISPlay'] = self.query(':REF:DISP?')
  refSettingsDict[':REF:CURRent?'] = self.query(':REF:CURR?')
  refSettingsDict[key('ENABle')] = self.query(key('ENAB?'))
  refSettingsDict[key('SOURce')] = self.query(key('SOUR?'))
  refSettingsDict[key('VSCale')] = self.query(key('VSC?'))
  refSettingsDict[key('VOFFset')] = self.query(key('VOFF?'))
  refSettingsDict[key('COLor')] = self.query(key('COL?'))
  return refSettingsDict

 def saveREFSettings(self, n : int) -> None:
  """For the :REFerence command, save the settings of a reference channel

.. note::
 Via the instrument the reference waveforms can be saved in a '\*.ref' binary file,
 whose format is undocumented.

:param n: reference channel to be saved
  """
  assert n in range(1, self.numberOfReferenceChannels+1)
  key = lambda _key, channel = n: ':REF{}:{}'.format(channel, _key)
  self.write(key('ENAB 1'))
  try:
   self.write(':REF:CURR REF{}'.format(n))
  except:
   pass
  self.write(':REF:SAVE')

 def getMASKSettings(self) -> Dict[str, float]:
  """For the :MASK command, it returns the following settings:

.. csv-table:: MASK Settings
 :header: "Key", "Range", "Description"
 :widths: 30, 30, 50
   
 *:MASK:ENABle*, 0|1, Pass/fail test enabled
 *:MASK:SOURce*, CHAN<n>, Source for pass/fail test
 *:MASK:OPERate*,	RUN|STOP, Status of pass/fail test
 *:MASK:MDISplay*,	0|1, Pass/fail test statistic display enabled
 *:MASK:SOOutput*,	0|1, Stop-on-Fail for pass/fail test enabled
 *:MASK:OUTPut*,	0|1, Sound for pass/fail test enabled
 *:MASK:X*,	float, Relative horizontal window for pass/fail [time division]
 *:MASK:Y*,	float, Relative vertical window for pass/fail [vertical division]
 *:MASK:PASSed?*,	int, Number of passed frames
 *:MASK:FAILed?*,	int, Number of failed frames
 *:MASK:TOTal?*,	int, Total number of frames

:returns: Dict[key, value]
  """
  maskSettingsDict = dict()
  maskSettingsDict[':MASK:ENABle'] = int(self.query(':MASK:ENAB?'))
  maskSettingsDict[':MASK:SOURce'] = self.query(':MASK:SOUR?')
  if maskSettingsDict[':MASK:ENABle'] == 1:
   maskSettingsDict[':MASK:OPERate'] = self.query(':MASK:OPER?')
   maskSettingsDict[':MASK:MDISplay'] = int(self.query(':MASK:MDIS?'))
  maskSettingsDict[':MASK:SOOutput'] = int(self.query(':MASK:SOO?'))
  maskSettingsDict[':MASK:OUTPut'] = int(self.query(':MASK:OUTPut?'))
  maskSettingsDict[':MASK:X'] = float(self.query(':MASK:X?'))
  maskSettingsDict[':MASK:Y'] = float(self.query(':MASK:Y?'))
  maskSettingsDict[':MASK:PASSed?'] = int(self.query(':MASK:PASS?'))
  maskSettingsDict[':MASK:FAILed?'] = int(self.query(':MASK:FAIL?'))
  maskSettingsDict[':MASK:TOTal?'] = int(self.query(':MASK:TOT?'))
  
  return maskSettingsDict

 def createMASK(self, resetStatisticsOnly : bool = False) -> None:
  """For the :MASK command, create a mask

:param resetStatisticsOnly: return after resetting the displayed statistics
  """
  self.write(':MASK:RE')
  if resetStatisticsOnly:
   return
  self.write(':MASK:ENAB 1')
  self.write(':MASK:OPER STOP')
  self.write(':MASK:CRE')

 def getDECSettings(self, n : int) -> Dict[str, Optional[Any]]:
  """For the :DECoder command, it returns the following settings:
The :DECoder command is available only on the DS1000/MSO1000 oscilloscopes,
later devices support the :BUS command.

:param n: decoder ID to be queried
:returns: Dict[key, value]

.. csv-table:: Bus Types
 :header: "Key", "Opt", "Description"
 :widths: 30, 10, 50
  
 *:DEC:PARallel*,, Clock and 1 data bit line of a Parallel Bus Interface (`PBI`_)
 *:DEC:UART*,, Universal Asynchronous Receiver Transmitter (`UART`_) bus
 *:DEC:IIC*, Inter-Integrated Circuit (`IIC`_) interface
 *:DEC:IIC*, Serial Peripheral Interface (`SPI`_)

.. csv-table:: General Parameters
 :header: "Key", "Range", "Description"
 :widths: 30, 30,50

 *:TRIG:<m>:ADDRess*, int, address in I2C trigger
 *:DEC:MODE*, PAR|UART|SPI|IIC, Decoder bus
 *:DEC:DISPlay* 0|1, Status of decoder
 *:DEC:FORMat*, HEX|ASCii|DEC|BIN|LINE, Bus display format
 *:DEC:POSition*, int, Vertical position of the bus on screen
 *:DEC:THREshold:CHANnel[1-4]*, float, Threshold level (only if :DEC:THREshold:AUTO == 0)
 *:DEC:THREshold:AUTO*, 0|1, Status of the auto threshold for an analog channel
 *:DEC:CONFig:LABel*, 0|1, Status of the label display
 *:DEC:CONFig:LINE*, 0|1, Status of the bus display
 *:DEC:CONFig:FORMat*, 0|1, Status of the bus format display
 *:DEC:CONFig:ENDian*, 0|1, Status of the bus endian display
 *:DEC:CONFig:WIDth*, 0|1, Status of the frame width display
 *:DEC:CONFig:SRATe?*, float, Sample rate

.. csv-table:: :DEC:<Bus> Parameters
 :header: "Key", "Range", "Description"
 :widths: 30, 30, 50

 *ADDRess*, NORM|RW, Status of address mode of IIC decoding
 *BAUD*, int, Baud rate of UART decoding
 *BITX*, int, Data bit for the parallel bus
 *CCOMpensation*, float, Clock compensation time for parallel decoding
 *CLK*, CHAN<m>|D<m>, Clock channel
 *CS*, CHAN<m>|D<m>, CS channel of SPI decoding
 *DATA*, CHAN<m>|D<m>, Data channel of IIC decoding
 *EDGE*, RISE|FALL, Edge selection
 *ENDian*, LSB|MSB, Endian of data
 *MISO*, CHAN<m>|D<m>, MISO channel of SPI decoding
 *MODE*, CS|TIMeout, Frame synchronization mode of SPI decoding
 *MOSI*, CHAN<m>|D<m>, MOSI channel of SPI decoding
 *NREJect*, 0|1, Status of noise rejection function of parallel decoding
 *NRTime*, float, Noise rejection time of parallel decoding
 *PARity*, NONE|EVEN|ODD, Mode of transmission of UART decoding
 *PLOT*, 0|1, Status of curve function for parallel decoding
 *POLarity*, POS|NEG, Polarity of the SDA data line in SPI decoding.
 *RX*, CHAN<m>|D<m>, RX channel of UART decoding
 *SELect*, NCS|CS, CS polarity in SPI decoding
 *SOURCe*, CHAN<m>|D<m>, Data channel of IIC decoding
 *STOP*, 1|1.5|2, Number of stop bits of UART decoding
 *TIMeout*, real, Timeout for SPI decoding
 *TX*, CHAN<m>|D<m>, TX channel of UART decoding
 *WIDth*, int, Frame width (number of bits)
 
All parameters are RW.

.. _PBI: https://en.wikipedia.org/wiki/Parallel_Bus_Interface
.. _UART: https://en.wikipedia.org/wiki/Universal_asynchronous_receiver-transmitter
.. _IIC: https://en.wikipedia.org/wiki/I%C2%B2C
.. _SPI: https://en.wikipedia.org/wiki/I%C2%B2C
  """
  assert n in range(1, self.numberOfDecoders+1)
  key = lambda _key, id = n: ':DEC{}:{}'.format(id, _key)
  mode = self.query(key('MODE?'))
  key2 = lambda _key, id = n, mode = mode: ':DEC{}:{}:{}'.format(id, mode, _key)
  decSettings = dict()
  decSettings[key('MODE')] = mode
  decSettings[key('DISPlay')] = int(self.query(key('DISP?')))
  decSettings[key('FORMat')] = self.query(key('FORM?'))
  decSettings[key('POSition')] = int(self.query(key('POS?')))
  decSettings[key('THREshold:AUTO')] = int(self.query(key('THRE:AUTO?')))
  if decSettings[key('THREshold:AUTO')] == 0:
   for m in range(1, 5):
    decSettings[key('THREshold:CHANnel{}'.format(m))] = float(self.query(key('THRE:CHAN{}?'.format(m))))
  decSettings[key('CONFig:LABel')] = int(self.query(key('CONF:LAB?')))
  decSettings[key('CONFig:LINE')] = int(self.query(key('CONF:LINE?')))
  decSettings[key('CONFig:FORMat')] = int(self.query(key('CONF:FORM?')))
  if decSettings[key('MODE')] != 'PAR':
   decSettings[key('CONFig:ENDian')] = int(self.query(key('CONF:END?')))
  decSettings[key('CONFig:WIDth')] = int(self.query(key('CONF:WID?')))
  decSettings[key('CONFig:SRATe?')] = float(self.query(key('CONF:SRAT?')))
  # ['PAR', 'UART', 'SPI', 'IIC']
  if mode in ['PAR', 'SPI', 'IIC']:
   decSettings[key2('CLK')] =  self.query(key2('CLK?'))
  if mode in ['PAR',  'UART', 'SPI']:
   decSettings[key2('POLarity')] =  self.query(key2('POL?'))
   decSettings[key2('WIDTh')] =  int(self.query(key2('WIDT?')))
  if mode in ['PAR',  'SPI']:
   decSettings[key2('EDGE')] =  self.query(key2('EDGE?'))
  if mode in ['UART',  'SPI']:
   decSettings[key2('ENDian')] =  self.query(key2('END?'))
  if mode == 'PAR':
   decSettings[key2('BITX')] =  int(self.query(key2('BITX?')))
   decSettings[key2('SOURce')] =  self.query(key2('SOUR?'))
   decSettings[key2('NREJect')] =  int(self.query(key2('NREJ?')))
   if decSettings[key2('NREJect')] == 1:
    decSettings[key2('NRTime')] =  float(self.query(key2('NRT?')))
   if decSettings[key2('CLK')] != 'OFF':
    decSettings[key2('CCOMpensation')] =  float(self.query(key2('CCOM?')))
   decSettings[key2('PLOT')] =  int(self.query(key2('PLOT?')))
  if mode == 'UART':
   decSettings[key2('TX')] =  self.query(key2('TX?'))
   decSettings[key2('RX')] =  self.query(key2('RX?'))
   decSettings[key2('BAUD')] =  int(self.query(key2('BAUD?')))
   decSettings[key2('STOP')] =  self.query(key2('STOP?'))
   decSettings[key2('PARity')] =  self.query(key2('PAR?'))
  if mode == 'IIC':
   decSettings[key2('DATA')] =  self.query(key2('DATA?'))
   decSettings[key2('ADDRess')] =  self.query(key2('ADDR?'))
  if mode == 'SPI':
   decSettings[key2('MISO')] =  self.query(key2('MISO?'))
   decSettings[key2('MOSI')] =  self.query(key2('MOSI?'))
   decSettings[key2('CS')] =  self.query(key2('CS?'))
   decSettings[key2('SELect')] =  self.query(key2('SEL?'))
   decSettings[key2('MODE')] =  self.query(key2('MODE?'))
   decSettings[key2('TIMeout')] =  float(self.query(key2('TIM?')))

  return decSettings
