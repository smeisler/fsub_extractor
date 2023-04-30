# _fsub-extractor_
This is an application for extracing **F**unctional **Su**bcomponents of **B**undles. This software can take gray matter regions, project them into white matter, intersect them with the gray-matter-white-matter-interface (GMWMI), and find streamlines that connect to these intersected region. It will also produce a visualization of the streamlines, and can sample scalar values along the extracted streamlines (tract profile or average across all streamlines).

This software was conceived of and developed during NeuroHackademy 2022.

## Install from GitHub
```
foo@bar:~$ git clone https://github.com/smeisler/fsub-extractor.git
foo@bar:~$ cd fsub-extractor
foo@bar:~$ pip install .   # for end user
# you may remove the original source code if you are an end user:
foo@bar:~$ cd ..
foo@bar:~$ rm -r fsub-extractor
```

If you are a developer, and if there is any update in the source code locally, you may update the installation with:
```
# Suppose you're in root directory of fsub-extractor source code:
foo@bar:~$ pip install -e .    # for developer to update
```

## Dependencies and Prerequisites
Dependencies include:
* Python >= 3.9.0
* MRTrix = 3.0.3
* DIPY = 1.5.0
* vtk >= 9.1.0
* Fury = 0.8.0
* Dask = 2022.8.0
* FreeSurfer >= 7.2.0 (it might work with lower versions, but this code was not tested on previous versions).

If you are using this software, you should be at the point in your analysis where you have:
* Preprocessed DWI, with tract-files of interest.
    * .trk or .tck; could be whole-brain or segmented bundles.
    * You might also have scalar maps (e.g., FA, MD, NODDI metrics; .nii.gz) that you want to sample streamlines on.
* BINARY masks of ROIs, e.g. from fMRI GLM clusters.
    * Can be defined in volumetric space (.nii.gz) or surface space (.mgz or .label).
* FreeSurfer `recon-all` outputs on the subject's anatomical image.
    * This is needed to create the GMWMI and project ROIs perpendicular to the white matter.
* All files (anatomical, DWI/streamlines, fROIs) **must be in the same space** (voxel sizes do not need to be equal).
    
## Usage
### `extractor`
The `extractor` function has two main use cases:
1. Deriving *all* streamlines that connect to an ROI.
    * Best-suited for looking at segmented bundles as opposed to whole-brain tractograms.
2. Deriving streamlines that connect a pair of ROIs.
    * Whole-brain or segmented bundles can work, depending on the ROI locations.
