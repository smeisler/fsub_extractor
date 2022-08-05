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

    path_split = os.environ["PATH"].split(os.pathsep)
    if len(path_split) == 0:
        raise SystemExit("PATH environment variable is empty.")

    for path in path_split:
        path = path.strip('"')
        exe_file = op.join(path, program)
        if is_exe(exe_file):
            return program
        else:
            raise SystemExit("Command " + function_name + " could not be found in PATH.")


def run_command(cmd_list):
# [TODO] ADD DOC
    function_name = cmd_list[0]
    return_code = subprocess.run(cmd_list).returncode
    if return_code != 0:
       raise SystemExit("Command " + function_name + " exited with errors. See message above for more information.")

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
        mrcalc = find_program("mrcalc")
        cmd_mrcalc_mult = [mrcalc, roi2, "2", "-mult", labelled_roi2]
        run_command(cmd_mrcalc_mult)
        if not op.exists(labelled_roi2):
            raise Exception(err_mult)

        cmd_mrcalc_merge = [mrcalc, roi1, labelled_roi2, "-add", out_file]
        if not op.exists(out_file):
            raise Exception(err_mult)

    return out_file, err_mult, err_merg

def t1_to_gmwmi(anat, outpath_base):
    # Check for T1 file vs FreeSurfer directory
    if op.isdir(op.join(anat,'surf')):
         print('FreeSurfer input detected: Using 5ttgen HSVS algorithm to generate GMWMI')
         fivett_algo = 'hsvs'
    elif anat[-7:] == '.nii.gz' or anat[-4:] == '.nii' or anat[-4:] == '.mif':
         print('T1 image detected: Using default FSL 5ttgen algorithm to generate GMWMWI')
         fivett_algo = 'fsl'
    else:
         raise Exception("Neither T1 or FreeSurfer input detected; Unable to create GMWMI")

    # Run 5ttgen to generate 5tt image
    print('Generating 5TT Image')
    fivettgen = find_program("5ttgen")
    cmd_5ttgen = [fivettgen, fivett_algo, anat, outpath_base + '5tt.nii.gz', '-nocrop']
    run_command(cmd_5ttgen)

    # Run 5tt2gmwmi to generate GMWMI image
    print('Generating GMWMI Image')
    fivett2gmwmi = find_program("5tt2gmwmi")
    cmd_5tt2gmwmi = [fivett2gmwmi, outpath_base + '5tt.nii.gz', outpath_base + 'gmwmi.nii.gz']
    run_command(cmd_5tt2gmwmi)
    print('Finished creating GMWMI')
    return None

def extract_tck_mrtrix(tck_file, rois_in, outpath_base, search_dist, two_rois):  # nodes?
    # [TODO] docs
    # Run MRtrix CLI
    ### tck2connectome
    tck2connectome = find_program("tck2connectome")
    tck2connectome_cmd = [
            tck2connectome,
            tck_file,
            rois_in,
            outpath_base + "connectome.txt",
            "-assignment_forward_search",
            search_dist,
            "-out_assignments",
            outpath_base + "assignments.txt",
            "-force"
        ]
    run_command(tck2connectome_cmd)

    ### connectome2tck
    connectome2tck = find_program("connectome2tck")
    # Change connectome2tck arguments based on single node or pairwise nodes
    if two_rois:
        nodes = "1,2"
    else:
        nodes = "0,1"
    connectome2tck_cmd = [
            connectome2tck,
            tck_file,
            outpath_base + "assignments.txt",
            outpath_base + "extracted",
            "-nodes",
            nodes,
            "-exclusive",
            "-files",
            "single"
        ]
    run_command(connectome2tck_cmd)
    return None

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

