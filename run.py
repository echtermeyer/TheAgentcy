from PySide6.QtWidgets import QApplication
from src.pipeline import Pipeline
from src.gui import Gui
import argparse
import sys


def run(command_line_args):
    print(command_line_args)
    
    if command_line_args.disable_gui:
        pipeline = Pipeline(command_line_args)
        pipeline.start()
    else:
        app = QApplication(sys.argv)
        main_window = Gui(command_line_args)
        main_window.show()
        sys.exit(app.exec())



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

    parser.add_argument(
        "-ff", "--fast_forward",
        action='store_true',
        help="Pass this flag to skip the user interaction with the orchestrator and use a predefined use-case",
        required=False
    )

    parser.add_argument(
        "-dg", "--disable_gui",
        action='store_true',
        help="Pass this flag to disable GUI and run in terminal only",
        required=False
    )

    run(parser.parse_args())
