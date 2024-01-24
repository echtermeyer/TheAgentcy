import sys
import argparse

from PySide6.QtWidgets import QApplication

from src.gui import Gui
from src.pipeline import Pipeline


def run(command_line_args):
    """
    Default entry point for the application. If the user passes the -dg flag, the GUI will be disabled and the
    application will run in terminal only. If the user passes the -ff flag, the application will run in fast-forward
    mode, meaning that the user interaction with the orchestrator will be skipped and a predefined use-case will be
    executed.
    """
    if command_line_args.disable_gui:
        # Start terminal only
        pipeline = Pipeline(command_line_args)
        pipeline.start()
    else:
        # Start GUI
        app = QApplication(sys.argv)
        main_window = Gui(command_line_args)
        main_window.show()
        sys.exit(app.exec())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="argparse")

    parser.add_argument(
        "-ff",
        "--fast_forward",
        action="store_true",
        help="Pass this flag to skip the user interaction with the orchestrator and use a predefined use-case",
        required=False,
    )

    parser.add_argument(
        "-dg",
        "--disable_gui",
        action="store_true",
        help="Pass this flag to disable GUI and run in terminal only",
        required=False,
    )

    run(parser.parse_args())
