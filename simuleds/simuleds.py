from traceback import format_exc
from imp import find_module, load_module
from os.path import split

from PyQt4.QtCore import QObject, QThread, SIGNAL
from PyQt4.QtGui import QFileDialog, QMessageBox
from PyQt4.QtGui import QFrame

from . import api
from .leds_ui import Ui_Frame
from .api import delay, NOTUSED, OUTPUT, INPUT, SimException


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

    def __init__(self):
        QObject.__init__(self)
        self.pins = tuple(Pin() for index in xrange(api.ARDUINO_DIGITAL_PIN_NB))
        self.started = self.alive = False

    def reset(self):
        self.started = False
        self.log('<b>reset!</b>')

    def stop(self):
        self.alive = False
        self.started = False

    def isresetting(self):
        return not self.started

    def start(self):
        for pin in self.pins:
            pin.mode = OUTPUT
            pin.digitalWrite(True)
            delay(50)
            pin.digitalWrite(False)
            pin.mode = NOTUSED
        self.alive = True
        while self.alive:
            self._setup()
            while self.started:
                self.loop()

    def digitalWrite(self, index, value):
        self.pins[index].digitalWrite(value)

    def digitalRead(self, index):
        return self.pins[index].digitalRead()

    def pinMode(self, index, mode):
        self.pins[index].mode = mode

    def _setup(self):
        self.setup()
        self.started = True

    def log(self, message):
        self.emit(_LOOPMSGSIGNAL, '<span>%s</span><br/>' % message)


class ArduiThread(QThread):
    def __init__(self, start, stop, *args, **kwargs):
        self.start_fun = start
        self.stop_fun = stop
        self.args = args
        self.kwargs = kwargs
        QThread.__init__(self, None)

    def run(self):
        self.start_fun(*self.args, **self.kwargs)

    def stop(self):
        self.stop_fun()

def simfactory(name, filename):
    """
    Builds a sim from a filename
    """
    if filename.endswith('.py'):
        module = filename[:-3]
    else:
        module = filename
    path, module = split(module)

    plugin_info = find_module(module, [path,])
    loaded = load_module(name, *plugin_info)

    if not hasattr(loaded, 'setup') or not hasattr(loaded, 'loop'):
        raise SimException(
            "Please give me a Python source with a setup AND a loop functions"
            )

    Simobject = type(
        name, (Simardui, ),
        {'setup': loaded.setup, 'loop': loaded.loop}
        )

    return Simobject


class Interface(QFrame):
    def __init__(self, parent=None):
        QFrame.__init__(self, parent)
        self.design = Ui_Frame()
        self.design.setupUi(self)
        self.thread = None
        self._setupsignals()
        self.old_thread = None
        self.sim = None

    def _setupsignals(self):
        #ui signals -> load a firmware
        self.connect(self.design.load, SIGNAL('clicked()'), self.loadfile)

    def getboxbynum(self, num):
        return getattr(self.design, 'led_%d' % num)

    def setsim(self, sim):
        if self.thread:
            self.thread.stop()
            self.thread.terminate()
            self.thread.wait()

        if self.sim:
            self._disconnectsim(sim)
        self._connectsim(sim)

        self.old_thread = self.thread
        self.thread = ArduiThread(sim.start, sim.stop)
        self.thread.start()
        self.sim = sim

    def reset(self):
        if not self.sim:
            return
        self.sim.reset()

    def _connectsim(self, sim):
        #ui signals -> logs
        QObject.connect(sim, _LOOPMSGSIGNAL, self.design.log.append)

        #ui signals -> reset button on the proto
        QObject.connect(self.design.start, SIGNAL('clicked()'), self.reset)

        #signals to set box values
        for index in xrange(api.ARDUINO_DIGITAL_PIN_NB):
            box = self.getboxbynum(index)
            QObject.connect(sim.pins[index], _PINSIGNAL, box.setChecked)

    def _disconnectsim(self, sim):
        #ui signals -> logs
        QObject.disconnect(sim, _LOOPMSGSIGNAL, self.design.log.append)

        #ui signals -> reset button on the proto
        QObject.disconnect(self.design.start, SIGNAL('clicked()'), sim.start)

        #signals to set box values
        for index in xrange(api.ARDUINO_DIGITAL_PIN_NB):
            box = self.getboxbynum(index)
            QObject.disconnect(sim.pins[index], _PINSIGNAL, box.setChecked)

    def log(self, message, style=''):
        if style != '':
            style = 'style="%s"' % style
        self.design.log.append("<span %s>%s</span><br/>" % (style, message))

    def loadfile(self):
        simklass = self._loadfile()
        if not simklass:
            self.log("Cancel firmware load.")
            return
        else:
            try:
                self.setsim(simklass())
            except:
                self.err(format_exc())
                raise

    def err(self, message):
        self.log(message, style='color=#ff0000;')

    def _loadfile(self):
        """
        Interacts with user to get a sim plugin
        """
        while True:
            filename = unicode(QFileDialog.getOpenFileName())
            if not filename:
                QMessageBox.warning(
                    None, "Abort simuleds",
                    "Aborting, you did not specify a file."
                    )
                return
            self.log("opening file: %s." % filename)

            try:
                simklass = simfactory('my pony sim', filename)
            except (SyntaxError, TypeError), err:
                self.err(format_exc())
                QMessageBox.warning(
                    None, "Error",
                    "File '%s' looks like an invalid Python source." % filename
                    )
                continue
            except Exception, err:
                self.err(format_exc())
                QMessageBox.warning(None, "Error", unicode(err))
                continue
            return simklass

