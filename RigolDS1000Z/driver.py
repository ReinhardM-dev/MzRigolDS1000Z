from typing import Any, Type, Callable, Union, Optional, Iterable, Sequence, List, Dict, Tuple, Callable
# from enum import IntEnum, unique
import time, socket
import re,  functools

import pyvisa

class RigolError(Exception):
 """All errors related to Rigol devices"""

stdResourceManager = pyvisa.ResourceManager()

class Instrument(object):
 """Class handling Rigol devices exhibiting the following behavior:
 
 * compliance to `VXI-11`_, `LXI`_ and `SCPI`_ specifications
 * usage of 'LF' as read\_ and write_termination
 * support of the '\*IDN?' command starting with 'RIGOL TECHNOLOGIES,'
 * support of the ':SYST:ERR?' command
 * support of 'IEEE' data transfer format (#N<N bytes to be transferred><Byte1> ... <ByteN><LF>) for both binary and ASCII arrays
 
.. _VXI-11: https://www.vxibus.org
.. _LXI: https://www.lxistandard.org
.. _SCPI: https://www.ivifoundation.org/scpi
  """
 def __init__(self, resourceName : str, openTimeout_msec : int = 100,  
                            resourceManager : Optional[pyvisa.ResourceManager] = None) -> None:
  global stdResourceManager
  assert openTimeout_msec >= 0, '{}: openTimeout_msec = {} is not a positive integer'.format(self.__class__.__name__, openTimeout_msec)
  if openTimeout_msec == 0:
   accessMode = pyvisa.constants.AccessModes.no_lock
  else:                                                                                                                                        
   accessMode = pyvisa.constants.AccessModes.exclusive_lock
  try:
   if resourceManager is not None:
    self._dev = resourceManager.open_resource(resourceName, access_mode = accessMode,  open_timeout = openTimeout_msec)
   else:
    self._dev = stdResourceManager.open_resource(resourceName, access_mode = accessMode,  open_timeout = openTimeout_msec)
  except pyvisa.VisaIOError as err:
   raise RigolError('{} on {}, potential route cause: instrument in STOP mode'.format(err, resourceName))
  self._dev.read_termination = '\n'
  self._dev.write_termination = '\n'
  self._dev.timeout = 20000
  idn = self._dev.query('*IDN?')
  if not Instrument._validateIDN(idn):
   raise ValueError('{}: device is not supported (idn = {})'.format(self.__class__.__name__, idn))
  self._dev.write('*CLS\n*WAI')
  self._idnDict = dict()
  self._idnDict['*IDN?'] = idn
  for key, value in zip(['vendor', 'model', 'serialID', 'softwareVersion'], idn.split(',')):
   self._idnDict[key] = value
 
 @property
 def resource_manager(self) -> str:
  ":returns: pyvisa resource manager"
  return self._dev.resource_manager
 
 @property
 def resource_name(self) -> str:
  ":returns: pyvisa resource name"
  return self._dev.resource_name

 @property
 def session(self) -> str:
  ":returns: pyvisa (unique) session ID"
  return self._dev.session

 @property
 def manufacturer_name(self) -> str:
  ":returns: Instrument's manufacturer name"
  return self._idnDict['vendor']

 @property
 def model_name(self) -> str:
  ":returns: Instrument's model name"
  return self._idnDict['model']

 @property
 def serial_ID(self) -> str:
  ":returns: Instrument's serial ID"
  return self._idnDict['serialID']

 @property
 def software_version(self) -> str:
  ":returns: Instrument's software version"
  return self._idnDict['softwareVersion']

 @property
 def idnDict(self)->Dict[str, str]:
  ":returns: Dict[name, value]"
  return self._idnDict
 
 def setRST(self) -> None:
  "Resets the instrument to default state (handle with care!)"
  self.write('*RST')
   
 def handleErrors(self, message : str, silent : bool = False, extraMsg : Optional[str] = None) -> List[str]:
  """Returns the most recent errors

:returns: Tuple[error message]
  """  
  messageList = list()
  if extraMsg is not None:
   messageList.append(extraMsg)
  while True:
   try:
    rigolMsg = self._dev.query('SYST:ERR?')
    errCode, errMessage = rigolMsg.split(',')
   except:
    errCode = 9999
    errMessage = 'Timeout during SYST:ERR?: instrument in STOP mode?'
   if errCode == '0':
    break
   messageList.append(' {} : {}'.format(int(errCode), errMessage))
  if silent or len(messageList) == 0:
   return messageList
  raise RigolError('{} :\n{}'.format(message, '\n'.join(messageList)))

 def write(self, message : str)->int:
  """A combination of write(message) and read()

driver.py:param message: Message to send.

:returns: number of sended bytes
  """  
  if self._dev.write('{}\n*WAI'.format(message)) != len(message) + 6:
   extraMsg = '{}.write: Failed to write message {}.'.format(self.__class__.__name__, message)
  else:
   extraMsg = None
  self.handleErrors(message, extraMsg = extraMsg)
  return len(message) + 1
  
 def query(self, message : str, delay_msec : int = 10) -> Optional[str]:
  """Query a value from the instrument

:param message: Message to send.
:param delay_msec: Delay in msec between write and read operations. 

:returns: Parsed data
  """  
  try:
   response = self._dev.query(message, delay = delay_msec/1000)
   return response
  except:
   self.handleErrors(message)
 
 def query_binary_values(self, 
        message : str, 
        datatype : str = "B",
        container : Union[Type, Callable[[Iterable], Sequence]] = list,
        delay_msec : int = 0,
        chunk_size : Optional[int] = 20*1024) -> Sequence[Union[int, float, bytes]]:
  """Query the device for values in binary format returning an iterable
        of values.

:param message: Message to send.
:param datatype: Format string for a single element (see struct module)
:param is_big_endian: Are the received data in big or little endian order?
:param container: Container type to use for the output data (e.g. list, tuple, np.ndarray, ...)
:param delay_msec: Delay in msec between write and read operations. 
:param chunk_size: Size of the chunks to read from the device.

:returns: Parsed data
  """
  try:
   response = self._dev.query_binary_values(message, 
        datatype = datatype, is_big_endian = False,
        container = container, header_fmt = 'ieee',
        expect_termination = True, chunk_size = chunk_size, 
        delay = delay_msec/1000)
   return response
  except:  
   self.handleErrors(message)
   
 def query_ascii_values(self, 
        message : str,
        converter : str = "f",
        container : Union[Type, Callable[[Iterable], Sequence]] = list,
        delay_msec : int = 0) -> Sequence[Union[Any]]:
  """Query the device for values in ascii format returning an iterable of values.

:param message: Message to send.
:param converter: Str format of function to convert each value.
:param container: Container type to use for the output data (e.g. list, tuple, np.ndarray, ...)
:param delay_msec: Delay in msec between write and read operations. 

:returns: Parsed data
  """
  # RIGOL send a header_fmt = 'ieee' also for ASCII data
  _converters: Dict[str, Callable[[str], Any]] = {
    "s": str,
    "b": functools.partial(int, base=2),
    "c": ord,
    "d": int,
    "o": functools.partial(int, base=8),
    "x": functools.partial(int, base=16),
    "X": functools.partial(int, base=16),
    "h": functools.partial(int, base=16),
    "H": functools.partial(int, base=16),
    "e": float,
    "E": float,
    "f": float,
    "F": float,
    "g": float,
    "G": float,
  }
  assert converter in _converters, "Invalid converter '{}', use ({})".format(converter, '|'.join(_converters.keys()))
  converter = _converters[converter]

  responseStr = str(b''.join(self.query_binary_values(message, datatype = 'c')), 'UTF-8')
  response = list()
  for item in responseStr.split(','):
   response.append(converter(item))
   
  return container(response)

 @staticmethod
 def _validateIDN(idnString : str) -> bool:
  return idnString.upper().startswith('RIGOL TECHNOLOGIES,')
  
 @staticmethod
 def discoverUSBInstruments(notify : Optional[Callable[[str], None]] = None) -> List[Tuple[str, str]]:
  """Search for Rigol Instruments connected via the USB interface
:param notify: notification function (e.g. print)

:returns: List[(resource_name, response to \*IDN?)]
  """
  global stdResourceManager
  candidates = list()
  if notify:
   notify('------------- discoverUSBInstruments started -------------')
  for visaSpec in stdResourceManager.list_resources():
   if visaSpec.startswith('USB') and visaSpec.endswith('::INSTR'):
    try:
     dev = Instrument(visaSpec)
     if notify:
      notify(' {}: IDN = {}'.format(dev._dev.resource_name, dev.idnDict['*IDN?']))
     candidates.append((dev._dev.resource_name, dev.idnDict['*IDN?']))
    except ValueError:
     pass
  if notify:
   notify('------------- discoverUSBInstruments completed -------------')
  return candidates

 @staticmethod
 def discoverIP4Instruments(subnetBytes : int = 3, ignoreVMIDs : bool = True,  notify : Optional[Callable[[str], None]] = None) -> List[Tuple[str, str]]:
  """Search for Rigol Instruments connected via the TCPIP interface (ip4 - address)

:param notify: notification function (e.g. print)
:returns: List[(resource_name, response to \*IDN?)]
  """
  def netMaskIP4(address, subnetBytes, ignoreVMIDs):
   parts = address.split(".")
   if len(parts) != 4:
    return None
   for item in parts:
    if not (item.isdigit() and int(item) < 256):
     return None
   if ignoreVMIDs and parts[-1] == '1':
    return None
   return '.'.join(parts[:subnetBytes])
 
  global stdResourceManager
  assert 0 <= subnetBytes <= 3, "discoverIP4Instruments: improper subnetBytes = {}".format(subnetBytes)
  socket.setdefaulttimeout(.01)
  candidates = list()
  lxiPort = 111
  if notify:
   notify('------------- discoverIP4Instruments started -------------')
  for addrInfo in socket.getaddrinfo(socket.gethostname(), None):
   ip4Net = netMaskIP4(addrInfo[-1][0], subnetBytes, ignoreVMIDs)
   if ip4Net is not None:
    for i in range(0,255):
     hostAddr = '{}.{}'.format(ip4Net, i)
     sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
     result = sock.connect_ex((hostAddr, lxiPort))
     sock.close()
     if result == 0:
      try:
       visaSpec = 'TCPIP::{}::INSTR'.format(hostAddr)
       dev = Instrument(visaSpec)
       idn = dev.query('*IDN?')
       if Instrument._validateIDN(idn):
        if notify:
         notify(' {}: IDN = {}'.format(dev.resource_name, idn))
        candidates.append((dev.resource_name, idn))
      except:
       pass
  if notify:
   notify('------------- discoverIP4Instruments completed -------------')
  return candidates

 @staticmethod
 def discoverInstruments(notify : Optional[Callable[[str], None]] = None) -> List[Tuple[str, str]]:
  """Search for Rigol Instruments connected via the USB or TCPIP interface (ip4 - address)
:param notify: notification function (e.g. print)

:returns: List[(resource_name, response to \*IDN?)]
  """
  usbInstruments = Instrument.discoverUSBInstruments(notify = notify)
  if len(usbInstruments) > 0:
   return usbInstruments 
  return Instrument.discoverIP4Instruments(notify = notify)

