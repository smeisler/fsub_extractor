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
* DIPY >= 1.5.0
* vtk >= 9.1.0
* Fury >= 0.8.0
* FreeSurfer >= 7.2.0 (it might work with lower versions, but this code was not tested on previous versions).

If you are using this software, you should be at the point in your analysis where you have:
* Preprocessed DWI, with tract-files of interest.
    * .trk or .tck; could be whole-brain or segmented bundles.
    * You might also have scalar maps (e.g., FA, MD, NODDI metrics; .nii.gz) that you want to sample streamlines on.
* BINARY masks of ROIs, e.g. from fMRI GLM clusters.
    * Can be defined in volumetric space (.nii.gz) or surface space (.mgz, .label, .gii).
* FreeSurfer `recon-all` outputs on the subject's anatomical image.
    * This is needed to create the GMWMI and project ROIs into the white matter.
* Functional ROIs should be in the same space as FreeSurfer outputs. If DWI is in a different space (e.g., rotated to ACPC like in QSIPrep), a transformation can be supplied to define the rotation between FreeSurfer and DWI space (`--fs2dwi`).
    
## Usage
### `extractor`
The `extractor` function has two main use cases:
1. Deriving *all* streamlines that connect to an ROI.
    * Best-suited for looking at segmented bundles, as opposed to whole-brain tractograms.
2. Deriving streamlines that connect a pair of ROIs.
    * Whole-brain or segmented bundles can work, depending on the ROI locations and sizes.
