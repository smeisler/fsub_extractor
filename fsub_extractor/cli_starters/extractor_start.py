import argparse
import os.path as op
from os import getcwd
from pathlib import Path
from fsub_extractor.functions.extractor import extractor

# Add input arguments
def get_parser():

    parser = argparse.ArgumentParser(
        description="Functionally segments a tract file based on intersections with prespecified ROI(s) in gray matter."
    )
    parser.add_argument(
        "--subject",
        help="Subject name. This must match the subject name in the FreeSurfer folder.",
        required=True,
        metavar=("sub-XXX"),
    )
    extract_or_generate = parser.add_mutually_exclusive_group(required=True)
    extract_or_generate.add_argument(
        "--tract",
        help="Path to original tract file (.tck or .trk). Should be in DWI space. Must either specify this or choose '--generate'.",
        type=validate_file,
        metavar=("/PATH/TO/TRACT.trk|.tck"),
        action=CheckExt({".trk", ".tck"}),
    )
    extract_or_generate.add_argument(
        "--generate",
        help="Generate an FSuB instead of extracting it from a tract file. Must either specify this or input a file for '--tract'.",
        default=False,
        action="store_true",
    )
    parser.add_argument(
        "--tract-name",
        "--tract_name",
        help="Label for tract used in file names. Should not contain spaces. E.g., 'LeftAF' or 'wholebrain'. Default is 'tract'.",
        default="tract",
    )
    parser.add_argument(
        "--roi1",
        help="Path to first ROI file (.mgz, .label, .gii, or .nii.gz). File should be binary (1 in ROI, 0 elsewhere).",
        type=validate_file,
        required=True,
        metavar=("/PATH/TO/ROI1.mgz|.label|.gii|.nii.gz"),
        action=CheckExt({".mgz", ".label", ".gii", ".nii.gz"}),
    )
    parser.add_argument(
        "--roi1-name",
        "--roi1_name",
        help="Label for ROI1 outputs. Default is roi1",
        default="roi1",
    )
    parser.add_argument(
        "--roi2",
        help="Path to second ROI file (.mgz, .label, .gii, or .nii.gz). If specified, program will find streamlines connecting ROI1 and ROI2. File should be binary (1 in ROI, 0 elsewhere).",
        type=validate_file,
        metavar=("/PATH/TO/ROI2.mgz|.label|.gii|.nii.gz"),
        action=CheckExt({".mgz", ".label", ".gii", ".nii.gz"}),
    )
    parser.add_argument(
        "--roi2-name",
        "--roi2_name",
        help="Label for ROI2 outputs. Default is roi2",
        default="roi2",
    )
    parser.add_argument(
        "--hemi",
        help="FreeSurfer hemisphere name(s) corresponding to locations of the ROIs, separated by a comma (no spaces) if different for two ROIs (e.g 'lh,rh'). Required unless --skip-roi-proj is specified.",
        choices=["lh", "rh", "lh,rh", "rh,lh"],
        metavar=("{lh|rh|lh,rh|rh,lh}"),
    )
    parser.add_argument(
        "--fs-dir",
        "--fs_dir",
        help="Path to FreeSurfer subjects directory. It should have a folder in it with your subject name. Required unless --skip-roi-proj is specified. If not specified, will be inferred from environment (e.g., `echo $SUBJECTS_DIR`).",
        type=op.abspath,
        metavar=("/PATH/TO/FreeSurfer/SUBJECTSDIR/"),
    )
    # parser.add_argument(
    #    "--fs-license",
    #    "--fs-license",
    #    help="Path to FreeSurfer license.",
    #    type=op.abspath,
    #    metavar=("/PATH/TO/FS_LICENSE.txt),
    #    action=CheckExt({".txt"}),
    # )  # TODO: MAKE REQUIRED LATER FOR CONTAINER?
    # parser.add_argument(
    #    "--gmwmi",
    #    help="Path to GMWMI image (.nii.gz or .mif). If not specified or not found, it will be created from FreeSurfer inputs. Ignored if --skip-gmwmi-intersection is specified. Should be in DWI space.",
    #    type=validate_file,
    #    metavar=("/PATH/TO/GMWMI.nii.gz|.mif"),
    #    action=CheckExt({".nii.gz", ".mif"}),
    # )
    parser.add_argument(
        "--projfrac-params",
        "--projfrac_params",
        help="Comma delimited list (no spaces) of projfrac parameters for mri_surf2vol / mri_label2vol. Provided as start,stop,delta. Default is --projfrac-params='-1,0,0.05'. Start must be negative to project into white matter.",
        default="-1,0,0.05",
        metavar=("START,STOP,DELTA"),
    )
    parser.add_argument(
        "--fivett",
        help="Path to 5TT image (.nii.gz or .mif). Skips making it from FreeSurfer inputs. This is used if you opt to intersect ROIs with the GMWMI, and/or an FSuB is being generated (--generate).",
        type=validate_file,
        metavar=("/PATH/TO/5TT.nii.gz|.mif"),
        action=CheckExt({".nii.gz", ".mif"}),
    )
    parser.add_argument(
        "--gmwmi-thresh",
        "--gmwmi_thresh",
        help="Threshold above which to binarize the GMWMI image. Default is 0.0",
        type=check_positive_float,
        default=0.0,
        metavar=("THRESHOLD"),
    )
    parser.add_argument(
        "--skip-fivett-registration",
        "--skip_fivett-registration",
        help="If not specified, a registration (if supplied) will be applied to the 5TT and GMWMI images. Specify this flag if your 5TT image is in DWI space, but FreeSurfer and DWI inputs are not aligned.",
        default=False,
        action="store_true",
    )
    parser.add_argument(
        "--skip-roi-projection",
        "--skip_roi_projection",
        help="Skip projecting ROI into WM (not recommended unless ROI is already projected). Default is to not skip projection. ROIs must already be in .nii.gz if this is specified.",
        default=False,
        action="store_true",
    )
    parser.add_argument(
        "--skip-gmwmi-intersection",
        "--skip_gmwmi_intersection",
        help="Skip intersecting ROI with GMWMI (not recommended unless ROI is already intersected). Default is to not skip intersection.",
        default=False,
        action="store_true",
    )
    parser.add_argument(
        "--out-dir",
        "--out_dir",
        help="Directory where outputs will be stored (a subject-folder will be created there if it does not exist). Default is current directory.",
        type=op.abspath,
        default=getcwd(),
        metavar=("/PATH/TO/OUTDIR/"),
    )
    parser.add_argument(
        "--overwrite",
        help="Whether to overwrite outputs. Default is to overwrite.",
        default=True,
        action=argparse.BooleanOptionalAction,
    )

    # Streamline masking arguments
    mask_group = parser.add_argument_group("Options for Streamline Masking")
    mask_group.add_argument(
        "--exclude-mask",
        "--exclude_mask",
        help="Path to exclusion mask (.nii.gz or .mif). If specified, streamlines that enter this mask will be discarded. Must be in DWI space.",
        type=validate_file,
        metavar=("/PATH/TO/EXCLUDE_MASK.nii.gz|.mif"),
        action=CheckExt({".nii.gz", ".mif"}),
    )
    mask_group.add_argument(
        "--include-mask",
        "--include_mask",
        help="Path to inclusion mask (.nii.gz or .mif). If specified, streamlines must intersect with this mask to be included (e.g., a waypoint ROI). Must be in DWI space.",
        type=validate_file,
        metavar=("/PATH/TO/INCLUDE_MASK.nii.gz|.mif"),
        action=CheckExt({".nii.gz", ".mif"}),
    )
    mask_group.add_argument(
        "--streamline-mask",
        "--streamline_mask",
        help="Path to streamline mask (.nii.gz or .mif). If specified, streamlines exiting this mask will be truncated. Must be in DWI space.",
        type=validate_file,
        metavar=("/PATH/TO/STREAMLINE_MASK.nii.gz|.mif"),
        action=CheckExt({".nii.gz", ".mif"}),
    )

    # Registration arguments
    reg_group = parser.add_argument_group("Options for Registration")
    reg_dir_group = reg_group.add_mutually_exclusive_group()
    reg_dir_group.add_argument(
        "--fs2dwi",
        help="Path to MRTrix-ready or ANTs/ITK-generated registration for mapping FreeSurfer-to-DWI space. Mutually exclusive with --dwi2fs.",
        type=validate_file,
        metavar=("/PATH/TO/FS2DWI-REG.txt"),
        action=CheckExt({".txt"}),
    )
    reg_dir_group.add_argument(
        "--dwi2fs",
        help="Path to MRTrix-ready or ANTs/ITK-generated registration for mapping DWI-to-FreeSurfer space. Mutually exclusive with --fs2dwi.",
        type=validate_file,
        metavar=("/PATH/TO/DWI2FS-REG.txt"),
        action=CheckExt({".txt"}),
    )
    reg_group.add_argument(
        "--reg-type",
        "--reg_type",
        choices=["mrtrix", "itk"],
        help="Registration software compatability for .txt files. Only set if the program does not figure this out automatically.",
    )

    # Extractor-specific arguments
    ext_args = parser.add_argument_group("Options Specific to Streamline Extractor")
    ext_args.add_argument(
        "--search-dist",
        "--search_dist",
        help="Distance in mm to search from streamlines for ROIs (float). Default is 3.0 mm. Ignored if --search-type is 'end' or 'all'.",
        type=check_positive_float,
        default=3.0,
        metavar=("DISTANCE"),
    )
    ext_args.add_argument(
        "--search-type",
        "--search_type",
        choices=["forward", "radial", "reverse", "end", "all"],
        help="Method of searching for streamlines (see documentation for MRTrix3 'tck2connectome'). Default is radial.",
        default="radial",
    )
    ext_args.add_argument(
        "--sift2-weights",
        "--sift2_weights",
        help="Path to SIFT2 weights file corresponding to input tract. If supplied, the sum of weights will be output with streamline extraction.",
        type=validate_file,
        metavar=("/PATH/TO/SIFT2_WEIGHTS.csv|.txt"),
        action=CheckExt({".csv", ".txt"}),
    )

    # Generator-specific arguments
    gen_args = parser.add_argument_group("Options Specific to Streamline Generator")
    gen_args.add_argument(
        "--wmfod",
        help="Path to white matter FOD image (.nii.gz or .mif). Used as source for iFOD2 tracking.",
        type=validate_file,
        metavar=("/PATH/TO/WMFOD.nii.gz|.mif"),
        action=CheckExt({".nii.gz", ".mif"}),
    )
    gen_args.add_argument(
        "--n-streamlines",
        "--n_streamlines",
        help="Number of streamlines per generated FSuB ('-select' param of tckgen). Should be an even number. Default is 1000.",
        type=check_positive_int,
        metavar=("N"),
        default=1000,
    )
    gen_args.add_argument(
        "--tckgen-params",
        "--tckgen_params",
        help="Path to .txt file containing additional arguments for MRtrix tckgen, space-delimited (e.g., -minlength X -maxlength X)",
        type=validate_file,
        metavar=("/PATH/TO/PARAMS.txt"),
        action=CheckExt({".txt"}),
    )

    # Visualization arguments
    viz_args = parser.add_argument_group("Options for Visualization")
    viz_args.add_argument(
        "--make-viz",
        "--make_viz",
        help="Whether to make the output figure. Default is to not produce the figure.",
        default=False,
        action="store_true",
    )
    viz_args.add_argument(
        "--interactive-viz",
        "--interactive_viz",
        help="Whether to produce an interactive visualization. Default is not interactive.",
        default=False,
        action="store_true",
    )
    viz_args.add_argument(
        "--img-viz",
        "--img-viz",
        help="Path to image to plot in visualization (.nii.gz). Should be in DWI space.",
        type=validate_file,
        metavar=("/PATH/TO/BACKGROUND_IMG.nii.gz"),
        action=CheckExt({".nii.gz"}),
    )
    viz_args.add_argument(
        "--orig-color",
        "--orig_color",
        help="Comma-delimited (no spaces) color spec for original bundle in visualization, as fractional R,G,B. Default is 0.8,0.8,0.",
        default="0.8,0.8,0",
        metavar=("R,G,B"),
    )
    viz_args.add_argument(
        "--fsub-color",
        "--fsub_color",
        help="Comma-delimited (no spaces) color spec for FSuB bundle in visualization, as fractional R,G,B. Default is 0.2,0.6,1.",
        default="0.2,0.6,1",
        metavar=("R,G,B"),
    )
    viz_args.add_argument(
        "--roi1-color",
        "--roi1_color",
        help="Comma-delimited (no spaces) color spec for ROI1 in visualization, as fractional R,G,B. Default is 0.2,1,1.",
        default="0.2,1,1",
        metavar=("R,G,B"),
    )
    viz_args.add_argument(
        "--roi2-color",
        "--roi2_color",
        help="Comma-delimited (no spaces) color spec for ROI2 in visualization, as fractional R,G,B. Default is 1,0.2,1.",
        default="1,0.2,1",
        metavar=("R,G,B"),
    )
    viz_args.add_argument(
        "--roi-opacity",
        "--roi_opacity",
        help="Opacity (0,1) for ROI(s) in visualization (float). Default is 0.7.",
        default=0.7,
        type=float,
        metavar=("OPACITY"),
        choices=[Range(0.0, 1.0)],
    )
    viz_args.add_argument(
        "--fsub-linewidth",
        "--fsub_linewidth",
        help="Linewidth for extracted steamlines in visualization (float). Default is 3.0.",
        default=3.0,
        type=check_positive_float,
        metavar=("LINEWIDTH"),
    )
    viz_args.add_argument(
        "--axial-offset",
        "--axial_offset",
        help="Float (-1,1) describing where to display axial slice. -1.0 is bottom, 1.0 is top. Default is 0.0.",
        type=float,
        default=0.0,
        metavar=("OFFSET"),
        choices=[Range(-1.0, 1.0)],
    )
    viz_args.add_argument(
        "--saggital-offset",
        "--saggital_offset",
        help="Float (-1,1) describing where to display saggital slice. -1.0 is left, 1.0 is right. Default is 0.0.",
        type=float,
        default=0.0,
        metavar=("OFFSET"),
        choices=[Range(-1.0, 1.0)],
    )
    viz_args.add_argument(
        "--camera-angle",
        "--camera_angle",
        choices=["saggital", "axial"],
        help="Camera angle for visualization. Default is 'saggital.'",
        default="saggital",
    )

    return parser


