import os.path as op
import os
from fsub_extractor.utils.system_utils import *


def trk_to_tck(trk_file, ref, out_dir, overwrite):
    """Converts a .trk file to .tck using DIPY
    Parameters
    ==========
    trk_file: str
            Path to .trk file
    ref: str
            Path to image (.nii.gz) in same space as streamlines
    out_dir: str
            Path to output directory
    overwrite: bool
            Whether to allow overwriting outputs

    Outputs
    =======
    tck_file: str
            Path to output .tck file
    """
    from dipy.io.streamline import load_tractogram, save_tractogram

    trk_loaded = load_tractogram(trk_file, ref)
    filename = op.basename(trk_file).replace(".trk", ".tck")
    tck_file = op.join(out_dir, filename)
    save_tractogram(trk_loaded, tck_file)

    return tck_file


def extract_tck_mrtrix(
    tck_file, rois_in, outpath_base, search_dist, search_type, two_rois, overwrite
):
    """Uses MRtrix tools to extract the TCK file that connects to the ROI(s)
    If the ROI image contains one value, finds all streamlines that connect to that region
    If the ROI image contains two values, finds all streamlines that connect the two regions

    Parameters
    ==========
    tck_file: str
            Path to the input tractography file (.tck)
    rois_in: str
            Atlas-like image (.nii.gz, .nii., .mif) containing all ROIs, each with different intensities
    outpath_base: str
            Path to output directory, including output prefix
    search_dist: float
            How far to search ahead of streamlines for ROIs, in mm
    search_type: string
            Method of searching for streamlines (forward, reverse, or radial).
    two_rois: bool
            True if two ROIs in rois_in, False, if one ROI in rois_in
    overwrite: bool
            Whether to allow overwriting outputs

    Outputs
    =======
    Function returns the path of the extracted tck file
    outpath_base + assignments.txt/connectome.txt describe the streamline-to-node assignments
    outpath_base + extracted.txt is the extracted sub-bundle
    """

    ### tck2connectome
    tck2connectome = find_program("tck2connectome")
    tck2connectome_connectome_out = outpath_base + "connectome.txt"
    tck2connectome_assignments_out = outpath_base + "assignments.txt"
    cmd_tck2connectome = [
        tck2connectome,
        tck_file,
        rois_in,
        tck2connectome_connectome_out,
        "-assignment_" + search_type + "_search",
        search_dist,
        "-out_assignments",
        tck2connectome_assignments_out,
    ]
    if overwrite == False:
        overwrite_check(tck2connectome_assignments_out)
        overwrite_check(tck2connectome_connectome_out)
    else:
        cmd_tck2connectome += ["-force"]
    run_command(cmd_tck2connectome)

    ### connectome2tck
    connectome2tck = find_program("connectome2tck")
    connectome2tck_out = outpath_base + "extracted.tck"
    # Change connectome2tck arguments based on single node or pairwise nodes
    if two_rois:
        nodes = "1,2"
    else:
        nodes = "0,1"
    cmd_connectome2tck = [
        connectome2tck,
        tck_file,
        tck2connectome_assignments_out,
        connectome2tck_out,
        "-nodes",
        nodes,
        "-exclusive",
        "-files",
        "single",
    ]
    if overwrite == False:
        overwrite_check(connectome2tck_out)
    else:
        cmd_connectome2tck += ["-force"]
    run_command(cmd_connectome2tck)

    return connectome2tck_out
