import cv2

def downsample_video(input_path, output_path, scale_factor=0.5, fps=None):
    # Open the original video
    cap = cv2.VideoCapture(input_path)
    
    # Get the original video's width, height, and frame rate
    original_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    original_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    original_fps = cap.get(cv2.CAP_PROP_FPS)
    
    # Calculate the new width and height
    new_width = int(original_width * scale_factor)
    new_height = int(original_height * scale_factor)
    
    # If fps is not specified, use the original fps
    if fps is None:
        fps = original_fps
    
    # Define the codec and create a VideoWriter object
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    out = cv2.VideoWriter(output_path, fourcc, fps, (new_width, new_height))
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        
        # Resize the frame
        frame_resized = cv2.resize(frame, (new_width, new_height), interpolation=cv2.INTER_AREA)
        
        # Write the frame to the new video
        out.write(frame_resized)
    
    # Release the resources
    cap.release()
    out.release()

# Downsample the video
input_video_path = './materials/David.avi'
output_video_path = './materials/David_downsampled.avi'
downsample_video(input_video_path, output_video_path, scale_factor=0.5, fps=30)  # Adjust scale_factor and fps as needed
