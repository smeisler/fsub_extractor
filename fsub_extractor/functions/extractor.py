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
    hemi,
    fs_dir,
    # fs_license,
    projfrac_params,
    fivett,
    gmwmi_thresh,
    skip_fivett_registration,
    skip_roi_projection,
    skip_gmwmi_intersection,
    out_dir,
    overwrite,
    exclude_mask,
    include_mask,
    streamline_mask,
    fs2dwi,
    dwi2fs,
    reg_type,
    search_dist,
    search_type,
    sift2_weights,
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

    # Set flag for whether two rois were passed in ###
    if roi2 != None:
        two_rois = True
    else:
        two_rois = False

    # If --fs_dir was not specified, infer from environment
    if fs_dir == None:
        fs_dir = os.getenv("SUBJECTS_DIR")
        warnings.warn(
            f"--fs_dir was not specified, so it is being inferred as {fs_dir}. If this is not correct, please manually supply that argument.)"
        )

    # If skipping ROI projection, make sure ROIs are NIFTI files
    if skip_roi_projection:
        nifti_check1 = True
        nifti_check2 = True
        if roi1[-7:] != ".nii.gz":
            nifti_check1 = False
        if roi2 != None:
            if roi2[-7:] != ".nii.gz":
                nifti_check2 = False
        if nifti_check1 == False or nifti_check2 == False:
            raise Exception(
                f"If skipping ROI projection, all input ROIs must be .nii.gz files."
            )

    # Split hemisphere input into list (useful if multiple are hemis are used)
    if hemi != None:
        hemi_list = hemi.split(",")

    # If ROIs are to be projected or 5TT/GMWMI created, make sure FreeSurfer directory exists
    if skip_roi_projection == False or (
        fivett == None and (skip_gmwmi_intersection == False or generate == True)
    ):
        if op.isfile(op.join(fs_dir, subject, "surf", "lh.white")) == False:
            raise Exception(
                f"{fs_sub_dir} does not appear to be contain completed recon-all outputs."
            )

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
        if float(projfrac_params_list[0]) >= 0:
            raise Exception(
                "The 'start' paramater of projfrac-params must be negative to project into white matter."
            )
        if float(projfrac_params_list[1]) <= float(projfrac_params_list[0]):
            raise Exception(
                "The 'stop' paramater of projfrac-params must be greater than the 'start' parameter."
            )
        if float(projfrac_params_list[-1]) <= 0:
            raise Exception(
                "The 'delta' paramater of projfrac-params must be positive to iterate correctly."
            )

    # Define and prepare registration
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
            f"A registration type of '{reg_type}' was inferred based on the contents of {reg}. If this is incorrect, please manually specify type with the '--reg-type' flag."
        )

    # XX. Make sure FS license is valid [TODO: HOW??]

    ### Pre-checks are over, begin the processing!

    # Make output folders if they do not exist, and define the naming convention
    anat_out_dir = op.join(out_dir, subject, "anat")
    dwi_out_dir = op.join(out_dir, subject, "dwi")
    func_out_dir = op.join(out_dir, subject, "func")
    os.makedirs(anat_out_dir, exist_ok=True)
    os.makedirs(dwi_out_dir, exist_ok=True)
    os.makedirs(func_out_dir, exist_ok=True)

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

    # TODO: Parallelize stuff...

    ### Create a 5TT and GMWMI if needed ###
    if skip_fivett_registration:
        # Assume anatomicals are already aligned to DWI
        anat_space_label = "DWI"
    else:
        # Add FreeSurfer space label to differentiate if not aligned
        anat_space_label = "FS"

    # Check if 5TT exists or can be created if needed
    fivett_path_check = op.join(
        out_dir, subject, "anat", f"{subject}_space-FS_desc-5tt.nii.gz"
    )
    if fivett == None and op.exists(fivett_path_check):
        fivett = fivett_path_check
        warnings.warn(
            f"Found already-made final-stage 5TT image at {fivett}. Please delete, move, or rename this file if you do not want it to be used."
        )
    elif fivett != None and op.exists(fivett) == False:
        warnings.warn(
            "5TT image was specified but not found on the system. A new one will be created from the FreeSurfer input if needed."
        )
        fivett = None

    if skip_gmwmi_intersection == False or generate == True:
        print("\n Running GMWMI creation workflow \n")
        (fivett, gmwmi, gmwmi_bin) = anat_to_gmwmi(
            op.join(fs_dir, subject),
            anat_out_dir,
            threshold=gmwmi_thresh,
            subject=subject,
            fivett=fivett,
            space_label=anat_space_label,
            overwrite=overwrite,
        )

    # Register 5TT / GMWMI to DWI space if needed
    if skip_fivett_registration == False and reg != None:
        print("\n Registering 5TT and GMWMI to DWI space \n")
        fivett = register_to_dwi(
            fivett,
            op.join(out_dir, subject, "anat", f"{subject}_space-DWI_desc-5tt.nii.gz"),
            reg,
            invert=reg_invert,
            overwrite=True,
        )
        gmwmi = register_to_dwi(
            gmwmi,
            gmwmi.replace("space-FS", "space-DWI"),
            reg,
            invert=reg_invert,
            overwrite=True,
        )
        gmwmi_bin = register_to_dwi(
            gmwmi_bin,
            gmwmi_bin.replace("space-FS", "space-DWI"),
            reg,
            invert=reg_invert,
            interp="nearest",
            overwrite=True,
        )

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
        registed_roi_name = roi1_projected.replace("space-FS", "space-DWI")
        roi1_projected = register_to_dwi(
            roi1_projected,
            registed_roi_name,
            reg,
            invert=reg_invert,
            interp="nearest",
            overwrite=True,
        )
    if skip_gmwmi_intersection == False:
        print(f"\n Intersecting {roi1_name} with GMWMI \n")
        roi1_projected = intersect_gmwmi(
            roi_in=roi1_projected,
            roi_name=roi1_name,
            gmwmi=gmwmi_bin,
            outpath_base=op.join(func_out_dir, subject),
            overwrite=overwrite,
        )

    ### Process ROI2 the same way if specified ###
    if two_rois == False:
        rois_atlas_in = roi1_projected
        rois_name = roi1_name
        roi2_projected = None
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
                projfrac_params=projfrac_params_list,
                overwrite=overwrite,
            )
        else:
            print(f"\n Skipping {roi2_name} projection \n")
            roi2_projected = roi2
        if reg != None:
            registed_roi_name = roi2_projected.replace("space-FS", "space-DWI")
            roi2_projected = register_to_dwi(
                roi2_projected,
                registed_roi_name,
                reg,
                invert=reg_invert,
                interp="nearest",
                overwrite=True,
            )
        if skip_gmwmi_intersection == False:
            print(f"\n Intersecting {roi2_name} with GMWMI \n")
            roi2_projected = intersect_gmwmi(
                roi_in=roi2_projected,
                roi_name=roi2_name,
                gmwmi=gmwmi_bin,
                outpath_base=op.join(func_out_dir, subject),
                overwrite=overwrite,
            )

        ### Merge ROIS ###
        print("\n Merging ROIs \n")
        rois_atlas_in = merge_rois(
            roi1=roi1_projected,
            roi2=roi2_projected,
            out_file=op.join(
                func_out_dir, f"{subject}_rec-merged_desc-{roi1_name}{roi2_name}.nii.gz"
            ),
            overwrite=overwrite,
        )

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
            rois_atlas_in,
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

    ### Seed and generate FSuB instead
    else:
        tck_file = None  # No original streamline object (for visualization function)

        ### Make a outer surface exclusion mask to make tractography more efficient
        print(f"\n Getting pial surface")
        pial_surf = get_pial_surf(
            subject,
            fs_dir,
            surf_name="pial",
            anat_out_dir=anat_out_dir,
            overwrite=overwrite,
        )

        print(f"\n Generating Sub-bundles \n")

        if two_rois:
            # Seed half of streamlines from each seed ROI
            n_streamlines = int(n_streamlines / 2)

            fsub_1_name = f"{subject}_space-DWI_from-{roi1_name}_to-{roi2_name}_desc-{tract_name}_fsub.tck"
            fsub_2_name = f"{subject}_space-DWI_from-{roi2_name}_to-{roi1_name}_desc-{tract_name}_fsub.tck"

            # Generate FSuB from 2nd ROI
            fsub_gen_2 = generate_tck_mrtrix(
                roi_begin=roi2_projected,
                roi_end=roi1_projected,
                wmfod=wmfod,
                fivett=fivett,
                n_streamlines=n_streamlines,
                outfile=op.join(dwi_out_dir, fsub_2_name),
                pial_exclusion_mask=pial_surf,
                exclude_mask=exclude_mask,
                include_mask=include_mask,
                streamline_mask=streamline_mask,
                tckgen_params=tckgen_params,
                overwrite=overwrite,
            )
        else:
            fsub_1_name = (
                f"{subject}_space-DWI_from-{roi1_name}_desc-{tract_name}_fsub.tck"
            )
            fsub_2_name = None

        # Generate FSuB from 1st ROI
        fsub_gen_1 = generate_tck_mrtrix(
            roi_begin=roi1_projected,
            roi_end=roi2_projected,
            wmfod=wmfod,
            fivett=fivett,
            n_streamlines=n_streamlines,
            outpath_base=op.join(dwi_out_dir, fsub_1_name),
            pial_exclusion_mask=pial_surf,
            exclude_mask=exclude_mask,
            include_mask=include_mask,
            streamline_mask=streamline_mask,
            tckgen_params=tckgen_params,
            overwrite=overwrite,
        )

        if two_rois:
            # Merge the tracks
            fsub_bundle = op.join(
                dwi_out_dir,
                f"{subject}_space-DWI_from-{roi1_name}_to-{roi2_name}_desc-{tract_name}_desc-merged_fsub.tck",
            )
            tckedit = find_program("tckedit")
            cmd_tckedit = [
                tckedit,
                fsub_gen_1,
                fsub_gen_2,
                fsub_bundle,
            ]
        else:
            fsub_bundle = fsub_gen_1

    ### Visualize the outputs if requested ####
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
            roi1=roi1_projected,
            roi2=roi2_projected,
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

    print("\n DONE! \n")
