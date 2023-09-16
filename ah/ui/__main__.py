import sys
import logging
import traceback

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import qFatal

from ah import config
from ah.ui.main_controller import Window

sys._excepthook = sys.excepthook


def application_exception_hook(exctype, value, tb):
    # StackOverflow
    # https://stackoverflow.com/questions/45488531

    # write to log file
    with open("crash.log", "w") as f:
        traceback.print_exception(exctype, value, tb, file=f)

    sys._excepthook(exctype, value, tb)

    # somehow app does not exit with a custom excepthook,
    # maybe it only happens with threads. we'd do it manually.
    # also, sys.exit() does not work here.
    qFatal("Exiting due to uncaught exception")


sys.excepthook = application_exception_hook

if __name__ == "__main__":
    # create logger with lowest level, with stream handler.
    # we do this because there will be another handler that
    # displays logs on the GUI with adjustable level.
    logging.basicConfig(level=logging.NOTSET)
    logger = logging.getLogger()
    logger.handlers[0].setLevel(config.LOGGING_LEVEL)

    app = QApplication(sys.argv)
    win = Window()
    win.show()
    sys.exit(app.exec())