```
extractor -h
usage: extractor [-h] --subject SUBJECT --tract TRACT --roi1 ROI1
                 [--fs-dir FS_DIR] [--hemi HEMI] [--trk-ref TRK_REF]
                 [--gmwmi GMWMI] [--roi2 ROI2] [--search-dist SEARCH_DIST]
                 [--search-type SEARCH_TYPE]
                 [--projfrac-params START,STOP,DELTA] [--out-dir OUT_DIR]
                 [--out-prefix OUT_PREFIX] [--scratch SCRATCH]
                 [--overwrite | --no-overwrite]
                 [--skip-roi-projection | --no-skip-roi-projection | --skip_roi_projection | --no-skip_roi_projection]
                 [--skip-gmwmi-intersection | --no-skip-gmwmi-intersection | --skip_gmwmi_intersection | --no-skip_gmwmi_intersection]
                 [--skip-viz | --no-skip-viz | --skip-viz | --no-skip-viz]
                 [--interactive-viz | --no-interactive-viz | --interactive_viz | --no-interactive_viz]
                 [--orig-color R,G,B] [--fsub-color R,G,B]
                 [--roi1-color R,G,B] [--roi2-color R,G,B]
                 [--roi-opacity ROI_OPACITY] [--fsub-linewidth FSUB_LINEWIDTH]
                 [--img-viz IMG_VIZ] [--axial-offset AXIAL_OFFSET]
                 [--saggital-offset SAGGITAL_OFFSET]
                 [--camera-angle CAMERA_ANGLE]

Functionally segments a tract file based on intersections with prespecified
ROI(s) in gray matter.

options:
  -h, --help            show this help message and exit
  --subject SUBJECT     Subject name. Unless --skip-roi-proj is specified,
                        this must match the name in the FreeSurfer folder.
  --tract TRACT         Path to tract file (.tck or .trk). Should be in the
                        same space as FreeSurfer inputs.
  --roi1 ROI1           First ROI file (.mgz, .label, or .nii.gz). File should
                        be binary (1 in ROI, 0 elsewhere).
  --fs-dir FS_DIR, --fs_dir FS_DIR
                        Path to FreeSurfer directory for the subject. Required
                        unless --skip-roi-proj is specified.
  --hemi HEMI           FreeSurfer hemisphere name(s) corresponding to
                        locations of the ROIs, separated by a comma (no
                        spaces) if different for two ROIs (e.g 'lh,rh').
                        Required unless --skip-roi-proj is specified.
  --trk-ref TRK_REF, --trk_ref TRK_REF
                        Path to reference file, if passing in a .trk file.
                        Typically a nifti-related object from the native
                        diffusion used for streamlines generation (e.g., an FA
                        map)
  --gmwmi GMWMI         Path to GMWMI image (.nii.gz or .mif). If not
                        specified or not found, it will be created from
                        FreeSurfer inputs. Image must be a binary mask.
                        Ignored if --skip-gmwmi-intersection is specified.
  --roi2 ROI2           Second ROI file (.mgz, .label, or .nii.gz). If
                        specified, program will find streamlines connecting
                        ROI1 and ROI2. File should be binary (1 in ROI, 0
                        elsewhere).
  --search-dist SEARCH_DIST, --search_dist SEARCH_DIST
                        Distance in mm to search ahead of streamlines for ROIs
                        (float). Default is 4.0 mm.
  --search-type SEARCH_TYPE, --search_type SEARCH_TYPE
                        Method of searching for streamlines (radial, reverse,
                        forward). Default is forward.
  --projfrac-params START,STOP,DELTA, --projfrac_params START,STOP,DELTA
                        Comma delimited list (no spaces) of projfrac
                        parameters for mri_surf2vol / mri_label2vol. Provided
                        as start,stop,delta. Default is --projfrac-
                        params='-2,0,0.05'. Start must be negative to project
                        into white matter.
  --out-dir OUT_DIR, --out_dir OUT_DIR
                        Directory where outputs will be stored (a subject-
                        folder will be created there if it does not exist).
  --out-prefix OUT_PREFIX, --out_prefix OUT_PREFIX
                        Prefix for all output files. Default is no prefix.
  --scratch SCRATCH, --scratch SCRATCH
                        Path to scratch directory. Default is current
                        directory.
  --overwrite, --no-overwrite
                        Whether to overwrite outputs. Default is to overwrite.
                        (default: True)
  --skip-roi-projection, --no-skip-roi-projection, --skip_roi_projection, --no-skip_roi_projection
                        Whether to skip projecting ROI into WM (not
                        recommended unless ROI is already projected). Default
                        is to not skip projection. (default: False)
  --skip-gmwmi-intersection, --no-skip-gmwmi-intersection, --skip_gmwmi_intersection, --no-skip_gmwmi_intersection
                        Whether to skip intersecting ROI with GMWMI (not
                        recommended unless ROI is already intersected).
                        Default is to not skip intersection. (default: False)
  --skip-viz, --no-skip-viz, --skip-viz, --no-skip-viz
                        Whether to skip the output figure. Default is to
                        produce the figure. (default: False)
  --interactive-viz, --no-interactive-viz, --interactive_viz, --no-interactive_viz
                        Whether to produce an interactive visualization.
                        Default is not interactive. (default: False)
  --orig-color R,G,B, --orig_color R,G,B
                        Comma-delimited (no spaces) color spec for original
                        bundle in visualization, as fractional R,G,B. Default
                        is 0.8,0.8,0.
  --fsub-color R,G,B, --fsub_color R,G,B
                        Comma-delimited (no spaces) color spec for FSuB bundle
                        in visualization, as fractional R,G,B. Default is
                        0.2,0.6,1.
  --roi1-color R,G,B, --roi1_color R,G,B
                        Comma-delimited (no spaces) color spec for ROI1 in
                        visualization, as fractional R,G,B. Default is
                        0.2,1,1.
  --roi2-color R,G,B, --roi2_color R,G,B
                        Comma-delimited (no spaces) color spec for ROI2 in
                        visualization, as fractional R,G,B. Default is
                        0.2,1,1.
  --roi-opacity ROI_OPACITY, --roi_opacity ROI_OPACITY
                        Opacity for ROI(s) in visualization (float). Default
                        is 0.7.
  --fsub-linewidth FSUB_LINEWIDTH, --fsub_linewidth FSUB_LINEWIDTH
                        Linewidth for extracted steamlines in visualization
                        (float). Default is 3.0.
  --img-viz IMG_VIZ, --img-viz IMG_VIZ
                        Path to image to plot in visualization (.nii.gz). Must
                        be in same space as DWI/anatomical inputs.
  --axial-offset AXIAL_OFFSET, --axial_offset AXIAL_OFFSET
                        Float (-1,1) describing where to display axial slice.
                        -1 is bottom, 1 is top. Default is 0.0.
  --saggital-offset SAGGITAL_OFFSET, --saggital_offset SAGGITAL_OFFSET
                        Float (-1,1) describing where to display saggital
                        slice. -1 is left, 1 is right. Default is 0.0.
  --camera-angle CAMERA_ANGLE, --camera_angle CAMERA_ANGLE
                        Camera angle for visualization. Choices are either
                        'saggital' or 'axial'. Default is 'saggital.'
 ```
 ### `streamline_scalar`
 The `streamline_scalar` function can be used to find summary stats of a given scalar map (e.g. fractional anisotropy) within a given tract, as well as produce tract-profiles for these scalars along the length of the tract.
 ```
 streamline_scalar -h
usage: streamline_scalar [-h] --subject SUBJECT --tract TRACT --scalar_paths
                         SCALAR_PATHS --scalar_names SCALAR_NAMES
                         [--n_points N_POINTS] [--out-dir OUT_DIR]
                         [--out-prefix OUT_PREFIX]
                         [--overwrite | --no-overwrite]

Extracts tract-average and along-the-tract measures of input scalar metrics
(.nii.gz) for a specified streamline file (.tck/.trk).

options:
  -h, --help            show this help message and exit
  --subject SUBJECT     Subject name.
  --tract TRACT         Path to tract file (.tck or .trk). Should be in the
                        same space as the scalar map inputs.
  --scalar_paths SCALAR_PATHS, --scalar-paths SCALAR_PATHS
                        Comma delimited list (no spaces) of path(s) to scalar
                        maps (e.g. /path/to/FA.nii.gz). This will also be used
                        as a spatial reference file is a .trk file is passed
                        in as a streamlines object.
  --scalar_names SCALAR_NAMES, --scalar-names SCALAR_NAMES
                        Comma delimited list (no spaces) of names to scalar
                        maps (e.g. Fractional_Anisotropy). The number of names
                        must match the number of scalar paths
  --n_points N_POINTS, --n-points N_POINTS
                        Number of nodes to use in tract profile (default is
                        100)
  --out-dir OUT_DIR, --out_dir OUT_DIR
                        Directory where outputs will be stored (a subject-
                        folder will be created there if it does not exist).
  --out-prefix OUT_PREFIX, --out_prefix OUT_PREFIX
                        Prefix for all output files. Default is no prefix.
  --overwrite, --no-overwrite
                        Whether to overwrite outputs. Default is to overwrite.
                        (default: True)
```