```
❯ extractor -h
usage: extractor [-h] --subject sub-XXX --tract /PATH/TO/TRACT.trk|.tck [--tract-name TRACT_NAME]
                 --roi1 /PATH/TO/ROI1.mgz|.label|.gii|.nii.gz [--roi1-name ROI1_NAME]
                 [--roi2 /PATH/TO/ROI2.mgz|.label|.gii|.nii.gz] [--roi2-name ROI2_NAME]
                 [--fs-dir /PATH/TO/FreeSurfer/SUBJECTSDIR/] [--hemi {lh|rh|lh,rh|rh,lh}]
                 [--fs2dwi /PATH/TO/FS2DWI-REG.lta|.txt|.mat]
                 [--dwi2fs /PATH/TO/DWI2FS-REG.lta|.txt|.mat] [--reg-type {LTA,ITK,FSL}]
                 [--gmwmi /PATH/TO/GMWMI.nii.gz|.mif] [--gmwmi-thresh THRESHOLD]
                 [--search-dist DISTANCE] [--search-type {forward,radial,reverse}]
                 [--projfrac-params START,STOP,DELTA] [--sift2-weights /PATH/TO/SIFT2_WEIGHTS.csv]
                 [--exclude-mask /PATH/TO/EXCLUDE_MASK.nii.gz|.mif]
                 [--include-mask /PATH/TO/INCLUDE_MASK.nii.gz|.mif] [--out-dir /PATH/TO/OUTDIR/]
                 [--overwrite | --no-overwrite]
                 [--skip-roi-projection | --no-skip-roi-projection | --skip_roi_projection | --no-skip_roi_projection]
                 [--skip-gmwmi-intersection | --no-skip-gmwmi-intersection | --skip_gmwmi_intersection | --no-skip_gmwmi_intersection]
                 [--make-viz | --no-make-viz | --make_viz | --no-make_viz]
                 [--interactive-viz | --no-interactive-viz | --interactive_viz | --no-interactive_viz]
                 [--img-viz /PATH/TO/BACKGROUND_IMG.nii.gz] [--orig-color R,G,B] [--fsub-color R,G,B]
                 [--roi1-color R,G,B] [--roi2-color R,G,B] [--roi-opacity OPACITY]
                 [--fsub-linewidth LINEWIDTH] [--axial-offset OFFSET] [--saggital-offset OFFSET]
                 [--camera-angle {saggital,axial}]

Functionally segments a tract file based on intersections with prespecified ROI(s) in gray matter.

options:
  -h, --help            show this help message and exit
  --subject sub-XXX     Subject name. This must match the subject name in the FreeSurfer folder.
  --tract /PATH/TO/TRACT.trk|.tck
                        Path to original tract file (.tck or .trk). Should be in DWI space.
  --tract-name TRACT_NAME, --tract_name TRACT_NAME
                        Label for tract used in file names. Should not contain spaces. E.g., 'LeftAF'
                        or 'wholebrain'. Default is 'tract'.
  --roi1 /PATH/TO/ROI1.mgz|.label|.gii|.nii.gz
                        First ROI file (.mgz, .label, .gii, or .nii.gz). File should be binary (1 in
                        ROI, 0 elsewhere).
  --roi1-name ROI1_NAME, --roi1_name ROI1_NAME
                        Label for ROI1 outputs. Default is roi1
  --roi2 /PATH/TO/ROI2.mgz|.label|.gii|.nii.gz
                        Second ROI file (.mgz, .label, .gii, or .nii.gz). If specified, program will
                        find streamlines connecting ROI1 and ROI2. File should be binary (1 in ROI, 0
                        elsewhere).
  --roi2-name ROI2_NAME, --roi2_name ROI2_NAME
                        Label for ROI2 outputs. Default is roi2
  --fs-dir /PATH/TO/FreeSurfer/SUBJECTSDIR/, --fs_dir /PATH/TO/FreeSurfer/SUBJECTSDIR/
                        Path to FreeSurfer subjects directory. It should have a folder in it with your
                        subject name. Required unless --skip-roi-proj is specified.
  --hemi {lh|rh|lh,rh|rh,lh}
                        FreeSurfer hemisphere name(s) corresponding to locations of the ROIs, separated
                        by a comma (no spaces) if different for two ROIs (e.g 'lh,rh'). Required unless
                        --skip-roi-proj is specified.
  --fs2dwi /PATH/TO/FS2DWI-REG.lta|.txt|.mat
                        Path to registration for mapping FreeSurfer-to-DWI space. Mutually exclusive
                        with --dwi2fs.
  --dwi2fs /PATH/TO/DWI2FS-REG.lta|.txt|.mat
                        Path to registration for mapping DWI-to-FreeSurfer space. Mutually exclusive
                        with --fs2dwi.
  --reg-type {LTA,ITK,FSL}, --reg_type {LTA,ITK,FSL}
                        Registration format. LTA is the default for FreeSurfer and is .lta, ITK comes
                        from ITK and ANTS and is presumed to be a .txt, FSL comes from FSL and is .mat.
                        If left blank, will try to infer from file extension. Only try defining this if
                        inferring the registration type does not work and creates errors.
  --gmwmi /PATH/TO/GMWMI.nii.gz|.mif
                        Path to GMWMI image (.nii.gz or .mif). If not specified or not found, it will
                        be created from FreeSurfer inputs. Ignored if --skip-gmwmi-intersection is
                        specified. Should be in DWI space.
  --gmwmi-thresh THRESHOLD, --gmwmi_thresh THRESHOLD
                        Threshold above which to binarize the GMWMI image. Default is 0.0
  --search-dist DISTANCE, --search_dist DISTANCE
                        Distance in mm to search from streamlines for ROIs (float). Default is 3.0 mm.
  --search-type {forward,radial,reverse}, --search_type {forward,radial,reverse}
                        Method of searching for streamlines. Default is forward.
  --projfrac-params START,STOP,DELTA, --projfrac_params START,STOP,DELTA
                        Comma delimited list (no spaces) of projfrac parameters for mri_surf2vol /
                        mri_label2vol. Provided as start,stop,delta. Default is --projfrac-
                        params='-1,0,0.1'. Start must be negative to project into white matter.
  --sift2-weights /PATH/TO/SIFT2_WEIGHTS.csv, --sift2_weights /PATH/TO/SIFT2_WEIGHTS.csv
                        Path to SIFT2 weights file. If supplied, the sum of weights will be output with
                        streamline extraction.
  --exclude-mask /PATH/TO/EXCLUDE_MASK.nii.gz|.mif, --exclude_mask /PATH/TO/EXCLUDE_MASK.nii.gz|.mif
                        Path to exclusion mask (.nii.gz or .mif). If specified, streamlines that enter
                        this mask will be discarded. Must be in DWI space.
  --include-mask /PATH/TO/INCLUDE_MASK.nii.gz|.mif, --include_mask /PATH/TO/INCLUDE_MASK.nii.gz|.mif
                        Path to inclusion mask (.nii.gz or .mif). If specified, streamlines must
                        intersect with this mask to be included (e.g., a waypoint ROI). Must be in DWI
                        space.
  --out-dir /PATH/TO/OUTDIR/, --out_dir /PATH/TO/OUTDIR/
                        Directory where outputs will be stored (a subject-folder will be created there
                        if it does not exist). Default is current directory.
  --overwrite, --no-overwrite
                        Whether to overwrite outputs. Default is to overwrite. (default: True)
  --skip-roi-projection, --no-skip-roi-projection, --skip_roi_projection, --no-skip_roi_projection
                        Whether to skip projecting ROI into WM (not recommended unless ROI is already
                        projected). Default is to not skip projection. (default: False)
  --skip-gmwmi-intersection, --no-skip-gmwmi-intersection, --skip_gmwmi_intersection, --no-skip_gmwmi_intersection
                        Whether to skip intersecting ROI with GMWMI (not recommended unless ROI is
                        already intersected). Default is to not skip intersection. (default: False)

Options for Visualization:
  --make-viz, --no-make-viz, --make_viz, --no-make_viz
                        Whether to make the output figure. Default is to not produce the figure.
                        (default: False)
  --interactive-viz, --no-interactive-viz, --interactive_viz, --no-interactive_viz
                        Whether to produce an interactive visualization. Default is not interactive.
                        (default: False)
  --img-viz /PATH/TO/BACKGROUND_IMG.nii.gz, --img-viz /PATH/TO/BACKGROUND_IMG.nii.gz
                        Path to image to plot in visualization (.nii.gz). Should be in DWI space.
  --orig-color R,G,B, --orig_color R,G,B
                        Comma-delimited (no spaces) color spec for original bundle in visualization, as
                        fractional R,G,B. Default is 0.8,0.8,0.
  --fsub-color R,G,B, --fsub_color R,G,B
                        Comma-delimited (no spaces) color spec for FSuB bundle in visualization, as
                        fractional R,G,B. Default is 0.2,0.6,1.
  --roi1-color R,G,B, --roi1_color R,G,B
                        Comma-delimited (no spaces) color spec for ROI1 in visualization, as fractional
                        R,G,B. Default is 0.2,1,1.
  --roi2-color R,G,B, --roi2_color R,G,B
                        Comma-delimited (no spaces) color spec for ROI2 in visualization, as fractional
                        R,G,B. Default is 1,0.2,1.
  --roi-opacity OPACITY, --roi_opacity OPACITY
                        Opacity (0,1) for ROI(s) in visualization (float). Default is 0.7.
  --fsub-linewidth LINEWIDTH, --fsub_linewidth LINEWIDTH
                        Linewidth for extracted steamlines in visualization (float). Default is 3.0.
  --axial-offset OFFSET, --axial_offset OFFSET
                        Float (-1,1) describing where to display axial slice. -1.0 is bottom, 1.0 is
                        top. Default is 0.0.
  --saggital-offset OFFSET, --saggital_offset OFFSET
                        Float (-1,1) describing where to display saggital slice. -1.0 is left, 1.0 is
                        right. Default is 0.0.
  --camera-angle {saggital,axial}, --camera_angle {saggital,axial}
                        Camera angle for visualization. Default is 'saggital.'
 ```
 ### `streamline_scalar`
 The `streamline_scalar` function can be used to find summary stats of a given scalar map (e.g. fractional anisotropy) within a given tract, as well as produce tract-profiles for these scalars along the length of the tract.
