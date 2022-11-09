import argparse
import os.path as op
from fsub_extractor.utils.utils import *

# Add input arguments
def get_parser():

    parser = argparse.ArgumentParser(
        description="Extracts tract-average and along-the-tract measures of an input scalar metric (.nii.gz) along a specified streamline file (.tck/.trk)."
    )
    parser.add_argument(
        "--tract",
        help="Path to tract file (.tck or .trk). Should be in the same space as the scalar map inputs.",
        type=op.abspath,
        required=True,
    )
    #parser.add_argument(
    #    "--roi1",
    #    help="First ROI file (.mgz, .label, or .nii.gz). File should be binary (1 in ROI, 0 elsewhere).",
    #    type=op.abspath,
    #    required=True,
    #)
    parser.add_argument(
        "--scalars",
        help="Comma delimited list (no spaces) of path(s) to scalar maps (e.g. FA). This will also be used as a spatial reference file is a .trk file is passed in as a streamlines object.",
        required=True,
    )
    #parser.add_argument(
    #    "--roi2",
    #    help="Second ROI file (.mgz, .label, or .nii.gz). If specified, program will find streamlines connecting ROI1 and ROI2. File should be binary (1 in ROI, 0 elsewhere).",
    #    type=op.abspath,
    #)
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

    return parser


def main():

    # Parse arguments and run the main code
    parser = get_parser()
    args = parser.parse_args()

    main = extractor(
        tract=args.tract,
        #roi1=args.roi1,
        #roi2=args.roi2,
        scalars=args.scalars,
        out_dir=args.out_dir,
        out_prefix=args.out_prefix,
        scratch=args.scratch,
        overwrite=args.overwrite,
    )


def extractor(
    tract,
    #roi1,
    #roi2,
    scalars,
    out_dir,
    out_prefix,
    scratch,
    overwrite,
):

    # TODO: add docs

    ### Split string of scalars in to list
    
    ### Check for assertion errors ###

    # 1. Make sure tract file is okay
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
    subject_base = op.join(out_dir,subject)
    outpath_base = op.join(subject_base, out_prefix)
    scratch_base = op.join(scratch, subject + "_scratch", out_prefix)

    # TODO: Parallelize GMWMI creation, roi projection/intersection
    ### Create a GMWMI, intersect with ROI ###
    if skip_gmwmi_intersection == False:
        if gmwmi == None:
            print("\n Creating a GMWMI \n")
            gmwmi = anat_to_gmwmi(fs_sub_dir, subject_base, overwrite)

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
        tck_file, rois_in, outpath_base, search_dist, search_type, two_rois, overwrite
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
