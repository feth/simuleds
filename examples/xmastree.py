from simuleds.api import OUTPUT, delay, ARDUINO_DIGITAL_PIN_NB


def setup(self):
    for index in xrange(ARDUINO_DIGITAL_PIN_NB):
        self.pinMode(index, OUTPUT)


GROUPS = 3

def loop(self):
    for rotation in xrange(GROUPS):

        #HERE IS THE BREAK FOR THE RESET SWITCH
        if self.isresetting():
            return
        #END RESET DIRTY HACK

        for index in xrange(ARDUINO_DIGITAL_PIN_NB):
            ledgroup = index % GROUPS
            outputvalue = ledgroup == rotation
            self.digitalWrite(index, outputvalue)
        delay(500)

