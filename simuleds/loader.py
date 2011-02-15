from sys import argv

from PyQt4.QtGui import QApplication

from .simuleds import Interface

def main():

    app = QApplication(argv)
    frame = Interface()
    frame.show()
    app.exec_()

