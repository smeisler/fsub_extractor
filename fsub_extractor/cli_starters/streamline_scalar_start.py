import argparse
import os.path as op
from os import getcwd
from pathlib import Path
from fsub_extractor.functions.streamline_scalar import streamline_scalar

# Add input arguments
def get_parser():

    parser = argparse.ArgumentParser(
        description="Extracts tract-average and along-the-tract measures of input scalar metrics (.nii.gz) for a specified streamline file (.tck/.trk)."
    )
    parser.add_argument(
        "--subject",
        help="Subject name.",
        required=True,
        metavar=("sub-XXX"),
    )
    parser.add_argument(
        "--tract",
        help="Path to tract file (.tck or .trk). Should be in the same space as the scalar map inputs.",
        type=validate_file,
        required=True,
        metavar=("/PATH/TO/TRACT.trk|.tck"),
        action=CheckExt({".trk", ".tck"}),
    )
    parser.add_argument(
        "--scalar_paths",
        "--scalar-paths",
        help="Comma delimited list (no spaces) of path(s) to scalar maps (e.g. /path/to/FA.nii.gz).",
        required=True,
        metavar=("/PATH/TO/SCALAR1.nii.gz,/PATH/TO/SCALAR2.nii.gz..."),
    )
    parser.add_argument(
        "--scalar_names",
        "--scalar-names",
        help="Comma delimited list (no spaces) of names to scalar maps (e.g. Fractional_Anisotropy). The number of names must match the number of scalar paths",
        required=True,
        metavar=("SCALAR1,SCALAR2..."),
    )
    # parser.add_argument(
    #    "--roi_begin",
    #    "--roi-begin",
    #    help="Binary ROI that will be used to denote where streamlines begin (lower number nodes on tract profiles)",
    #    type=op.abspath,
    #    required=True,
    #    metavar=("/PATH/TO/ROI1.nii.gz")
    # )
    # parser.add_argument(
    #    "--roi_end",
    #    "--roi-end",
    #    help="Binary ROI that will be used to denote where streamlines end (higher number nodes on tract profiles)",
    #    type=op.abspath,
    #    required=True,
    #    metavar=("/PATH/TO/ROI1.nii.gz")
    # )
    parser.add_argument(
        "--n_points",
        "--n-points",
        help="Number of nodes to use in tract profile (default is 100)",
        type=check_positive,
        default=100,
        metavar=("POINTS"),
    )
    parser.add_argument(
        "--out-dir",
        "--out_dir",
        help="Directory where outputs will be stored (a subject-folder will be created there if it does not exist). Default is current directory.",
        type=op.abspath,
        default=os.getcwd(),
        metavar=("/PATH/TO/OUTDIR/"),
    )
    parser.add_argument(
        "--out-prefix",
        "--out_prefix",
        help="Prefix for all output files. Default is no prefix.",
        type=str,
        default="",
        metavar=("PREFIX"),
    )
    parser.add_argument(
        "--overwrite",
        help="Whether to overwrite outputs. Default is to overwrite.",
        default=True,
        action=argparse.BooleanOptionalAction,
    )

    return parser


# Check that files exist
def validate_file(arg):
    if (file := Path(arg)).is_file():
        return op.abspath(file)
    else:
        raise FileNotFoundError(arg)


# Function for checking file extensions
def CheckExt(choices):
    class Act(argparse.Action):
        def __call__(self, parser, namespace, fname, option_string=None):
            file_has_valid_ext = False
            for choice in choices:
                len_ext = len(choice)
                if fname[(-1 * len_ext) :] == choice:
                    file_has_valid_ext = True
                    break

            if file_has_valid_ext == False:
                option_string = "({})".format(option_string) if option_string else ""
                parser.error(
                    "file doesn't end with one of {}{}".format(choices, option_string)
                )
            else:
                setattr(namespace, self.dest, fname)

    return Act


# Check for positive values
def check_positive(value):
    value = int(value)
    if value <= 0:
        raise argparse.ArgumentTypeError("%s is not positive" % value)
    return value


def main():

    # Parse arguments and run the main code
    parser = get_parser()
    args = parser.parse_args()

    main = streamline_scalar(
        subject=args.subject,
        tract=args.tract,
        # roi_begin=args.roi_begin,
        # roi_end=args.roi_end,
        scalar_paths=args.scalar_paths,
        scalar_names=args.scalar_names,
        out_dir=args.out_dir,
        out_prefix=args.out_prefix,
        overwrite=args.overwrite,
        n_points=args.n_points,
    )
