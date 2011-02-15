from sys import argv

from PyQt4.QtGui import QApplication, QFileDialog

from .simuleds import Interface, Simardui


def simfactory(name, filename):
    setup = lambda: None
    loop = lambda: None

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

    Simobject = type(name, (Simardui, ), {'setup': setup, 'loop': loop})

    return Simobject


def main():

    app = QApplication(argv)

    filename = unicode(QFileDialog.getOpenFileName())
    print "opening file", filename

    PonySim = simfactory('my pony sim', filename)

    #set up ui
    frame = Interface()
    frame.show()

    #bind to my ui
    frame.setsim(PonySim())

    app.exec_()


if __name__ == '__main__':
    main()
