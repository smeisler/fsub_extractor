import os.path as op
import os
from fsub_extractor.utils.system_utils import *


def project_roi(
    roi_in,
    fs_dir,
    subject,
    hemi,
    outpath_base,
    projfrac_params=[-2, 0, 0.05],
    overwrite=True,
):
    """Projects input ROI into the white matter. If volumetric ROI is input, starts by mapping it to the surface.

    Parameters
    ==========
    roi_in: str
            Path to input ROI mask file (.nii.gz, .mgz, .label). Should be binary (1 in ROI, 0 elsewhere).
    fs_dir: str
            Path to FreeSurfer subjects folder
    subject: str
            Subject name. Must match folder name in fs_dir.
    hemi: str
            Hemisphere corresponding to the ROI ('lh' or 'rh')
    projfrac_params: list
            List containing strings of ['start','stop','delta'] parameters for projfrac
    outpath_base: str
            Path to output directory, including output prefix
    overwrite: bool
            Whether to allow overwriting outputs

    Outputs
    =======
    Function returns path to the projected ROI.
    Image is saved out to outpath_base + gmwmi_intersected.nii.gz
    """

    os.environ["SUBJECTS_DIR"] = fs_dir
    if roi_in[-7:] == ".nii.gz":
        print("Using volumetric ROI projection pipeline")
        # roi_surf = roi_in.replace(".nii.gz", ".mgz")
        roi_surf = outpath_base + op.basename(roi_in).replace(".nii.gz", ".mgz")
        mri_vol2surf = find_program("mri_vol2surf")
        cmd_mri_vol2surf = [
            mri_vol2surf,
            "--src",
            roi_in,
            "--out",
            roi_surf,
            "--regheader",
            subject,
            "--hemi",
            hemi,
            "--projfrac-max",
            "-.5",
            "1",
            ".1",
        ]
        run_command(cmd_mri_vol2surf)
    else:
        roi_surf = roi_in

    if roi_surf[-6:] == ".label":
        print("Projecting FS .label file")
        # out_path = roi_surf.replace(".label",".projected.nii.gz")
        filename = roi_surf.replace(".label", ".projected.nii.gz")
        filename = op.basename(filename)
        mri_label2vol = find_program("mri_label2vol")
        cmd_mri_label2vol = [
            mri_label2vol,
            "--label",
            roi_surf,
            "--o",
            outpath_base + filename,
            "--subject",
            subject,
            "--hemi",
            hemi,
            "--temp",
            op.join(fs_dir, subject, "mri", "aseg.mgz"),
            "--proj",
            "frac",
            projfrac_params[0],
            projfrac_params[1],
            projfrac_params[2],
            "--identity",
        ]
        run_command(cmd_mri_label2vol)

        return outpath_base + filename

    if roi_surf[-4:] == ".mgz":
        print("Projecting FS .mgz surface file")
        # out_path = roi_surf.replace(".mgz",".projected.nii.gz")
        filename = roi_surf.replace(".mgz", ".projected.nii.gz")
        filename = op.basename(filename)
        mri_surf2vol = find_program("mri_surf2vol")
        cmd_mri_surf2vol = [
            mri_surf2vol,
            "--surfval",
            roi_surf,
            "--o",
            outpath_base + filename,
            "--subject",
            subject,
            "--hemi",
            hemi,
            "--template",
            op.join(fs_dir, subject, "mri", "aseg.mgz"),
            "--identity",
            subject,
            "--fill-projfrac",
            projfrac_params[0],
            projfrac_params[1],
            projfrac_params[2],
        ]
        run_command(cmd_mri_surf2vol)

        return outpath_base + filename


def intersect_gmwmi(
    roi_in, gmwmi, outpath_base, overwrite=True
):  # TODO: Fix so that it is meant to run on individual ROIs, not combined
    """Intersects an input ROI file with the GMWMI

    Parameters
    ==========
    rois_in: str
            Path to input ROI mask file (.nii.gz, .mif). Should be binary (1 in ROI, 0 elsewhere).
    gmwmi: str
            Path to gray-matter-white-matter-interface image (.nii.gz, .mif)
    outpath_base: str
            Path to output directory, including output prefix
    overwrite: bool
            Whether to allow overwriting outputs

    Outputs
    =======
    Function returns path to the intersected image.
    Image is saved out to outpath_base + _gmwmi_intersected.nii.gz
    """

    mrcalc = find_program("mrcalc")
    mrcalc_out = outpath_base + "_gmwmi_intersected.nii.gz"
    cmd_mrcalc = [
        mrcalc,
        gmwmi,
        roi_in,
        "-mult",
        mrcalc_out,
    ]

    if overwrite == False:
        overwrite_check(mrcalc_out)
    else:
        cmd_mrcalc += ["-force"]

    run_command(cmd_mrcalc)

    return mrcalc_out


def merge_rois(roi1, roi2, out_file, overwrite=True):  # TODO: REFACTOR THIS
    """Creates the input ROI atlas-like file to be passed into tck2connectome.
        Multiplies the second ROI file passed by 2, and merges this file with the first file.
        Returns the merged file
    Parameters
    ==========
    roi1: str
            abspath to the first ROI mask file
    roi2: str
            abspath to the second ROI mask file
    out_file: str
            abspath of filename to save output merged ROI file
    overwrite: bool
            Whether to allow overwriting outputs

    Outputs
    =======
    out_file: str
            abspath of output file created by this function

    """

    roi2_mult2 = roi2.removesuffix(".nii.gz") + "_mult-2.nii.gz"

    mrcalc = find_program("mrcalc")

    # Multiply second ROI by 2
    cmd_mrcalc_mult = [mrcalc, roi2, "2", "-mult", roi2_mult2]

    # Merge ROIs
    cmd_mrcalc_merge = [mrcalc, roi1, roi2_mult2, "-add", out_file]

    # Abort if file already exists and overwriting not allowed
    if overwrite == False:
        overwrite_check(labelled_roi2)
        overwrite_check(out_file)
    else:
        cmd_mrcalc_mult += ["-force"]
        cmd_mrcalc_merge += ["-force"]

    run_command(cmd_mrcalc_mult)
    run_command(cmd_mrcalc_merge)

    return out_file
