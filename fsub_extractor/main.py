import argparse
import os.path as op
import warnings
from fsub_extractor.utils.utils import *

# Add input arguments
def get_parser():

    parser = argparse.ArgumentParser(
        description="Functionally segments a tract file based on intersections with prespecified ROI(s) in gray matter."
    )
    parser.add_argument(
        "--subject",
        help="Subject name. Unless --skip-roi-proj is specified, this must match the name in the FreeSurfer folder.",
        type=str,
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
        help="Path to FreeSurfer directory for the subject. Required unless --skip-roi-proj is specified.",
        type=op.abspath,
    )
    parser.add_argument(
        "--hemi",
        help="FreeSurfer hemisphere name(s) corresponding to locations of the ROIs, separated by a comma (no spaces) if different for two ROIs (e.g 'lh,rh'). Required unless --skip-roi-proj is specified.",
    )
    #parser.add_argument(
    #    "--fs-license",
    #    "--fs-license",
    #    help="Path to FreeSurfer license.",
    #    type=op.abspath,
    #)  # TODO: MAKE REQUIRED LATER
    parser.add_argument(
        "--trk-ref", "--trk_ref"
        help="Path to reference file, if passing in a .trk file. Typically a nifti-related object from the native diffusion used for streamlines generation",
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
        help="Comma-delimited (no spaces) color spec for original bundle in visualization, as R,G,B. Default is 0.8,0.8,0.",
        default="0.8,0.8,0",
    )
    parser.add_argument(
        "--fsub-color",
        "--fsub_color",
        help="Comma-delimited (no spaces) color spec for FSuB bundle in visualization, as R,G,B. Default is 0.2,0.6,1.",
        default="0.2,0.6,1",
    )
    parser.add_argument(
        "--roi1-color",
        "--roi1_color",
        help="Comma-delimited (no spaces) color spec for ROI1 in visualization, as R,G,B. Default is 0.2,1,1.",
        default="0.2,1,1",
    )
    parser.add_argument(
        "--roi2-color",
        "--roi2_color",
        help="Comma-delimited (no spaces) color spec for ROI2 in visualization, as R,G,B. Default is 0.2,1,1.",
        default="0.2,1,1",
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
        type=int,
        default=0 # TODO: get floats to work
    )
    parser.add_argument(
        "--saggital-offset",
        "--saggital_offset",
        help="Float (-1,1) describing where to display saggital slice. -1 is left, 1 is right. Default is 0.0.",
        type=int,
        default=0 # TODO: get floats to work
    )
    parser.add_argument(
        "--camera-angle",
        "--camera_angle",
        help="Camera angle for visualization. Choices are either 'saggital' or 'axial'. Default is 'saggital.'",
        default="saggital"
    )
    

    return parser


def main():

    # Parse arguments and run the main code
    parser =  get_parser()
    args = parser.parse_args()

    main = extractor(
        subject=args.subject,
        tract=args.tract,
        roi1=args.roi1,
        fs_dir=args.fs_dir,
        hemi=args.hemi,
        #fs_license=args.fs_license,
        trk_ref=args.trk_ref,
        gmwmi=args.gmwmi,
        roi2=args.roi2,
        scalars=args.scalars,
        search_dist=str(args.search_dist),
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
    #fs_license,
    trk_ref,
    gmwmi,
    roi2,
    scalars,
    search_dist,
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
    img_viz,
    axial_offset,
    saggital_offset,
    camera_angle,
):

    # TODO: add docs

    ### Check for assertion errors ###
    # 1. If ROIs are to be projected, make sure FS dir exists and hemispheres are valid
    fs_sub_dir = op.join(fs_dir, subject)
    if skip_roi_projection == False:
        if op.isdir(op.join(fs_sub_dir, "surf")) == False:
            raise Exception(
                fs_sub_dir + " does not appear to be a valid FreeSurfer directory."
            )
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
        raise Exception("Tract file " + tract+ " is not found on the system.")
    if tract[-4:] not in [".trk", ".tck"]:
        raise Exception("Tract file " + tract+ " is not of a supported file type.")
    if tract[-4:] == ".trk" and trk_ref == None:
        raise Exception(".trk file passed in without a --trk-ref input.")

    # 4. Check if gmwmi exists or can be created if needed
    if gmwmi != None and op.exists(gmwmi) == False:
        warnings.warn(
            "GMWMI was specified but not found on the system. A new one will be created from the FreeSurfer input."
        )
        gmwmi = None
    if gmwmi == None and fs_dir == None and skip_gmwmi_intersection == False:
        raise Exception(
            "GMWMI cannot be created unless a FreeSurfer directory is passed into --fs-dir."
        )

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
        raise Exception("Camera angle must be either 'saggital' or 'axial'. '" + camera_angle + "' was specified.")

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

    ### Set flag for whether two rois were passed in ###
    if roi2 != None:
        two_rois = True
    else:
        two_rois = False

    ### Project the ROI(s) into the white matter ###
    if skip_roi_projection == False:
        print("\n Projecting ROI1 \n")
        roi1_projected = project_roi(
            roi1, fs_dir, subject, hemi_list[0], outpath_base, overwrite
        )
    else:
        print("\n Skipping ROI projection \n")
        roi1_projected = roi1

    if two_rois == False:
        rois_in = roi1_projected
        roi2_projected = None
    else:
        if skip_roi_projection == False:
            print("\n Projecting ROI2 \n")
            roi2_projected = project_roi(
                roi2, fs_dir, subject, hemi_list[-1], outpath_base, overwrite
            )
        else:
            roi2_projected = roi2
        ### Merge ROIS ###
        print("\n Merging ROIs \n")
        roi1_basename = op.basename(roi1_projected).removesuffix(".nii.gz")
        roi2_basename = op.basename(roi2_projected).removesuffix(".nii.gz")
        rois_in = merge_rois(
            roi1,
            roi2,
            outpath_base + roi1_basename + "_" + roi2_basename + "_merged.nii.gz",
            overwrite,
        )

    ### Create a GMWMI, intersect with ROI ###
    if skip_gmwmi_intersection == False:
        if gmwmi == None:
            print("\n Creating a GMWMI \n")
            gmwmi = anat_to_gmwmi(fs_sub_dir, outpath_base, overwrite)

        # Intersect ROI with GMWMI
        print("\n Intersecting ROI(s) with GMWMI \n")
        intersected_roi = intersect_gmwmi(rois_in, gmwmi, outpath_base, overwrite)
    else:
        intersected_roi = rois_in

    ### Convert .trk to .tck if needed ###
    if tract[-4:] == ".trk":
        print("\n Converting .trk to .tck \n")
        tck_file = trk_to_tck(tract, gmwmi, out_dir, overwrite)
    else:
        tck_file = tract
        
    ### Run MRtrix Tract Extraction ###
    print("\n Extracing the sub-bundle \n")
    extracted_tck = extract_tck_mrtrix(
        tck_file, intersected_roi, outpath_base, search_dist, two_rois, overwrite
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

        visualize_sub_bundles(
            orig_bundle=tract,
            fsub_bundle=extracted_tck,
            ref_anat=ref_anat,
            outpath_base=outpath_base,
            roi1=roi1_projected,
            roi2=roi2_projected,
            orig_color=orig_color_list,
            fsub_color=fsub_color_list,
            roi1_color=roi1_color_list,
            roi2_color=roi2_color_list,
            interactive=interactive_viz,
            show_anat=show_anat,
            axial_offset=axial_offset,
            saggital_offset=saggital_offset,
            camera_angle=camera_angle,
        )
    
    ### [TODO: Add scalar map stats] ###
