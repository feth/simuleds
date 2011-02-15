from simuleds.api import OUTPUT, delay


PIN_NB = 5
COMBINATIONS = 1 << 5

def setup(self):
    for index in xrange(PIN_NB):
        self.pinMode(index, OUTPUT)


def loop(self):
    for number in xrange(COMBINATIONS):
        self.log(u"evaluating 0x%.2x" % number)
        for index in xrange(PIN_NB):

            #HERE IS THE BREAK FOR THE RESET SWITCH
            if self.isresetting():
                return
            #END RESET DIRTY HACK

            pinvalue = 1 << index
            outputvalue = bool(pinvalue & number)
            self.log(u"value 0x%.2x -> %s" % (pinvalue, outputvalue))
            self.digitalWrite(index, outputvalue)
        delay(500)

