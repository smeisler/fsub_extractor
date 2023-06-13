import os.path as op
import warnings
from numpy import unique
from fsub_extractor.utils.anat_utils import *
from fsub_extractor.utils.system_utils import *
from fsub_extractor.utils.froi_utils import *
from fsub_extractor.utils.streamline_utils import *


def extractor(
    subject,
    tract,
    generate,
    tract_name,
    roi1,
    roi1_name,
    roi2,
    roi2_name,
    fs_dir,
    hemi,
    fs2dwi,
    dwi2fs,
    reg_type,
    # fs_license,
    gmwmi,
    gmwmi_thresh,
    search_dist,
    search_type,
    projfrac_params,
    sift2_weights,
    exclude_mask,
    include_mask,
    streamline_mask,
    out_dir,
    overwrite,
    skip_roi_projection,
    skip_gmwmi_intersection,
    wmfod,
    n_streamlines,
    tckgen_params,
    make_viz,
    interactive_viz,
    img_viz,
    orig_color,
    fsub_color,
    roi1_color,
    roi2_color,
    roi_opacity,
    fsub_linewidth,
    axial_offset,
    saggital_offset,
    camera_angle,
):
    # Force start log outputs on new line
    print("\n")

    ### Check for assertion errors ###

    # 1. If ROIs are to be projected or GMWMI craeted, make sure FS dir exists, hemispheres are valid, and proj-frac params are valid
    fs_sub_dir = op.join(fs_dir, subject)
    if skip_roi_projection == False or gmwmi == None:
        # Check FreeSurfer directory passed in and is valid
        if fs_dir == None:
            raise Exception("No FreeSurfer directory passed in.")
        if op.isdir(op.join(fs_sub_dir, "surf")) == False:
            raise Exception(
                f"{fs_sub_dir} does not appear to be a valid FreeSurfer directory."
            )

    # Split hemisphere input into list (useful if multiple are hemis are used)
    if hemi != None:
        hemi_list = hemi.split(",")

    if skip_roi_projection == False:
        # Check hemi(s)
        if hemi == None:
            raise Exception("--hemi must be specified if not skipping ROI projection.")
        else:
            if len(hemi_list) > 1 and roi2 == None:
                warnings.warn(
                    f"More than one hemisphere specified for only one ROI. Will only use first hemisphere ({hemi_list[0]}.)"
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

    # 2. Check if gmwmi exists or can be created if needed
    gmwmi_path_check = op.join(
        out_dir, subject, "anat", f"{subject}_desc-gmwmi.nii.gz"
    )  # Where to look for pre-existing GMWMI
    if gmwmi == None and fs_dir == None and skip_gmwmi_intersection == False:
        raise Exception(
            "GMWMI cannot be created unless a FreeSurfer directory is passed into --fs-dir."
        )
    elif gmwmi == None and op.exists(gmwmi_path_check):
        gmwmi = gmwmi_path_check
    elif gmwmi != None and op.exists(gmwmi) == False:
        warnings.warn(
            "GMWMI was specified but not found on the system. A new one will be created from the FreeSurfer input."
        )
        gmwmi = None

    # 3. Define and prepare registration
    if fs2dwi == None and dwi2fs == None:
        reg = None
        reg_invert = None
        reg_type = None
    elif fs2dwi != None:
        reg = fs2dwi
        reg_invert = False
    elif dwi2fs != None:
        reg = dwi2fs
        reg_invert = True
    # Infer registration type if not supplied
    if reg != None and reg_type == None:
        with open(reg) as f:
            reg_first_line = f.readlines()[0]
        f.close()
        if "command_history" in reg_first_line:
            reg_type = "mrtrix"
        else:
            reg_type = "itk"
        warnings.warn(
            f"A registration type of {reg_type} was inferred based on the contents of the file. If this is incorrect, please manually specify type with --reg-type flag."
        )
    # Prepare registration, if needed
    if reg != None and reg_type != "mrtrix":
        if reg_invert:
            mrtrix_reg_out = op.join(
                anat_out_dir, f"{subject}_from-DWI_to-FS_mode-image_desc-MRTrix_xfm.txt"
            )
        else:
            mrtrix_reg_out = op.join(
                anat_out_dir, f"{subject}_from-FS_to-DWI_mode-image_desc-MRTrix_xfm.txt"
            )
        reg = convert_to_mrtrix_reg(
            reg, mrtrix_reg_out, reg_in_type=reg_type, overwrite=overwrite
        )

    # XX. Make sure FS license is valid [TODO: HOW??]

    # Make output folders if they do not exist, and define the naming convention
    anat_out_dir = op.join(out_dir, subject, "anat")
    dwi_out_dir = op.join(out_dir, subject, "dwi")
    func_out_dir = op.join(out_dir, subject, "func")
    os.makedirs(anat_out_dir, exist_ok=True)
    os.makedirs(dwi_out_dir, exist_ok=True)
    os.makedirs(func_out_dir, exist_ok=True)

    # TODO: Parallelize stuff...

    ### Create a GMWMI, intersect with ROI ###
    if skip_gmwmi_intersection == False and gmwmi == None:
        print("\n Creating a GMWMI \n")
        (fivett, gmwmi, gmwmi_bin) = anat_to_gmwmi(
            fs_sub_dir,
            anat_out_dir,
            threshold=gmwmi_thresh,
            subject=subject,
            overwrite=overwrite,
        )
    else:
        gmwmi_bin = binarize_image(
            gmwmi,
            outfile=op.join(anat_out_dir, f"{subject}_rec-binarized_desc-gmwmi.nii.gz"),
            threshold=gmwmi_thresh,
            comparison="gt",
            overwrite=overwrite,
        )

    ### Set flag for whether two rois were passed in ###
    if roi2 != None:
        two_rois = True
    else:
        two_rois = False

    ### Project the ROI(s) into the white matter and intersect with GMWMI ###
    if skip_roi_projection == False:
        print(f"\n Projecting {roi1_name} into white matter \n")
        roi1_projected = project_roi(
            roi_in=roi1,
            roi_name=roi1_name,
            fs_dir=fs_dir,
            subject=subject,
            hemi=hemi_list[0],
            outdir=func_out_dir,
            projfrac_params=projfrac_params_list,
            overwrite=overwrite,
        )
    else:
        print(f"\n Skipping {roi1_name} projection \n")
        roi1_projected = roi1
    if reg != None:
        registed_roi_name = roi_in.replace("space-FS", "space-DWI")
        roi1_projected = register_to_dwi(
            roi_in, registed_roi_name, reg, interp="nearest", overwrite=True
        )
    if skip_gmwmi_intersection == False:
        print(f"\n Intersecting {roi1_name} with GMWMI \n")
        roi1_intersected = intersect_gmwmi(
            roi_in=roi1_projected,
            roi_name=roi1_name,
            gmwmi=gmwmi_bin,
            outpath_base=op.join(func_out_dir, subject),
            overwrite=overwrite,
        )
    else:
        roi1_intersected = roi1_projected
    ### TODO: Register ROI to DWI space

    ### Process ROI2 the same way if specified ###
    if two_rois == False:
        rois_in = roi1_intersected
        rois_name = roi1_name
        roi2_projected = None
        roi2_intersected = None
    else:
        rois_name = f"{roi1_name}-{roi2_name}"
        if skip_roi_projection == False:
            print(f"\n Projecting {roi2_name} into white matter \n")
            roi2_projected = project_roi(
                roi_in=roi2,
                roi_name=roi2_name,
                fs_dir=fs_dir,
                subject=subject,
                hemi=hemi_list[-1],
                outdir=func_out_dir,
                # fs_to_dwi_lta=reg,
                projfrac_params=projfrac_params_list,
                overwrite=overwrite,
            )
        else:
            print(f"\n Skipping {roi2_name} projection \n")
            roi2_projected = roi2
        if skip_gmwmi_intersection == False:
            print(f"\n Intersecting {roi2_name} with GMWMI \n")
            roi2_intersected = intersect_gmwmi(
                roi_in=roi2_projected,
                roi_name=roi2_name,
                gmwmi=gmwmi_bin,
                outpath_base=op.join(func_out_dir, subject),
                overwrite=overwrite,
            )
        else:
            roi2_intersected = roi2_projected

        ### Merge ROIS ###
        print("\n Merging ROIs \n")
        rois_in = merge_rois(
            roi1=roi1_intersected,
            roi2=roi2_intersected,
            out_file=op.join(
                func_out_dir, f"{subject}_rec-merged_desc-{roi1_name}{roi2_name}.nii.gz"
            ),
            overwrite=overwrite,
        )

    raise ("TESTING STOPS HERE BUDDY")
    ### Extract FSuB from tractogram
    if generate == False:
        ### Convert .trk to .tck if needed ###
        if op.splitext(tract)[-1] == ".trk":
            print("\n Converting .trk to .tck \n")
            tck_file = trk_to_tck(tract, dwi_out_dir, overwrite=overwrite)
        else:
            tck_file = tract

        ### Run MRtrix Tract Extraction ###
        print("\n Extracing the sub-bundle \n")
        extracted_tck = extract_tck_mrtrix(
            tck_file,
            rois_in,
            outpath_base=op.join(dwi_out_dir, f"{subject}_{tract_name}_{rois_name}"),
            two_rois=two_rois,
            search_dist=search_dist,
            search_type=search_type,
            sift2_weights=sift2_weights,
            exclude_mask=exclude_mask,
            include_mask=include_mask,
            streamline_mask=streamline_mask,
            overwrite=overwrite,
        )
        print("\n The extracted tract is located at " + extracted_tck + ".\n")

        ### Visualize the outputs ####
        if make_viz:
            from fsub_extractor.utils.fury_viz import visualize_sub_bundles

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

            visualize_sub_bundles(
                orig_bundle=tck_file,
                fsub_bundle=extracted_tck,
                ref_anat=ref_anat,
                fname=op.join(
                    dwi_out_dir,
                    f"{subject}_hemi-{hemi_list[0]}_{tract_name}_{rois_name}_desc-visualization.png",
                ),
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
                hemi=hemi_list[0],
            )

    ### Seed and generate FSuB instead
    else:
        ### Make a outer surface exclusion mask to make tractography more efficient
        print(f"\n Getting pial surface")
        get_pial_surf(
            subject,
            fs_dir,
            surf_name="pial",
            anat_out_dir=anat_out_dir,
            overwrite=overwrite,
        )

    print("\n DONE \n")
