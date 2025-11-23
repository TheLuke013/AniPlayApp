import sys
from PySide6.QtWidgets import QApplication

from app import AniPlayApp

def main():    
    app = QApplication(sys.argv)
    aniplay = AniPlayApp()
    aniplay.showMaximized()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()