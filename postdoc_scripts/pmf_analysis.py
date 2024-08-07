import os
import glob
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
from scipy.integrate import trapz

# Define font sizes and tick parameters as constants
LABEL_FONTSIZE = 18
TITLE_FONTSIZE = 22
TICK_LABELSIZE = 14
LEGEND_FONTSIZE = 14
TICK_LENGTH_MAJOR = 8
TICK_WIDTH_MAJOR = 1

# This function reads the force_stats_report.txt and extracts the values
def read_force_stats(file_path, target_steps=None):
    with open(file_path, 'r') as file:
        lines = file.readlines()
        stats = {}
        
        # Parse initial values
        if len(lines) > 2:
            stats['CV'] = float(lines[1].split(':')[1].strip())
            if target_steps is None:
                stats['Mean Force'] = -1 * np.around(float(lines[2].split(':')[1].strip()), 2)
                stats['Standard Deviation'] = float(lines[3].split(':')[1].strip())
                stats['MD steps'] = int(lines[4].split(':')[1].strip())

            # Parse cumulative analysis results
            for line in lines[6:]:  # Assuming the Cumulative Analysis starts at line 7
                parts = line.split()
                if len(parts) == 3 and int(parts[0]) == target_steps:
                    stats['Mean Force'] = -1 * float(parts[1])
                    stats['Standard Deviation'] = float(parts[2])
                    stats['MD steps'] = target_steps

        return stats

# Calculate areas for the mean, upper, and lower force curves
def calculate_area(x, y):
    zero_crossings = np.where(np.diff(np.sign(y)))[0]
    roots = []

    def interpolate_zero_crossing(x1, y1, x2, y2):
        return x1 - y1 * (x2 - x1) / (y2 - y1)

    if len(zero_crossings) < 2:
        # Fit a second-order polynomial if not enough zero crossings are found
        coeffs = np.polyfit(x, y, 2)
        p = np.poly1d(coeffs)
        roots = np.roots(p).real
        roots.sort()
        if len(roots) >= 2:
            zero_crossings = roots[:2]
            x_integration = np.linspace(min(zero_crossings), max(zero_crossings), num=500)
            y_integration = p(x_integration)
            idx_start = np.argmin(np.abs(x_integration - zero_crossings[0]))
            idx_end = np.argmin(np.abs(x_integration - zero_crossings[1]))
            area = abs(trapz(y_integration[idx_start:idx_end + 1], x_integration[idx_start:idx_end + 1]))
            return area, roots

    if len(zero_crossings) >= 2:
        zero_crossings.sort()
        start, end = zero_crossings[0], zero_crossings[1]
        roots = [
            interpolate_zero_crossing(x[start], y[start], x[start+1], y[start+1]),
            interpolate_zero_crossing(x[end], y[end], x[end+1], y[end+1])
        ]
        start_idx = np.argmin(np.abs(x - roots[0]))
        end_idx = np.argmin(np.abs(x - roots[1]))
        area = abs(trapz(y[start_idx:end_idx + 1], x[start_idx:end_idx + 1]))
        return area, roots

    return None, roots

# for target_steps in np.arange(500, 10500, 500):
for target_steps in [None]:
    # This dictionary will hold our data
    data = {'Constrained_Bond_Length (Å)' : [], 'Mean_Force (eV/Å)' : [], 'Standard_Deviation (eV/Å)' : [], 'MD_Steps': []}

    # Assuming your directories are named in the '1.06_793' format and are in the current working directory
    for folder in glob.glob("[0-9].[0-9][0-9]_*"):
        file_path = os.path.join(folder, 'force_stats_report.txt')
        if os.path.isfile(file_path):
            stats = read_force_stats(file_path, target_steps=target_steps)
            data['Constrained_Bond_Length (Å)' ].append(stats['CV'])
            data['Mean_Force (eV/Å)' ].append(stats['Mean Force'])
            data['Standard_Deviation (eV/Å)' ].append(stats['Standard Deviation'])
            data['MD_Steps'].append(stats['MD steps'])

    # Create a DataFrame from the data
    df = pd.DataFrame(data)

    # Sort the DataFrame based on the constrained bond length
    df = df.sort_values(by=['Constrained_Bond_Length (Å)' ])

    # Assuming 'df' is the DataFrame with your data sorted by 'Constrained_Bond_Length (Å)' 
    x = df['Constrained_Bond_Length (Å)' ].to_numpy()
    y = df['Mean_Force (eV/Å)' ].to_numpy()
    std_dev = df['Standard_Deviation (eV/Å)' ].to_numpy()

    # Calculate the standard areas and the areas with error adjustments
    activation_barrier, roots = calculate_area(x, y)
    area_upper, _ = calculate_area(x, y + std_dev)
    area_lower, _ = calculate_area(x, y - std_dev)

    # Calculate the uncertainty as half the difference between the upper and lower areas
    if area_upper is not None and area_lower is not None:
        # Calculate activation barrier error as half the absolute difference between upper and lower area estimates.
        activation_barrier_error = np.abs(area_upper - area_lower) / 2
        results_string = f"Activation Barrier (Area under the curve): {activation_barrier:.2f} ± {activation_barrier_error:.2f} eV\n"
    else:
        results_string = "Not enough zero crossings found to compute the area and its error."
    
    # Add roots information to the results string
    if len(roots) >= 2:
        results_string += f"Equilibrium Bond Distances: Initial State = {roots[0]:.3f} Å, Transition State = {roots[1]:.3f} Å\n"

# Print data in a table format and save it to a text file
table_string = df.to_string(index=False)
print(table_string + '\n')
print(results_string)
with open("pmf_analysis_results.txt", "w") as text_file:
    text_file.write(table_string + '\n\n')
    text_file.write(results_string + '\n')

# Plotting
plt.figure(figsize=(10, 6))
ax = plt.gca()
plt.errorbar(df['Constrained_Bond_Length (Å)' ], df['Mean_Force (eV/Å)' ], yerr=df['Standard_Deviation (eV/Å)' ], fmt='o', color='black', ecolor='black', capsize=3.5)
# plt.plot(df['Constrained_Bond_Length (Å)' ], df['Mean_Force (eV/Å)' ] + df['Standard_Deviation (eV/Å)' ], linestyle='--', color='black', alpha=0.5)
# plt.plot(df['Constrained_Bond_Length (Å)' ], df['Mean_Force (eV/Å)' ] - df['Standard_Deviation (eV/Å)' ], linestyle='--', color='black', alpha=0.5)

# Create a polygon to fill the area under the curve
verts = [(df['Constrained_Bond_Length (Å)' ].iloc[0], 0)] + list(zip(df['Constrained_Bond_Length (Å)' ], df['Mean_Force (eV/Å)' ])) + [(df['Constrained_Bond_Length (Å)' ].iloc[-1], 0)]
poly = Polygon(verts, facecolor='0.9', edgecolor='0.1')
ax.add_patch(poly)

plt.title('Mean Force vs. Constrained Bond Length', fontsize=TITLE_FONTSIZE)
plt.xlabel('Constrained Bond Length (Å)', fontsize=LABEL_FONTSIZE)
plt.ylabel('Mean Force (eV/Å)', fontsize=LABEL_FONTSIZE)
plt.tick_params(axis='both', which='major', labelsize=TICK_LABELSIZE, length=TICK_LENGTH_MAJOR, width=TICK_WIDTH_MAJOR)
plt.savefig('mean_force_plot.png', dpi=300, bbox_inches='tight')
