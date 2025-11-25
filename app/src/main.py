import sys
import ctypes
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon, QFont

from app import AniPlayApp

import os
os.environ["QT_MULTIMEDIA_BACKEND"] = "ffmpeg"  # Força usar ffmpeg
os.environ["QT_OPENGL"] = "software"  # Desativa OpenGL
os.environ["QMLSCENE_DEVICE"] = "softwarecontext"  # Contexto software

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