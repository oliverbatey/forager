import argparse
import extract
import summarise
import publish


def parse_args():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(help="sub-command help", dest="command")
    parser_extract = subparsers.add_parser("extract")
    parser_extract.add_argument(
        "-s",
        "--subreddit",
        default="deliveroos",
        help=(
            "Name of the subreddit to the extract data from. Default is 'r/deliveroos'."
        ),
    )
    parser_extract.add_argument(
        "--limit",
        default=10,
        help=("Limit on the number of submissions to extract."),
    )
    parser_extract.add_argument(
        "-o",
        "--output_directory",
        default="extract_output",
        help=("Directory that the extract steps saves Reddit content to."),
    )

    parser_summarise = subparsers.add_parser("summarise")
    parser_summarise.add_argument(
        "-i",
        "--input_directory",
        default="extract_output",
        help=("Directory that the summarise step loads files from."),
    )
    parser_summarise.add_argument(
        "-o",
        "--output_directory",
        default="summarise_output",
        help=("Directory that the publish step saves files to."),
    )
    parser_publish = subparsers.add_parser("summarise")
    parser_publish.add_argument(
        "-i",
        "--input_directory",
        default="extract_output",
        help=("Directory that the publish step loads files from."),
    )
    parser_publish.add_argument(
        "-o",
        "--output_directory",
        default="summarise_output",
        help=("Directory that the publish step saves files to."),
    )
    return parser.parse_args()


def main():
    args = parse_args()
    if args.command == "extract":
        extract.main(
            subreddit_name=args.subreddit,
            limit=args.limit,
            output_directory=args.output_directory,
        )
    elif args.command == "summarise":
        summarise.main(
            input_directory=args.input_directory, output_directory=args.output_directory
        )
    elif args.command == "publish":
        publish.main(
            input_directory=args.input_directory, output_directory=args.output_directory
        )
    else:
        raise ValueError(
            f"Unknown command: '{getattr(args, 'command', None)}', use --help to get possible commands"
        )


if __name__ == "__main__":
    main()
