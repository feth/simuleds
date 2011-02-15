# api.py
# Copyright (C) 2011 Feth Arezki <feth <A+> tuttu.info>
#
# This module is part of simuleds and is released under the GPLv3
# License: http://www.gnu.org/licenses/gpl-3.0.txt
#
from PyQt4.QtCore import QThread


ARDUINO_DIGITAL_PIN_NB = 14

NOTUSED = 0
INPUT = 1
OUTPUT = 2


def delay(msecs):
    QThread.msleep(msecs)


class SimException(Exception): pass

