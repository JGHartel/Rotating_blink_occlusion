#load required libraries
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import curve_fit

#load response data
response_data = pd.read_csv('data/qc/response_data.csv')

#plot video jump over cycke
plt.plot(response_data['video_jump'])

# Overlay the plot with regions corresponding to the response type
for i, row in response_data.iterrows():
    if row['response_type'] == 'correct':
        plt.axvspan(i - 0.5, i + 0.5, color='green', alpha=0.3)
    elif row['response_type'] == 'missed':
        plt.axvspan(i - 0.5, i + 0.5, color='red', alpha=0.3)
    elif row['response_type'] == 'false positive':
        plt.axvspan(i - 0.5, i + 0.5, color='orange', alpha=0.3)
    else:
        plt.axvspan(i - 0.5, i + 0.5, color='blue', alpha=0.3)

# plot the likelihood of correct respons over windows of jump size
# find minimum and maximum jump size
min_jump = response_data['video_jump'].min()
max_jump = response_data['video_jump'].max()

# create bins for jump size
bins = np.linspace(min_jump, max_jump, 10)
print(np.size(bins))

# create a new column in the response data to store the bin
response_data['jump_bin'] = np.digitize(response_data['video_jump'], bins)

# calculate the likelihood of correct response in each bin
likelihood_correct = response_data.groupby('jump_bin')['response_type'].apply(lambda x: x.isin(['correct', 'correct rejection']).sum() / len(x))
#remove the first line from the data

# Sigmoid function
def sigmoid(x, L, k, x0):
    return L / (1 + np.exp(-k * (x - x0)))

# Data for fitting
x_data = np.linspace(min_jump, max_jump, np.size(likelihood_correct))
y_data = np.array(likelihood_correct)

# Perform the sigmoidal fit
popt, pcov = curve_fit(sigmoid, x_data, y_data, p0=[max(y_data), 1, np.median(x_data)])

# Plot the original data
plt.figure()
plt.plot(x_data, y_data, 'b-', label='data')

# Plot the fitted curve
x_fit = np.linspace(0, max(x_data), 600)
y_fit = sigmoid(x_fit, *popt)
plt.plot(x_fit, y_fit, 'r-', label='fit: L=%5.3f, k=%5.3f, $x_0$=%5.3f' % tuple(popt))

plt.legend()
plt.show()
