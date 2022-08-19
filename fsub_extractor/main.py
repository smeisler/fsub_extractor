import argparse
import os.path as op
import warnings
from dask import delayed
from fsub_extractor.utils.utils import *

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
        help="Path to tract file (.tck or .trk). Should be in the same space as FreeSurfer and scalar map inputs.",
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
        help="Path to reference file, if passing in a .trk file. Typically a nifti-related object from the native diffusion used for streamlines generation.",
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
        "--scalars",
        help="Comma delimited list (no spaces) of scalar map(s) to sample streamlines on (.nii.gz). Should be in the same space as .tck and FreeSurfer inputs.",
    )
    parser.add_argument(
        "--search-dist",
        "--search_dist",
        help="Distance in mm to search ahead of streamlines for ROIs (float). Default is 4.0 mm.",
        type=float,
        default=4.0,
    )
    parser.add_argument(
        "--projfrac-params",
        "--projfrac_params",
        help="Comma delimited list (no spaces) of projfrac parameters for mri_surf2vol / mri_label2vol. Provided as start,stop,delta. Default is --projfrac-params='-2,0,0.05'. Start must be negative to project into white matter.",
        default="-2,0,0.05",
        metavar=("START,STOP,DELTA"),
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
        "--scratch",
        "--scratch",
        help="Path to scratch directory. Default is current directory.",
        type=op.abspath,
        default=os.getcwd(),
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
        help="Float (-1,1) describing where to display axial slice. -1.0 is completely bottom, 1.0 is completely top. Default is 0.0.",
        type=float,
        default=0.0,
    )
    parser.add_argument(
        "--saggital-offset",
        "--saggital_offset",
        help="Float (-1,1) describing where to display saggital slice. -1.0 is completely left, 1.0 is completely right. Default is 0.0.",
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
        scalars=args.scalars,
        search_dist=str(args.search_dist),
        projfrac_params=args.projfrac_params,
        out_dir=args.out_dir,
        out_prefix=args.out_prefix,
        scratch=args.scratch,
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


def extractor(
    subject,
    tract,
    roi1,
    fs_dir,
    hemi,
    # fs_license,
    trk_ref,
    gmwmi,
    roi2,
    scalars,
    search_dist,
    projfrac_params,
    out_dir,
    out_prefix,
    scratch,
    overwrite,
    skip_roi_projection,
    skip_gmwmi_intersection,
    skip_viz,
    interactive_viz,
    orig_color,
    fsub_color,
    roi1_color,
    roi2_color,
    roi_opacity,
    fsub_linewidth,
    img_viz,
    axial_offset,
    saggital_offset,
    camera_angle,
):

    # TODO: add docs

    ### Check for assertion errors ###
    # 1. If ROIs are to be projected, make sure FS dir exists, hemispheres are valid, and proj-frac params are valid
    if skip_roi_projection == False:
        # Check FS dir
        if fs_dir == None:
            raise Exception("No FreeSurfer directory passed in.")
        fs_sub_dir = op.join(fs_dir, subject)
        if op.isdir(op.join(fs_sub_dir, "surf")) == False:
            raise Exception(
                fs_sub_dir + " does not appear to be a valid FreeSurfer directory."
            )
        # Check hemi(s)
        if hemi == None:
            raise Exception("--hemi must be specified if not skipping ROI projection.")
        else:
            hemi_list = hemi.split(",")
            for hemisphere in hemi_list:
                if hemisphere != "lh" and hemisphere != "rh":
                    raise Exception(
                        "Hemispheres must be either 'lh' or 'rh'. Current input is "
                        + str(hemi_list)
                        + "."
                    )
            if len(hemi_list) > 2:
                raise Exception(
                    "Invalid number of hemispheres specified. Number of inputs should match the number of ROIs (or just one input if both ROIs are in the same hemisphere)."
                )
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

    # 2. Make sure ROI(s) exist and are the correct file types
    if op.exists(roi1) == False:
        raise Exception("ROI file " + roi1 + " is not found on the system.")
    if roi1[-7:] != ".nii.gz" and roi1[-4:] != ".mgz" and roi1[-6:] != ".label":
        raise Exception("ROI file " + roi1 + " is not a supported file type.")
    if roi2 != None and op.exists(roi2) == False:
        raise Exception("ROI file " + roi2 + " is not found on the system.")
    if (
        roi2 != None
        and roi2[-7:] != ".nii.gz"
        and roi2[-4:] != ".mgz"
        and roi2[-6:] != ".label"
    ):
        raise Exception("ROI file " + roi2 + " is not of a supported file type.")

    # 3. Make sure tract file is okay
    if op.exists(tract) == False:
        raise Exception("Tract file " + tract + " is not found on the system.")
    if tract[-4:] not in [".trk", ".tck"]:
        raise Exception("Tract file " + tract + " is not of a supported file type.")
    if tract[-4:] == ".trk" and trk_ref == None:
        raise Exception(".trk file passed in without a --trk-ref input.")

    # 4. Check if gmwmi exists or can be created if needed
    if gmwmi == None and fs_dir == None and skip_gmwmi_intersection == False:
        raise Exception(
            "GMWMI cannot be created unless a FreeSurfer directory is passed into --fs-dir."
        )
    elif gmwmi != None and op.exists(gmwmi) == False:
        warnings.warn(
            "GMWMI was specified but not found on the system. A new one will be created from the FreeSurfer input."
        )
        gmwmi = None

    # 5. Check if scalar files exist
    if scalars != None:
        scalar_list = [op.abspath(scalar) for scalar in scalars.split(",")]
        for scalar in scalar_list:
            if op.exists(scalar) == False:
                raise Exception("Scalar map " + scalar + " not found on the system.")

    # 6. Check if out and scratch directories exist
    if op.isdir(out_dir) == False:
        raise Exception("Output directory " + out_dir + " not found on the system.")
    if op.isdir(scratch) == False:
        raise Exception("Scratch directory " + scratch + " not found on the system.")

    # 7. Make sure FS license is valid [TODO: HOW??]

    # 8. Make sure camera angle is valid
    if camera_angle != "saggital" and camera_angle != "axial":
        raise Exception(
            "Camera angle must be either 'saggital' or 'axial'. '"
            + camera_angle
            + "' was specified."
        )

    ### Prepare output directories ###
    # Add an underscore to separate prefix from file names if a prefix is specified
    if len(out_prefix) > 0:
        if out_prefix[-1] != "_":
            out_prefix += "_"

    # Make output and scratch folders if they do not exist, and define the naming convention
    if op.isdir(op.join(out_dir, subject)) == False:
        os.mkdir(op.join(out_dir, subject))
    if op.isdir(op.join(scratch, subject + "_scratch")) == False:
        os.mkdir(op.join(scratch, subject + "_scratch"))
    outpath_base = op.join(out_dir, subject, out_prefix)
    scratch_base = op.join(scratch, subject + "_scratch", out_prefix)

    # TODO: Parallelize GMWMI creation, roi projection/intersection
    ### Create a GMWMI, intersect with ROI ###
    if skip_gmwmi_intersection == False:
        if gmwmi == None:
            print("\n Creating a GMWMI \n")
            gmwmi = anat_to_gmwmi(fs_sub_dir, outpath_base, overwrite)

    ### Set flag for whether two rois were passed in ###
    if roi2 != None:
        two_rois = True
    else:
        two_rois = False

    ### Project the ROI(s) into the white matter and intersect with GMWMI ###
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

    ### Process ROI2 the same way if specified ###
    if two_rois == False:
        rois_in = roi1_intersected
        roi2_projected = None
        roi2_intersected = None
    else:
        if skip_roi_projection == False:
            print("\n Projecting ROI2 \n")
            roi2_projected = project_roi(
                roi_in=roi2,
                fs_dir=fs_dir,
                subject=subject,
                hemi=hemi_list[-1],
                projfrac_params=projfrac_params_list,
                outpath_base=outpath_base,
                overwrite=overwrite,
            )
        else:
            roi2_projected = roi2
        if skip_gmwmi_intersection == False:
            print("\n Intersecting ROI2 with GMWMI \n")
            roi2_intersected = intersect_gmwmi(
                roi_in=roi2_projected,
                gmwmi=gmwmi,
                outpath_base=op.join(
                    out_dir,
                    subject,
                    op.basename(roi2_projected).removesuffix(".nii.gz"),
                ),
                overwrite=overwrite,
            )
        else:
            roi2_intersected = roi2_projected

        ### Merge ROIS ###
        print("\n Merging ROIs \n")
        rois_in = merge_rois(
            roi1=roi1_intersected,
            roi2=roi2_intersected,
            out_file=outpath_base + "rois_merged.nii.gz",
            overwrite=overwrite,
        )

    ### Convert .trk to .tck if needed ###
    if tract[-4:] == ".trk":
        print("\n Converting .trk to .tck \n")
        tck_file = trk_to_tck(tract, gmwmi, out_dir, overwrite)
    else:
        tck_file = tract

    ### Run MRtrix Tract Extraction ###
    print("\n Extracing the sub-bundle \n")
    extracted_tck = extract_tck_mrtrix(
        tck_file, rois_in, outpath_base, search_dist, two_rois, overwrite
    )
    print("\n The extracted tract is located at " + extracted_tck + ".\n")

    ### Visualize the outputs ####
    if skip_viz == False:
        from fsub_extractor.viz.fury_viz import visualize_sub_bundles

        # Convert color strings to lists
        orig_color_list = [float(color) for color in orig_color.split(",")]
        fsub_color_list = [float(color) for color in fsub_color.split(",")]
        roi1_color_list = [float(color) for color in roi1_color.split(",")]
        roi2_color_list = [float(color) for color in roi2_color.split(",")]

        # Set reference / background image if it is specified
        if img_viz == None:
            ref_anat = gmwmi
            show_anat = False
        else:
            ref_anat = img_viz
            show_anat = True

        # Make a picture for each hemisphere passed in, if saggital view
        if hemi == None:
            hemi_list = ["lh"]
        else:
            hemi_list = hemi.split(
                ","
            )  # TODO: redundant to define twice, already defined above if not skip projection

        if camera_angle == "saggital":
            for hemi_to_viz in hemi_list:
                visualize_sub_bundles(
                    orig_bundle=tract,
                    fsub_bundle=extracted_tck,
                    ref_anat=ref_anat,
                    outpath_base=outpath_base + hemi_to_viz + "_",
                    roi1=roi1_intersected,
                    roi2=roi2_intersected,
                    orig_color=orig_color_list,
                    fsub_color=fsub_color_list,
                    roi1_color=roi1_color_list,
                    roi2_color=roi2_color_list,
                    roi_opacity=roi_opacity,
                    fsub_linewidth=fsub_linewidth,
                    interactive=interactive_viz,
                    show_anat=show_anat,
                    axial_offset=axial_offset,
                    saggital_offset=saggital_offset,
                    camera_angle=camera_angle,
                    hemi=hemi_to_viz,
                )
        else:
            visualize_sub_bundles(
                orig_bundle=tract,
                fsub_bundle=extracted_tck,
                ref_anat=ref_anat,
                outpath_base=outpath_base + camera_angle + "_",
                roi1=roi1_intersected,
                roi2=roi2_intersected,
                orig_color=orig_color_list,
                fsub_color=fsub_color_list,
                roi1_color=roi1_color_list,
                roi2_color=roi2_color_list,
                roi_opacity=roi_opacity,
                fsub_linewidth=fsub_linewidth,
                interactive=interactive_viz,
                show_anat=show_anat,
                axial_offset=axial_offset,
                saggital_offset=saggital_offset,
                camera_angle=camera_angle,
            )

    ### [TODO: Add scalar map stats] ###

    print("\n DONE \n")
