from typing import Optional, Union, Dict, Tuple, Any
import pytest

import re
import copy
if __name__ == "__main__":
 import os,  sys
 fileDirectory = os.path.dirname(os.path.abspath(__file__)) 
 sys.path.insert(0, os.path.dirname(fileDirectory))

from MzRigolDS1000Z import Instrument, RigolError

def runCommand(dev, command, shouldFail = False) -> Union[str, bool]:
 try:
  if command.endswith('?'):
   response = dev.query(command)
   print('{} = {}, expected? = {}'.format(command, response, not shouldFail))
   return response
  else:
   print('{} = {}, expected? = {}'.format(command, dev.write(command), not shouldFail))
   return not shouldFail
 except RigolError as err:
  print('{} -> {}, expected? = {}'.format(command, err, shouldFail))
  return shouldFail

def findInstrumentName():
 instruments = Instrument.discoverInstruments(notify = print)
 if len(instruments) == 0:
  print('No Instruments found')
  return None
 return instruments[0][0]

def runInstrument(devName : Optional[str] = None):
 if devName is None:
  devName = findInstrumentName()
 dev = Instrument(devName)
 sMode = runCommand(dev, ':TRIG:MODE?')
 sMode = runCommand(dev, ':tRiG:mOdE?')
 if sMode != 'VID':
  runCommand(dev, ':TRIG:Mode VID')
 else:
  runCommand(dev, ':TRIG:Mode EDGE')
 sMode = runCommand(dev, ':BLA?', shouldFail = True)
 isFailed = runCommand(dev, ':BLA FOO', shouldFail = True)
 assert isinstance(sMode, bool) and isFailed, 'Command fail test not working'

def test_instrument(pytestconfig):
 devName = pytestconfig.getoption('oscilloscope')
 runInstrument(devName)
    
if __name__ == "__main__":
 runInstrument()


