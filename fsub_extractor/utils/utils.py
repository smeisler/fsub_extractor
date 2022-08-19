import os.path as op
import os
import shutil
import subprocess


def overwrite_check(file):
    """Checks whether a file exists. If so, aborts the function.
    Parameters
    ==========
    file: str
            name of file to look for

    Outputs
    =======
    None
    """
    if op.exists(file):
        raise Exception(
            "Output file "
            + file
            + " already exists. Aborting program. Specify --overwrite if you would like to overwrite files."
        )

    return None


def find_program(program):
    """Checks that a command line tools is executable on path.
    Parameters
    ==========
    program: str
            name of command to look for

    Outputs
    =======
    program: str
            returns the program if found, and errors out if not found
    """

    #  Simple function for checking if a program is executable
    def is_exe(fpath):
        return op.exists(fpath) and os.access(fpath, os.X_OK)

    path_split = os.environ["PATH"].split(os.pathsep)
    if len(path_split) == 0:
        raise Exception("PATH environment variable is empty.")

    for path in path_split:
        path = path.strip('"')
        exe_file = op.join(path, program)
        if is_exe(exe_file):
            return program
    raise Exception("Command " + program + " could not be found in PATH.")


def run_command(cmd_list):
    """Interface for running CLI commands in Python. Crashes if command returns an error.
    Parameters
    ==========
    cmd_list: list
            List containing arguments for the function, e.g. ['CommandName', '--argName1', 'arg1']

    Outputs
    =======
    None
    """

    function_name = cmd_list[0]
    return_code = subprocess.run(cmd_list).returncode
    if return_code != 0:
        raise Exception(
            "Command "
            + function_name
            + " exited with errors. See message above for more information."
        )

    return None


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


def anat_to_gmwmi(anat, outpath_base, overwrite):
    """Creates a gray-matter-white-matter-interface (GMWMI) from a T1 or FreeSurfer image
    If a T1 image is passed (not recommended), uses FSL FAST to create 5TT and GMWMI
    If a FreeSurfer directory is passed in, uses the surface reconstruction to create 5TT and GMWMI

    Parameters
    ==========
    anat: str
            Either a path to a T1 image (.nii, .nii.gz, .mif) or FreeSurfer subject directory
    outpath_base: str
            Path to output directory, including output prefix
    overwrite: bool
            Whether to allow overwriting outputs

    Outputs
    =======
    Function returns path to binarized GMWMI output image.
    outpath_base + 5tt.nii.gz is the 5TT segmented anatomical image
    outpath_base + gmwmi.nii.gz is the GMWMI image
    outpath_base + gmwmi_bin.nii.gz is the binarized GMWMI image
    """

    # Check for T1 file vs FreeSurfer directory
    if op.isdir(op.join(anat, "surf")):
        print(
            "FreeSurfer input detected: Using 5ttgen HSVS algorithm to generate GMWMI"
        )
        fivett_algo = "hsvs"
    elif anat[-7:] == ".nii.gz" or anat[-4:] == ".nii" or anat[-4:] == ".mif":
        print("T1 image detected: Using FSL 5ttgen algorithm to generate GMWMWI")
        fivett_algo = "fsl"
    else:
        raise Exception(
            "Neither T1 or FreeSurfer input detected; Unable to create GMWMI"
        )

    # Run 5ttgen to generate 5tt image
    print("\n Generating 5TT Image \n")
    fivettgen = find_program("5ttgen")
    fivettgen_out = outpath_base + "5tt.nii.gz"
    cmd_5ttgen = [fivettgen, fivett_algo, anat, fivettgen_out, "-nocrop"]
    if overwrite:
        cmd_5ttgen += ["-force"]
    else:
        overwrite_check(fivettgen_out)
    run_command(cmd_5ttgen)

    # Run 5tt2gmwmi to generate GMWMI image
    print("\n Generating GMWMI Image \n")
    fivett2gmwmi = find_program("5tt2gmwmi")
    fivett2gmwmi_out = outpath_base + "gmwmi.nii.gz"
    cmd_5tt2gmwmi = [
        fivett2gmwmi,
        fivettgen_out,
        fivett2gmwmi_out,
    ]
    if overwrite:
        cmd_5tt2gmwmi += ["-force"]
    else:
        overwrite_check(fivett2gmwmi_out)
    run_command(cmd_5tt2gmwmi)

    # Run mrthreshold to binarize the GMWMI
    print("\n Binarizing GMWMI \n")
    binarized_gmwmi_outpath = outpath_base + "gmwmi_bin.nii.gz"
    binarized_gmwmi_out = binarize_image(fivett2gmwmi_out, binarized_gmwmi_out, overwrite)

    return binarized_gmwmi_out

def binarize_image(img, outfile, overwrite):
    mrthreshold = find_program("mrthreshold")
    cmd_mrthreshold = [
    mrthreshold,
    "-abs",
    "0",
    "-comparison",
    "gt",
    img,
    outfile,
    ]
    
    if overwrite:
        cmd_mrthreshold += ["-force"]
    else:
        overwrite_check(outfile)
        
    run_command(cmd_mrthreshold)
    
    return outfile

