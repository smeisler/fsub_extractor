import os.path as op
import os
from fsub_extractor.utils.system_utils import *


def trk_to_tck(trk_file, out_dir=os.getcwd(), overwrite=True):
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
    import nibabel.filebasedimages

    # trk_loaded = load_tractogram(trk_file, ref)
    trk_loaded = load_tractogram(trk_file, "same")
    filename = op.basename(trk_file).replace(".trk", ".tck")
    tck_file = op.join(out_dir, filename)
    save_tractogram(trk_loaded, tck_file)

    return tck_file


def extract_tck_mrtrix(
    tck_file,
    rois_in,
    outpath_base,
    two_rois,
    search_dist=3.0,
    search_type="forward",
    sift2_weights=None,
    exclude_mask=None,
    include_mask=None,
    streamline_mask=None,
    overwrite=True,
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
    sift2_weights: str
            Path to SIFT2 weights CSV file
    exclude_mask: str
            Path to streamline exclusion mask (.nii.gz). Streamlines leaving this mask will be discarded
    overwrite: bool
            Whether to allow overwriting outputs

    Outputs
    =======
    Function returns the path of the extracted tck file
    outpath_base + assignments.txt/connectome.txt describe the streamline-to-node assignments
    outpath_base + extracted.tck is the extracted sub-bundle
    outpath_base + extracted_masked.tck is the extracted bundle after applying exclusion masking (if masking is done)
    *_weights.csv files are the SIFT2 weights for the extracted and masked bundles
    """

    ### tck2connectome
    tck2connectome = find_program("tck2connectome")
    tck2connectome_connectome_out = outpath_base + "_desc-connectome.txt"
    tck2connectome_assignments_out = outpath_base + "_desc-assignments.txt"
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
    if sift2_weights != None:
        cmd_tck2connectome += ["-tck_weights_in", sift2_weights]
    run_command(cmd_tck2connectome)

    ### connectome2tck
    connectome2tck = find_program("connectome2tck")
    connectome2tck_out = outpath_base + "_desc-fsub.tck"
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
    if sift2_weights != None:
        sift2_weights_extracted = outpath_base + "desc-fsubSIFT2weights.csv"
        cmd_connectome2tck += [
            "-tck_weights_in",
            sift2_weights,
            "-prefix_tck_weights_out",
            sift2_weights_extracted,
        ]
    run_command(cmd_connectome2tck)

    # Mask streamlines if requested
    if exclude_mask != None or include_mask != None:
        tckedit_out = outpath_base + "_desc-fsub_desc-masked.tck"
        tckedit = find_program("tckedit")
        cmd_tckedit = [
            tckedit,
            connectome2tck_out,
            tckedit_out,
        ]
        if exclude_mask != None:
            cmd_tckedit += ["-exclude", exclude_mask]
        if include_mask != None:
            cmd_tckedit += ["-include", include_mask]
        if streamline_mask != None:
            cmd_tckedit += ["-mask", streamline_mask]
        if overwrite == False:
            overwrite_check(tckedit_out)
        else:
            cmd_tckedit += ["-force"]
        if sift2_weights != None:
            sift2_weights_edited = (
                outpath_base + "desc-fsubSIFT2weights_desc-masked.csv"
            )
            cmd_tckedit += [
                "-tck_weights_in",
                sift2_weights_extracted,
                "-tck_weights_out",
                sift2_weights_edited,
            ]
        run_command(cmd_tckedit)

        return tckedit_out
    else:
        return connectome2tck_out
