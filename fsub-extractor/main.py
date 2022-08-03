import argparse
import os.path as op

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
    return parser

def main():

    parser = get_parser()
    args = parser.parse_args()
    main = extractor(tck_file=args.tck_file,
                        roi1=args.roi1,
                        roi2=args.roi2,
                        out_dir=args.out_dir,
                        out_prefix=args.out_prefix,
			scalar=args.scalar)
   
def extractor(tck_file, roi1, roi2, out_dir, out_prefix, scalar):
    # [TODO] add docus

    # Check for assertion errors [TODO]

    # Create atlas-like file if multiple ROIs avaialble
    if roi2 == None:
	rois_in = roi1
    else:
	rois_in = merge_rois(roi1,roi2)
    # [TODO] check validity of ROI file

    # Run MRtrix CLI
    command_tck2connectome = "tck2connectome 
    
