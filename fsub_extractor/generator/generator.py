import argparse
import os
import os.path as op
from dipy.tracking.streamline import orient_by_rois
from dipy.io.image import load_nifti, load_nifti_data
from dipy.io.streamline import load_tractogram
from fsub_extractor.utils.utils import (
    run_command,
    overwrite_check,
    find_program,
    anat_to_gmwmi,
    project_roi,
    intersect_gmwmi,
)

# Add input arguments
def get_parser():

    parser = argparse.ArgumentParser(
        description="Extracts tract-average and along-the-tract measures of input scalar metrics (.nii.gz) for a specified streamline file (.tck/.trk)."
    )
    parser.add_argument(
        "--subject", help="Subject name.", type=str, required=True,
    )
    parser.add_argument(
        "--fodf",
        help="Fiber orientation distribution function, input to MRTrix iFOD2 tracking. .mif or .nii.gz file.",
        type=op.abspath,
        required=True,
    )
    parser.add_argument(
        "--roi1",
        help="Binary ROI that will be used to denote where streamlines begin/end",
        type=op.abspath,
        required=True,
    )
    parser.add_argument(
        "--roi2",
        help="Binary ROI that will be used to denote where streamlines begin/end",
        type=op.abspath,
        required=True,
    )
    parser.add_argument(
        "--hemi",
        help="FreeSurfer hemisphere name(s) corresponding to locations of the ROIs, separated by a comma (no spaces) if different for two ROIs (e.g 'lh,rh'). Required unless --skip-roi-projection is specified.",
    )
    parser.add_argument(
        "--projfrac-params",
        "--projfrac_params",
        help="Comma delimited list (no spaces) of projfrac parameters for mri_surf2vol / mri_label2vol. Provided as start,stop,delta. Default is --projfrac-params='-2,0,0.05'. Start must be negative to project into white matter. Used for projecting ROIs into WM.",
        default="-2,0,0.05",
        metavar=("START,STOP,DELTA"),
    )
    parser.add_argument(
        "--gmwmi",
        help="Gray matter white matter interface file (.nii.gz or .mif). If not specified, one will be created based on the FreeSurfer outputs.",
        type=op.abspath,
    )
    parser.add_argument(
        "--fs-dir",
        "--fs_dir",
        help="Path to FreeSurfer directory for the subject. Used to create GMWMI.",
        type=op.abspath,
    )
    parser.add_argument(
        "--n_streamlines",
        "--n-streamlines",
        help="Number of streamlines to produce. Half of this number (rounding up) will be used to seed in each direction (roi1-->roi2 and roi2-->roi1). Default is 5000 streamlines (2500 produced in each direction)",
        type=int,
        default=5000,
    )
    parser.add_argument(
        "--skip-roi-projection",
        "--skip_roi_projection",
        help="Whether to skip projecting ROI into WM (not recommended unless ROI is already projected). Default is to not skip projection.",
        default=False,
        action=argparse.BooleanOptionalAction,
    )
    parser.add_argument(
        "--skip-gmwmi-intersection",
        "--skip_gmwmi_intersection",
        help="Whether to skip intersecting ROI with GMWMI (not recommended unless ROI is already intersected). Default is to not skip intersection.",
        default=False,
        action=argparse.BooleanOptionalAction,
    )
    parser.add_argument(
        "--out-dir",
        "--out_dir",
        help="Directory where outputs will be stored (a subject-folder will be created there if it does not exist).",
        type=op.abspath,
        default=os.getcwd(),
    )
    parser.add_argument(
        "--out-prefix",
        "--out_prefix",
        help="Prefix for all output files. Default is no prefix.",
        type=str,
        default="",
    )
    # parser.add_argument(
    #    "--scratch",
    #    "--scratch",
    #    help="Path to scratch directory. Default is current directory.",
    #    type=op.abspath,
    #    default=os.getcwd(),
    # )
    parser.add_argument(
        "--overwrite",
        help="Whether to overwrite outputs. Default is to overwrite.",
        default=True,
        action=argparse.BooleanOptionalAction,
    )

    return parser


def main():

    # Parse arguments and run the main code
    parser = get_parser()
    args = parser.parse_args()

    main = streamline_scalar(
        subject=args.subject,
        fodf=args.fodf,
        roi1=args.roi2,
        roi2=args.roi2,
        hemi=args.hemi,
        projfrac_params=args.projfrac_params,
        gmwmi=args.gmwmi,
        fs_dir=args.fs_dir,
        n_streamlines=args.n_streamlines,
        skip_roi_projection=args.skip_roi_projection,
        skip_gmwmi_intersection=args.skip_gmwmi_intersection,
        out_dir=args.out_dir,
        out_prefix=args.out_prefix,
        # scratch=args.scratch,
        overwrite=args.overwrite,
    )


