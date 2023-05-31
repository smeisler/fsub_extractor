#!/bin/bash

#rois=(lh_mOTS_words lh_mFus_faces)
#sub=subj04
#tract=../data/${sub}/dwi/lh_AF.tck
#t1=../data/${sub}/anat/T1.nii.gz
#gmwmi=../data/${sub}/anat/gmwmi.nii.gz
#hem=lh
#outdir=../extractor_outputs
#fsdir=../freesurfer

# Single ROI case

extractor --subject subj04 --tract ../data/subj04/dwi/lh_AF.tck --roi1 ../data/subj04/func/lh_mOTS_words.label --fs-dir ../freesurfer --hemi lh --trk-ref ../data/sub04/anat/T1.nii.gz --out-dir ../extractor_outputs --search_dist 3 --search_type radial --out_prefix lh_mOTS_words --projfrac-params=-1,0,.1

extractor --subject subj04 --tract ../data/subj04/dwi/lh_AF.tck --roi1 ../data/subj04/func/lh_mFus_faces.label --fs-dir ../freesurfer --hemi lh --trk-ref ../data/sub04/anat/T1.nii.gz --out-dir ../extractor_outputs --search_dist 3 --search_type radial --out_prefix lh_mFus_faces --projfrac-params=-1,0,.1

#for roi in "${rois[@]}";
#do
#	roipath=../data/${sub}/func/${roi}.label
#	extractor --subject $sub --tract $tract --roi1 $roipath --hemi $hem --trk-ref $t1 --out-dir $outdir --out_prefix $roi --fs-dir $fsdir --projfrac-params=-1,0,.1
#done 


# Two ROI case 
#roipath1=../data/${sub}/func/lh_mOTS_words.label
#roipath2=../data/${sub}/func/lh_IFS_words.label

extractor --subject subj04 --tract ../data/subj04/dwi/lh_AF.tck --roi1 ../data/subj04/func/lh_mOTS_words.label --roi2 ../data/subj04/func/lh_IFS_words.label --hemi lh --trk-ref ../data/sub04/anat/T1.nii.gz --out-dir ../extractor_outputs --search_dist 3 --search_type radial --out_prefix lh_mOTS_IFS --fs-dir ../freesurfer --projfrac-params=-1,0,.1
