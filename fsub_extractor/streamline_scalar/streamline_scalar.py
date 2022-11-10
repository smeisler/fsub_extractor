import argparse
import os
import os.path as op
import pandas as pd
import numpy as np
from dipy.tracking.streamline import orient_by_rois
import dipy.stats.analysis as dsa
from dipy.io.image import load_nifti, load_nifti_data
from dipy.io.streamline import load_tractogram
from fsub_extractor.utils.utils import (
    run_command,
    overwrite_check,
    trk_to_tck,
    find_program,
)
import matplotlib.pyplot as plt

# Add input arguments
def get_parser():

    parser = argparse.ArgumentParser(
        description="Extracts tract-average and along-the-tract measures of input scalar metrics (.nii.gz) for a specified streamline file (.tck/.trk)."
    )
    parser.add_argument(
        "--subject", help="Subject name.", type=str, required=True,
    )
    parser.add_argument(
        "--tract",
        help="Path to tract file (.tck or .trk). Should be in the same space as the scalar map inputs.",
        type=op.abspath,
        required=True,
    )
    parser.add_argument(
        "--scalar_paths",
        "--scalar-paths",
        help="Comma delimited list (no spaces) of path(s) to scalar maps (e.g. /path/to/FA.nii.gz). This will also be used as a spatial reference file is a .trk file is passed in as a streamlines object.",
        required=True,
    )
    parser.add_argument(
        "--scalar_names",
        "--scalar-names",
        help="Comma delimited list (no spaces) of names to scalar maps (e.g. FA). The number of names must match the number of scalar paths",
        required=True,
    )
    parser.add_argument(
        "--roi_begin",
        "--roi-begin",
        help="Binary ROI that will be used to denote where streamlines begin (lower number nodes on tract profiles)",
        type=op.abspath,
        # required=True,
    )
    parser.add_argument(
        "--roi_end",
        "--roi-end",
        help="Binary ROI that will be used to denote where streamlines end (higher number nodes on tract profiles)",
        type=op.abspath,
        # required=True,
    )
    parser.add_argument(
        "--n_points",
        "--n-points",
        help="Number of nodes to use in tract profile (default is 100)",
        type=int,
        default=100,
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
    parser.add_argument(
        "--scratch",
        "--scratch",
        help="Path to scratch directory. Default is current directory.",
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

    main = streamline_scalar(
        subject=args.subject,
        tract=args.tract,
        roi_begin=args.roi_begin,
        roi_end=args.roi_end,
        scalar_paths=args.scalar_paths,
        scalar_names=args.scalar_names,
        n_points=args.n_points,
        out_dir=args.out_dir,
        out_prefix=args.out_prefix,
        scratch=args.scratch,
        overwrite=args.overwrite,
    )


def streamline_scalar(
    subject,
    tract,
    roi_begin,
    roi_end,
    scalar_paths,
    scalar_names,
    n_points,
    out_dir,
    out_prefix,
    scratch,
    overwrite,
):

    # TODO: add docs

    ### Split string of scalars to lists
    scalar_path_list = [op.abspath(scalar) for scalar in scalar_paths.split(",")]
    scalar_name_list = scalar_names.split(",")

    # Make sure number of scalar paths equal number of scalar names
    if len(scalar_path_list) != len(scalar_name_list):
        raise Exception("Number of scalar images and scalar names do not match")

    # Check that scalars exist
    for scalar in scalar_path_list:
        if op.exists(scalar) == False:
            raise Exception(f"Scalar map {scalar} not found on the system.")

    ### Check for assertion errors ###
    # Make sure tract file is okay
    if op.exists(tract) == False:
        raise Exception(f"Tract file {tract} is not found on the system.")
    if tract[-4:] not in [".trk", ".tck"]:
        raise Exception(f"Tract file {tract} is not of a supported file type.")
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
    if op.isdir(scratch) == False:
        raise Exception(f"Scratch directory {scratch} not found on the system.")

    ### Prepare output directories ###
    # Add an underscore to separate prefix from file names if a prefix is specified
    if len(out_prefix) > 0:
        if out_prefix[-1] != "_":
            out_prefix += "_"

    # Make subject output and scratch folders if they do not exist, and define the naming convention
    if op.isdir(op.join(out_dir, subject)) == False:
        os.mkdir(op.join(out_dir, subject))
    if op.isdir(op.join(scratch, subject + "_scratch")) == False:
        os.mkdir(op.join(scratch, subject + "_scratch"))
    subject_base = op.join(out_dir, subject)
    outpath_base = op.join(subject_base, out_prefix)
    scratch_base = op.join(scratch, subject + "_scratch", out_prefix)

    ### Reorient streamlines so beginning of each streamline are at the same end
    tract_loaded = load_tractogram(tract, trk_ref).streamlines
    # trk_ref_img, ref_affine = load_nifti(trk_ref)
    # roi_begin_img = load_nifti_data(roi_begin)
    # roi_end_img = load_nifti_data(roi_end)
    # oriented_bundle = orient_by_rois(
    #   tract_loaded,
    #   ref_affine,
    #   roi_begin_img,
    #   roi_end_img)

    # Calculate bundle weights and the profile
    # weights_bundle = dsa.gaussian_weights(oriented_bundle)
    weights_bundle = dsa.gaussian_weights(tract_loaded, n_points=n_points)

    for scalar_path, scalar_name in zip(scalar_path_list, scalar_name_list):

        print(f"\n Processing scalar {scalar_path} under name {scalar_name} \n")

        # Calculate tract profile
        print(f"\n Calculating tract profile for {scalar_name} \n")
        scalar_img, scalar_affine = load_nifti(scalar_path)
        profile_bundle = dsa.afq_profile(
            scalar_img,
            tract_loaded,
            scalar_affine,
            weights=weights_bundle,
            n_points=n_points,
            orient_by=tract_loaded[0],
        )
        # Save out plot
        plt.plot(profile_bundle)
        plt.ylabel(scalar_name)
        plt.xlabel("Node along bundle")
        profile_fig_outfile = op.join(subject_base, scalar_name + "_profile.png")
        plt.savefig(profile_fig_outfile)
        # TODO: SAVE OUT CSV AND PLOT

        ### Calculate tract average scalar
        # Start by finding average per streamline with 'tcksample'
        print(f"\n Calculating tract-average summary stats for {scalar_name} \n")
        tcksample = find_program("tcksample")
        tcksample_out = op.join(subject_base, scalar_name + "_streamline_means.csv")

        cmd_tcksample = [
            tcksample,
            tck_file,
            scalar_path,
            tcksample_out,
            "-stat_tck",
            "mean",
        ]
        if overwrite == False:
            overwrite_check(tcksample_out)
        else:
            cmd_tcksample += ["-force"]
        run_command(cmd_tcksample)

        # Load per-streamline averages, average across streamlines to get whole track mean
        streamline_avgs = pd.read_csv(tcksample_out, skiprows=1)
        streamline_avgs_num = [
            float(avg.removesuffix(".1")) for avg in streamline_avgs.columns
        ]
        # Calculate summary stats across streamlines
        tract_avg = np.mean(streamline_avgs_num)
        tract_std = np.std(streamline_avgs_num)
        tract_med = np.median(streamline_avgs_num)
        n_streamlines = len(streamline_avgs_num)
        # Write summary stats to outfile
        stats_outfile = op.join(subject_base, scalar_name + "_stats.txt")
        stats_outfile_object = open(stats_outfile, "w")
        stats_string = f"Mean: {tract_avg} \nMedian: {tract_med} \nStandard Deviation: {tract_std} \nTract Profile: {profile_bundle} \nNumber of Streamlines: {n_streamlines}"
        stats_outfile_object.write(stats_string)
        stats_outfile_object.close()

    print("\n DONE \n")
