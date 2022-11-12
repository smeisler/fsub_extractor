import os
import os.path as op
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from dipy.tracking.streamline import orient_by_rois
import dipy.stats.analysis as dsa
from dipy.io.image import load_nifti, load_nifti_data
from dipy.io.streamline import load_tractogram
from fsub_extractor.utils.system_utils import (
    run_command,
    overwrite_check,
    find_program,
)
from fsub_extractor.utils.streamline_utils import trk_to_tck


def streamline_scalar(
    subject,
    tract,
    # roi_begin,
    # roi_end,
    scalar_paths,
    scalar_names,
    n_points,
    out_dir,
    out_prefix,
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
    # Check if output directories exist
    if op.isdir(out_dir) == False:
        raise Exception(f"Output directory {out_dir} not found on the system.")

    ### Prepare output directories ###
    # Add an underscore to separate prefix from file names if a prefix is specified
    if len(out_prefix) > 0:
        if out_prefix[-1] != "_":
            out_prefix += "_"

    # Make output folders if they do not exist, and define the naming convention
    anat_out_dir = op.join(out_dir, subject, "anat")
    dwi_out_dir = op.join(out_dir, subject, "dwi")
    func_out_dir = op.join(out_dir, subject, "func")
    os.makedirs(anat_out_dir, exist_ok=True)
    os.makedirs(dwi_out_dir, exist_ok=True)
    os.makedirs(func_out_dir, exist_ok=True)
    anat_out_base = op.join(anat_out_dir, out_prefix)
    dwi_out_base = op.join(dwi_out_dir, out_prefix)
    func_out_base = op.join(func_out_dir, out_prefix)

    ### Reorient streamlines so beginning of each streamline are at the same end
    tract_loaded = load_tractogram(tract, trk_ref).streamlines
    # TODO: See if we need to reorient streamlines, and how
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
        plt.xlabel("Node along Bundle")
        profile_fig_outfile = dwi_out_base + scalar_name + "_profile.png"
        if overwrite == False:
            overwrite_check(profile_fig_outfile)
        plt.savefig(profile_fig_outfile)

        ### Calculate tract average scalar
        # Start by finding average per streamline with 'tcksample'
        print(f"\n Calculating tract-average summary stats for {scalar_name} \n")
        tcksample = find_program("tcksample")
        tcksample_out = dwi_out_base + scalar_name + "_streamline_means.csv"

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
        stats_outfile = dwi_out_base + scalar_name + "_stats.txt"
        if overwrite == False:
            overwrite_check(stats_outfile)
        stats_outfile_object = open(stats_outfile, "w")
        stats_string = f"Tract: {tract} \nNumber of Streamlines: {n_streamlines} \nScalar: {scalar_path} \nMean: {tract_avg} \nMedian: {tract_med} \nStandard Deviation: {tract_std} \nTract Profile: {profile_bundle} \nProfile Length: {n_points}"
        stats_outfile_object.write(stats_string)
        stats_outfile_object.close()

    print("\n DONE \n")
