import argparse
import os.path as op
import os
import shutil
import subprocess

def find_program(program):

    def is_exe(fpath):
        return op.exists(fpath) and os.access(fpath, os.X_OK)

    for path in os.environ["PATH"].split(os.pathsep):
        path = path.strip('"')
        exe_file = op.join(path, program)
        if is_exe(exe_file):
            return program
    return None

def get_parser():

    parser = argparse.ArgumentParser(
        description="Functionally segments a tract file based on intersections with prespecified ROI(s)")
    parser.add_argument(
        "--tck-file", "--tck_file",
        help="Tract File (.tck)",
        required=True)
    parser.add_argument(
        "--roi1",
        help="First ROI file (.nii.gz)",
        required=True)
    parser.add_argument(
        "--roi2",
        help="Second ROI file (.nii.gz), optional",
        default=None)
    parser.add_argument(
        "--out_dir", "--out-dir",
        help="Directory where outputs will be stored",
        type=op.abspath, 
        default="./")
    parser.add_argument(
        "--out_prefix", "--out-prefix",
        help="Prefix for all output files",
        type=str, 
        default="")
    parser.add_argument(
        "--scalar",
        help="Scalar map(s) to sample streamlines on (.nii.gz)",
        default=None)
    parser.add_argument(
        "--search_dist", "--search-dist",
        help="Distance in mm to search ahead of streamlines for ROIs",
        default=4)
    return parser

def main():

    parser = get_parser()
    args = parser.parse_args()
    main = extractor(tck_file=args.tck_file,
                        roi1=args.roi1,
                        roi2=args.roi2,
                        out_dir=args.out_dir,
                        out_prefix=args.out_prefix,
			scalar=args.scalar,
			search_dist=args.search_dist)

def merge_rois(roi1, roi2, out_file):
    """Creates the input ROI file to be passed into tck2connectome.
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
        labelled_roi2 = roi2.remove_suffix(".nii.gz") + "_labelled.nii.gz"
        mrcalc_path = find_program("mrcalc")
        mult_proc = subprocess.Popen([mrcalc_path, roi2, 2, "-mult", labelled_roi2], stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
        _, err_mult = mult_proc.communicate()
        if not op.exists(labelled_roi2):
            raise Exception(err_mult)

        merg_proc = subprocess.Popen([mrcalc_path, roi1, labelled_roi2, out_file, "-add"], stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
        _, err_merg = merg_proc.communicate()
        if not op.exists(out_file):
            raise Exception(err_mult)
            
    return out_file, err_mult, err_merg

def extract_tck_mrtrix(tck_file, rois_in, outpath_base, search_dist): #nodes?
    # [TODO] docs
    # Run MRtrix CLI
    ### tck2connectome
    tck2connectome_path = find_program('tck2connectome')
    tck2conn_proc = subprocess.Popen([tck2connectome_path, tck_file, rois_in, outpath_base + "connectome.txt", 
	'-assignment_forward_search', search_dist, "-out_assignments", outpath_base + "assignments.txt"],
	stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    _, err_tck2conn = tck2conn_proc.communicate()
    # [TODO] check for output, if not present, print error

    ### connectome2tck
    connectome2tck_path = find_program('connectome2tck')
    # [TODO] FIX NODES BASED ON 1 OR 2 ROI INPUTS
    conn2tck_proc = subprocess.Popen([connectome2tck_path, tck_file, outpath_base + "assignments.txt", outpath_base + "extracted.tck", 
	'-nodes', "1,2", "-exclusive", "-files single"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    _, err_conn2tck = conn2tck_proc.communicate()
    # [TODO] check for output, if not present, print error

    return [err_tck2conn, err_conn2tck]

def extractor(tck_file, roi1, roi2, out_dir, out_prefix, scalar):
    # [TODO] add docs

    # Check for assertion errors [TODO]

    outpath_base = op.join(out_dir, out_prefix) + "_"

    # Create atlas-like file if multiple ROIs avaialble
    if roi2 == None:
	rois_in = roi1
    else:
	roi1_basename = op.basename(roi1).remove_suffix(".nii.gz")
	roi2_basename = op.basename(roi2).remove_suffix(".nii.gz")
	[rois_in, err1, err2] = merge_rois(roi1, roi2, outpath_base + roi1_basename + "_" + roi2_basename + "_merged.nii.gz") # [TODO] make naming more flexible
    # [TODO] check validity of ROI file

    # Run MRtrix commands
    cmd_errs = extract_tck_mrtrix(tck_file, rois_in, outpath_base, search_dist)

    


