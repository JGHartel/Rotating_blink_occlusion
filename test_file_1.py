from psychopy import core, visual, event
from psychopy.event import Mouse
import random
import csv

# Initialize window
win = visual.Window([800, 600], color=(1, 1, 1))

# Initialize mouse
mouse = Mouse(win=win)

# Load the .avi video
video_path = './materials/Animation.avi'
video = visual.MovieStim3(win, video_path, size=(800, 600), flipVert=False, flipHoriz=False)

# Create an occluder stimulus
occluder = visual.Rect(win, width=800, height=600, fillColor='black')

# Initial conditions
rotation_speed = 1.0
responses = []

def detect_mouseclick(mouse):
    buttons = mouse.getPressed()
    if any(buttons):
        return True
    return False

def simulate_eyelid_closure(win, duration=0.3, jump_duration=1.0):
    # Simulate eyelid closure by jumping forward or backward in the video
    # collect start time
    start_time = core.getTime()
    #autodraw the occluder
    video.autoDraw = False
    occluder.autoDraw = True
    win.flip()
    core.wait(duration-(core.getTime()-start_time))  # Wait for the duration
    #stop the video
    video.pause()

    video.seek(video.getCurrentFrameTime() + jump_duration)  # Jump forward or backward in the video
    # conitnue the video
    video.play()
    occluder.autoDraw = False
    win.flip()
    video.autoDraw = True
   


def main_experiment(win):
    global rotation_speed
    frame_number = 0
    
    while True:
        # Draw the video frame
        video.draw()
        
        # Check for mouse click to simulate blink
        if detect_mouseclick(mouse):
            action = random.choice(['forward', 'backward'])
            if action == 'forward':
                jump_duration = 0.3  # Jump forward in the video
                simulate_eyelid_closure(win, jump_duration=jump_duration)
                win.flip()
            elif action == 'backward':
                jump_duration = -0.3  # Jump backward in the video
                simulate_eyelid_closure(win, jump_duration=jump_duration)
                win.flip()

        # Flip the window to update the display
        win.flip()
        
        # Collect responses on spacebar press
        if 'space' in event.getKeys():
            responses.append((frame_number, rotation_speed))
        
        # Increment frame number
        frame_number += 1
      
        # End experiment condition (for example, duration or number of frames)
        if frame_number > 10000:  # Adjust this based on your experiment duration
            break

        # smoothly exit
        if event.getKeys(['escape']):
            break

    return responses

# Run the main experiment
responses = main_experiment(win)

# Save responses to CSV
with open('responses.csv', 'w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(['Frame Number', 'Rotation Speed'])
    writer.writerows(responses)

# Clean up
win.close()
core.quit()