def generator(
    subject,
    fodf,
    roi1,
    roi2,
    gmwmi,
    projfrac_params,
    fs_dir,
    n_streamlines,
    skip_roi_projection,
    skip_gmwmi_intersection,
    out_dir,
    out_prefix,
    # scratch,
    overwrite,
):

    # TODO: add docs

    ### Check for assertion errors ###

    # Make sure input files exists and are the right file types
    if op.exists(fodf) == False:
        raise Exception(f"FODF file {fodf} not found on the system.")
    if fodf[-7:] != ".nii.gz" and fodf[-4:] != ".nii" and fodf[-4:] != ".mif":
        raise Exception(f"FODF file {fodf} is not a supported file type.")
    if op.exists(roi1) == False:
        raise Exception(f"ROI file {roi1} not found on the system.")
    if roi1[-7:] != ".nii.gz" and roi1[-4:] != ".mgz" and roi1[-6:] != ".label":
        raise Exception(f"ROI file {roi1} is not a supported file type.")
    if op.exists(roi2) == False:
        raise Exception(f"ROI file {roi2} not found on the system.")
    if roi2[-7:] != ".nii.gz" and roi2[-4:] != ".mgz" and roi2[-6:] != ".label":
        raise Exception(f"ROI file {roi2} is not a supported file type.")
    if gmwmi != None and op.exists(gmwmi) == False:
        raise Exception(
            f"GMWMI file {gmwmi} was specified but not found on the system."
        )
    if fs_dir != None:
        fs_sub_dir = op.join(fs_dir, subject)
        if op.isdir(fs_sub_dir) == False:
            raise Exception(
                f"Expected subject FreeSurfer folder {fs_sub_dir} was specified but not found on the system."
            )
    if gmwmi == None and fs_dir == None:
        raise Exception("Please specify either a GMWMI or FreeSurfer directory")
    # Make sure number of points for tract profile is not negative
    if n_streamlines < 1:
        raise Exception(
            "Number of streamlines ({n_points}) must be a positive integer."
        )
    # If odd number of streamlines entered, add 1 to make it even
    if (n_streamlines % 2) == 1:
        n_streamlines += 1
        print("Odd number of streamlines entered, adding 1 to make it even")
    # Check projfrac-params
    projfrac_params_list = projfrac_params.split(",")
    if len(projfrac_params_list) != 3:
        raise Exception(
            "Invalid number of projfrac-params specified. --projfrac-params should be provided as start,stop,delta."
        )
    elif float(projfrac_params_list[0]) >= 0:
        raise Exception(
            "The 'start' paramater of projfrac-params must be negative to project into white matter."
        )
    elif float(projfrac_params_list[-1]) <= 0:
        raise Exception(
            "The 'delta' paramater of projfrac-params must be positive to iterate correctly."
        )
    elif float(projfrac_params_list[1]) <= float(projfrac_params_list[0]):
        raise Exception(
            "The 'stop' paramater of projfrac-params must be greater than the 'start' parameter."
        )
    # Check if out and scratch directories exist
    if op.isdir(out_dir) == False:
        raise Exception(f"Output directory {out_dir} not found on the system.")
    # if op.isdir(scratch) == False:
    #    raise Exception(f"Scratch directory {scratch} not found on the system.")

    ### Prepare output directories ###
    # Add an underscore to separate prefix from file names if a prefix is specified
    if len(out_prefix) > 0:
        if out_prefix[-1] != "_":
            out_prefix += "_"

    # Make subject output and scratch folders if they do not exist, and define the naming convention
    if op.isdir(op.join(out_dir, subject)) == False:
        os.mkdir(op.join(out_dir, subject))
    # if op.isdir(op.join(scratch, subject + "_scratch")) == False:
    #    os.mkdir(op.join(scratch, subject + "_scratch"))
    subject_base = op.join(out_dir, subject)
    outpath_base = op.join(subject_base, out_prefix)
    # scratch_base = op.join(scratch, subject + "_scratch", out_prefix)

    ### Create GMWMI if it does not exist
    if gmwmi == None and op.isdir(fs_sub_dir):
        print("\n Creating GMWMI from FreeSurfer")
        gmwmi = anat_to_gmwmi(fs_sub_dir, subject_base, overwrite)

    ### Project ROIs
    if skip_roi_projection == False:
        print("\n Projecting ROI1 \n")
        roi1_projected = project_roi(
            roi_in=roi1,
            fs_dir=fs_dir,
            subject=subject,
            hemi=hemi_list[0],
            projfrac_params=projfrac_params_list,
            outpath_base=outpath_base,
            overwrite=overwrite,
        )
    else:
        print("\n Skipping ROI projection \n")
        roi1_projected = roi1
    if skip_gmwmi_intersection == False:
        print("\n Intersecting ROI1 with GMWMI \n")
        roi1_intersected = intersect_gmwmi(
            roi_in=roi1_projected,
            gmwmi=gmwmi,
            outpath_base=op.join(
                out_dir, subject, op.basename(roi1_projected).removesuffix(".nii.gz")
            ),
            overwrite=overwrite,
        )
    else:
        roi1_intersected = roi1_projected

    print("\n DONE \n")
