from typing import Optional
import re, io, time
import pytest

try:
 from PIL import Image, ImageFile
 hasPIL = True
except:
 print('PIL not installed')
 hasPIL = False
 
try:
 import numpy
 import matplotlib.pyplot as plt
 hasMatplotlib = True
except:
 print('numpy and/or matplotlib not installed')
 hasMatplotlib = False

if __name__ == "__main__":
 import os,  sys
 fileDirectory = os.path.dirname(os.path.abspath(__file__)) 
 sys.path.insert(0, os.path.dirname(fileDirectory))

from MzRigolDS1000Z import DigitalOscilloscopeBase

def findOscilloscopeName() -> Optional[DigitalOscilloscopeBase]:
 instruments = DigitalOscilloscopeBase.discoverInstruments(notify = print)
 for instrument in instruments:
  idn = instrument[1]
  modelMatch = re.match('[^,]+,(DS|MSO)[1-9][0-9][0-9][1-9][^0-9]', idn, flags = re.I)
  if modelMatch is not None:
   return instrument[0]
 print('No Instruments found')
 return None

def runACQ(devName : Optional[str] = None):
 if devName is None:
  devName = findOscilloscopeName()
 dev = DigitalOscilloscopeBase(devName)
 acqDict1 = dev.getACQSettings()
 dev.setSettings(acqDict1)
 acqDict2 = dev.getACQSettings()
 assert acqDict1 == acqDict2

def test_ACQ(pytestconfig):
 devName = pytestconfig.getoption('oscilloscope')
 runACQ(devName)
    
def runCHAN(devName : Optional[str] = None):
 if devName is None:
  devName = findOscilloscopeName()
 dev = DigitalOscilloscopeBase(devName)
 for n in range(1, dev.numberOfAnalogChannels+1):
  chDict1 = dev.getCHANSettings(n)
  dev.setSettings(chDict1)
  chDict2 = dev.getCHANSettings(n)
  assert chDict1 == chDict2

def test_CHAN(pytestconfig):
 devName = pytestconfig.getoption('oscilloscope')
 runCHAN(devName)
    
def runDISP(devName : Optional[str] = None):
 if devName is None:
  devName = findOscilloscopeName()
 dev = DigitalOscilloscopeBase(devName)
 dispDict1 = dev.getDISPSettings()
 dev.setSettings(dispDict1)
 dispDict2 = dev.getDISPSettings()
 assert dispDict1 == dispDict2
 for fmt in ['PNG', 'BMP', 'TIFF']:
  fp = io.BytesIO(dev.getDISPData(fmt = fmt))
  if hasPIL:
   ImageFile.LOAD_TRUNCATED_IMAGES =True
   img = Image.open(fp, mode = "r", formats = [fmt])
   img.show()

def test_DISP(pytestconfig):
 devName = pytestconfig.getoption('oscilloscope')
 runDISP(devName)

def runTIM(devName : Optional[str] = None):
 if devName is None:
  devName = findOscilloscopeName()
 dev = DigitalOscilloscopeBase(devName)
 timDict1 = dev.getTIMSettings()
 dev.setSettings(timDict1)
 timDict2 = dev.getTIMSettings()
 assert timDict1 == timDict2

def test_TIM(pytestconfig):
 devName = pytestconfig.getoption('oscilloscope')
 runTIM(devName)

def runTRIG(devName : Optional[str] = None):
 if devName is None:
  devName = findOscilloscopeName()
 dev = DigitalOscilloscopeBase(devName)
 trStart = dev.getTRIGSettings()
 for mode in ['EDGE', 'PULS', 'SLOP', 'VID', 'DUR', 'TIM', 'RUNT', 'WIND', 'DEL', 'SHOL',  'NEDG', 'RS232', 'IIC']:
  dev.write(':TRIG:MODE {}'.format(mode))
  time.sleep(0.3)
  trDict1 = dev.getTRIGSettings()
  dev.setSettings(trDict1)
  time.sleep(0.1)
  trDict2 = dev.getTRIGSettings()
  pytest.helpers.compareDicts(trDict1, trDict2, mode)
 dev.setSettings(trStart)
 assert dev.query(':TRIG:STAT?') == dev.triggerStatus

def test_TRIG(pytestconfig):
 devName = pytestconfig.getoption('oscilloscope')
 runTRIG(devName)

def runWAV(devName : Optional[str] = None):
 if devName is None:
  devName = findOscilloscopeName()
 dev = DigitalOscilloscopeBase(devName)
 isRunning = dev.triggerStatus != 'STOP'
 if not isRunning:
  print('Running in :STOP mode')
  dev.setRUN()
 else:
  print('Running in :RUN mode')
 wavDict1 = dev.getWAVSettings()
 dev.setSettings(wavDict1)
 wavDict2 = dev.getWAVSettings()
 assert wavDict1 == wavDict2
 channelList = list()
 for channel in range(1, dev.numberOfAnalogChannels + 1):
  if dev.query(':CHAN{}:DISP?'.format(channel)) == '1':
   channelList.append(channel)
  else:
   print('CHANnel{} skipped'.format(channel))
 assert len(channelList) > 0
 if not isRunning:
  dev.setRUN()
  dev.write(':ACQ:MDEP {}'.format(600000))
  dev.setSTOP()
 timSettings = dev.getTIMSettings()
 assert timSettings[':TIM:MODE'] == 'MAIN'
 tData = None
 colors = ['yellow', 'cyan', 'magenta', 'blue']
 yUnit = None
 if hasMatplotlib:
  plt.axes().set_facecolor('black')
  plt.grid(visible = True, linestyle='dotted')
 for channel in channelList:
  chData = dev.getWAVData('CHAN{}'.format(channel), MODE = 'MAX', FORMat = 'BYTE', showHiddenData = False)
  if not hasMatplotlib:
   continue
  if tData is None:
   tData = numpy.linspace(timSettings['TIM:TL?'], timSettings['TIM:TR?'], num = len(chData))
  chData = numpy.array(chData) 
  plt.plot(tData, chData, color = colors[(channel - 1) % 4], linewidth = 0.5, label = 'CHAN{}'.format(channel) )
  chDict = dev.getCHANSettings(channel)
  if yUnit is None:
   yUnit = chDict[':CHAN{}:UNITs'.format(channel)]
  elif yUnit != chDict[':CHAN{}:UNITs'.format(channel)]:
   yUnit = 'UNKN'
 if hasMatplotlib and yUnit is not None:
  plt.xlabel('Time [s]')
  if yUnit == 'VOLT':
   plt.ylabel('Voltage [V]')
  elif yUnit == 'AMP':
   plt.ylabel('Current [A]')
  elif yUnit == 'WATT':
   plt.ylabel('Power [W]')
  else:
   plt.ylabel('??? [?]')
  plt.show()

def test_WAV(pytestconfig):
 devName = pytestconfig.getoption('oscilloscope')
 runWAV(devName)

if __name__ == "__main__":
 
 #runACQ()
 #runCHAN()
 #runDISP()
 #runTIM()
 runTRIG()
 #runWAV()
 print('++++++++++++++++++ completed ++++++++++++++++++')
