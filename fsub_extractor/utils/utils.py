import os.path as op
import os
import shutil
import subprocess

def find_program(program):
    """Checks that a command line tools is on path to be passed into subprocess.
    Parameters
    ==========
    program: str
            name of command to look for 

    Outputs
    =======
    program: str
            returns the program if found, and None if not found
    """
    def is_exe(fpath):
        return op.exists(fpath) and os.access(fpath, os.X_OK)
    for path in os.environ["PATH"].split(os.pathsep):
        path = path.strip('"')
        exe_file = op.join(path, program)
        if is_exe(exe_file):
            return program
    return None

def merge_rois(roi1, roi2, out_file):
    """Creates the input ROI atlas-like file to be passed into tck2connectome.
    If a single ROI file is passed:
            Copies the same single ROI file.
    If multiple ROI files are passed:
            Multiplies the second ROI file passed by 2, and merges this file with the first file.
            Returns the merged file
    Parameters
    ==========
    roi1: str
            abspath to a roi mask file
    roi2: str [Optional]
            abspath to a second roi mask file

    Outputs
    =======
    roi_merge: str
            abspath to the
    """
    if roi2 == None:
        shutil.copyfile(roi1, out_file)
        err_mult = None
        err_merg = None

    else:
        labelled_roi2 = roi2.removesuffix(".nii.gz") + "_labelled.nii.gz"
        mrcalc_path = find_program("mrcalc")
        mult_proc = subprocess.Popen(
            [mrcalc_path, roi2, "2", "-mult", labelled_roi2],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        _, err_mult = mult_proc.communicate()
        if not op.exists(labelled_roi2):
            raise Exception(err_mult)

        merg_proc = subprocess.Popen(
            [mrcalc_path, roi1, labelled_roi2, "-add", out_file],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        _, err_merg = merg_proc.communicate()
        if not op.exists(out_file):
            raise Exception(err_mult)

    return out_file, err_mult, err_merg

def t1_to_gmwmi(anat, outpath_base):
    # Check for T1 file vs FreeSurfer directory
    anat_path_split = op.splitext(anat)
    file_extension = anat_path_split[-1]
    if op.isdir(anat+'/surf'):
         print('FreeSurfer input detected: Using 5ttgen HSVS algorithm to generate GMWMI')
         fivett_algo = 'hsvs'
    elif file_extension == '.nii.gz':
         print('T1 image detected: Using default FSL 5ttgen algorithm to generate GMWMWI')
         fivett_algo = 'fsl'
    else:
         raise Exception("Neither T1 or FreeSurfer input detected; Unable to create GMWMI")

    # Run 5ttgen to generate 5tt image
    print('Generating 5TT Image')
    fivettgen_path = find_program("5ttgen")
    mult_proc = subprocess.Popen(
            [fivettgen_path, fivett_algo, anat, outpath_base + '5tt.nii.gz'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    _, err_5tt = mult_proc.communicate()

    # Run 5tt2gmwmi to generate GMWMI image
    print('Generating GMWMI Image')
    fivett2gmwmi_path = find_program("5tt2gmwmi")
    mult_proc = subprocess.Popen(
            [fivett2gmwmi_path, outpath_base + '5tt.nii.gz', outpath_base + 'gmwmi.nii.gz'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    _, err_gmwmi = mult_proc.communicate()
    print('Finished creating GMWMI')
    return None

def extract_tck_mrtrix(tck_file, rois_in, outpath_base, search_dist, two_rois):  # nodes?
    # [TODO] docs
    # Run MRtrix CLI
    ### tck2connectome
    tck2connectome_path = find_program("tck2connectome")
    tck2conn_proc = subprocess.Popen(
        [
            tck2connectome_path,
            tck_file,
            rois_in,
            outpath_base + "connectome.txt",
            #"-assignment_forward_search",
            #search_dist,
            "-assignment_all_voxels",
            "-out_assignments",
            outpath_base + "assignments.txt",
            "-force"
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    _, err_tck2conn = tck2conn_proc.communicate()
    # [TODO] check for output, if not present, print error

    ### connectome2tck
    connectome2tck_path = find_program("connectome2tck")
    # Change connectome2tck arguments based on single node or pairwise nodes
    if two_rois:
        nodes = "1,2"
        extra_args = ["-exclusive",
            "-files",
            "single"]
    else:
        nodes = "1"
        extra_args = ["-keep_self"]
    conn2tck_proc = subprocess.Popen(
        [
            connectome2tck_path,
            tck_file,
            outpath_base + "assignments.txt",
            outpath_base + "extracted",
            "-nodes",
            nodes
        ] + extra_args,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    _, err_conn2tck = conn2tck_proc.communicate()
    # [TODO] check for output, if not present, print error

    return [err_tck2conn, err_conn2tck]


def dilate_rois(rois_in, outpath_base):
    pass

def intersect_gmwmi(rois_in, gmwmi, outpath_base):
    mrcalc_path = find_program("mrcalc")
    mult_proc = subprocess.Popen(
            [mrcalc_path, rois_in, gmwmi, "-mult", outpath_base + 'gmwmi_roi_intersect.nii.gz'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    _, err_gmwmi = mult_proc.communicate()

