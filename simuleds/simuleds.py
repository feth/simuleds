from PyQt4.QtCore import QObject, QThread, SIGNAL
from PyQt4.QtGui import QFrame

from . import api
from .leds_ui import Ui_Frame
from .api import NOTUSED, OUTPUT, INPUT, SimException


_PINSIGNAL = SIGNAL('value changed')
_LOOPMSGSIGNAL = SIGNAL('loop message')

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

    plugin_env = dict(
        ARDUINO_DIGITAL_PIN_NB=api.ARDUINO_DIGITAL_PIN_NB,
        delay=api.delay,
        INPUT=api.INPUT,
        NOTUSED=api.NOTUSED,
        OUTPUT=api.OUTPUT,
        )

    def __init__(self):
        QObject.__init__(self)
        self.pins = tuple(Pin() for index in xrange(api.ARDUINO_DIGITAL_PIN_NB))
        self.started = self.alive = False

        plugin_env = self.__class__.plugin_env
        plugin_env.update(dict(
                    digitalWrite=self.digitalWrite,
                    isresetting=self.isresetting,
                    log=self.log,
                    pinMode=self.pinMode,
                    )
                )

        self.plugin_env = plugin_env

    def start(self):
        self.started = False
        if self.alive:
            self.log('<b>reset!</b>')
            return
        self.live()

    def isresetting(self):
        return not self.started

    def live(self):
        self.alive = True
        while True:
            self._setup()
            while self.started:
                exec self.loop in self.plugin_env, locals()

    def digitalWrite(self, index, value):
        self.pins[index].digitalWrite(value)

    def digitalRead(self, index):
        return self.pins[index].digitalRead()

    def pinMode(self, index, mode):
        self.pins[index].mode = mode

    def _setup(self):
        global pinMode
        pinMode = self.pinMode
        exec self.setup in self.plugin_env, locals()
        self.started = True

    def log(self, message):
        self.emit(_LOOPMSGSIGNAL, '<span>%s</span><br/>' % message)


class ArduiThread(QThread):
    def __init__(self, method, *args, **kwargs):
        self.method = method
        self.args = args
        self.kwargs = kwargs
        QThread.__init__(self, None)

    def run(self):
        self.method(*self.args, **self.kwargs)


class Interface(QFrame):
    def __init__(self, parent=None):
        QFrame.__init__(self, parent)
        self.design = Ui_Frame()
        self.design.setupUi(self)

    def getboxbynum(self, num):
        return getattr(self.design, 'led_%d' % num)

    def setsim(self, sim):
        #ui signals -> logs
        QObject.connect(sim, _LOOPMSGSIGNAL, self.design.log.append)

        #ui signals -> reset button on the proto
        QObject.connect(self.design.start, SIGNAL('clicked()'), sim.start)

        #signals to set box values
        for index in xrange(api.ARDUINO_DIGITAL_PIN_NB):
            box = self.getboxbynum(index)
            QObject.connect(sim.pins[index], _PINSIGNAL, box.setChecked)

        self.thread = ArduiThread(sim.start)
        self.thread.start()

