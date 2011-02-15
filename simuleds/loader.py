from sys import argv, stderr
from traceback import print_exc

from PyQt4.QtGui import QApplication, QFileDialog, QMessageBox

from .simuleds import Interface, Simardui, SimException


def simfactory(name, filename):
    setup = None
    loop = None

    with open(filename, 'r') as fdesc:
        source = fdesc.read()
        code = compile(source, filename, 'exec')


        for value in code.co_consts:
            if not hasattr(value, 'co_name'):
                continue
            elif value.co_name == 'setup':
                setup = value
            elif value.co_name == 'loop':
                loop = value

    if None in (setup, loop):
        raise SimException(
            "Python source file '%s' does not contain setup AND "
            "loop functions (required)." % filename
            )
    for func in setup, loop:
        if func.co_argcount != 0:
            raise SimException(
                "In Python source file '%s', function '%s' "
                "should not take args." % (filename, func.co_name)
                )

    Simobject = type(name, (Simardui, ), {'setup': setup, 'loop': loop})

    return Simobject

def getsim():
    while True:
        filename = unicode(QFileDialog.getOpenFileName())
        if not filename:
            QMessageBox.warning(
                None, "Abort simuleds",
                "Aborting, you did not specify a file."
                )
            return
        print "opening file", filename

        try:
            simklass = simfactory('my pony sim', filename)
        except (SyntaxError, TypeError), err:
            print_exc(stderr)
            QMessageBox.warning(
                None, "Error",
                "File '%s' looks like an invalid Python source." % filename
                )
            continue
        except Exception, err:
            print_exc(stderr)
            QMessageBox.warning(None, "Error", unicode(err))
            continue
        return simklass

def main():

    app = QApplication(argv)

    simklass = getsim()
    if not simklass:
        return

    #set up ui
    frame = Interface()
    frame.show()

    #bind to my ui
    frame.setsim(simklass())

    app.exec_()


if __name__ == '__main__':
    main()
