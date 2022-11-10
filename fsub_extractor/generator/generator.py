import argparse
import os
import os.path as op
from dipy.tracking.streamline import orient_by_rois
from dipy.io.image import load_nifti, load_nifti_data
from dipy.io.streamline import load_tractogram
from fsub_extractor.utils.utils import (
    run_command,
    overwrite_check,
    find_program,
    anat_to_gmwmi,
    project_roi,
    intersect_gmwmi,
)

# Add input arguments
def get_parser():

    parser = argparse.ArgumentParser(
        description="Extracts tract-average and along-the-tract measures of input scalar metrics (.nii.gz) for a specified streamline file (.tck/.trk)."
    )
    parser.add_argument(
        "--subject", help="Subject name.", type=str, required=True,
    )
    parser.add_argument(
        "--roi1",
        help="Binary ROI that will be used to denote where streamlines begin/end",
        type=op.abspath,
        required=True,
    )
    parser.add_argument(
        "--roi2",
        help="Binary ROI that will be used to denote where streamlines begin/end",
        type=op.abspath,
        required=True,
    )
    parser.add_argument(
        "--out-dir",
        "--out_dir",
        help="Directory where outputs will be stored (a subject-folder will be created there if it does not exist).",
        type=op.abspath,
        default=os.getcwd(),
    )
    parser.add_argument(
        "--out-prefix",
        "--out_prefix",
        help="Prefix for all output files. Default is no prefix.",
        type=str,
        default="",
    )
    # parser.add_argument(
    #    "--scratch",
    #    "--scratch",
    #    help="Path to scratch directory. Default is current directory.",
    #    type=op.abspath,
    #    default=os.getcwd(),
    # )
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

    main = streamline_scalar(
        subject=args.subject,
        roi1=args.roi2,
        roi2=args.roi2,
        out_dir=args.out_dir,
        out_prefix=args.out_prefix,
        # scratch=args.scratch,
        overwrite=args.overwrite,
    )


def generator(
    subject,
    roi1,
    roi2,
    out_dir,
    out_prefix,
    # scratch,
    overwrite,
):

    # TODO: add docs

    ### Check for assertion errors ###

    # If .trk, use first scalar as reference file for conversion to .tck
    trk_ref = scalar_path_list[0]
    print(f"\n Using {trk_ref} as reference anatomy image. \n")
    if tract[-4:] == ".trk":
        print("\n Converting .trk to .tck \n")
        tck_file = trk_to_tck(tract, trk_ref, out_dir, overwrite)
    else:
        tck_file = tract
    # Make sure number of points for tract profile is not negative
    if n_points < 2:
        raise Exception(
            "Number of points ({n_points}) must be an integer larger than 1."
        )
    # Check if out and scratch directories exist
    if op.isdir(out_dir) == False:
        raise Exception(f"Output directory {out_dir} not found on the system.")
    # if op.isdir(scratch) == False:
    #    raise Exception(f"Scratch directory {scratch} not found on the system.")

    ### Prepare output directories ###
    # Add an underscore to separate prefix from file names if a prefix is specified
    if len(out_prefix) > 0:
        if out_prefix[-1] != "_":
            out_prefix += "_"

    # Make subject output and scratch folders if they do not exist, and define the naming convention
    if op.isdir(op.join(out_dir, subject)) == False:
        os.mkdir(op.join(out_dir, subject))
    # if op.isdir(op.join(scratch, subject + "_scratch")) == False:
    #    os.mkdir(op.join(scratch, subject + "_scratch"))
    subject_base = op.join(out_dir, subject)
    outpath_base = op.join(subject_base, out_prefix)
    # scratch_base = op.join(scratch, subject + "_scratch", out_prefix)

    print("\n DONE \n")
