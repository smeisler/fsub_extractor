#!/bin/bash

# Try tcksample on one subject's extracted tract (.tck)

subjid="subj01"
folder_main="../../data"
folder_subj="${folder_main}/${subjid}"

fn_scalar_image="${folder_subj}/fa.nii.gz"
fn_streamlines="${folder_subj}/tracks_1_2_2mm.tck"
fn_output="${fn_streamlines/.tck/_output_tcksample.txt}"

# per-streamline mean:
cmd="tcksample ${fn_streamlines} ${fn_scalar_image} ${fn_output} -stat_tck mean"    # per-streamline mean; will generate a txt file that includes mean scalar for each streamline
#echo $cmd
#$cmd

num_points=100
temp="_fixedPoints-${num_points}.tck"
fn_streamlines_fixedPoints="${fn_streamlines/.tck/"$temp"}"
cmd="tckresample ${fn_streamlines} ${fn_streamlines_fixedPoints} -num_points ${num_points}"
echo $cmd
$cmd

# then re-run tcksample on the updated streamlines:
fn_output_fixedPoints="${fn_streamlines_fixedPoints/.tck/_output_tcksample.txt}"
cmd="tcksample ${fn_streamlines_fixedPoints} ${fn_scalar_image} ${fn_output_fixedPoints}"
echo $cmd
$cmd