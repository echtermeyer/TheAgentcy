import sys
import json
import time
import argparse

import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

from pathlib import Path
from PySide6.QtWidgets import QApplication

from src.gui import Gui
from src.pipeline import Pipeline


ROOT = Path(__file__).parent


def evaluate(command_line_args):
    if not command_line_args.skip_evaluation:
        if not command_line_args.project:
            raise ValueError("No project name specified. Please add a project name using -p or --project_name")
        
        if command_line_args.disable_gui:
            metrics = []
            for i in range(command_line_args.iterations):
                pipeline = Pipeline(command_line_args, evaluate_index=i)
                try:
                    pipeline.start()
                except Exception as e:
                    print("Execution failed. Skipping this run. Error: ", e)

                metrics.append(pipeline.metrics)
                time.sleep(60)

            (ROOT / "evaluate").mkdir(parents=True, exist_ok=True)
            with open(ROOT / f"evaluate/{command_line_args.project}.json", "w+") as f:
                json.dump(metrics, f)
        else:
            raise ValueError("Evaluation with GUI is not supported due to required user interaction")

    # Visualize the metrics. Also use evaluation runs from before
    visualize_metrics(ROOT / "evaluate")


def _load_datasets(names):
    datasets = {}
    for name in names:
        with open("evaluate/" + name, "r") as f:
            datasets[name.split(".json")[0]] = pd.DataFrame(json.load(f))

    return datasets


def visualize_metrics(folder: Path):
    evaluations = [file.name for file in folder.iterdir() if file.is_file()]
    datasets = _load_datasets(evaluations)

    # Set the Seaborn style
    sns.set(style="whitegrid")

    # Create the figure and grid spec
    fig = plt.figure(figsize=(9, 7))
    gs = fig.add_gridspec(2, 2)

    plt.suptitle("Evaluation of the Multiagent Development Framework\n", size=18)

    # Time Boxplot
    ax_time = fig.add_subplot(gs[0, 0])
    sns.boxplot(
        data=pd.DataFrame(
            {name: dataset["time"] for name, dataset in datasets.items()}
        ),
        ax=ax_time,
    )
    ax_time.set_title("Average Execution Time per Model")
    # ax_time.set_xlabel("Datasets")  # X-axis label
    ax_time.set_ylabel("Time (secs)")  # Y-axis label

    # Human Feedback Boxplot
    ax_feedback = fig.add_subplot(gs[0, 1])
    sns.boxplot(
        data=pd.DataFrame(
            {name: dataset["human_feedback"] for name, dataset in datasets.items()}
        ),
        ax=ax_feedback,
    )
    ax_feedback.set_title("Human Feedback per Model")
    # ax_feedback.set_xlabel("Models")  # X-axis label
    ax_feedback.set_ylabel("Feedback Score")  # Y-axis label

    # Linechart for turns spanning the width of both boxplots
    ax_linechart = fig.add_subplot(gs[1, :])
    for name, dataset in datasets.items():
        database_mean = dataset["turns_database"].mean()
        backend_mean = dataset["turns_backend"].mean()
        frontend_mean = dataset["turns_frontend"].mean()

        # Data for line chart
        line_data = [database_mean, backend_mean, frontend_mean]
        line_labels = ["Database", "Backend", "Frontend"]

        sns.lineplot(x=line_labels, y=line_data, label=name, ax=ax_linechart)
    ax_linechart.set_title("Average Test Iterations for Different Layers")
    # ax_linechart.set_xlabel("System Component")  # X-axis label
    ax_linechart.set_ylabel("Average Test Iterations")  # Y-axis label
    ax_linechart.legend()

    # Adjust layout
    plt.tight_layout()
    plt.savefig("evaluate/evaluation.pdf")
    plt.show()



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
        "-s",
        "--skip_evaluation",
        action="store_true",
        help="Skip the evalation and instantly show the metrics",
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
        required=False,
    )

    evaluate(parser.parse_args())
