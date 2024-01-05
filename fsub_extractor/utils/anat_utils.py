import os.path as op
import os
import shlex
from fsub_extractor.utils.system_utils import *


def anat_to_gmwmi(
    anat, outdir, subject, threshold=0, fivett=None, space_label="FS", overwrite=True
):
    """Creates a gray-matter-white-matter-interface (GMWMI) from a T1w or FreeSurfer image
    If a T1w image is passed (not recommended), uses FSL FAST to create 5TT and GMWMI
    If a FreeSurfer directory is passed in, uses the surface reconstruction to create 5TT and GMWMI

    Parameters
    ==========
    anat: str
            Either a path to a T1w image (.nii, .nii.gz, .mif) or FreeSurfer subject directory
    outdir: str
            Path to output directory
    subject: str
            Subject name
    threshold: float
            Threshold above which to binarize GMWMI
    fivett: str
            Path to 5TT image (.nii, .nii.gz, .mif), skips the 5ttgen step
    space_label: str
            "FS" for FreeSurfer Space, "DWI" for DWI space
    overwrite: bool
            Whether to allow overwriting outputs

    Outputs
    =======
    Function returns paths to 5tt, gmwmi, and binarized gmwmi
    outdir/{subject}_space-{space_label}_desc-5tt.nii.gz is the 5TT segmented anatomical image
    outdir/{subject}_space-{space_label}_desc-gmwmi.nii.gz is the GMWMI image
    outdir/{subject}_space-{space_label}_rec-binarized_desc-gmwmi.nii.gz is the binarized GMWMI image
    """

    # Check for T1 file vs FreeSurfer directory
    if op.isdir(op.join(anat, "surf")):
        print(
            "   FreeSurfer input detected: Using 5ttgen HSVS algorithm to generate GMWMI"
        )
        fivett_algo = "hsvs"
    elif anat[-7:] == ".nii.gz" or anat[-4:] == ".nii" or anat[-4:] == ".mif":
        print("   T1w image detected: Using FSL 5ttgen algorithm to generate GMWMI")
        fivett_algo = "fsl"
    else:
        raise Exception(
            "Neither T1w or FreeSurfer input detected; Unable to create GMWMI"
        )

    if fivett == None:
        # Run 5ttgen to generate 5tt image
        print("\n   Generating 5TT Image \n")
        fivettgen = find_program("5ttgen")
        fivettgen_out = op.join(
            outdir, f"{subject}_space-{space_label}_desc-5tt.nii.gz"
        )
        cmd_5ttgen = [fivettgen, fivett_algo, anat, fivettgen_out]  # , "-nocrop"
        if overwrite:
            cmd_5ttgen += ["-force"]
        else:
            overwrite_check(fivettgen_out)
        run_command(cmd_5ttgen)
    else:
        print("\n   Using user-supplied 5TT image \n")
        fivettgen_out = fivett

    # Run 5tt2gmwmi to generate GMWMI image
    print("\n   Generating GMWMI Image \n")
    fivett2gmwmi = find_program("5tt2gmwmi")
    fivett2gmwmi_out = op.join(
        outdir, f"{subject}_space-{space_label}_desc-gmwmi.nii.gz"
    )
    cmd_5tt2gmwmi = [
        fivett2gmwmi,
        fivettgen_out,
        fivett2gmwmi_out,
    ]
    if overwrite:
        cmd_5tt2gmwmi += ["-force"]
    else:
        overwrite_check(fivett2gmwmi_out)
    run_command(cmd_5tt2gmwmi)

    # Run mrthreshold to binarize the GMWMI
    print(f"\n   Binarizing GMWMI at threshold of {threshold} \n")
    binarized_gmwmi_out = op.join(
        outdir, f"{subject}_space-{space_label}_rec-binarized_desc-gmwmi.nii.gz"
    )
    binarized_gmwmi = binarize_image(
        fivett2gmwmi_out, binarized_gmwmi_out, threshold=threshold, overwrite=overwrite
    )

    return fivettgen_out, fivett2gmwmi_out, binarized_gmwmi