# Check that files exist
def validate_file(arg):
    if (file := Path(arg)).is_file():
        return op.abspath(file)
    else:
        raise FileNotFoundError(arg)


# Function for checking file extensions
def CheckExt(choices):
    class Act(argparse.Action):
        def __call__(self, parser, namespace, fname, option_string=None):
            file_has_valid_ext = False
            for choice in choices:
                len_ext = len(choice)
                if fname[(-1 * len_ext) :] == choice:
                    file_has_valid_ext = True
                    break

            if file_has_valid_ext == False:
                option_string = "({})".format(option_string) if option_string else ""
                parser.error(
                    "file doesn't end with one of {}{}".format(choices, option_string)
                )
            else:
                setattr(namespace, self.dest, fname)

    return Act


# For checking ranges of inputs
class Range(object):
    def __init__(self, start, end):
        self.start = start
        self.end = end

    def __eq__(self, other):
        return self.start <= other <= self.end


# Check for positive values
def check_positive_float(value):
    value = float(value)
    if value <= 0:
        raise argparse.ArgumentTypeError("%s is not positive" % value)
    return value


def check_positive_int(value):
    value = int(value)
    if value <= 0:
        raise argparse.ArgumentTypeError("%s is not positive" % value)
    return value


def main():

    # Parse arguments and run the main code
    parser = get_parser()
    args = parser.parse_args()

    # Temp: generator doesn't work yet, so do not let it run
    if args.generate:
        raise Exception(
            "Generator function (--generate) is not functional yet. Please use --tract method instead, for now."
        )

    main = extractor(
        subject=args.subject,
        tract=args.tract,
        generate=args.generate,
        tract_name=args.tract_name,
        roi1=args.roi1,
        roi1_name=args.roi1_name,
        roi2=args.roi2,
        roi2_name=args.roi2_name,
        hemi=args.hemi,
        fs_dir=args.fs_dir,
        # fs_license=args.fs_license,
        # gmwmi=args.gmwmi,
        projfrac_params=args.projfrac_params,
        fivett=args.fivett,
        gmwmi_thresh=args.gmwmi_thresh,
        skip_fivett_registration=args.skip_fivett_registration,
        skip_roi_projection=args.skip_roi_projection,
        skip_gmwmi_intersection=args.skip_gmwmi_intersection,
        out_dir=args.out_dir,
        overwrite=args.overwrite,
        exclude_mask=args.exclude_mask,
        include_mask=args.include_mask,
        streamline_mask=args.streamline_mask,
        fs2dwi=args.fs2dwi,
        dwi2fs=args.dwi2fs,
        reg_type=args.reg_type,
        search_dist=str(args.search_dist),
        search_type=str(args.search_type),
        sift2_weights=args.sift2_weights,
        wmfod=args.wmfod,
        n_streamlines=args.n_streamlines,
        tckgen_params=args.tckgen_params,
        make_viz=args.make_viz,
        interactive_viz=args.interactive_viz,
        img_viz=args.img_viz,
        orig_color=args.orig_color,
        fsub_color=args.fsub_color,
        roi1_color=args.roi1_color,
        roi2_color=args.roi2_color,
        roi_opacity=args.roi_opacity,
        fsub_linewidth=args.fsub_linewidth,
        axial_offset=args.axial_offset,
        saggital_offset=args.saggital_offset,
        camera_angle=args.camera_angle,
    )
