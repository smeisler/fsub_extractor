import argparse
import os
import os.path as op
from fsub_extractor.functions.extractor import extractor

# Add input arguments
def get_parser():

    parser = argparse.ArgumentParser(
        description="Functionally segments a tract file based on intersections with prespecified ROI(s) in gray matter."
    )
    parser.add_argument(
        "--subject",
        help="Subject name. Unless --skip-roi-proj is specified, this must match the name in the FreeSurfer folder.",
        required=True,
    )
    parser.add_argument(
        "--tract",
        help="Path to tract file (.tck or .trk). Should be in the same space as FreeSurfer inputs.",
        type=op.abspath,
        required=True,
    )
    parser.add_argument(
        "--roi1",
        help="First ROI file (.mgz, .label, or .nii.gz). File should be binary (1 in ROI, 0 elsewhere).",
        type=op.abspath,
        required=True,
    )
    parser.add_argument(
        "--fs-dir",
        "--fs_dir",
        help="Path to FreeSurfer subjects directory. Required unless --skip-roi-proj is specified.",
        type=op.abspath,
    )
    parser.add_argument(
        "--hemi",
        help="FreeSurfer hemisphere name(s) corresponding to locations of the ROIs, separated by a comma (no spaces) if different for two ROIs (e.g 'lh,rh'). Required unless --skip-roi-proj is specified.",
    )
    # parser.add_argument(
    #    "--fs-license",
    #    "--fs-license",
    #    help="Path to FreeSurfer license.",
    #    type=op.abspath,
    # )  # TODO: MAKE REQUIRED LATER
    parser.add_argument(
        "--trk-ref",
        "--trk_ref",
        help="Path to reference file, if passing in a .trk file. Typically a nifti-related object from the native diffusion used for streamlines generation (e.g., an FA map).",
        type=op.abspath,
    )
    parser.add_argument(
        "--gmwmi",
        help="Path to GMWMI image (.nii.gz or .mif). If not specified or not found, it will be created from FreeSurfer inputs. Image must be a binary mask. Ignored if --skip-gmwmi-intersection is specified.",
        type=op.abspath,
    )
    parser.add_argument(
        "--roi2",
        help="Second ROI file (.mgz, .label, or .nii.gz). If specified, program will find streamlines connecting ROI1 and ROI2. File should be binary (1 in ROI, 0 elsewhere).",
        type=op.abspath,
    )
    parser.add_argument(
        "--search-dist",
        "--search_dist",
        help="Distance in mm to search ahead of streamlines for ROIs (float). Default is 4.0 mm.",
        type=float,
        default=4.0,
    )
    parser.add_argument(
        "--search-type",
        "--search_type",
        help="Method of searching for streamlines (radial, reverse, forward). Default is forward.",
        type=str,
        default="forward",
    )
    parser.add_argument(
        "--projfrac-params",
        "--projfrac_params",
        help="Comma delimited list (no spaces) of projfrac parameters for mri_surf2vol / mri_label2vol. Provided as start,stop,delta. Default is --projfrac-params='-2,0,0.05'. Start must be negative to project into white matter.",
        default="-2,0,0.05",
        metavar=("START,STOP,DELTA"),
    )
    parser.add_argument(
        "--sift2-weights",
        "--sift2_weights",
        help="Path to SIFT2 weights file. If supplied, the sum of weights will be output with streamline extraction.",
        type=op.abspath,
    )
    parser.add_argument(
        "--tract-mask",
        "--tract_mask",
        help="Path to inclusion mask (.nii.gz or .mif). If specified, streamlines exiting this mask will be excluded.",
        type=op.abspath,
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
    parser.add_argument(
        "--overwrite",
        help="Whether to overwrite outputs. Default is to overwrite.",
        default=True,
        action=argparse.BooleanOptionalAction,
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
        "--skip-viz",
        "--skip-viz",
        help="Whether to skip the output figure. Default is to produce the figure.",
        default=False,
        action=argparse.BooleanOptionalAction,
    )
    parser.add_argument(
        "--interactive-viz",
        "--interactive_viz",
        help="Whether to produce an interactive visualization. Default is not interactive.",
        default=False,
        action=argparse.BooleanOptionalAction,
    )
    parser.add_argument(
        "--orig-color",
        "--orig_color",
        help="Comma-delimited (no spaces) color spec for original bundle in visualization, as fractional R,G,B. Default is 0.8,0.8,0.",
        default="0.8,0.8,0",
        metavar=("R,G,B"),
    )
    parser.add_argument(
        "--fsub-color",
        "--fsub_color",
        help="Comma-delimited (no spaces) color spec for FSuB bundle in visualization, as fractional R,G,B. Default is 0.2,0.6,1.",
        default="0.2,0.6,1",
        metavar=("R,G,B"),
    )
    parser.add_argument(
        "--roi1-color",
        "--roi1_color",
        help="Comma-delimited (no spaces) color spec for ROI1 in visualization, as fractional R,G,B. Default is 0.2,1,1.",
        default="0.2,1,1",
        metavar=("R,G,B"),
    )
    parser.add_argument(
        "--roi2-color",
        "--roi2_color",
        help="Comma-delimited (no spaces) color spec for ROI2 in visualization, as fractional R,G,B. Default is 1,0.2,1.",
        default="1,0.2,1",
        metavar=("R,G,B"),
    )
    parser.add_argument(
        "--roi-opacity",
        "--roi_opacity",
        help="Opacity for ROI(s) in visualization (float). Default is 0.7.",
        default=0.7,
        type=float,
    )
    parser.add_argument(
        "--fsub-linewidth",
        "--fsub_linewidth",
        help="Linewidth for extracted steamlines in visualization (float). Default is 3.0.",
        default=3.0,
        type=float,
    )
    parser.add_argument(
        "--img-viz",
        "--img-viz",
        help="Path to image to plot in visualization (.nii.gz). Must be in same space as DWI/anatomical inputs.",
        type=op.abspath,
    )
    parser.add_argument(
        "--axial-offset",
        "--axial_offset",
        help="Float (-1,1) describing where to display axial slice. -1 is bottom, 1 is top. Default is 0.0.",
        type=float,
        default=0.0,
    )
    parser.add_argument(
        "--saggital-offset",
        "--saggital_offset",
        help="Float (-1,1) describing where to display saggital slice. -1 is left, 1 is right. Default is 0.0.",
        type=float,
        default=0.0,
    )
    parser.add_argument(
        "--camera-angle",
        "--camera_angle",
        help="Camera angle for visualization. Choices are either 'saggital' or 'axial'. Default is 'saggital.'",
        default="saggital",
    )

    return parser


def main():

    # Parse arguments and run the main code
    parser = get_parser()
    args = parser.parse_args()

    main = extractor(
        subject=args.subject,
        tract=args.tract,
        roi1=args.roi1,
        fs_dir=args.fs_dir,
        hemi=args.hemi,
        # fs_license=args.fs_license,
        trk_ref=args.trk_ref,
        gmwmi=args.gmwmi,
        roi2=args.roi2,
        search_dist=str(args.search_dist),
        search_type=str(args.search_type),
        projfrac_params=args.projfrac_params,
        sift2_weights=args.sift2_weights,
        tract_mask=args.tract_mask,
        out_dir=args.out_dir,
        out_prefix=args.out_prefix,
        overwrite=args.overwrite,
        skip_roi_projection=args.skip_roi_projection,
        skip_gmwmi_intersection=args.skip_gmwmi_intersection,
        skip_viz=args.skip_viz,
        interactive_viz=args.interactive_viz,
        orig_color=args.orig_color,
        fsub_color=args.fsub_color,
        roi1_color=args.roi1_color,
        roi2_color=args.roi2_color,
        roi_opacity=args.roi_opacity,
        fsub_linewidth=args.fsub_linewidth,
        img_viz=args.img_viz,
        axial_offset=args.axial_offset,
        saggital_offset=args.saggital_offset,
        camera_angle=args.camera_angle,
    )