def project_roi(
    roi_in, fs_dir, subject, hemi, projfrac_params, outpath_base, overwrite
):
    """Projects input ROI into the white matter. If volumetric ROI is input, starts by mapping it to the surface.

    Parameters
    ==========
    roi_in: str
            Path to input ROI mask file (.nii.gz, .mgz, .label). Should be binary (1 in ROI, 0 elsewhere).
    fs_dir: str
            Path to FreeSurfer subjects folder
    subject: str
            Subject name. Must match folder name in fs_dir.
    hemi: str
            Hemisphere corresponding to the ROI ('lh' or 'rh')
    projfrac_params: list
            List containing strings of ['start','stop','delta'] parameters for projfrac
    outpath_base: str
            Path to output directory, including output prefix
    overwrite: bool
            Whether to allow overwriting outputs

    Outputs
    =======
    Function returns path to the projected ROI.
    Image is saved out to outpath_base + gmwmi_intersected.nii.gz
    """

    os.environ["SUBJECTS_DIR"] = fs_dir
    if roi_in[-7:] == ".nii.gz":
        print("Using volumetric ROI projection pipeline")
        # roi_surf = roi_in.replace(".nii.gz", ".mgz")
        roi_surf = outpath_base + op.basename(roi_in).replace(".nii.gz", ".mgz")
        mri_vol2surf = find_program("mri_vol2surf")
        cmd_mri_vol2surf = [
            mri_vol2surf,
            "--src",
            roi_in,
            "--out",
            roi_surf,
            "--regheader",
            subject,
            "--hemi",
            hemi,
            "--projfrac-max",
            "-.5",
            "1",
            ".1",
        ]
        run_command(cmd_mri_vol2surf)
    else:
        roi_surf = roi_in

    if roi_surf[-6:] == ".label":
        print("Projecting FS .label file")
        # out_path = roi_surf.replace(".label",".projected.nii.gz")
        filename = roi_surf.replace(".label", ".projected.nii.gz")
        filename = op.basename(filename)
        mri_label2vol = find_program("mri_label2vol")
        cmd_mri_label2vol = [
            mri_label2vol,
            "--label",
            roi_surf,
            "--o",
            outpath_base + filename,
            "--subject",
            subject,
            "--hemi",
            hemi,
            "--temp",
            op.join(fs_dir, subject, "mri", "aseg.mgz"),
            "--proj",
            "frac",
            projfrac_params[0],
            projfrac_params[1],
            projfrac_params[2],
        ]
        run_command(cmd_mri_label2vol)

    if roi_surf[-4:] == ".mgz":
        print("Projecting FS .mgz surface file")
        # out_path = roi_surf.replace(".mgz",".projected.nii.gz")
        filename = roi_surf.replace(".mgz", ".projected.nii.gz")
        filename = op.basename(filename)
        mri_surf2vol = find_program("mri_surf2vol")
        cmd_mri_surf2vol = [
            mri_surf2vol,
            "--surfval",
            roi_surf,
            "--o",
            outpath_base + filename,
            "--subject",
            subject,
            "--hemi",
            hemi,
            "--template",
            op.join(fs_dir, subject, "mri", "aseg.mgz"),
            "--identity",
            subject,
            "--fill-projfrac",
            projfrac_params[0],
            projfrac_params[1],
            projfrac_params[2],
        ]
        run_command(cmd_mri_surf2vol)

        return outpath_base + filename


def intersect_gmwmi(
    roi_in, gmwmi, outpath_base, overwrite
):  # TODO: Fix so that it is meant to run on individual ROIs, not combined
    """Intersects an input ROI file with the GMWMI

    Parameters
    ==========
    rois_in: str
            Path to input ROI mask file (.nii.gz, .mif). Should be binary (1 in ROI, 0 elsewhere).
    gmwmi: str
            Path to gray-matter-white-matter-interface image (.nii.gz, .mif)
    outpath_base: str
            Path to output directory, including output prefix
    overwrite: bool
            Whether to allow overwriting outputs

    Outputs
    =======
    Function returns path to the intersected image.
    Image is saved out to outpath_base + _gmwmi_intersected.nii.gz
    """

    mrcalc = find_program("mrcalc")
    mrcalc_out = outpath_base + "_gmwmi_intersected.nii.gz"
    cmd_mrcalc = [
        mrcalc,
        gmwmi,
        roi_in,
        "-mult",
        mrcalc_out,
    ]

    if overwrite == False:
        overwrite_check(mrcalc_out)
    else:
        cmd_mrcalc += ["-force"]

    run_command(cmd_mrcalc)

    return mrcalc_out


def merge_rois(roi1, roi2, out_file, overwrite):  # TODO: REFACTOR THIS
    """Creates the input ROI atlas-like file to be passed into tck2connectome.
        Multiplies the second ROI file passed by 2, and merges this file with the first file.
        Returns the merged file
    Parameters
    ==========
    roi1: str
            abspath to the first ROI mask file
    roi2: str
            abspath to the second ROI mask file
    out_file: str
            abspath of filename to save output merged ROI file
    overwrite: bool
            Whether to allow overwriting outputs

    Outputs
    =======
    out_file: str
            abspath of output file created by this function

    """

    roi2_mult2 = roi2.removesuffix(".nii.gz") + "_mult-2.nii.gz"

    mrcalc = find_program("mrcalc")

    # Multiply second ROI by 2
    cmd_mrcalc_mult = [mrcalc, roi2, "2", "-mult", roi2_mult2]

    # Merge ROIs
    cmd_mrcalc_merge = [mrcalc, roi1, roi2_mult2, "-add", out_file]

    # Abort if file already exists and overwriting not allowed
    if overwrite == False:
        overwrite_check(labelled_roi2)
        overwrite_check(out_file)
    else:
        cmd_mrcalc_mult += ["-force"]
        cmd_mrcalc_merge += ["-force"]

    run_command(cmd_mrcalc_mult)
    run_command(cmd_mrcalc_merge)

    return out_file


def extract_tck_mrtrix(
    tck_file, rois_in, outpath_base, search_dist, two_rois, overwrite
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
        "-assignment_forward_search",
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
