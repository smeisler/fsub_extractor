#####################################################################################
#                                                                                   #
#             Bundle stats                                                          #
#   A part of ex-tract, a package for functionally defined white matter tracts      #
#   This module extracts average statistics (e.g. FA, MD) from the segmented        #
#   white matter streamlines.                                                       #
#                                                                                   #
#   Author: Alicja Olszewska, Laboratory of Brain Imaging,                          #
#           Nencki Institute of Experimental Biology                                #
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

# calling the mrtrix processes
import subprocess

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


# path where all subjects live
path_allsub = '/Users/alicja/Documents/Neurohackademy22/fsub'

# get address to statfiles and couple them with statnames
statfiles = ['/Users/alicja/Documents/Neurohackademy22/fsub/subj01/fa.nii.gz',
             '/Users/alicja/Documents/Neurohackademy22/fsub/subj01/md.nii.gz',
             '/Users/alicja/Documents/Neurohackademy22/fsub/subj01/rd.nii.gz']
statnames = ['fa', 'md', 'rd']
stats = dict(zip(statnames, statfiles))
# [TODO] make it into arguments

# convention for the name of the tck files -> output of the segmentation from the ex-tract
TCK_NAME = 'extracted'  # [TODO] check with convention

# get all subjects
subjects = [f.name for f in os.scandir(path_allsub) if f.is_dir() and 'sub' in f.name]


def find_program(program):
	# this will be later imported from the main part of the package

	def is_exe(fpath):
		return op.exists(fpath) and os.access(fpath, os.X_OK)

	for path in os.environ["PATH"].split(os.pathsep):
		path = path.strip('"')
		exe_file = op.join(path, program)
		if is_exe(exe_file):
			return program
	return None


def extract_means(filename):
	"""
	Reads the tcksample output to get tract statistics
	:param filename: a path with the filename to the file containing the values, output of the tcksample command
	:return: a list with the values in floating point format
	"""
	with open(filename) as f:
		return [float(val) for val in f.read().splitlines()[1].split(' ')]


def create_statfiles(sub, tck_file, stat):
	"""
	Takes a bundle file and extracts statistics from relevant streamlines
	:param sub: subject identifier
	:param tck_file: a list (string, string), name[0] and path[1] of the segmented streamlines file
	:param stat: a list (string, string), the name[0] and path[1] of statistics we are interested in
	:return: name of the file which is created
	"""
	# Run MRtrix CLI
	### tcksample

	# create a name for the output file
	outname = tck_file[0].split('.')[0] + '_' + stat[0] + '_stats.txt'
	# path to the output file
	outfile = op.join(path_allsub, sub, outname)
	tcksample_path = find_program('tcksample')
	tcksample_proc = subprocess.Popen([tcksample_path, tck_file[1], stat[1], outfile, '-stat_tck', 'mean'],
	                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	_, err_tcksample_proc = tcksample_proc.communicate()
	return outfile

def process_subject(subject, stats, plot=True):
	"""
	Processes a single subject from the given path
	:param subject: string, subject identifier
	:param stats: a list of strings, the statistics we are interested in
	:param plot: boolean, should it export plots for the statistics, default is True
	:return: none
	"""

	subj_path = op.join(path_allsub, subject)  # path to subject

	# paths to the files containing extracted tracks
	tck_files = [[f.name, f.path] for f in os.scandir(subj_path) if f.is_file() if TCK_NAME in f.name and '.tck' in f.name]
	print(tck_files)
	# initiate a list for files with the mean statistics for all stramlines
	inlist = []

	# create stats with a mean statistic for all streamlines
	for tck_file in tck_files:
		for stat in stats:
			inlist.append(create_statfiles(subject, [tck_file[0].split('.')[0], tck_file[1]], [stat, stats[stat]]))

	print(inlist)

		# initiate a dictionary which will store the files for conversion to pandas
		stat_dict = {}
		# extract means from the output files
		for stat, infile in zip(stats.keys(), inlist):
			print(stat, infile)
			stat_dict[stat] = extract_means(infile)

		# gather the data into a single dataframe
		stat_df = pd.DataFrame(stat_dict)
		stat_df.reset_index(inplace=True)
		stat_df = stat_df.rename(columns={'index': 'streamline'})
		stat_df['streamline'] = stat_df['streamline'] + 1

		# make a tidy dataframe 'Stats' with the values for all the statistics - not used at the moment, might be used later
		stat_melted = pd.melt(stat_df,
		                      ['streamline'],
		                      var_name='measurement',
		                      value_name='value')

		stats_tidy = stat_melted.sort_values(by=['streamline'], ignore_index=True)

		# #Just checking
		# print('FA Mean:\t', np.mean(stat_df['FA']), '\nFA SD:\t\t', np.std(stat_df['FA']))
		# print('MD Mean:\t', np.mean(stat_df['MD']), '\nMD SD:\t\t', np.std(stat_df['MD']))
		# print('RD Mean:\t', np.mean(stat_df['RD']), '\nMD SD:\t\t', np.std(stat_df['RD']))

		# write the full statistics per streamline and the mean of all streamlines to a .tsv file
		stat_df.to_csv(op.join(path_allsub, subject, tck_file[0].split('.')[0] + '_stats_per_streamline.tsv'), sep='\t', index=False)
		# you can also do that for the tidy data
		stats_tidy.to_csv(op.join(path_allsub, subject, tck_file[0].split('.')[0] + '_tidy_stats.tsv'), sep='\t', index=False)

		# write summary statistics
		summaryfile = op.join(path_allsub, subject, tck_file[0].split('.')[0] + '_summary_statistics_out.tsv')
		with open(summaryfile, 'w+') as fp:
			# column names
			fp.write('Stat\tMean\tSD\n')
			# contents
			for stat in stats:
				print(stat)
				mean_stat = np.mean(stat_df[stat])
				sd_stat = np.std(stat_df[stat])
				fp.write(stat + '\t' + str(mean_stat) + '\t' + str(sd_stat) + '\n')

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
				figfile = op.join(path_allsub, subject, subject + '_' + tck_file[0].split('.')[0] + '_' + stat + '_visuals.png')
				plt.savefig(figfile, dpi=300)

				# don't show the plot
				plt.close()


for sub in subjects:
	process_subject(sub, stats)

#%%
