import pathlib

from dinora import DEFAULT_WEIGHTS
from dinora.cli_utils import Args, Subparsers
from dinora.bench.selfplay import selfplay


def build_parser(subparsers: Subparsers) -> None:
    parser = subparsers.add_parser(name="bench", help="Benchmark speed of engine")
    parser.add_argument(
        "--model",
        default="alphanet",
        help="Name of the model to use",
    )
    parser.add_argument(
        "--weights",
        default=DEFAULT_WEIGHTS,
        help="Path to model weights",
        type=pathlib.Path,
    )
    parser.add_argument(
        "--device",
        default="cuda",
    )


def run_cli(args: Args) -> None:
    selfplay(args.model, args.weights, args.device)