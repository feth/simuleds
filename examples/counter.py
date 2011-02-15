
def setup():
    PIN_NB = 5
    COMBINATIONS = 1 << PIN_NB
    for index in xrange(PIN_NB):
        pinMode(index, OUTPUT)


def loop():
    PIN_NB = 5
    COMBINATIONS = 1 << PIN_NB
    for number in xrange(COMBINATIONS):
        log(u"evaluating 0x%.2x" % number)
        for index in xrange(PIN_NB):

            #HERE IS THE BREAK FOR THE RESET SWITCH
            if isresetting():
                return
            #END RESET DIRTY HACK

            pinvalue = 1 << index
            outputvalue = bool(pinvalue & number)
            log(u"value 0x%.2x -> %s" % (pinvalue, outputvalue))
            digitalWrite(index, outputvalue)
        delay(500)

def dumb():
    print "in dumb"

