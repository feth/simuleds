from abc import abstractmethod
from sys import argv

from PyQt4.QtCore import QObject, QThread, SIGNAL
from PyQt4.QtGui import QApplication, QFrame

from .leds_ui import Ui_Frame


PIN_NB = 5
COMBINATIONS = 1 << PIN_NB


class Simardui(object):
    def __init__(self, log, output_fns):
        self.log = log
        self.output_fns = output_fns
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

    @abstractmethod
    def setup(self):
        self.started = True

    @abstractmethod
    def loop(self):
        pass

class Mysim(Simardui):
    def setup(self):
        for output_fn in self.output_fns:
            output_fn(False)
        Simardui.setup(self)

    def loop(self):
        for number in xrange(COMBINATIONS):
            self.log.append(u"evaluating 0x%.2x" % number)
            for index, pin in enumerate(self.output_fns):
                if not self.started:
                    return
                pinvalue = 1 << index
                outputvalue = bool(pinvalue & number)
                self.log.append(
                    u"value 0x%.2x -> %s" % (pinvalue, outputvalue)
                    )
                pin(outputvalue)
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
    frame = QFrame()
    leds = Ui_Frame()
    leds.setupUi(frame)

    outputs = tuple(
        checkerfactory(leds, num)
        for num in xrange(PIN_NB)
        )

    sim = Mysim(leds.log, outputs)
    thread = ArduiThread(sim.start)
    QObject.connect(leds.start, SIGNAL('clicked()'), sim.start)
    thread.start()
    frame.show()
    app.exec_()

if __name__ == '__main__':
    main()

