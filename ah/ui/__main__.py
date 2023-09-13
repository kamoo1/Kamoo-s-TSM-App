import sys
import logging

from PyQt5.QtWidgets import QApplication

from ah import config
from ah.ui.main_controller import Window

if __name__ == "__main__":
    logging.basicConfig(level=config.LOGGING_LEVEL)
    app = QApplication(sys.argv)
    win = Window()
    win.show()
    sys.exit(app.exec())
