"""Entry point: build the controller and GUI, then run the Qt event loop."""

from __future__ import annotations

import sys

from PyQt6.QtWidgets import QApplication

from app.controller import Controller
from gui.main_window import MainWindow


def main() -> int:
    app = QApplication(sys.argv)
    controller = Controller()
    window = MainWindow(controller)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
