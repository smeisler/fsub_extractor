from dipy.io.streamline import load_tck
from dipy.io.image import load_nifti
from fury import actor, window, colormap as cmap
from os.path import exists
import nibabel as nib
import numpy as np


def visualize_sub_bundles(
    orig_bundle,
    fsub_bundle,
    ref_anat,
    outpath_base,
    roi1,
    roi2=None,
    orig_color=[0.8, 0.8, 0],
    fsub_color=[0.2, 0.6, 1],
    roi1_color=[0.2, 1, 1],
    roi2_color=[1, 0.2, 1],
    roi_opacity=0.7,
    fsub_linewidth=3.0,
    interactive=False,
    show_anat=False,
    axial_offset=0,
    saggital_offset=0,
    camera_angle="saggital",
    hemi="lh",
):
    """Takes in tck and nifti files and makes a fury visualization

    Parameters
    ==========
    orig_bundle: Original bundle (.tck)
    fsub_bundle: Sub bundle output (.tck)
    ref_anat: Reference anatomy (.nii.gz)
    fig_path = Path to save the figure
    fname = filename (.png)
    roi1: ROI that was used to create sub bundle file (.nii.gz)
    roi2 (Optional): Second ROI that was used to create pairwise sub-bundle (.nii.gz)
    orig_color (Optional): Color for original bundle ([R,G,B])
    fsub_color (Optional): Color for fsub bundle ([R,G,B])
    roi1_color (Optional): Color for ROI1 ([R,G,B])
    roi2_color (Optional): Color for ROI2 ([R,G,B])
    Interactive (Optional): Make interactive fury visualization (True) or save out screenshot (default = False)
    show_anat (Optional): Whether to overlay anatomy on the figure (default = False)
    axial_offset (Optional): Where to display axial slice (-1,1) where -1 is bottom of image and 1 is top.
        (default = 0, which is the middle of the image)
    saggital_offset (Optional): Where to display saggital slice (-1,1) where -1 is left of image and 1 is right.
        (default = 0, which is the middle of the image)
    camera_angle (Optional): Angle for screenshot ('saggital' (default) or 'axial')
    hemi (Optional): For saggital picture, what hemisphere to view from. Accepts either 'lh' or 'rh'.

    Outputs
    =======
    Function saves out image to the out_dir
    """

    # Load in reference anatomy
    reference_anatomy = nib.load(ref_anat)

    # Load in streamlines
    orig_streamlines = load_tck(orig_bundle, reference_anatomy)
    orig_streamlines = orig_streamlines.streamlines

    # Repeat the color matrix for each streamline (orig)
    n_orig_streamlines = np.shape(orig_streamlines)[0]
    orig_color = np.array([orig_color])
    orig_color = np.repeat(orig_color, n_orig_streamlines, axis=0)

    # Make the streamline actor (orig)
    orig_streamlines_actor = actor.line(orig_streamlines, orig_color, opacity=0.1)

    # Load in streamlines
    fsub_streamlines = load_tck(fsub_bundle, reference_anatomy)
    fsub_streamlines = fsub_streamlines.streamlines

    # Repeat the color matrix for each streamline (fsub)
    n_fsub_streamlines = np.shape(fsub_streamlines)[0]
    fsub_color = np.array([fsub_color])
    fsub_color = np.repeat(fsub_color, n_fsub_streamlines, axis=0)

    # Make the streamline actor (fsub)
    fsub_streamlines_actor = actor.line(
        fsub_streamlines, fsub_color, linewidth=fsub_linewidth
    )

    # Load in ROI(s)
    roi1_data, affine, img = load_nifti(roi1, return_img=True)
    roi1_mask = roi1_data > 0
    roi1_actor = actor.contour_from_roi(roi1_mask, affine, roi1_color, roi_opacity)

    # Add actors to scene
    figure = window.Scene()
    figure.add(orig_streamlines_actor)
    figure.add(fsub_streamlines_actor)
    figure.add(roi1_actor)

    if roi2 is not None:
        roi2_data, affine, img = load_nifti(roi2, return_img=True)
        roi2_mask = roi2_data > 0
        roi2_actor = actor.contour_from_roi(roi2_mask, affine, roi2_color, roi_opacity)
        figure.add(roi2_actor)

    if show_anat:
        data = reference_anatomy.get_data()
        affine = reference_anatomy.affine

        # restrict values for visualization
        mean, std = data[data > 0].mean(), data[data > 0].std()
        value_range = (mean - 0.5 * std, mean + 1.5 * std)

        # make slice actor
        slice_actor = actor.slicer(data, affine, value_range)

        # calculate where to display the image based on the offset
        axial_offset = (
            slice_actor.shape[1] - (slice_actor.shape[1] // 2)
        ) * axial_offset
        slice_actor.display(None, None, slice_actor.shape[1] // 2 + int(axial_offset))
        figure.add(slice_actor)

        # add to figure
        figure.add(slice_actor)

        # make a copy to make a saggital slice
        saggital_actor = slice_actor.copy()

        # calculate where to display the image based on the offset
        saggital_offset = (
            saggital_actor.shape[0] - (saggital_actor.shape[0] // 2)
        ) * saggital_offset
        saggital_actor.display(
            saggital_actor.shape[0] // 2 + int(saggital_offset), None, None
        )
        figure.add(saggital_actor)

    cam = figure.GetActiveCamera()
    cam.SetViewUp(0, 0, 0)
    if camera_angle == "saggital":
        if hemi == "lh":
            cam.Yaw(270)
            cam.Roll(90)

        if hemi == "rh":
            cam.Yaw(90)
            cam.Roll(270)

    if interactive:
        window.show(figure)

    window.record(
        figure, out_path=(outpath_base + "visualization.png"), size=(1200, 900)
    )  # TODO: make better file output name


def define_streamline_actor(tck, reference_anatomy, color):
    """Takes in tck reference anatomy files and outputs a fury streamline actor.
    Parameters
    ==========
    tck: streamline to plot (.tck)
    reference_anatomy: Reference anatomy (.nii.gz)
    color = color to plot streamlines as ([R,B,G])

    Outputs
    =======
    streamlines_actor to be added to a fury scene
    """
    # read in reference anatomy
    reference_anatomy = nib.load(reference_anatomy)

    # read in streamlines
    streamlines = load_tck(tck, reference_anatomy)
    streamlines = streamlines.streamlines

    # get number of streamlines in order to make them the same color
    n_streamlines = np.shape(streamlines)[0]
    color = np.array([color])
    color = np.repeat(color, n_streamlines, axis=0)

    # make the streamline actor
    if n_streamlines > 0:
        streamlines_actor = actor.line(streamlines, color, opacity=0.1)
    else:
        streamlines_actor = None
    return streamlines_actor


def define_roi_actor(roi_path, color, opacity=0, roi_val=1):
    """Takes in roi file and outputs a fury roi actor.
    Parameters
    ==========
    roi_path: path to roi file (.nii.gz)
    color = color to plot roi as ([R,B,G])
    opacity = how opaque to make the roi ([0-1], default =  0)
    roi_val = roi value (default = 1)

    Outputs
    =======
    roi_actor to be added to a fury scene
    """
    if exists(roi_path):
        roi_data, affine, img = load_nifti(roi_path, return_img=True)
        roi_mask = roi_data == roi_val
        roi_actor = actor.contour_from_roi(roi_mask, affine, color, opacity)
    else:
        roi_actor = None
    return roi_actor


def define_slice_actor(reference_anatomy, view="axial", offset=0):

    """Takes in reference anatomy file and returns slice actor.
    Parameters
    ==========
    reference_anatomy: path to reference anatomy file (.nii.gz)
    view: view of the slice, options are 'saggital' or 'axial' (default)
    offset = how far off center the slice should be plotted ([-1,1]). 0 (center) is default.

    Outputs
    =======
    slice_actor to be added to a fury scene
    """

    # read in reference anatomy
    reference_anatomy = nib.load(reference_anatomy)

    data = reference_anatomy.get_fdata()
    affine = reference_anatomy.affine

    # restrict values for visualization
    mean, std = data[data > 0].mean(), data[data > 0].std()
    min_val, max_val = data[data > 0].min(), data[data > 0].max()
    value_range = (min_val, max_val)

    # make slice actor
    slice_actor = actor.slicer(data, affine, value_range)

    # calculate where to display the image based on the offset
    if view == "axial":
        offset = (slice_actor.shape[1] - (slice_actor.shape[1] // 2)) * offset
        slice_actor.display(None, None, slice_actor.shape[1] // 2 + int(offset))
    if view == "saggital":
        offset = (slice_actor.shape[0] - (slice_actor.shape[0] // 2)) * offset
        slice_actor.display(slice_actor.shape[0] // 2 + int(offset), None, None)

    return slice_actor


def visualize_bundles(
    streamline_actor,
    interactive,
    slice_actor=None,
    roi_actor=None,
    camera_angle="saggital",
    hemi="lh",
    filename=None,
):

    """Takes in streamline actor, optional roi actor and slice actors
    and ouputs a fury scene.

    Parameters
    ==========
    streamline_actor: list of fury streamline actors (e.g., [output] of define_streamline_actor)
    interactive: whether you want an interactive window to pop up
    camera_angle: angle of the camera (options: 'saggital' or 'axial', default: 'saggital')
    hemi = hemisphere (default: 'lh')
    roi_actor: list of fury roi actors (e.g., [output] of define roi_actor)
    slice_actor: list fury slice actors (e.g., [output] of define_slice_actor)
    filename: fullpath to save the image (e.g., .png)

    note: for plotting multiple streamlines, rois, or slices the function
    will loop over a list of actors and add them to the scene.

    Outputs
    =======
    slice_actor to be added to a fury scene
    """

    figure = window.Scene()

    for t in range(len(streamline_actor)):
        figure.add(streamline_actor[t])

    for r in range(len(roi_actor)):
        figure.add(roi_actor[r])

    for s in range(len(slice_actor)):
        figure.add(slice_actor[s])

    cam = figure.GetActiveCamera()
    cam.SetViewUp(0, 0, 0)

    if camera_angle == "saggital":
        if hemi == "lh":
            cam.Yaw(270)
            cam.Roll(90)
        if hemi == "rh":
            cam.Yaw(90)
            cam.Roll(270)

    if interactive:
        window.show(figure)
    else:
        window.record(figure, outpath=filename, size=(1200, 900))
