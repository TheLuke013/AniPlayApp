import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont

from app import AniPlayApp

def main():    
    app = QApplication(sys.argv)
    font = QFont("Arial", 10)
    app.setFont(font)
    aniplay = AniPlayApp()
    aniplay.showMaximized()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()