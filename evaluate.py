import sys
import json
import argparse

from pathlib import Path
from PySide6.QtWidgets import QApplication

from src.gui import Gui
from src.pipeline import Pipeline

# TODO: visualize the metrics


def evaluate(command_line_args):
    if command_line_args.disable_gui:
        metrics = []
        for _ in range(command_line_args.iterations):
            pipeline = Pipeline(command_line_args, evaluate=True)
            pipeline.start()

            metrics.append(pipeline.metrics)

        root = Path("evaluate")
        root.mkdir(parents=True, exist_ok=True)
        with open(root / f"{command_line_args.project}.json", "w+") as f:
            json.dump(metrics, f)

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
        "-ff",
        "--fast_forward",
        action="store_true",
        default="-ff",
        help="Pass this flag to skip the user interaction with the orchestrator and use a predefined use-case",
        required=False,
    )

    parser.add_argument(
        "-dg",
        "--disable_gui",
        action="store_true",
        default="-dg",
        help="Pass this flag to disable GUI and run in terminal only",
        required=False,
    )

    parser.add_argument(
        "-i",
        "--iterations",
        type=int,
        default=10,
        help="Set the number of iterations to run the evaluation for",
        required=False,
    )

    parser.add_argument(
        "-p",
        "--project",
        type=str,
        help="Set the project name to run the evaluation for",
        required=True,
    )

    evaluate(parser.parse_args())
