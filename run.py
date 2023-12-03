import argparse

from src.pipeline import Pipeline


def run(args):
    pipeline = Pipeline(args.description)
    pipeline.start()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="argparse")
    parser.add_argument(
        "-d",
        "--description",
        type=str,
        default="No webapp yet",
        help="Full-stack webapp description",
        required=True,
    )

    run(parser.parse_args())
