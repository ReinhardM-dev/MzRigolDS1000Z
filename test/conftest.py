from typing import Dict, Any
import sys
import platform
if platform.system() == 'Windows':
 import winreg
import os, os.path
import pytest

# e.g. 
# pytest --pdb --component Enigma_D --notify

# fileDirectory = os.path.dirname(os.path.abspath(__file__)) 
# sys.path.insert(0, os.path.dirname(fileDirectory))
packageDirectory = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) 
sys.path.insert(0, packageDirectory)

def pytest_addoption(parser):
 home = homeFolder()
 parser.addoption("--notify", action="store_true", default = False, help = "Enable notify")
 parser.addoption("--oscilloscope", action="store", help = "Resource name")

#"A calm and modest life brings more happiness than the pursuit of success combined with constant restlessness"

@pytest.helpers.register
def notify(pytestconfig): 
 return [None, print][pytestconfig.getoption('notify')]

@pytest.helpers.register
def compareDicts(dict1 : Dict[str, Any], dict2 : Dict[str, Any], header :str) -> None:
 keyList = dict1.keys()
 assert keyList == dict2.keys()
 keyList = list()
 for key, value in dict1.items():
  if str(value) != str(dict2[key]): 
   keyList.append(key)
 if len(keyList) != 0:
  print('WARNING: {}, keys differ'.format(header))
  for key in keyList:
   print(' {:<20} : {:>20} {:>20}'.format(key, dict1[key], dict2[key]))

@pytest.helpers.register
def message(pytestconfig): 
 rawMsg = pytestconfig.getoption('message')
 if rawMsg:
  msg = str()
  for c in rawMsg.upper():
   if c == ' ':
    c = 'X'
   msg += c
  print('message = {}'.format(msg))
 else:
  msg = None
  print('message = actual Alphabet')
 return msg

@pytest.helpers.register
def homeFolder() -> str: 
 if platform.system() == 'Windows':
  try:
   handle= winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders")
   return winreg.QueryValueEx(handle,'Personal')[0] 
  except:
   pass
 return os.path.expanduser('~')
 
