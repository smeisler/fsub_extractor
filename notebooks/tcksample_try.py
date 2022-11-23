# get the averaged value

import os.path as op
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np



subjid="subj01"
num_points = 100
scalar_name="FA"

folder_main="/home/chenying/Desktop/fsub_extractor/data"
folder_subj = op.join(folder_main, subjid)

fn_output_fixedPoints = op.join(folder_subj, "tracks_1_2_2mm_fixedPoints-" + str(num_points) + "_output_tcksample.txt")

table = pd.read_csv(fn_output_fixedPoints, sep = " ", header = None, skiprows=1)

avg_perPoint = table.mean(axis = 0)  # each row is a streamline, average across streamlines

## Plot:
# plot averaged value per point:
fig, ax = plt.subplots()
ax.plot(avg_perPoint)
ax.set_ylabel(scalar_name)
ax.legend()

#plt.show()

# plot all streamlines:
# fig, ax = plt.subplots()
# table.shape[0]
# #for i in np.arange(0,table.shape[0])
# ax.plot()

print()