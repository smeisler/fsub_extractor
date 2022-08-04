#####################################################################################
#                                                                                   #
#             Bundle stats                                                          #
#   A part of ex-tract, a package for functionally defined white matter tracts      #
#   This module extracts average statistics (e.g. FA, MD) from the segmented        #
#   white matter streamlines.                                                       #
#                                                                                   #
#   Author: Alicja Olszewska, Laboratory of Brain Imaging,                          #
#           Nencki Institute of Experimental Biology                                #
#           a.olszewska@nencki.edu.pl                                               #
#                                                                                   #
#   Neurohackademy 2022, 27.07 - 05.08.2022, FSUB-extractor team                    #
#                                                                                   #
#####################################################################################

# data analysis
import numpy as np
import pandas as pd

# file handling
import os
import os.path as op

# visualisations
import matplotlib.pyplot as plt
import seaborn as sns
import ptitprince as pt

# inputs

# calling the mrtrix processes
import subprocess
from fsub_extractor.main import find_program

'''
Input: 
- a folder containing:
-- .tck files with extracted streamlines
-- .nii.gz files with statistics to be extracted (e.g. FA, MD)
Outputs:
- stats per streamline in raw (.txt), tidy and "excel" forms (.tsv)
- summary statistics for each statistic (.tsv)
- visual representation of the tract statistics (mean per streamline, mean & sd for extracted tract,
  distribution among streamline means) (.png)
'''


TCK_FILEPATH = '/Users/alicja/Documents/Neurohackademy22/fsub/subj01/extracted.tck' #this will be pased from the main
TCK_NAME = TCK_FILEPATH.split('/')[-1]
MAINPATH = TCK_FILEPATH.split(TCK_NAME)[0]

# get address to statfiles and couple them with statnames
statfiles = ['/Users/alicja/Documents/Neurohackademy22/fsub/subj01/fa.nii.gz',
             '/Users/alicja/Documents/Neurohackademy22/fsub/subj01/md.nii.gz',
             '/Users/alicja/Documents/Neurohackademy22/fsub/subj01/rd.nii.gz']
statnames = ['fa', 'md', 'rd']
stats = dict(zip(statnames, statfiles))
# [TODO] make it into arguments


def extract_means(filename):
	"""
	Reads the tcksample output to get tract statistics
	:param filename: a path with the filename to the file containing the values, output of the tcksample command
	:return: a list with the values in floating point format
	"""
	with open(filename) as f:
		return [float(val) for val in f.read().splitlines()[1].split(' ')]


