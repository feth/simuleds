from imp import find_module, load_module
from os.path import split
from sys import argv, stderr
from traceback import print_exc

from PyQt4.QtGui import QApplication, QFileDialog, QMessageBox

from .simuleds import Interface, Simardui


def simfactory(name, filename):
    """
    Builds a sim from a filename
    """
    setup = None
    loop = None

    if filename.endswith('.py'):
        module = filename[:-3]
    else:
        module = filename
    path, module = split(module)

    plugin_info = find_module(module, [path,])
    loaded = load_module(name, *plugin_info)

    Simobject = type(name, (Simardui, ), {'setup': loaded.setup, 'loop': loaded.loop})

    return Simobject


def getsim():
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