```
❯ streamline_scalar -h
usage: streamline_scalar [-h] --subject sub-XXX --tract /PATH/TO/TRACT.trk|.tck --scalar_paths
                         /PATH/TO/SCALAR1.nii.gz,/PATH/TO/SCALAR2.nii.gz... --scalar_names
                         SCALAR1,SCALAR2... [--n_points POINTS] [--out-dir /PATH/TO/OUTDIR/]
                         [--out-prefix PREFIX] [--overwrite | --no-overwrite]

Extracts tract-average and along-the-tract measures of input scalar metrics (.nii.gz) for a specified
streamline file (.tck/.trk).

options:
  -h, --help            show this help message and exit
  --subject sub-XXX     Subject name.
  --tract /PATH/TO/TRACT.trk|.tck
                        Path to tract file (.tck or .trk). Should be in the same space as the scalar
                        map inputs.
  --scalar_paths /PATH/TO/SCALAR1.nii.gz,/PATH/TO/SCALAR2.nii.gz..., --scalar-paths /PATH/TO/SCALAR1.nii.gz,/PATH/TO/SCALAR2.nii.gz...
                        Comma delimited list (no spaces) of path(s) to scalar maps (e.g.
                        /path/to/FA.nii.gz).
  --scalar_names SCALAR1,SCALAR2..., --scalar-names SCALAR1,SCALAR2...
                        Comma delimited list (no spaces) of names to scalar maps (e.g.
                        Fractional_Anisotropy). The number of names must match the number of scalar
                        paths
  --n_points POINTS, --n-points POINTS
                        Number of nodes to use in tract profile (default is 100)
  --out-dir /PATH/TO/OUTDIR/, --out_dir /PATH/TO/OUTDIR/
                        Directory where outputs will be stored (a subject-folder will be created there
                        if it does not exist). Default is current directory.
  --out-prefix PREFIX, --out_prefix PREFIX
                        Prefix for all output files. Default is no prefix.
  --overwrite, --no-overwrite
                        Whether to overwrite outputs. Default is to overwrite. (default: True)
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
