from psychopy import core, visual, event, gui, data
import random
import pandas as pd
import os

VIDEO_JUMP_START = 0.5
main_start_time = core.getTime()

# Initialize window
win = visual.Window([800, 600], color=(1, 1, 1))

# Initialize mouse
mouse = event.Mouse(win=win)

# Load the .avi video
video_path = './materials/Animation.avi'
video = visual.MovieStim3(win, video_path, size=(800, 600), flipVert=False, flipHoriz=False, loop=True)
#get video frame rate
frame_rate = video.getFPS()

# Create an occluder stimulus
occluder = visual.Rect(win, width=800, height=600, fillColor='black')

# QUEST parameters
quest = data.QuestHandler(startVal=0.3, startValSd=0.2, pThreshold=0.75, gamma=0.5, 
                          nTrials=50, minVal=0.0, maxVal=1.0, beta=3.5, delta=0.1)

def simulate_eyelid_closure(win, duration=0.3, video_jump=1):
    start_time = core.getTime()

    occluder.autoDraw = True
    video.autoDraw = False  
    win.flip()

    video.pause()
    video.seek((video.getCurrentFrameTime() + video_jump) % video.duration)
    video.play()
    occluder.autoDraw = False

    core.wait(core.getTime() + duration - start_time)
    end_time = core.getTime()

    video.autoDraw = True
    win.flip()

    return start_time, end_time

def check_response(cycle_number, space_click_time, occ_end_time, IsJump, IsDetected, response_data):
    if cycle_number > 0:
        global video_jump
        video_jump_old = video_jump

        for value in quest:
            video_jump = value
            break
        
        print(f"Cycle Number: {cycle_number}, Video jump: {video_jump}")

        response_speed = space_click_time - occ_end_time
        if IsJump and IsDetected:
            response_type = 'correct'
            quest.addResponse(1)
        elif IsJump and not IsDetected:
            response_type = 'missed'
            quest.addResponse(0)
        elif not IsJump and IsDetected:
            response_type = 'false positive'
            quest.addResponse(0)
        else:  # not IsJump and not IsDetected
            response_type = 'correct rejection'
            quest.addResponse(1)


        response_data = response_data._append({'time': core.getTime() - main_start_time, 'video_jump': video_jump_old, 'response_speed': response_speed, 'response_type': response_type, 'quest_threshold': quest.mean(), 'quest_sd': quest.sd()}, ignore_index=True)
        

    cycle_number += 1
    return cycle_number, response_data


def main_experiment(win):

    global main_start_time
    main_start_time = core.getTime()

    global cycle_number
    cycle_number = 0

    global video_jump
    video_jump = VIDEO_JUMP_START

    IsJump = False
    IsDetected = False 

    event_data = pd.DataFrame(columns=['event_type', 'time'])
    response_data = pd.DataFrame(columns=['time', 'video_jump', 'response_speed', 'response_type', 'quest_threshold', 'quest_sd'])

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
        #end the main
        return

    global folder_path
    folder_path = os.path.join('data', participant_data['participant_id'])


    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    while True:
        video.draw()

        # On average, blinks occur roughly every 2-10 seconds
        time_since_last_blink = core.getTime() - occ_end_time - main_start_time
        #add a refractory period of 1 second between blink events

        #add a refractory period of 1 second between blink events
        if time_since_last_blink > 2 and random.random() < 1/frame_rate/5:
            #check if there was a response to the previous jump

            cycle_number, response_data = check_response(cycle_number,  space_click_time, occ_end_time, IsJump, IsDetected, response_data)

            #randomly choose whether there is a jump or not
            if random.random() < 0.5:
                IsDetected=False
                IsJump=True
                occ_start_time, occ_end_time= simulate_eyelid_closure(win, video_jump=video_jump)
                occ_start_time -= main_start_time
                occ_end_time -= main_start_time
            else:
                IsDetected=False
                IsJump=False
                occ_start_time, occ_end_time= simulate_eyelid_closure(win, video_jump=0)
                occ_start_time -= main_start_time
                occ_end_time -= main_start_time

            event_data = event_data._append({'event_type': 'blink_start', 'time': occ_start_time}, ignore_index=True)
            event_data = event_data._append({'event_type': 'blink_end', 'time': occ_end_time}, ignore_index=True)

        win.flip()

        keys=event.getKeys()
        
        if 'space' in keys:
            space_click_time = core.getTime() - main_start_time
            if space_click_time - occ_end_time < 2:
                IsDetected = True

        if 'escape' in keys or 'q' in keys:
            print("Escape pressed, exiting...")
            break

        if cycle_number > 50:
            print("Max time reached, exiting...")
            break

    return event_data, response_data, quest

# Run the main experiment
event_data, response_data, quest = main_experiment(win)

# Save data to csv
event_data.to_csv(os.path.join(folder_path, 'event_data.csv'))
response_data.to_csv(os.path.join(folder_path, 'response_data.csv'))

# Save the final threshold estimate
with open(os.path.join(folder_path, 'quest_threshold.txt'), 'w') as f:
    f.write(f"Estimated threshold: {quest.mean()}\n")

# Clean up
win.close()
core.quit()