## Questions? Want to contribute?
We welcome any questions, feedback, or collaboration! We ask that you start by opening an [issue](https://github.com/smeisler/fsub_extractor/issues) or [pull request](https://github.com/smeisler/fsub_extractor/pulls) in this repository to discuss. When doing so, please follow the [Code of Conduct](https://github.com/smeisler/fsub_extractor/blob/main/CODE_OF_CONDUCT.md).

## License information
([more information on the MIT license](https://en.wikipedia.org/wiki/MIT_License))

MIT License

Copyright (c) 2022 Steven Meisler

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

## Contributors
<!-- readme: contributors -start -->
<table>
<tr>
    <td align="center">
        <a href="https://github.com/smeisler">
            <img src="https://avatars.githubusercontent.com/u/27028726?v=4" width="100;" alt="smeisler"/>
            <br />
            <sub><b>Steven Meisler</b></sub>
        </a>
    </td>
    <td align="center">
        <a href="https://github.com/emilykubota">
            <img src="https://avatars.githubusercontent.com/u/19805108?v=4" width="100;" alt="emilykubota"/>
            <br />
            <sub><b>Emily Kubota</b></sub>
        </a>
    </td>
    <td align="center">
        <a href="https://github.com/zhao-cy">
            <img src="https://avatars.githubusercontent.com/u/20084724?v=4" width="100;" alt="zhao-cy"/>
            <br />
            <sub><b>Chenying Zhao</b></sub>
        </a>
    </td>
    <td align="center">
        <a href="https://github.com/drewwint">
            <img src="https://avatars.githubusercontent.com/u/53614162?v=4" width="100;" alt="drewwint"/>
            <br />
            <sub><b>Drew E. Winters</b></sub>
        </a>
    </td>
    <td align="center">
        <a href="https://github.com/mckenziephagen">
            <img src="https://avatars.githubusercontent.com/u/35019015?v=4" width="100;" alt="mckenziephagen"/>
            <br />
            <sub><b>McKenzie Paige Hagen</b></sub>
        </a>
    </td></tr>
</table>
<!-- readme: contributors -end -->
