import sys
import ctypes
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon, QFont

from app import AniPlayApp

def main():
    myappid = 'thrillerempress.aniplay_app'
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

    app = QApplication(sys.argv)
    font = QFont("Arial", 10)
    app.setFont(font)
    app.setWindowIcon(QIcon("./icon.ico"))
    aniplay = AniPlayApp()
    aniplay.showMaximized()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()