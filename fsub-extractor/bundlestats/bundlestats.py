import numpy as np
import pandas as pd
import os
import os.path as op

import matplotlib.pyplot as plt
import seaborn as sns
import ptitprince as pt

stats_list = ['FA', 'MD', 'RD']  # this should be an input argument
TCK_NAME = 'extracted'  # check with convention
# path where all subjects live
path_allsub = '/Users/alicja/Documents/Neurohackademy22/fsub'
# get all subjects
subjects = [f.name for f in os.scandir(path_allsub) if f.is_dir() and 'sub' in f.name]

tck_files = [f.path for f in os.scandir(op.join(path_allsub, subjects[0])) if f.is_file() if TCK_NAME in f.name]

fls = [f.path for f in os.scandir(op.join(path_allsub, subjects[0])) if f.is_file() if 'stats.txt' in f.name]


def extract_means(filename):
	"""
	Reads the tcksample output to get tract statistics
	:param filename: a path with the filename to the file containing the values, output of the tcksample command
	:return: a list with the values in floating point values
	"""
	with open(filename) as f:
		return [float(val) for val in f.read().splitlines()[1].split(' ')]


def proces_subject(sub, stats, plot=True):
	"""
	processes a single subject from the given path
	:param sub: string, subject name; a string
	:param stats: a list of strings, the statistics we are interested in
	:param plot: boolean, should it export plots for the statistics, default is True
	:return: none
	"""
	path = '/Users/alicja/Documents/Neurohackademy22/fsub/subj01/'  # path to subject
	inlist = []

	# [TODO] generate the statistic files with mrtrix commandline "tcksample" command

	# directory to the file containing statistics per streamline in the segmented data
	for stat in stats:
		inlist.append(op.join(path, stat))

	stat_dict = {}

	for stat, infile in zip(stats, inlist):
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

	stats_tidy = Stat_melted.sort_values(by=['streamline'], ignore_index=True)

	# #Just checking
	# print('FA Mean:\t', np.mean(stat_df['FA']), '\nFA SD:\t\t', np.std(stat_df['FA']))
	# print('MD Mean:\t', np.mean(stat_df['MD']), '\nMD SD:\t\t', np.std(stat_df['MD']))
	# print('RD Mean:\t', np.mean(stat_df['RD']), '\nMD SD:\t\t', np.std(stat_df['RD']))

	# write the full statistics per streamline and the mean of all streamlines to a .tsv file
	stat_df.to_csv('Stats_per_streamline.tsv', sep='\t', index=False)
	# you can also do that for the tidy data
	# Stats_tidy.to_csv('Tidy_stats.tsv', sep = '\t', index = False)

	# write summary statistics
	with open(r'Summary_statistics_out.tsv', 'w') as fp:
		# column names
		fp.write('Stat\tMean\tSD\n')
		# contents
		for stat in stats:
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
			# distriibution
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

			# don't show the plot
			plt.close()
			# save to a file
			plt.savefig(op.join(path, sub, stat + '_visuals.png'), dpi=300)


for subject in subjects:
	proces_subject(subject)
