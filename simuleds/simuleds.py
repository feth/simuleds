from abc import abstractmethod
from sys import argv

from PyQt4.QtCore import QObject, QThread, SIGNAL
from PyQt4.QtGui import QApplication, QFrame

from .leds_ui import Ui_Frame


PIN_NB = 5
COMBINATIONS = 1 << PIN_NB

ARDUINO_DIGITAL_PIN_NB = 14

NOTUSED = 0
INPUT = 1
OUTPUT = 2

_PINSIGNAL = SIGNAL('value changed')
_LOOPMSGSIGNAL = SIGNAL('loop message')

class SimException(Exception): pass

class Pin(QObject):

    def __init__(self):
        QObject.__init__(self)
        self.value = False
        self.value = False
        self.mode = NOTUSED

    def digitalWrite(self, value):
        if not (self.mode is OUTPUT):
            raise SimException("pin not in write mode")
        self.value = bool(value)
        self.emit(_PINSIGNAL, self.value)

    def digitalRead(self):
        if not (self.mode & INPUT):
            raise SimException("pin not in read mode")
        return self.value

    #'mode' is a property, and self._mode is indirectly set in __init__
    # pylint: disable=W0201
    def _setmode(self, mode):
        if not mode in (NOTUSED, INPUT, OUTPUT):
            raise ValueError(mode)
        self._mode = mode

    def _getmode(self):
        return self._mode

    mode = property(fget=_getmode, fset=_setmode)
    # pylint: enable=W0201


class Simardui(QObject):
    def __init__(self):
        QObject.__init__(self)
        self.pins = tuple(Pin() for index in xrange(ARDUINO_DIGITAL_PIN_NB))
        self.started = self.alive = False

    def start(self):
        self.started = False
        if self.alive:
            return
        self.live()

    def live(self):
        self.alive = True
        while True:
            self.setup()
            while self.started:
                self.loop()

    def digitalWrite(self, index, value):
        self.pins[index].digitalWrite(value)

    def digitalRead(self, index):
        return self.pins[index].digitalRead()

    def pinMode(self, index, mode):
        self.pins[index].mode = mode

    @abstractmethod
    def setup(self):
        self.started = True

    @abstractmethod
    def loop(self):
        pass


class Mysim(Simardui):
    def setup(self):
        for index in xrange(PIN_NB):
            self.pinMode(index, OUTPUT)
        Simardui.setup(self)

    def loop(self):
        for number in xrange(COMBINATIONS):
            self.emit(_LOOPMSGSIGNAL, u"evaluating 0x%.2x" % number)
            for index in xrange(PIN_NB):
                if not self.started:
                    return
                pinvalue = 1 << index
                outputvalue = bool(pinvalue & number)
                self.emit(_LOOPMSGSIGNAL,
                    u"value 0x%.2x -> %s" % (pinvalue, outputvalue)
                    )
                self.digitalWrite(index, outputvalue)
            QThread.msleep(500)

class ArduiThread(QThread):
    def __init__(self, method, *args, **kwargs):
        self.method = method
        self.args = args
        self.kwargs = kwargs
        QThread.__init__(self, None)

    def run(self):
        self.method(*self.args, **self.kwargs)

def getboxbynum(design, num):
    return getattr(design, 'led_%d' % num)

def checkerfactory(design, num):
    box = getboxbynum(design, num)
    def checker(value):
        box.setChecked(value)
    return checker

def main():
    app = QApplication(argv)

    #set up ui
    frame = QFrame()
    leds = Ui_Frame()
    leds.setupUi(frame)

    #the fake proto
    sim = Mysim()
    thread = ArduiThread(sim.start)

    #ui signals -> reset button on the proto and debug messages in the console
    QObject.connect(leds.start, SIGNAL('clicked()'), sim.start)
    QObject.connect(sim, _LOOPMSGSIGNAL, leds.log.append)

    #signals to set box values
    for index in xrange(PIN_NB):
        box = getboxbynum(leds, index)
        QObject.connect(sim.pins[index], _PINSIGNAL, box.setChecked)

    #start it all
    thread.start()
    frame.show()
    app.exec_()

if __name__ == '__main__':
    main()

