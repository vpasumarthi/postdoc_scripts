import numpy as np
import os
import matplotlib.pyplot as plt
from ase.io import read, write

def compute_distance(coord1, coord2, lattice):
    diff = np.dot(lattice, coord1 - coord2)
    return np.linalg.norm(diff)

def calculate_atom_distances(trajectory, atom1_index, atom2_index):
    """
    Calculate distances between two specified atoms across all frames in a trajectory.

    Parameters:
    trajectory (list): List of atomic configurations.
    atom1_index (int): Index of the first atom.
    atom2_index (int): Index of the second atom.
    """        
    return [frame.get_distance(atom1_index, atom2_index, mic=True) for frame in trajectory]

def find_frames_within_distance_range(trajectory, atom1_index, atom2_index, target_length, tolerance):
    """
    Find frames with bond length between two specified atoms within the specified range.

    Parameters:
    trajectory (list): List of atomic configurations.
    atom1_index (int): Index of the first atom.
    atom2_index (int): Index of the second atom.
    target_distance (float): Target bond length between the two atoms.
    tolerance (float): Tolerance for matching the bond lengths.
    """
    close_frames = [i for i, frame in enumerate(trajectory) 
                    if abs(frame.get_distance(atom1_index, atom2_index, mic=True) - target_length) < tolerance]
    return close_frames

def find_target_frames_between_two_atoms(trajectory, target_bond_lengths, atom1_index, atom2_index, initial_tolerance, secondary_tolerance):
    """
    Find frames where the bond length between the pair of atoms is within the specified range.

    Parameters:
    trajectory (list): List of atomic configurations.
    target_bond_lengths (list): Target bond lengths between the first pair of atoms to match.
    atom1_index (int): Index of the first atom.
    atom2_index (int): Index of the second atom.
    initial_tolerance (float): Initial tolerance for matching the bond lengths.
    secondary_tolerance (float): Secondary tolerance for matching the bond lengths.
    """
    target_frames = []
    for target_length in target_bond_lengths:
        frames_within_range = find_frames_within_distance_range(trajectory, atom1_index, atom2_index, target_length, initial_tolerance)

        # If no frame is found with initial tolerance, try with secondary tolerance
        if not frames_within_range:
            frames_within_range = find_frames_within_distance_range(trajectory, atom1_index, atom2_index, target_length, secondary_tolerance)

        if frames_within_range:
            frame_with_min_bond = frames_within_range[np.argmin([trajectory[i].get_distance(atom1_index, atom2_index, mic=True) for i in frames_within_range])]
            bond_distance = trajectory[frame_with_min_bond].get_distance(atom1_index, atom2_index, mic=True)
            target_frames.append((frame_with_min_bond, bond_distance))
        else:
            print(f"No frame found for target bond length: {target_length:.2f} Å.")

    return target_frames

def find_target_frames_with_third_atom(trajectory, target_bond_lengths, atom1_index, atom2_index, atom3_index, initial_tolerance, secondary_tolerance):
    """
    Find frames where the bond length between the first pair of atoms is within the specified range and has minimum bond length with a third atom.

    Parameters:
    trajectory (list): List of atomic configurations.
    target_bond_lengths (list): Target bond lengths between the first pair of atoms to match.
    atom1_index (int): Index of the first atom in the primary bond.
    atom2_index (int): Index of the second atom in the primary bond.
    atom3_index (int): Index of the third atom to compare with the first atom.
    initial_tolerance (float): Initial tolerance for matching the primary bond lengths.
    secondary_tolerance (float): Secondary tolerance for matching the primary bond lengths.
    """
    target_frames = []
    for target_length in target_bond_lengths:
        frames_within_range = find_frames_within_distance_range(trajectory, atom1_index, atom2_index, target_length, initial_tolerance)

        # If no frame is found with initial tolerance, try with secondary tolerance
        if not frames_within_range:
            frames_within_range = find_frames_within_distance_range(trajectory, atom1_index, atom2_index, target_length, secondary_tolerance)

        if frames_within_range:
            frame_with_min_bond = frames_within_range[np.argmin([trajectory[i].get_distance(atom1_index, atom3_index, mic=True) for i in frames_within_range])]
            primary_bond_distance = trajectory[frame_with_min_bond].get_distance(atom1_index, atom2_index, mic=True)
            target_frames.append((frame_with_min_bond, primary_bond_distance))
        else:
            print(f"No frame found for target bond length: {target_length:.2f} Å.")

    return target_frames

def create_poscar_directories(trajectory, frame_data, base_dir):
    """
    Create directories and write POSCAR files for specified frames.

    Parameters:
    trajectory (list): List of atomic configurations.
    frame_data (list of tuples): Tuples of frame indices and corresponding C-H bond lengths.
    base_dir (str): Base directory to create frame directories.
    """
    for frame_index, bond_length in frame_data:
        rounded_bond_length = np.round(bond_length, 2)  # Round the bond length to 2 decimal places
        dir_name = os.path.join(base_dir, f"{rounded_bond_length:.2f}_{frame_index}")
        os.makedirs(dir_name, exist_ok=True)
        write(f'{dir_name}/POSCAR', trajectory[frame_index], format='vasp')  # Use ASE to write the POSCAR file

def plot_atom_distances(trajectory, atom1_index, atom2_index, figname='atom_distance_plot.png', show_plot=True):
    """
    Plot and optionally save the bond distance between two specified atoms against the frame index.

    Parameters:
    trajectory (list): List of atomic configurations.
    atom1_index (int): Index of the first atom.
    atom2_index (int): Index of the second atom.
    figname (str): The filename to save the plot.
    show_plot (bool): If True, display the plot; if False, don't display.
    """
    # Calculate C-H distances
    atom_distances = calculate_atom_distances(trajectory, atom1_index, atom2_index)

    # Extract frame indices
    frame_indices = np.arange(len(atom_distances))

    # Plotting
    plt.plot(frame_indices, atom_distances, marker='o', linestyle='-')
    plt.xlabel('Frame Index')
    plt.ylabel('Distance (Å)')
    plt.title('Distance between atoms vs Frame Index')
    plt.grid(True)

    # Saving the plot
    plt.savefig(figname)

    # Displaying the plot
    if show_plot:
        plt.show()

    # Close the plot to free up memory
    plt.close()

def main():
    # Specified inputs
    C_index, H_index, Pt_index = 2, 35, 116
    C_H_start = 0.70  # Start distance for C-H
    C_H_end = 1.70  # End distance for C-H
    num_images = 21  # Number of target images
    initial_tolerance = 0.01  # Initial Tolerance level
    # Secondary tolerance level to use if no frame is found within the initial tolerance
    secondary_tolerance = 0.02

    # Read trajectory
    trajectory = read("XDATCAR", index=':', format='vasp-xdatcar')

    # Find target frames
    C_H_targets = np.linspace(C_H_start, C_H_end, num_images, endpoint=True)
    target_frames = find_target_frames_with_third_atom(trajectory, C_H_targets, C_index, H_index, Pt_index, initial_tolerance, secondary_tolerance)

    # Create directories and write POSCAR
    create_poscar_directories(trajectory, target_frames, os.getcwd())

    # Plot distances
    plot_atom_distances(trajectory, C_index, H_index, figname='C-H_distance_plot.png', show_plot=False)

if __name__ == "__main__":
    main()

