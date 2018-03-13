import numpy as np
import matplotlib.pyplot as plt

N = 3
senders_means = (67.042, 342.5339, 680.417)
#sender_std = (2, 3, 4, 1, 2)

ind = np.array([1.2, 6.0, 12.0])#np.arange(N)  # the x locations for the groups
width = 0.45       # the width of the bars

fig, ax = plt.subplots()
rects1 = ax.bar(ind, senders_means, width, color='r')#, yerr=sender_std)
#print(rects1)

ingest_means = (65.642, 340.8659, 679.328)
#ingest_std = (3, 5, 2, 3, 3)
rects2 = ax.bar(ind + width, ingest_means, width, color='y')#, yerr=ingest_std)

sender_means_no_dlg = (70.467, 338.990, 676.056)
rects4 = ax.bar(ind + width * 3, sender_means_no_dlg, width, color='cyan')#, yerr=ingest_std)

sender_means_no_dlg_binary = (71.215, 338.194, 672.861)
rects5 = ax.bar(ind + width * 4, sender_means_no_dlg_binary, width, color='g')

data_vol = (21, 101, 200)

ax1 = ax.twinx()
rects3 = ax1.bar(ind + width * 2, data_vol, width, color='b')
ax1.set_ylabel("Data volume in MB", fontsize=14)
ax1.set_ylim([0, 300])

# add some text for labels, title and axes ticks
ax.set_ylabel('Seconds', fontsize=14)
ax.set_xlabel('Number of simulated time steps', fontsize=14)
ax.set_title('Completition time and data volume per node by Senders and Ingest pipeline or MPI Receiver')
ax.set_xticks(ind + width * 1.5)
ax.set_xticklabels(('   1200', '   6000', '   12000'))
ax.set_ylim([0, 800])

ax.legend((rects1[0], rects2[0], rects4[0], rects5[0]), ('Sender (5 nodes)', 'Ingest (5 nodes)',\
 'Sender (2 nodes) with MPI receiver. No DALiuGE, No dummy flagging', \
 'Sender (1 node) with MPI receiver binary dump'), loc="upper left")
ax1.legend((rects3[0],), ('Data volume',), loc="upper right")

ax.grid(True, linestyle='-.', which='major', color='lightgrey',
               alpha=0.9, axis='y')


def autolabel(rects, x_offset=0, y_offset=1.01):
    """
    Attach a text label above each bar displaying its height
    """
    for rect in rects:
        height = rect.get_height()
        print(rect.get_x())
        ax.text(rect.get_x() + rect.get_width()/2. + x_offset, y_offset * height,
                '%.3f' % height,
                ha='center', va='bottom')

autolabel(rects1, x_offset=-1.5 * width)
autolabel(rects2, x_offset=0.5 * width)
autolabel(rects4, x_offset=width)
autolabel(rects5, x_offset=width * 1.5, y_offset=0.9)
#autolabel(rects3, x_offset=0.5 * width)

plt.show()
