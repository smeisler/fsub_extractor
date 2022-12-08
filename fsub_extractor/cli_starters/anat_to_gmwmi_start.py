import argparse
import os
import os.path as op
from fsub_extractor.utils.anat_utils import anat_to_gmwmi

# Add input arguments
def get_parser():

    parser = argparse.ArgumentParser(
        description="CLI tool for converting anatomical file (FreeSurfer output or T1) to a GMWMI. Also produces the 5TT image as an intermediate file."
    )
    parser.add_argument(
        "--subject",
        help="Subject name. This must match the name in the FreeSurfer folder.",
        required=True,
    )
    parser.add_argument(
        "--anat_path",
        "--anat-path",
        help="Either the path to the FreeSurfer subject's directory (recommended) or path to the subject's T1 image.",
        type=op.abspath,
        required=True,
    )
    parser.add_argument(
        "--threshold",
        help="Threshold (float) above which to binarize GMWMI image. Default is 0.0",
        type=float,
        default=0.0,
    )
    parser.add_argument(
        "--out-dir",
        "--out_dir",
        help="Directory where outputs will be stored (a subject-folder will be created there if it does not exist).",
        type=op.abspath,
        default=os.getcwd(),
    )
    parser.add_argument(
        "--overwrite",
        help="Whether to overwrite outputs. Default is to overwrite.",
        default=True,
        action=argparse.BooleanOptionalAction,
    )

    return parser


def main():

    # Parse arguments and run the main code
    parser = get_parser()
    args = parser.parse_args()
    subject = args.subject
    anat_path = args.anat_path
    out_dir = args.out_dir
    overwrite = args.overwrite

    # Create output directory
    anat_out_dir = op.join(out_dir, subject, "anat")
    os.makedirs(anat_out_dir, exist_ok=True)

    # If anat is a path, get path to subject's FreeSurfer folder
    if op.isdir(op.join(anat_path, subject)):
        anat_path = op.join(anat_path, subject)
        print(f"\n Using {anat_path} as FreeSurfer input for GMWMI creation \n")
    elif anat_path[-7:] == ".nii.gz":
        print(f"\n Using {anat_path} as T1 input for GMWMI creation \n")

    # Run function
    main = anat_to_gmwmi(anat_path, anat_out_dir, overwrite=overwrite)