def binarize_image(img, outfile, threshold=0, comparison="gt", overwrite=True):
    """Binarizes an image at a given threshold (wrapper around mrthreshold)

    Parameters
    ==========
    img: str
            Path to image to binarize
    outfile: str
            Output path for binarized img
    threshold: number
            Threshold to use for binarizing
    comparison: string
            'mrthreshold' comparison option for thresholding. Default is 'gt' / greater than.
    overwrite: bool
            Whether to allow overwriting outputs

    Outputs
    =======
    Function returns path to binarized image
    outfile is the binarized image
    """
    mrthreshold = find_program("mrthreshold")
    cmd_mrthreshold = [
        mrthreshold,
        "-abs",
        str(threshold),
        "-comparison",
        comparison,
        img,
        outfile,
    ]

    if overwrite:
        cmd_mrthreshold += ["-force"]
    else:
        overwrite_check(outfile)

    run_command(cmd_mrthreshold)

    return outfile


def get_pial_surf(
    subject,
    fs_dir,
    surf_name="pial",
    anat_out_dir=os.getcwd(),
    overwrite=True,
):
    """Returns volumetric mask of pial surface

    Parameters
    ==========
    subject: str
            Subject name as found in FreeSurfer subjects directory
    fs_dir: str
            Path to FreeSurfer subjects directory

    Outputs
    =======
    Function returns path to binarized image
    outfile is the binarized image
    """

    ### Tell FreeSurfer where subject data is
    os.environ["SUBJECTS_DIR"] = fs_dir

    ### Define the mri_surf2surf command, recreat pial surface in each hemisphere
    mri_surf2vol = find_program("mri_surf2vol")

    for hemi in ["lh", "rh"]:
        outpath_hemi = op.join(
            anat_out_dir, f"{subject}_surf-{surf_name}_hemi-{hemi}_space-FS.nii.gz"
        )

        cmd_mri_surf2vol = [
            mri_surf2vol,
            "--subject",
            subject,
            "--identity",
            subject,
            "--template",
            op.join(fs_dir, subject, "mri", "orig.mgz"),
            "--mkmask",
            "--hemi",
            hemi,
            "--surf",
            surf_name,
            "--o",
            outpath_hemi,
        ]

        if overwrite == False:
            overwrite_check(outpath_hemi)

        run_command(cmd_mri_surf2vol)

    ### Merge the images into one mask
    outpath_merged = op.join(
        anat_out_dir, f"{subject}_surf-{surf_name}_hemi-combined_space-FS.nii.gz"
    )
    mrcalc = find_program("mrcalc")
    cmd_mrcalc = [
        mrcalc,
        outpath_hemi,
        outpath_hemi.replace("hemi-rh", "hemi-lh"),
        "-max",
        outpath_merged,
    ]
    if overwrite:
        cmd_mrcalc += ["-force"]
    else:
        overwrite_check(outpath_merged)

    run_command(cmd_mrcalc)

    return outpath_merged


def convert_to_mrtrix_reg(reg_in, mrtrix_reg_out, reg_in_type="itk", overwrite=True):
    """Makes an LTA convert file for mapping between FreeSurfer and DWI space

    Parameters
    ==========
    reg_in: str
            Path to input registration
    mrtrix_reg_out: str
            Where to save output registration
    reg_type: str
            Format of input registration. Currently only ANTs/ITK is supported.
    overwrite: bool
            Whether to allow overwriting outputs

    Outputs
    =======
    Function MRTrix-readable registration file
    """

    if reg_in_type == "itk":
        reg_fmt_string = "itk_import"

    # Define the lta_convert command
    transformconvert = find_program("transformconvert")
    cmd_transformconvert = [
        transformconvert,
        reg_in,
        reg_fmt_string,
        mrtrix_reg_out,
    ]

    if overwrite:
        cmd_transformconvert += ["-force"]
    else:
        overwrite_check(mrtrix_reg_out)

    run_command(cmd_transformconvert)

    return mrtrix_reg_out


