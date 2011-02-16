"""
example of a binary counter from 0 to 31.

Produces:
00000
00001
00010
...
11111

cpp version
-----------

int PIN_NB = 5;
int COMBINATIONS = 1 << 5;

void setup()
  {
  for (int index=0 ; index < PIN_NB ; index++)
    {
    pinMode(index, OUTPUT);
    }

  }


void loop()
  {
  for (int number=0 ; number < COMBINATIONS ; number++)
    {
    for (int index=0 ; number < PIN_NB ; index++)
      {
      int pinvalue = 1 << index;
      if (pinvalue & number)
        {
        digitalWrite(index, HIGH);
        } else {
        digitalWrite(index, LOW);
        }
      }
    delay(500);
  }

"""

from simuleds.api import OUTPUT, delay


PIN_NB = 5
COMBINATIONS = 1 << 5

def setup(self):
    for index in xrange(PIN_NB):
        self.pinMode(index, OUTPUT)


def loop(self):
    for number in xrange(COMBINATIONS):
        self.log(u"evaluating %.2d=0x%.2x" % (number, number))
        for index in xrange(PIN_NB):

            #HERE IS THE BREAK FOR THE RESET SWITCH
            if self.isresetting():
                return
            #END RESET DIRTY HACK

            pinvalue = 1 << index
            outputvalue = bool(pinvalue & number)
            self.log(u"led_%d w/ val %.2d=0x%.2x: %s" %
                (index, pinvalue, pinvalue, 'HIGH' if outputvalue else 'LOW')
                )
            self.digitalWrite(index, outputvalue)
        delay(500)

