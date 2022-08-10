import os.path as op
import os
import shutil
import subprocess

def overwrite_check(file):
    """ Checks whether a file exists. If so, aborts the function.
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
    """ Checks that a command line tools is executable on path.
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
    """ Interface for running CLI commands in Python. Crashes if command returns an error.
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
    """ Converts a .trk file to .tck using DIPY
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
    from dipy.io.streamline import load_tractogram,save_tractogram
    trk_loaded = load_tractogram(trk_file, ref)
    filename = op.basename(trk_file).replace(".trk",".tck")
    tck_file = op.join(out_dir, filename)
    save_tractogram(trk_loaded, tck_file)
    
    return tck_file


def anat_to_gmwmi(anat, outpath_base, overwrite):
    """ Creates a gray-matter-white-matter-interface (GMWMI) from a T1 or FreeSurfer image
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
        print(
            "T1 image detected: Using FSL 5ttgen algorithm to generate GMWMWI"
        )
        fivett_algo = "fsl"
    else:
        raise Exception(
            "Neither T1 or FreeSurfer input detected; Unable to create GMWMI"
        )

    # Run 5ttgen to generate 5tt image
    print("\n Generating 5TT Image \n")
    fivettgen = find_program("5ttgen")
    cmd_5ttgen = [fivettgen, fivett_algo, anat, outpath_base + "5tt.nii.gz", "-nocrop"]
    if overwrite:
        cmd_5ttgen += ["-force"]
    else:
        overwrite_check(outpath_base + "5tt.nii.gz")
    run_command(cmd_5ttgen)

    # Run 5tt2gmwmi to generate GMWMI image
    print("\n Generating GMWMI Image \n")
    fivett2gmwmi = find_program("5tt2gmwmi")
    cmd_5tt2gmwmi = [
        fivett2gmwmi,
        outpath_base + "5tt.nii.gz",
        outpath_base + "gmwmi.nii.gz",
    ]
    if overwrite:
        cmd_5tt2gmwmi += ["-force"]
    else:
        overwrite_check(outpath_base + "gmwmi.nii.gz")
    run_command(cmd_5tt2gmwmi)

    print("\n Binarizing GMWMI \n")
    mrthreshold = find_program("mrthreshold")
    cmd_mrthreshold = [
        mrthreshold,
        "-abs",
        "0",
        "-comparison",
        "gt",
        outpath_base + "gmwmi.nii.gz",
        outpath_base + "gmwmi_bin.nii.gz",
    ]
    if overwrite:
        cmd_mrthreshold += ["-force"]
    else:
        overwrite_check(outpath_base + "gmwmi_bin.nii.gz")
    run_command(cmd_mrthreshold)
    
    return outpath_base + "gmwmi_bin.nii.gz"


def project_roi(roi_in, fs_dir, subject, hemi, projfrac_params, outpath_base, overwrite):
    # TODO: make projfrac parameters an input argument
    """ Projects input ROI into the white matter. If volumetric ROI is input, starts by mapping it to the surface.

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
    Image is saved out to outpath_base + gmwmi_roi_intersect.nii.gz
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
        out_path = outpath_base + op.basename(roi_surf).replace(
            ".label", ".projected.nii.gz"
        )
        mri_label2vol = find_program("mri_label2vol")
        cmd_mri_label2vol = [
            mri_label2vol,
            "--label",
            roi_surf,
            "--o",
            out_path,
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
        out_path = outpath_base + op.basename(roi_surf).replace(
            ".mgz", ".projected.nii.gz"
        )
        mri_surf2vol = find_program("mri_surf2vol")
        cmd_mri_surf2vol = [
            mri_surf2vol,
            "--surfval",
            roi_surf,
            "--o",
            out_path,
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

        return out_path


def intersect_gmwmi(roi_in, gmwmi, outpath_base, overwrite): # TODO: Fix so that it is meant to run on individual ROIs, not combined
    """ Intersects an input ROI file with the GMWMI

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
    Image is saved out to outpath_base + gmwmi_roi_intersect.nii.gz
    """
    
    mrcalc = find_program("mrcalc")
    cmd_mrcalc = [
        mrcalc,
        gmwmi,
        roi_in,
        "-mult",
        outpath_base + "gmwmi_roi_intersect.nii.gz",
    ]
    
    if overwrite == False:
        overwrite_check(outpath_base + "gmwmi_roi_intersect.nii.gz")
    else:
        cmd_mrcalc += ["-force"]
        
    run_command(cmd_mrcalc)

    return outpath_base + "gmwmi_roi_intersect.nii.gz"


def merge_rois(roi1, roi2, out_file, overwrite): # TODO: REFACTOR THIS
    """ Creates the input ROI atlas-like file to be passed into tck2connectome.
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


    labelled_roi2 = roi2.removesuffix(".nii.gz") + "_labelled.nii.gz"
    
    # Abort if file already exists and overwriting not allowed
    if overwrite == False:
        overwrite_check(labelled_roi2)
        overwrite_check(out_file)
        
    mrcalc = find_program("mrcalc")

    # Multiply second ROI by 2
    cmd_mrcalc_mult = [mrcalc, roi2, "2", "-mult", labelled_roi2]
    run_command(cmd_mrcalc_mult)

    # Merge ROIs
    cmd_mrcalc_merge = [mrcalc, roi1, labelled_roi2, "-add", out_file]
    run_command(cmd_mrcalc_merge)

    return out_file


def extract_tck_mrtrix(
    tck_file, rois_in, outpath_base, search_dist, two_rois, overwrite
):
    """ Uses MRtrix tools to extract the TCK file that connects to the ROI(s)
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
    cmd_tck2connectome = [
        tck2connectome,
        tck_file,
        rois_in,
        outpath_base + "connectome.txt",
        "-assignment_forward_search",
        search_dist,
        "-out_assignments",
        outpath_base + "assignments.txt",
        "-force",
    ]
    run_command(cmd_tck2connectome)

    ### connectome2tck
    connectome2tck = find_program("connectome2tck")
    # Change connectome2tck arguments based on single node or pairwise nodes
    if two_rois:
        nodes = "1,2"
    else:
        nodes = "0,1"
    cmd_connectome2tck = [
        connectome2tck,
        tck_file,
        outpath_base + "assignments.txt",
        outpath_base + "extracted",
        "-nodes",
        nodes,
        "-exclusive",
        "-files",
        "single",
        "-force",
    ]
    run_command(cmd_connectome2tck)

    return outpath_base + "extracted.tck"
