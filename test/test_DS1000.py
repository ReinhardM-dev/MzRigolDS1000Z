from typing import Optional
import re, time
import pytest

if __name__ == "__main__":
 import os,  sys
 fileDirectory = os.path.dirname(os.path.abspath(__file__)) 
 sys.path.insert(0, os.path.dirname(fileDirectory))

from MzRigolDS1000Z import DS1000Z

def findOscilloscopeName() -> Optional[DS1000Z]:
 instruments = DS1000Z.discoverInstruments(notify = print)
 for instrument in instruments:
  idn = instrument[1]
  modelMatch = re.match('[^,]+,(DS|MSO)[1-9][0-9][0-9][1-9][^0-9]', idn, flags = re.I)
  if modelMatch is not None:
   return instrument[0]
 print('No Instruments found')
 return None

def runCURS(devName : Optional[str] = None):
 if devName is None:
  devName = findOscilloscopeName()
 dev = DS1000Z(devName)
 cursStart = dev.getCURSSettings()
 for mode in ['MAN', 'TRAC', 'AUTO']:
  dev.write(':CURS:MODE {}'.format(mode))
  time.sleep(0.3)
  cursDict1 = dev.getCURSSettings()
  dev.setSettings(cursDict1)
  time.sleep(0.1)
  cursDict2 = dev.getCURSSettings()
  pytest.helpers.compareDicts(cursDict1, cursDict2, mode)
 dev.setSettings(cursStart)

def test_CURS(pytestconfig):
 devName = pytestconfig.getoption('oscilloscope')
 runCURS(devName)

def runDEC(devName : Optional[str] = None):
 if devName is None:
  devName = findOscilloscopeName()
 dev = DS1000Z(devName)
 for decoder in range(1, dev.numberOfDecoders +1):
  decDict1 = dev.getDECSettings(decoder)
  dev.setSettings(decDict1)
  decDict2 = dev.getDECSettings(decoder)
  assert decDict1 == decDict2

def test_DEC(pytestconfig):
 devName = pytestconfig.getoption('oscilloscope')
 runDEC(devName)

def runMASK(devName : Optional[str] = None):
 if devName is None:
  devName = findOscilloscopeName()
 dev = DS1000Z(devName)
 maskDict1 = dev.getMASKSettings()
 dev.setSettings(maskDict1)
 maskDict2 = dev.getMASKSettings()
 assert maskDict1 == maskDict2

def test_MASK(pytestconfig):
 devName = pytestconfig.getoption('oscilloscope')
 runMASK(devName)

def runMATH(devName : Optional[str] = None):
 if devName is None:
  devName = findOscilloscopeName()
 dev = DS1000Z(devName)
 mathDict1 = dev.getMASKSettings()
 dev.setSettings(mathDict1)
 mathDict2 = dev.getMASKSettings()
 assert mathDict1 == mathDict2

def test_MATH(pytestconfig):
 devName = pytestconfig.getoption('oscilloscope')
 runMATH(devName)

def runMEAS(devName : Optional[str] = None):
 if devName is None:
  devName = findOscilloscopeName()
 dev = DS1000Z(devName)
 measDict1 = dev.getMEASItem1Source('CHAN1')
 dev.setSettings(measDict1)
 measDict2 = dev.getMEASItem1Source('CHAN1')
 pytest.helpers.compareDicts(measDict1, measDict2, 'getMEASItem1Source')
 measDict1 = dev.getMEASItem2Source('CHAN1', 'CHAN2')
 dev.setSettings(measDict1)
 measDict2 = dev.getMEASItem2Source('CHAN1', 'CHAN2')
 pytest.helpers.compareDicts(measDict1, measDict2, 'getMEASItem2Source')
 measDict1 = dev.getMEASThresholdSettings()
 dev.setSettings(measDict1)
 measDict2 = dev.getMEASThresholdSettings()
 assert measDict1 == measDict2

def test_MEAS(pytestconfig):
 devName = pytestconfig.getoption('oscilloscope')
 runMEAS(devName)
 
def runREF(devName : Optional[str] = None):
 if devName is None:
  devName = findOscilloscopeName()
 dev = DS1000Z(devName)
 refDict1 = dev.getREFSettings(1)
 dev.setSettings(refDict1)
 refDict2 = dev.getREFSettings(1)
 pytest.helpers.compareDicts(refDict1, refDict2, 'ref')
 dev.saveREFSettings(1)

def test_REF(pytestconfig):
 devName = pytestconfig.getoption('oscilloscope')
 runREF(devName)

if __name__ == "__main__":
 
#  runCURS()
# runDEC()
# runMASK()
# runMATH()
# runMEAS()
 runREF()
 print('++++++++++++++++++ completed ++++++++++++++++++')

