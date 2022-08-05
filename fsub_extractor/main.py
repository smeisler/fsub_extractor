import argparse
import os.path as op
from fsub_extractor.utils.utils import *

def get_parser():

    parser = argparse.ArgumentParser(
        description="Functionally segments a tract file based on intersections with prespecified ROI(s)"
    )
    parser.add_argument(
        "--tck-file", "--tck_file", help="Tract File (.tck)", required=True
    )
    parser.add_argument("--roi1", help="First ROI file (.nii.gz)", required=True)
    parser.add_argument(
        "--roi2", help="Second ROI file (.nii.gz), optional", default=None
    )
    parser.add_argument(
        "--out_dir",
        help="Directory where outputs will be stored",
        type=op.abspath,
        default="./",
    )
    parser.add_argument(
        "--out_prefix",
        help="Prefix for all output files",
        type=str,
        default="",
    )
    parser.add_argument(
        "--scalar",
        help="Scalar map(s) to sample streamlines on (.nii.gz)",
        default=None,
    )
    parser.add_argument(
        "--search_dist",
        help="Distance in mm to search ahead of streamlines for ROIs",
        default=4,
    )
    return parser


def main():

    # Parse arguments and run the main code
    parser = get_parser()
    args = parser.parse_args()

    main = extractor(
        tck_file=args.tck_file,
        roi1=args.roi1,
        roi2=args.roi2,
        out_dir=args.out_dir,
        out_prefix=args.out_prefix,
        scalar=args.scalar,
        search_dist=str(args.search_dist),
    )

def extractor(tck_file, roi1, roi2, out_dir, out_prefix, scalar, search_dist):
    # [TODO] add docs

    # Check for assertion errors [TODO]

    outpath_base = op.join(out_dir, out_prefix) + "_"

    # Create atlas-like file if multiple ROIs avaialble
    if roi2 == None:
        print("1 ROI passed in")
        two_rois = False
        rois_in = roi1
    else:
        print("2 ROIs passed in, merging them")
        two_rois = True
        roi1_basename = op.basename(roi1).removesuffix(".nii.gz")
        roi2_basename = op.basename(roi2).removesuffix(".nii.gz")
        [rois_in, err1, err2] = merge_rois(
            roi1,
            roi2,
            outpath_base + roi1_basename + "_" + roi2_basename + "_merged.nii.gz",
        )  # [TODO] make naming more flexible
    # [TODO] check validity of ROI file

    # Run MRtrix commands
    print("Extracing the Sub-Bundle")
    cmd_errs = extract_tck_mrtrix(tck_file, rois_in, outpath_base, search_dist, two_rois)
    #print(cmd_errs)
