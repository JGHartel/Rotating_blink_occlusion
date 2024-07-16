from psychopy import core, visual, event, gui
from psychopy.event import Mouse
import random
import csv
import pandas as pd
import os

VIDEO_JUMP_START = 0.5
main_start_time = core.getTime()

# Initialize window
win = visual.Window([800, 600], color=(1, 1, 1))

# Initialize mouse
mouse = Mouse(win=win)

# Load the .avi video
video_path = './materials/Animation.avi'
video = visual.MovieStim3(win, video_path, size=(800, 600), flipVert=False, flipHoriz=False, loop=True)
#get video frame rate
frame_rate = video.getFPS()

# Create an occluder stimulus
occluder = visual.Rect(win, width=800, height=600, fillColor='black')

# Initial conditions
initial_jump_duration = VIDEO_JUMP_START
step_size = 0.05
max_trials = 100
reversals = 0
max_reversals = 50
correct_in_a_row = 0
incorrect_in_a_row = 0
pos_reversal_criteria = 2
neg_reversal_criteria = 1

def detect_mouseclick(mouse):
    buttons = mouse.getPressed()
    if any(buttons):
        return True, core.getTime()-main_start_time  # Record the click time
    return False, None  # Return None if no click occurred

def simulate_eyelid_closure(win, duration=0.3, video_jump=1):
    # Simulate eyelid closure by smoothly fading in and out the occluder
    start_time = core.getTime()

    occluder.autoDraw = True
    video.autoDraw = False  
    win.flip()

    video.pause()
    video.seek((video.getCurrentFrameTime() + video_jump) % video.duration) # Jump forward or backward in the video
    video.play()
    occluder.autoDraw = False

    core.wait(core.getTime() + duration - start_time)
    end_time = core.getTime()

    video.autoDraw = True
    win.flip()

    return start_time, end_time

def check_response(cycle_number, video_jump, space_click_time, occ_end_time, IsJump, IsDetected, response_data):
    global reversals
    global correct_in_a_row
    global incorrect_in_a_row
    if cycle_number > 0:
        video_jump_old = video_jump
        response_speed = space_click_time - occ_end_time
        if IsJump and IsDetected:
            response_type = 'correct'
            correct_in_a_row += 1
            incorrect_in_a_row = 0
            if correct_in_a_row >= pos_reversal_criteria:
                reversals += 1
                correct_in_a_row = 0
                video_jump = max(video_jump - step_size, 0)
        elif IsJump and not IsDetected:
            response_speed = None
            response_type = 'missed'
            incorrect_in_a_row += 1
            correct_in_a_row = 0
            if incorrect_in_a_row >= neg_reversal_criteria:
                reversals += 1
                incorrect_in_a_row = 0
                video_jump += step_size
        elif not IsJump and IsDetected:
            response_type = 'false positive'
            correct_in_a_row = 0
            incorrect_in_a_row +=1
            if incorrect_in_a_row >= neg_reversal_criteria:
                reversals += 1
                incorrect_in_a_row = 0
                video_jump += step_size
        else:  # not IsJump and not IsDetected
            response_speed = None
            response_type = 'correct rejection'
            correct_in_a_row +=1
            incorrect_in_a_row = 0
            if correct_in_a_row >= pos_reversal_criteria:
                reversals += 1
                correct_in_a_row = 0
                video_jump = max(video_jump - step_size, 0)

        response_data = response_data._append({'time': core.getTime() - main_start_time, 'video_jump': video_jump_old, 'response_speed': response_speed, 'response_type': response_type}, ignore_index=True)

    cycle_number += 1
    return cycle_number, video_jump, response_data

def main_experiment(win):
    frame_number = 0
    PLAY = True

    global main_start_time
    main_start_time = core.getTime()

    video_jump = initial_jump_duration
    cycle_number = 0

    IsJump = False
    IsDetected = False 

    event_data = pd.DataFrame(columns=['event_type', 'time'])
    response_data = pd.DataFrame(columns=['time', 'video_jump', 'response_speed', 'response_type'])

    space_click_time = main_start_time
    occ_end_time = 0

    # Define the dictionary to store participant data
    participant_data = {'participant_id': ''}

    # Create a dialogue box
    dlg = gui.DlgFromDict(dictionary=participant_data, title="Participant Data")

    # Check if the user pressed OK or Cancel
    if dlg.OK:
        print("Participant Data:", participant_data)
    else:
        print("User cancelled")

    # create a folder with the participant ID and save the data there
    global folder_path
    folder_path = os.path.join('data', participant_data['participant_id'])

    # Check if the folder exists, if not, create it
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    global reversals
    global correct_in_a_row
    global incorrect_in_a_row

    while cycle_number < max_trials and reversals < max_reversals:
        # Draw the video frame
        video.draw()
        
        # On average, blinks occur roughly every 2-10 seconds
        time_since_last_blink = core.getTime() - occ_end_time - main_start_time
        # Add a refractory period of 1 second between blink events
        if time_since_last_blink > 2 and random.random() < 1/frame_rate/5:
            # Check if there was a response to the previous jump
            cycle_number, video_jump, response_data = check_response(cycle_number, video_jump, space_click_time, occ_end_time, IsJump, IsDetected, response_data)

            # Randomly choose whether there is a jump or not
            if random.random() < 0.5:
                IsDetected = False
                IsJump = True
                occ_start_time, occ_end_time = simulate_eyelid_closure(win, video_jump=video_jump)
                occ_start_time -= main_start_time
                occ_end_time -= main_start_time
            else:
                IsDetected = False
                IsJump = False
                occ_start_time, occ_end_time = simulate_eyelid_closure(win, video_jump=0)
                occ_start_time -= main_start_time
                occ_end_time -= main_start_time

            event_data = event_data._append({'event_type': 'blink_start', 'time': occ_start_time}, ignore_index=True)
            event_data = event_data._append({'event_type': 'blink_end', 'time': occ_end_time}, ignore_index=True)

        win.flip()
        
        # Collect responses on spacebar press
        if 'space' in event.getKeys():
            space_click_time = core.getTime() - main_start_time
            # Check whether there has been a jump
            if space_click_time - occ_end_time < 2:
                IsDetected = True

        # Increment frame number
        frame_number += 1
            
        # Exit after 1 minute
        if core.getTime() - main_start_time > 180:
            print("Max time reached, exiting...")
            break

    return event_data, response_data

# Run the main experiment
event_data, response_data = main_experiment(win)

# Save data to csv
event_data.to_csv(os.path.join(folder_path, 'event_data.csv'))
response_data.to_csv(os.path.join(folder_path, 'response_data.csv'))

# Clean up
win.close()
core.quit()