def create_statfiles(tck_file, stat):
	"""
	Takes a bundle file and extracts statistics from relevant streamlines
	:param tck_file: a list (string, string), name[0] and path[1] of the segmented streamlines file
	:param stat: a list (string, string), the name[0] and path[1] of statistics we are interested in
	:return: name of the file which is created
	"""
	# Run MRtrix CLI
	### tcksample

	# create a name for the output file
	outname = tck_file[0].split('.')[0] + '_' + stat[0] + '_stats.txt'
	# path to the output file
	outfile = op.join(MAINPATH, outname)
	tcksample_path = find_program('tcksample')
	tcksample_proc = subprocess.Popen([tcksample_path, tck_file[1], stat[1], outfile, '-stat_tck', 'mean'],
	                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	_, err_tcksample_proc = tcksample_proc.communicate()
	return outfile

def process_tract(stats, plot=True):
	"""
	Processes a single subject from the given path
	:param subject: string, subject identifier
	:param stats: a list of strings, the statistics we are interested in
	:param plot: boolean, should it export plots for the statistics, default is True
	:return: none
	"""

	# initiate a list for files with the mean statistics for all stramlines
	inlist = []

	# create stats with a mean statistic for all streamlines
	for stat in stats:
		inlist.append(create_statfiles([TCK_NAME.split('.')[0], TCK_FILEPATH], [stat, stats[stat]]))

	# initiate a dictionary which will store the files for conversion to pandas
	stat_dict = {}
	# extract means from the output files
	for stat, infile in zip(stats.keys(), inlist):
		stat_dict[stat] = extract_means(infile)

	# gather the data into a single dataframe
	stat_df = pd.DataFrame(stat_dict) # converts to dataframe
	stat_df.reset_index(inplace=True) # gives each streamline a number
	stat_df = stat_df.rename(columns={'index': 'streamline'}) # renames the column to 'streamline'
	stat_df['streamline'] = stat_df['streamline'] + 1 #change convention so streamline numbering starts at 1

	# make a tidy dataframe 'Stats' with the values for all the statistics - not used at the moment, might be used later
	stat_melted = pd.melt(stat_df,
	                      ['streamline'],
	                      var_name='measurement',
	                      value_name='value')

	stats_tidy = stat_melted.sort_values(by=['streamline'], ignore_index=True)

	# Print the output
	for stat in stats:
		print('Stat:', stat,
		      '\n Mean:\t', np.mean(stat_df[stat]),
		      '\n SD:\t', np.std(stat_df[stat]))

	# write the full statistics per streamline and the mean of all streamlines to a .tsv file
	fname = TCK_NAME.split('.')[0] + '_stats_per_streamline.tsv'
	stat_df.to_csv(op.join(MAINPATH, fname), sep='\t', index=False)
	print('Mean statistics file created: ', op.join(MAINPATH, fname))
	# you can also do that for the tidy data
	tidyname = TCK_NAME.split('.')[0] + '_tidy_stats.tsv'
	stats_tidy.to_csv(op.join(MAINPATH, tidyname), sep='\t', index=False)

	# write summary statistics
	summaryname = TCK_NAME.split('.')[0] + '_summary_statistics_out.tsv'
	summaryfile = op.join(MAINPATH, summaryname)

	with open(summaryfile, 'w+') as fp:
		# column names
		fp.write('Stat\tMean\tSD\n')
		# contents
		for stat in stats:
			mean_stat = np.mean(stat_df[stat])
			sd_stat = np.std(stat_df[stat])
			fp.write(stat + '\t' + str(mean_stat) + '\t' + str(sd_stat) + '\n')
		print('Summary statistics file created: ', summaryfile)

	if plot:
		# plot the values and statistics
		for stat in stats:
			sns.set_theme(style="whitegrid")

			pal = 'viridis'
			d = stat_df
			dy = stat_df[stat]

			ax, fig = plt.subplots(figsize=(4, 10))

			# all of the individual values
			ax = sns.stripplot(data=d,
			                   y=dy,
			                   size=10,
			                   alpha=0.25,
			                   # hue = d['streamline'],
			                   palette=pal)
			# mean and SD
			ax = sns.pointplot(data=d,
			                   y=dy,
			                   ci='sd',
			                   scale=1.5,
			                   palette=pal)
			# distribution
			ax = pt.half_violinplot(data=d,
			                        y=dy,
			                        bw=.3,
			                        cut=0.,
			                        alpha=0.4,
			                        scale="area",
			                        width=.3,
			                        inner=None,
			                        linewidth=0,
			                        palette=pal)

			# set axes limit
			plt.ylim(0, 1.1 * max(dy))
			# add a caption
			text = 'Mean ' + stat + ': ' + str(np.mean(dy)) + '\nSD: ' + str(np.std(dy))
			plt.text(-0.4, 0.1 * max(dy), text)
			# make it pretty
			sns.despine()

			# save to a file
			figfile = op.join(MAINPATH, TCK_NAME.split('.')[0] + '_' + stat + '_visuals.png')
			plt.savefig(figfile, dpi=300)
			print('Figure created: ', figfile)

			# don't show the plot
			plt.close()



try:
	process_tract(stats)
except:
	print('That did not work. Try again')
else:
	print('Tract processed successfully.')

#%%
