import nibabel as nib
import subprocess 
import csv 

def dice_coefficient(
    tck_file1,
    tck_file2, 
    ref_anat,
    out_prefix,
    out_path
):
    """Uses tckmap to transform two input tck_files to nifti images and then calculate the dice overlap.

    Parameters
    ==========
    tck_file1: str
            Path to the first input tractography file (.tck)
    tck_file2: str
            Path to the second input tractography file (.tck)
    ref_anat: str
            Path to reference anatomy file (.nii.gz)
    out_prefix: str
            Prefix for output file 
    out_path: str
            Path to store output files 

    Outputs
    =======
    Function returns the dice coefficient as a .csv at the out_path. 
  
    """

    # Transform both tck files to nifti using tckmap
    out_name1=tck_file1[:-3]+'nii.gz'
    subprocess.run("tckmap -template "+ref_anat+" "+tck_file1+" "+out_name1,shell=True) 

    out_name2=tck_file2[:-3]+'nii.gz'
    subprocess.run("tckmap -template "+ref_anat+" "+tck_file2+" "+out_name2,shell=True)


    # Read in images
    img1 = nib.load(out_name1)
    img2 = nib.load(out_name2)
  
    data1 = img1.get_fdata()
    data2 = img2.get_fdata()

    overlap = sum(sum(sum((data1 > 0) & (data2 > 0))))
    sum1 = sum(sum(sum(data1 > 0)))
    sum2 = sum(sum(sum(data2 > 0)))

    dice = 2*overlap/(sum1+sum2)

    f = open(out_path+'/'+out_prefix+'_dice.csv','w')
    writer = csv.writer(f)
    writer.writerow([dice])
    f.close()
 


   
