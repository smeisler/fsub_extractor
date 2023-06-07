import os.path as op
import os
from fsub_extractor.utils.system_utils import *


def anat_to_gmwmi(anat, outdir, subject, threshold=0, overwrite=True):
    """Creates a gray-matter-white-matter-interface (GMWMI) from a T1w or FreeSurfer image
    If a T1w image is passed (not recommended), uses FSL FAST to create 5TT and GMWMI
    If a FreeSurfer directory is passed in, uses the surface reconstruction to create 5TT and GMWMI

    Parameters
    ==========
    anat: str
            Either a path to a T1w image (.nii, .nii.gz, .mif) or FreeSurfer subject directory
    outdir: str
            Path to output directory
    overwrite: bool
            Whether to allow overwriting outputs

    Outputs
    =======
    Function returns paths to 5tt, gmwmi, and binarized gmwmi
    outdir + 5tt.nii.gz is the 5TT segmented anatomical image
    outdir + gmwmi.nii.gz is the GMWMI image
    outdir + gmwmi_bin.nii.gz is the binarized GMWMI image
    """

    # Check for T1 file vs FreeSurfer directory
    if op.isdir(op.join(anat, "surf")):
        print(
            "FreeSurfer input detected: Using 5ttgen HSVS algorithm to generate GMWMI"
        )
        fivett_algo = "hsvs"
    elif anat[-7:] == ".nii.gz" or anat[-4:] == ".nii" or anat[-4:] == ".mif":
        print("T1w image detected: Using FSL 5ttgen algorithm to generate GMWMWI")
        fivett_algo = "fsl"
    else:
        raise Exception(
            "Neither T1w or FreeSurfer input detected; Unable to create GMWMI"
        )

    # Run 5ttgen to generate 5tt image
    print("\n Generating 5TT Image \n")
    fivettgen = find_program("5ttgen")
    fivettgen_out = op.join(outdir, f"{subject}_desc-5tt.nii.gz")
    cmd_5ttgen = [fivettgen, fivett_algo, anat, fivettgen_out, "-nocrop"]
    if overwrite:
        cmd_5ttgen += ["-force"]
    else:
        overwrite_check(fivettgen_out)
    run_command(cmd_5ttgen)

    # Run 5tt2gmwmi to generate GMWMI image
    print("\n Generating GMWMI Image \n")
    fivett2gmwmi = find_program("5tt2gmwmi")
    fivett2gmwmi_out = op.join(outdir, f"{subject}_desc-gmwmi.nii.gz")
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
    print(f"\n Binarizing GMWMI at threshold of {threshold} \n")
    binarized_gmwmi_out = op.join(outdir, f"{subject}_rec-binarized_desc-gmwmi.nii.gz")
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


def prepare_reg(
    reg_in, reg_out, src=None, trg=None, invert=False, reg_type="LTA", overwrite=True
):
    """Makes an LTA convert file for mapping between FreeSurfer and DWI space

    Parameters
    ==========
    reg_in: str
            Path to input registation
    reg_out: str
            Where to save output registation
    src: str
            Path to image used for source image geometric reference
    trg: str
            Path to image used for target image geometric reference
    invert: bool
            Whether to invert transformation.
    reg_type: str
            Format of input registration. Choices are LTA, ITK, and FSL
    overwrite: bool
            Whether to allow overwriting outputs

    Outputs
    =======
    Function returns path to binarized image
    outfile is the binarized image
    """
    # Import the correct kind of registration
    if reg_type == "LTA":
        reg_in_string = "--inlta"
    elif reg_type == "ITK":
        reg_in_string = "--initk"
    elif reg_type == "FSL":
        reg_in_string = "--infsl"

    # Define the lta_convert command
    lta_convert = find_program("lta_convert")
    cmd_lta_convert = [
        lta_convert,
        reg_in_string,
        reg_in,
        "--outlta",
        reg_out,
    ]

    # Add source and target geometric reference images if not inputting LTA
    if reg_type != "LTA":
        cmd_lta_convert += ["--src", src, "--trg", trg]

    # Invert transformation if requested
    if invert:
        cmd_lta_convert += ["--invert"]

    if overwrite == False:
        overwrite_check(reg_out)

    run_command(cmd_lta_convert)

    return reg_out