def calculate_fs2dwi_reg(
    subject, outdir, scratch_dir, fs_dir, t1, t1_mask, overwrite=True
):
    """Makes an LTA convert file for mapping between FreeSurfer and DWI space

    Parameters
    ==========
    subject: str
            Subject name as found in FreeSurfer subjects directory.
    outdir: str
            Path to output directory.
    scratch_dir: str
            Path to scratch directory.
    fs_dir: str
            Path to FreeSurfer subjects directory.
    t1: str
            Path to T1 image in DWI space (NIfTI).
    t1_mask: str
            Path to T1 brain mask image in DWI space (NIfTI).
    overwrite: bool
            Whether to allow overwriting outputs

    Outputs
    =======
    Function creates and returns path to MRTrix-readable registration file for mapping between FreeSurfer and DWI space
    """

    # Start by converting FS brain from .mgz to .nii
    mrconvert = find_program("mrconvert")
    fs_brain_path = op.join(fs_dir, subject, "mri", "brain.mgz")  # Input
    fs_brain_nii_out = op.join(scratch_dir, f"{subject}_fs_brain.nii")  # Output
    cmd_mrconvert = [mrconvert, "-stride", "-1,-2,3", fs_brain_path, fs_brain_nii_out]

    if overwrite:
        cmd_mrconvert += ["-force"]
    else:
        overwrite_check(fs_brain_nii_out)

    run_command(cmd_mrconvert)

    # Perform the registration
    antsRegistration = find_program("antsRegistration")
    cmd_antsRegistration = [
        antsRegistration,
        "--collapse-output-transforms",
        "1",
        "--dimensionality",
        "3",
        "--float",
        "0",
        "--initial-moving-transform",
        f"[{t1},{fs_brain_nii_out},1]",
        "--initialize-transforms-per-stage",
        "0",
        "--interpolation",
        "BSpline",
        "--output",
        f"[{scratch_dir}/transform,{scratch_dir}/transform_Warped.nii.gz]",
        "--transform",
        "Rigid[0.1]",
        "--metric",
        f"Mattes[{t1},{fs_brain_nii_out},1,32,Random,0.25]",
        "--convergence",
        "[1000x500x250x100,1e-06,10]",
        "--smoothing-sigmas",
        "3.0x2.0x1.0x0.0mm",
        "--shrink-factors",
        "8x4x2x1",
        "--use-histogram-matching",
        "0",
        "--masks",
        f"[{t1_mask},NULL]",
        "--winsorize-image-intensities",
        "[0.002,0.998]",
        "--write-composite-transform",
        "0",
    ]

    if overwrite == False:
        overwrite_check(f"{scratch_dir}/transform_Warped.nii.gz")

    run_command(cmd_antsRegistration)

    # Convert ANTs .mat transform to .txt, and rename it
    ConvertTransformFile = find_program("ConvertTransformFile")
    reg_txt = f"{scratch_dir}/{subject}_from-FS_to-T1wACPC_mode-image_xfm.txt"
    cmd_ConvertTransformFile = [
        ConvertTransformFile,
        "3",
        f"{scratch_dir}/transform0GenericAffine.mat",
        reg_txt,
    ]

    if overwrite == False:
        overwrite_check(reg_txt)

    run_command(cmd_ConvertTransformFile)

    # Convert ANTs transform to MRTrix compatible transform, save out
    transformconvert = find_program("transformconvert")
    mrtrix_reg_out = f"{outdir}/{subject}_from-FS_to-DWI_mode-image_xfm.txt"
    cmd_transformconvert = [
        transformconvert,
        reg_txt,
        "itk_import",
        mrtrix_reg_out,
    ]

    if overwrite:
        cmd_transformconvert += ["-force"]
    else:
        overwrite_check(mrtrix_reg_out)

    run_command(cmd_transformconvert)

    return mrtrix_reg_out
