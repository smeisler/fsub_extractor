# get the averaged value


subjid="subj01"
folder_main="../../data"
folder_subj="${folder_main}/${subjid}"

fn_scalar_image="${folder_subj}/fa.nii.gz"
fn_streamlines="${folder_subj}/tracks_1_2_2mm.tck"
fn_output = fn_streamlines.replace("bananas", "apples")