# simuleds.py
# Copyright (C) 2011 Feth Arezki <feth <A+> tuttu.info>
#
# This module is part of simuleds and is released under the GPLv3
# License: http://www.gnu.org/licenses/gpl-3.0.txt
#
from imp import find_module, load_module
from os.path import dirname, exists, split
from traceback import format_exc

from PyQt4.QtCore import QObject, QSettings, QThread, QVariant, SIGNAL
from PyQt4.QtGui import QFileDialog, QFrame, QMenu, QMessageBox

from . import api
from .api import INPUT, NOTUSED, OUTPUT, SimException, delay
from .leds_ui import Ui_Frame


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

    def dance(self):
        for pin in self.pins:
            pin.mode = OUTPUT
            pin.digitalWrite(True)
            delay(50)
            pin.digitalWrite(False)
            pin.mode = NOTUSED

    def start(self):
        self.alive = True
        while self.alive:
            self.dance()
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
        self.recentsmenu = QMenu()
        self.design.recent.setMenu(self.recentsmenu)
        self.thread = None
        self._setupsignals()
        self.old_thread = None
        self.sim = None
        self.settings = QSettings(
            "Random free software you stump around",
            "simuleds"
            )

        self.recents = list(self._readrecent())
        self._updaterecents()

    def _setupsignals(self):
        #ui signals -> load a firmware
        self.connect(self.design.load, SIGNAL('clicked()'), self.loadfile)

    def getboxbynum(self, num):
        return getattr(self.design, 'led_%d' % num)

    def setsim(self, simklass):
        try:
            self._setsim(simklass())
        except:
            self.err(format_exc())
            raise

    def err(self, message):
        self.log("<b>%s</b>" % message, style='color:#ff0000;')

    def log(self, message, style=''):
        if style != '':
            style = 'style="%s"' % style
        self.design.log.append("<span %s>%s</span><br/>" % (style, message))

    def _setsim(self, sim):
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

    def loadfile(self):
        self.settings.beginGroup("Last opened")
        filename = unicode(self.settings.value("firmware", ".").toString())

        simklass, filename = self._loadfile(filename)
        if not simklass:
            self.log("Cancel firmware load.")
            return
        else:
            self.setsim(simklass)
        self.settings.setValue("firmware", filename)
        self.settings.endGroup()

        self.addrecent(filename)
        self.writerecentlist()

        self.settings.sync()

    def loadfilefactory(self, filename):
        def loadit():
            simklass, unused = self._loadfile(filename, dialog=False)
            if simklass:
                self.setsim(simklass)
            self.addrecent(filename)
        return loadit

    def _updaterecents(self):
        self.design.recent.setEnabled(bool(self.recents))
        self.recentsmenu.clear()
        if not self.recents:
            return
        for item in self.recents:
            self.recentsmenu.addAction(item, self.loadfilefactory(item))

    def _readrecent(self):
        self.settings.beginGroup("Recent files")
        recents = self.settings.value("list", []).toList()
        self.settings.endGroup()
        return self._recentlist(recents)

    def writerecentlist(self):
        self.settings.beginGroup("Recent files")
        self.settings.setValue("list", self.recents)
        self.settings.endGroup()

    def addrecent(self, filename):
        if filename in self.recents:
            self.recents.remove(filename)
        self.recents.insert(0, filename)
        #limit to size 5
        self.recents = self.recents[:5]
        self._updaterecents()

    def _recentlist(self, origlist, mostrecent=''):
        if mostrecent:
            yield mostrecent
            count = 1
        else:
            count = 0
        for item in origlist:
            if isinstance(item, QVariant):
                item = unicode(item.toString())
            if item == mostrecent:
                continue
            yield item
            count += 1
            if count > 5:
                break
    def _loadfile(self, filename, dialog=True):
        """
        Interacts with user to get a sim plugin
        """
        while True:
            if dialog:
                filename = unicode(QFileDialog.getOpenFileName(
                    self,
                    "Choose a firmware",
                    dirname(filename)
                    ))
                if not filename:
                    self.log("Aborting, you did not specify a file.")
                    return None, None
            if not exists(filename):
                self.err("File '%s' does not exist." % filename)
                return None, None
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
            return simklass, filename

