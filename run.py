# from src.pipeline import Pipeline
from PySide6.QtWidgets import QApplication
from src.gui import Gui
import argparse
import sys


def run(command_line_args):
    app = QApplication(sys.argv)
    main_window = Gui(command_line_args)
    main_window.show()
    sys.exit(app.exec())

    # pipeline = Pipeline()
    # pipeline.start()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="argparse")
    parser.add_argument(
        "-d",
        "--description",
        type=str,
        default="No webapp yet",
        help="Full-stack webapp description",
        required=False,
    )

    run(parser.parse_args())
