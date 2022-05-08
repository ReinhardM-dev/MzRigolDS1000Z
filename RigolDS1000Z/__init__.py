__description__ = \
"""
Rigol oscilloscope of series DS1000/MSO1000
"""
__author__ = "Reinhard Maerz"
__date__ = "2022-05-01"
__version__ = "0.9.0"

import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

__all__ = ['driver', 'base', 'DS1000']

from .driver import RigolError, Instrument
from .base import DigitalOscilloscopeBase
from .DS1000 import DS1000Z
