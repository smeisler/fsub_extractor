import argparse
import os.path as op
from fsub_extractor.utils.utils import *


def get_parser():

    parser = argparse.ArgumentParser(
        description="Functionally segments a tract file based on intersections with prespecified ROI(s)"
    )
    parser.add_argument(
        "--subject", help="Subject name (must match name in FreeSurfer folder)", type=str, required=True,
    )
    parser.add_argument(
        "--tck-file", "--tck_file", help="Path to tract file (.tck)", type=op.abspath, required=True,
    )
    parser.add_argument("--roi1", help="First ROI file (.mgz, .label, or .nii.gz)", type=op.abspath, required=True)
    parser.add_argument("--fs_dir", "--fs-dir", help="Path to FreeSurfer directory for the subject", type=op.abspath, required=True)
    parser.add_argument(
        "--hemi",
        help="Hemisphere name(s) corresponding to locations of the ROIs, separated by a comma if different for two ROIs (e.g 'lh,rf').",
        required=True
    )
    parser.add_argument(
        "--out_dir",
        "--out-dir",
        help="Directory where outputs will be stored (a subject-folder will be created there if it does not exist)",
        type=op.abspath,
        required = True
        default=os.getcwd(),
    )
    parser.add_argument("--gmwmi", help="Path to GMWMI image (if not specified, will be created from FreeSurfer inputs)", type=op.abspath)
    parser.add_argument(
        "--roi2", help="Second ROI file (.mgz, .label, or .nii.gz), optional", type=op.abspath
    )
    parser.add_argument(
        "--scalars",
        help="Comma delimited list of scalar map(s) to sample streamlines on (.nii.gz)"
    )
    parser.add_argument(
        "--search_dist",
        "--search-dist",
        help="Distance in mm to search ahead of streamlines for ROIs",
        type=float,
        default=4.0
    )
    parser.add_argument(
        "--out_prefix",
        "--out-prefix",
        help="Prefix for all output files",
        type=str,
        default=""
    )
    parser.add_argument(
        "--scratch",
        "--scratch",
        help="Path to scratch directory",
        type=op.abspath,
        default=os.getcwd()
    )
    parser.add_argument("--fs_license", "--fs-license", help="Path to FreeSurfer license", type=op.abspath, required=False) #[TODO] MAKE REQUIRED LATER
    return parser


def main():

    # Parse arguments and run the main code
    parser = get_parser()
    args = parser.parse_args()

    main = extractor(
        subject=args.subject,
        tck_file=args.tck_file,
        roi1=args.roi1,
        fs_dir=args.fs_dir,
        hemi=args.hemi,
        gmwmi=args.gmwmi,
        roi2=args.roi2,
        scalars=args.scalars,
        search_dist=str(args.search_dist),
        out_dir=args.out_dir,
        out_prefix=args.out_prefix,
        scratch=args.scratch,
        fs_license=args.fs_license
    )


def extractor(subject, tck_file, roi1, fs_dir, fs_license, hemi, gmwmi, roi2, scalars, search_dist, out_dir, out_prefix, scratch):
    # [TODO] add docs

    # Check for assertion errors [TODO]

    # Add an underscore to separate prefix from file names if a prefix is specified
    if len(out_prefix) > 0:
        if out_prefix[-1] != '_':
            out_prefix += '_'

    outpath_base = op.join(out_dir, out_prefix)
    scratch_base = op.join(scratch, out_prefix)

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
    extract_tck_mrtrix(
        tck_file, rois_in, outpath_base, search_dist, two_rois
    )
