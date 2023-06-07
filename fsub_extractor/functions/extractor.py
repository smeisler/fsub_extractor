import os.path as op
import warnings
from fsub_extractor.utils.anat_utils import *
from fsub_extractor.utils.system_utils import *
from fsub_extractor.utils.froi_utils import *
from fsub_extractor.utils.streamline_utils import *


def extractor(
    subject,
    tract,
    tract_name,
    roi1,
    roi1_name,
    fs_dir,
    hemi,
    reg,
    reg_invert,
    reg_type,
    # fs_license,
    # trk_ref,
    gmwmi,
    gmwmi_thresh,
    roi2,
    roi2_name,
    search_dist,
    search_type,
    projfrac_params,
    sift2_weights,
    exclude_mask,
    out_dir,
    # out_prefix,
    overwrite,
    skip_roi_projection,
    skip_gmwmi_intersection,
    skip_viz,
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

    ### Check for assertion errors ###

    # 1. If ROIs are to be projected or GMWMI craeted, make sure FS dir exists, hemispheres are valid, and proj-frac params are valid
    fs_sub_dir = op.join(fs_dir, subject)
    if skip_roi_projection == False or gmwmi == None:
        # Check FS dir
        if fs_dir == None:
            raise Exception("No FreeSurfer directory passed in.")
        if op.isdir(op.join(fs_sub_dir, "surf")) == False:
            raise Exception(
                f"{fs_sub_dir} does not appear to be a valid FreeSurfer directory."
            )

    if hemi != None:
        hemi_list = hemi.split(",")

    if skip_roi_projection == False:
        # Check hemi(s)
        if hemi == None:
            raise Exception("--hemi must be specified if not skipping ROI projection.")
        else:
            for hemisphere in hemi_list:
                if hemisphere != "lh" and hemisphere != "rh":
                    raise Exception(
                        f"Hemispheres must be either 'lh' or 'rh'. Current input is {hemi_list}."
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
        raise Exception(f"ROI file {roi1} is not found on the system.")
    if (
        roi1[-7:] != ".nii.gz"
        and roi1[-4:] != ".mgz"
        and roi1[-6:] != ".label"
        and roi1[-4:] != ".gii"
    ):
        raise Exception(f"ROI file {roi1} is not a supported file type.")
    if roi2 != None and op.exists(roi2) == False:
        raise Exception(f"ROI file {roi2} is not found on the system.")
    if (
        roi2 != None
        and roi2[-7:] != ".nii.gz"
        and roi2[-4:] != ".mgz"
        and roi2[-6:] != ".label"
        and roi2[-3:] != ".gii"
    ):
        raise Exception(f"ROI file {roi2} is not of a supported file type.")

    # 3. Make sure tract file is okay
    if op.exists(tract) == False:
        raise Exception(f"Tract file {tract} is not found on the system.")
    if tract[-4:] not in [".trk", ".tck"]:
        raise Exception(f"Tract file {tract} is not of a supported file type.")
    # if tract[-4:] == ".trk" and trk_ref == None:
    #    raise Exception(".trk file passed in without a --trk-ref input.")

    # 4. Check if gmwmi exists or can be created if needed
    if gmwmi == None and fs_dir == None and skip_gmwmi_intersection == False:
        raise Exception(
            "GMWMI cannot be created unless a FreeSurfer directory is passed into --fs-dir."
        )
    elif gmwmi == None and op.exists(op.join(out_dir, subject, "anat", "gmwmi.nii.gz")):
        gmwmi = op.join(out_dir, subject, "anat", "gmwmi.nii.gz")
    elif gmwmi != None and op.exists(gmwmi) == False:
        warnings.warn(
            "GMWMI was specified but not found on the system. A new one will be created from the FreeSurfer input."
        )
        gmwmi = None

    # 5. Make sure camera angle is valid
    if camera_angle != "saggital" and camera_angle != "axial":
        raise Exception(
            f"Camera angle must be either 'saggital' or 'axial'. {camera_angle} was specified."
        )

    # 6. Make sure FS license is valid [TODO: HOW??]

    ### Prepare output directories ###
    # Add an underscore to separate prefix from file names if a prefix is specified
    # if len(out_prefix) > 0:
    #    if out_prefix[-1] != "_":
    #        out_prefix += "_"

    # Make output folders if they do not exist, and define the naming convention
    anat_out_dir = op.join(out_dir, subject, "anat")
    dwi_out_dir = op.join(out_dir, subject, "dwi")
    func_out_dir = op.join(out_dir, subject, "func")
    os.makedirs(anat_out_dir, exist_ok=True)
    os.makedirs(dwi_out_dir, exist_ok=True)
    os.makedirs(func_out_dir, exist_ok=True)
    # anat_out_base = op.join(anat_out_dir, out_prefix)
    # dwi_out_base = op.join(dwi_out_dir, out_prefix)
    # func_out_base = op.join(func_out_dir, out_prefix)

    # TODO: Parallelize GMWMI creation with other processes?
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

    ### Prepare registration, if needed
    if reg != None:
        if (
            reg_type != "LTA" or reg_invert == True
        ):  # We only need to prepare if doing an invert or working with a non-LTA file
            reg_transformed = op.join(anat_out_dir, f"{subject}_xfm-fs2dwi.lta")
            src = op.join(fs_sub_dir, "mri", "orig.mgz")
            trg = gmwmi_bin
            reg = prepare_reg(
                reg_in=reg,
                reg_out=reg_transformed,
                src=src,
                trg=trg,
                invert=reg_invert,
                reg_type=reg_type,
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
            fs_to_dwi_lta=reg,
            projfrac_params=projfrac_params_list,
            overwrite=overwrite,
        )
    else:
        print(f"\n Skipping {roi1_name} projection \n")
        roi1_projected = roi1
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
                outpath_base=func_out_base,
                fs_to_dwi_lta=reg,
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

    ### Convert .trk to .tck if needed ###
    if tract[-4:] == ".trk":
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
        overwrite=overwrite,
    )
    print("\n The extracted tract is located at " + extracted_tck + ".\n")

    ### Visualize the outputs ####
    if skip_viz == False:
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
            outpath_base=op.join(dwi_out_dir,f"{subject}_hemi-{hemi_list[0]}_{tract_name}_{rois_name}_desc-"),
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

    print("\n DONE \n")
