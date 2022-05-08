import shutil
import sys
import os, os.path

from setuptools import setup

package = 'RigolDS1000'
fileDirectory = os.path.dirname(os.path.abspath(__file__))
packageDirectory = os.path.join(fileDirectory, package)
sys.path.insert(0, fileDirectory)

with open(os.path.join(packageDirectory,'readme.rst'), 'r', encoding = 'utf-8') as f:
 long_description = f.read()

import RigolDS1000Z
pkgVersion = RigolDS1000Z.__version__

shutil.rmtree(os.path.join(fileDirectory, 'build'), ignore_errors = True)

setup(name = package,
  url = 'https://github.com/ReinhardM-dev/RigolDS1000Z', 
  project_urls={ 'Documentation': 'https://reinhardm-dev.github.io/RigolDS1000Z' }, 
  version = pkgVersion,
  packages = [package],
  options={'bdist_wheel':{'universal':True}},
  package_data = {package: ['*.txt', '*.gpl3', '*.rst'] }, 
  description='Python interface for Rigol DS1000Z/MSO1000Z oscilloscopes',
  long_description = long_description, 
  long_description_content_type="text/x-rst",
  author  ='Reinhard Maerz',
  python_requires = '>=3.6', 
  install_requires = [ 'pyvisa>=1.11.0' ],
  setup_requires=['wheel'], 
  classifiers = [
    'Programming Language :: Python', 
    'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
    'Operating System :: OS Independent',
    'Programming Language :: Python :: 3 :: Only',
    'Development Status :: 4 - Beta', 
    'Natural Language :: English', 
    'Topic :: System :: Hardware :: Hardware Drivers'])

