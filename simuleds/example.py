from sys import argv

from PyQt4.QtGui import QApplication

from .simuleds import Interface, OUTPUT, Simardui, delay

PIN_NB = 5
COMBINATIONS = 1 << PIN_NB

class Mysim(Simardui):
    def setup(self):
        for index in xrange(PIN_NB):
            self.pinMode(index, OUTPUT)

        #call parent
        Simardui.setup(self)

    def loop(self):
        for number in xrange(COMBINATIONS):
            self.log(u"evaluating 0x%.2x" % number)
            for index in xrange(PIN_NB):

                #HERE IS THE BREAK FOR THE RESET SWITCH
                if not self.started:
                    return
                #END RESET DIRTY HACK

                pinvalue = 1 << index
                outputvalue = bool(pinvalue & number)
                self.log(u"value 0x%.2x -> %s" % (pinvalue, outputvalue))
                self.digitalWrite(index, outputvalue)
            delay(500)

def main():
    app = QApplication(argv)

    #set up ui
    frame = Interface()
    frame.show()

    #bind to my ui
    frame.setsim(Mysim())

    app.exec_()

if __name__ == '__main__':
    main()

