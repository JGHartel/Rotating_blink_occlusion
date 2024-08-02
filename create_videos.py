import cv2
import os
import re
import numpy as np

# Path to the directory containing the images
image_folder = 'materials/renders/woman_1'

# Output video file name
video_name = 'materials/woman_1.mp4'

# Target frame rate
original_fps = 30
target_fps = 60

# Function to extract the number from the filename
def extract_number(filename):
    match = re.search(r'(\d+)', filename)
    return int(match.group(1)) if match else 0

# Get a list of all image files in the directory
images = [img for img in os.listdir(image_folder)]
# Sort the images numerically based on the number in the filename
images.sort(key=extract_number)

# Debugging: Print the list of images found
print(f"Images found: {images}")

# Ensure there are images to process
if not images:
    raise ValueError("No images found in the specified directory.")

# Skip the first image
images = images[1:-1]

# Read the first image to get the width and height
first_image_path = os.path.join(image_folder, images[0])
frame = cv2.imread(first_image_path)
height, width, layers = frame.shape

# Define the codec and create a VideoWriter object
fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # Using 'mp4v' for MP4
video = cv2.VideoWriter(video_name, fourcc, target_fps, (width, height))

def interpolate_frames(frame1, frame2, steps):
    """Generate intermediate frames between frame1 and frame2."""
    interpolated_frames = []
    for i in range(1, steps):
        alpha = i / steps
        inter_frame = cv2.addWeighted(frame1, 1 - alpha, frame2, alpha, 0)
        interpolated_frames.append(inter_frame)
    return interpolated_frames

# Iterate through the images and write them to the video
for i in range(len(images) - 1):
    img1_path = os.path.join(image_folder, images[i])
    img2_path = os.path.join(image_folder, images[i + 1])
    frame1 = cv2.imread(img1_path)
    frame2 = cv2.imread(img2_path)
    
    video.write(frame1)
    
    # Calculate the number of intermediate frames
    num_inter_frames = int((target_fps / original_fps) - 1)
    
    # Generate and write intermediate frames
    interpolated_frames = interpolate_frames(frame1, frame2, num_inter_frames + 1)
    for inter_frame in interpolated_frames:
        video.write(inter_frame)

# Write the last frame
last_frame_path = os.path.join(image_folder, images[-1])
last_frame = cv2.imread(last_frame_path)
video.write(last_frame)

# Generate and write intermediate frames between the last and the first frame for looping
first_frame = cv2.imread(first_image_path)
interpolated_frames = interpolate_frames(last_frame, first_frame, num_inter_frames + 1)
for inter_frame in interpolated_frames:
    video.write(inter_frame)

# Release the VideoWriter object
video.release()

print(f"Video {video_name} created successfully.")