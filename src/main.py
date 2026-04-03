import sys

from PyQt6.QtWidgets import QApplication

from .app import ConformalApp


def main() -> None:
	app = QApplication(sys.argv)
	window = ConformalApp()
	window.resize(800, 800)
	window.show()
	sys.exit(app.exec())


if __name__ == "__main__":
	main()
