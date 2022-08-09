from dipy.core.gradients import gradient_table
from dipy.io.streamline import load_tck
from dipy.reconst.shm import CsaOdfModel
from dipy.data import default_sphere, get_fnames
from dipy.direction import peaks_from_model
from dipy.io.gradients import read_bvals_bvecs
from dipy.io.image import load_nifti, load_nifti_data
from dipy.tracking.stopping_criterion import ThresholdStoppingCriterion
from dipy.tracking import utils
from dipy.tracking.local_tracking import LocalTracking
from dipy.tracking.streamline import Streamlines
from fury import actor, window, colormap as cmap
import nibabel as nib
import numpy as np


def visualize_sub_bundles(orig_bundle,fsub_bundle, ref_anat, fig_path, fname, 
	roi1, roi2 = None, orig_color = [.8,.8,0],fsub_color = [.2,.6,1],
	roi1_color = [.2,1,1],roi2_color = [.2,1,1],
	interactive = False):

# Takes in tck and nifti files and makes a fury visualization 
# 
# 
# 	Inputs: orig_bundle: Original bundle (.tck)
#			fsub_bundle: Sub bundle output (.tck)
#			ref_anat: Reference anatomy (e.g., fa.nii.gz)
# 			fig_path = path to save the figure
#			fname = filename (.png)
# 			roi1: ROI that was used to create sub bundle file (.nii.gz)
#			roi2 (Optional): Second ROI that was used to 
#					create pairwise sub-bundle (.nii.gz)
#			orig_color (Optional): Color for original bundle ([R,G,B])
#			fsub_color (Optional): Color for fsub bundle ([R,G,B])
#			roi1_color (Optional): Color for ROI1 ([R,G,B])
#			roi2_color (Optional): Color for ROI2 ([R,G,B])
# 			Interactive: Make interacctive fury visualization (True) or save out screenshot (False; default)

# Set defaults 

	# Load in reference anatomy 
	reference_anatomy = nib.load(ref_anat)

	# Load in streamlines 
	orig_streamlines = load_tck(orig_bundle,reference_anatomy)
	orig_streamlines = orig_streamlines.streamlines

	# Repeat the color matrix for each streamline (orig)
	n_orig_streamlines = np.shape(orig_streamlines)[0]
	orig_color = np.array([orig_color])
	orig_color = np.repeat(orig_color,n_orig_streamlines,axis=0)

	# Make the streamline actor (orig)
	orig_streamlines_actor = actor.line(orig_streamlines, 
	orig_color,opacity = .1)


	# Load in streamlines
	fsub_streamlines = load_tck(fsub_bundle,reference_anatomy)
	fsub_streamlines = fsub_streamlines.streamlines

	# Repeat the color matrix for each streamline (fsub)
	n_fsub_streamlines = np.shape(fsub_streamlines)[0]
	fsub_color = np.array([fsub_color])
	fsub_color = np.repeat(fsub_color,n_fsub_streamlines,axis=0)

	# Make the streamline actor (fsub)
	fsub_streamlines_actor = actor.line(fsub_streamlines, 
		fsub_color,linewidth = 3)

	# Load in ROI(s)
	roi1_data, affine, img = load_nifti(roi1, return_img=True)
	roi1_mask = roi1_data > 0
	roi_opacity = .7
	roi1_actor = actor.contour_from_roi(roi1_mask, affine,
                                       roi1_color, roi_opacity)

	# Add actors to scene 
	figure = window.Scene()
	figure.add(orig_streamlines_actor)
	figure.add(fsub_streamlines_actor)
	figure.add(roi1_actor)

	if(roi2 is not None):
		roi2_data, affine, img = load_nifti(roi2, return_img=True)
		roi2_mask = roi2_data > 0
		roi_opacity = .7
		roi2_actor = actor.contour_from_roi(roi2_mask, affine,
                                       roi2_color, roi_opacity)
		figure.add(roi2_actor)


	if interactive:
		window.show(figure)

	window.record(figure, out_path=(fig_path+'/'+fname), size=(1200, 900))

