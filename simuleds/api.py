from PyQt4.QtCore import QThread


ARDUINO_DIGITAL_PIN_NB = 14

NOTUSED = 0
INPUT = 1
OUTPUT = 2


def delay(msecs):
    QThread.msleep(msecs)


class SimException(Exception): pass

