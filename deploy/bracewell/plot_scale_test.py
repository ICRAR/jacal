import numpy as np
import matplotlib.pyplot as plt

x = np.arange(1, 6)
x_labels = ['2', '4', '8', '16', '32']
y = [10.31, 24.14, 56.14, 122.26, 251.62]
z = [10.31/32, 24.14/64, 56.14/128, 122.26/256, 251.62/512]
z = [100 * x1 for x1 in z]
y_err = [0.27, 0.10, 8.15, 20.86, 2.64]

fig, ax = plt.subplots()
plt.plot(x, y, label='Throughput', marker='o', markeredgecolor='r', markerfacecolor='orange')
plt.errorbar(x, y, yerr=y_err, fmt='o', markeredgecolor='r', markerfacecolor=None)
plt.xticks(x, x_labels)
#ax.set_xticklabels(x_labels)
ax.grid(True, linestyle='-.', which='major', color='lightgrey',
               alpha=0.9, axis='y')
ax.set_ylabel('Throughput (Gbps)', fontsize=14)
ax.set_xlabel('Number of compute nodes', fontsize=14)

ax1 = ax.twinx()
ax1.set_ylabel('Percentage of the bandwidth', fontsize=14)
ax1.set_ylim([20, 60])
#print(z)
#print(x)
ax1.plot(x, z, color='b', marker='x', label=r'$\frac{throughput}{bandwidth}\times 100$')
ax1.legend(loc='lower right', fontsize=13)
ax.legend(loc='upper left', fontsize=12)

plt.show()
