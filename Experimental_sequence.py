from psychopy import core, visual, event, gui, data
import random
import pandas as pd
import os
import numpy as np
from scipy.stats import norm
from matplotlib import pyplot as plt


def occluder_jump(win, duration=0.3, video_jump=1):
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

def blink_jump(win, duration=0.3, video_jump=1):
    start_time = core.getTime()

    video.pause()
    video.seek((video.getCurrentFrameTime() + video_jump) % video.duration)
    video.play()

    core.wait(core.getTime() + duration - start_time)
    end_time = core.getTime()
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

def blink_condition(win):
    event_data = pd.DataFrame(columns=['event_type', 'time'])
    response_data = pd.DataFrame(columns=['time', 'video_jump', 'response_speed', 'response_type', 'quest_threshold', 'quest_sd'])

    occ_end_time = 0

    blink_durations = []
    cycle_number = 0
    space_click_time = 0
    IsJump = False
    IsDetected = False

    global video
    video.autoDraw = True
    video.play()

    Blinking = False

    global video_jump
    video_jump = VIDEO_JUMP_START

    condition_start_time = core.getTime()
    event_data = event_data._append({'event_type': 'condition_start', 'time': condition_start_time-main_start_time}, ignore_index=True)

    while True:
        # use holds of 
        
        
        keys= event.getKeys()

        if 'b' in keys:

            if Blinking == False:
                blink_start = core.getTime()
                Blinking = True

                # draw a "blink" text in the top left corner
                blink_text = visual.TextStim(win, text='BLINK', pos=(-0.9, 0.9))
                blink_text.draw()
                blink_text.autoDraw = True

                # randomly choose if there is a blink or not
                if random.random() < 0.5:
                    IsDetected=False
                    IsJump=True
                    occ_start_time, occ_end_time= blink_jump(win, video_jump=video_jump)

                else:
                    IsDetected=False
                    IsJump=False
                    occ_start_time, occ_end_time= blink_jump(win, video_jump=0)

                #append occlusion on and offset to the event data
                event_data = event_data._append({'event_type': 'occlusion_start', 'time': occ_start_time - main_start_time}, ignore_index=True)
                event_data = event_data._append({'event_type': 'occlusion_end', 'time': occ_end_time - main_start_time }, ignore_index=True)
                event_data = event_data._append({'event_type': 'blink_start', 'time': blink_start - main_start_time}, ignore_index=True)

            elif Blinking == True:
                blink_end = core.getTime()
                Blinking = False

                event_data = event_data._append({'event_type': 'blink_end', 'time': blink_end - main_start_time}, ignore_index=True)
                blink_durations.append(blink_end - blink_start)

                blink_text.autoDraw = False

                cycle_number, response_data = check_response(cycle_number,  space_click_time, occ_end_time, IsJump, IsDetected, response_data)
            
            else:
                #do nothing
                pass

        win.flip()

        if 'space' in keys and cycle_number > 0:
            space_click_time = core.getTime() - main_start_time
            if space_click_time - occ_end_time < 2:
                IsDetected = True

        if 'escape' in keys or 'q' in keys or cycle_number >= MAX_CYCLES:
            break

    return event_data, response_data, blink_durations

def random_replay_condition(win, blink_data):
    event_data = pd.DataFrame(columns=['event_type', 'time'])
    response_data = pd.DataFrame(columns=['time', 'video_jump', 'response_speed', 'response_type', 'quest_threshold', 'quest_sd'])

    #pick blink start and end from the data
    blink_start = blink_data[blink_data['event_type'] == 'blink_start']['time']
    blink_end = blink_data[blink_data['event_type'] == 'blink_end']['time']

    #transorm the data to a numpy array
    blink_start = np.array(blink_start)
    blink_end = np.array(blink_end)

    #calculate the duration of each blink
    blink_durations = blink_end - blink_start

    #calculate the distance between each blink
    blink_distance = blink_start[1:] - blink_end[:-1]

    space_click_time = 0
    occ_end_time = 0
    
    # Fit a Gaussian distribution to previous blink durations
    dur_mu, dur_std = norm.fit(blink_durations)
    dis_mu, dis_std = norm.fit(blink_distance)

    # Optionally, you can use mu and std for further analysis or generation of durations
    # For example, generating a new set of durations from the fitted Gaussian:
    # new_durations = np.random.normal(mu, std, size=len(blink_durations))

    IsJump = False
    IsDetected = False
    cycle_number = 0

    global video
    video.autoDraw = True
    video.play()

    # sample an initial duration and distance from the Gaussian distribution
    duration = np.random.normal(dur_mu, dur_std)
    distance = np.random.normal(dis_mu, dis_std)

    condition_start_time = core.getTime()
    event_data = event_data._append({'event_type': 'condition_start', 'time': condition_start_time-main_start_time}, ignore_index=True)

    while True:
        video.draw()

        time_since_last_blink = core.getTime() - occ_end_time

        if time_since_last_blink > distance:
            
            cycle_number, response_data = check_response(cycle_number, space_click_time, occ_end_time, IsJump, IsDetected, response_data)

            #randomly choose whether there is a jump or not
            if random.random() < 0.5:
                IsDetected=False
                IsJump=True
                occ_start_time, occ_end_time= occluder_jump(win, video_jump=video_jump, duration=duration)

            else:
                IsDetected=False
                IsJump=False
                occ_start_time, occ_end_time= occluder_jump(win, video_jump=0, duration=duration)

            event_data = event_data._append({'event_type': 'occluder_start', 'time': occ_start_time - main_start_time}, ignore_index=True)
            event_data = event_data._append({'event_type': 'occluder_end', 'time': occ_end_time - main_start_time}, ignore_index=True)

            duration = np.random.normal(dur_mu, dur_std)
            distance = np.random.normal(dis_mu, dis_std)

        win.flip()
        keys=event.getKeys()

        if 'space' in keys:
            space_click_time = core.getTime() - main_start_time
            if space_click_time - occ_end_time < 2:
                IsDetected = True

        if 'escape' in keys or 'q' in keys:
            break
        if cycle_number >= np.size(blink_durations):
            break

    return event_data, response_data    

def true_replay_condition(win, blink_data):

    event_data = pd.DataFrame(columns=['event_type', 'time'])
    response_data = pd.DataFrame(columns=['time', 'video_jump', 'response_speed', 'response_type', 'quest_threshold', 'quest_sd'])

    #pick blink start and end from the data
    blink_start = blink_data[blink_data['event_type'] == 'blink_start']['time']
    blink_end = blink_data[blink_data['event_type'] == 'blink_end']['time']
    #get condition start time
    condition_start_time = blink_data[blink_data['event_type'] == 'condition_start']['time'].values[0]

    #transorm the data to a numpy array
    blink_start = np.array(blink_start)-condition_start_time
    blink_end = np.array(blink_end)-condition_start_time

    #calculate the duration of each blink
    blink_durations = blink_end - blink_start

    space_click_time = 0
    occ_end_time = 0

    IsJump = False
    IsDetected = False
    cycle_number = 0

    video.autoDraw = True
    video.play()
     
    condition_start_time = core.getTime()
    event_data = event_data._append({'event_type': 'condition_start', 'time': condition_start_time-main_start_time}, ignore_index=True)

    Blinked = False
    #add a refractory period of 1 second between blink events
    while True:
        video.draw()

        if core.getTime() - condition_start_time > blink_start[cycle_number] and not Blinked:
            Blinked = True
            cycle_number, response_data = check_response(cycle_number, space_click_time, occ_end_time, IsJump, IsDetected, response_data)

            #randomly choose whether there is a jump or not
            if random.random() < 0.5:
                IsDetected=False
                IsJump=True
                occ_start_time, occ_end_time= occluder_jump(win, video_jump=video_jump, duration=blink_durations[cycle_number-1])

            else:
                IsDetected=False
                IsJump=False
                occ_start_time, occ_end_time= occluder_jump(win, video_jump=0)


            event_data = event_data._append({'event_type': 'occluder_start', 'time': occ_start_time - main_start_time}, ignore_index=True)
            event_data = event_data._append({'event_type': 'occluder_end', 'time': occ_end_time - main_start_time}, ignore_index=True)

        elif core.getTime()- condition_start_time > blink_end[cycle_number] and Blinked:
            Blinked = False

        win.flip()
        keys=event.getKeys()

        if 'space' in keys and cycle_number > 1:
            space_click_time = core.getTime() - main_start_time
            if space_click_time - occ_end_time < 2:
                IsDetected = True

        if 'escape' in keys or 'q' in keys:
            break
        if cycle_number > np.size(blink_durations-1) or cycle_number > MAX_CYCLES-1:
            break

    return event_data, response_data  

VIDEO_JUMP_START = 0.5
main_start_time = core.getTime()
MAX_CYCLES = 10

# Initialize window
global win
win = visual.Window(size=[1920, 1200], fullscr=True, units='pix', screen=1)
#get size of winow

# Initialize mouse
mouse = event.Mouse(win=win)

# Load the .avi video
video_path = './materials/David.avi'
video = visual.MovieStim3(win, video_path, size=(1920, 1200), flipVert=False, flipHoriz=False, loop=True)
#get video frame rate
frame_rate = video.getFPS()

# Create an occluder stimulus
occluder = visual.Rect(win, width=1920, height=1200, fillColor='black')

# QUEST parameters
quest_forward = data.QuestHandler(startVal=0.3, startValSd=0.2, pThreshold=0.75, gamma=0.5, 
                          nTrials=50, minVal=0.0, maxVal=1.0, beta=3.5, delta=0.1)
quest_forward = data.QuestHandler(startVal=0.3, startValSd=0.2, pThreshold=0.75, gamma=0.5, 
                          nTrials=50, minVal=0.0, maxVal=1.0, beta=3.5, delta=0.1)



def main_experiment(win):

    try:
        global main_start_time
        main_start_time = core.getTime()

        global folder_path
        participant_data = {'participant_id': ''}
        dlg = gui.DlgFromDict(dictionary=participant_data, title="Participant Data")
        if dlg.OK:
            print("Participant Data:", participant_data)
        else:
            print("User cancelled")
            return

        folder_path = os.path.join('data', participant_data['participant_id'])
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

        #give information about the experiment
        background = visual.Rect(win, width=1920, height=1200, fillColor='gray')
        background.draw()
        
        info_text = visual.TextStim(win, text='In this experiment, you will see a rotating object. Press the spacebar whenever you feel like they are discontinuities in its movement', pos=(0, 0))
        info_text.draw()
        win.flip()
        #press space to continue
        event.waitKeys(keyList=['space'])
        win.flip()

        # Natural blink condition
        bc_event_data, bc_response_data, blink_durations = blink_condition(win)
        # Save natural blink durations
        bc_event_data.to_csv(os.path.join(folder_path, 'bc_event_data.csv'))
        bc_response_data.to_csv(os.path.join(folder_path, 'bc_response_data.csv'))
        video.pause()
        video.autoDraw = False

        background.draw()

        # check if at least 10 blinks were detected
        '''
        if len(blink_durations) < 10:
            error_text = visual.TextStim(win, text='Not enough blinks detected. Experiment ending', pos=(0, 0))
            error_text.draw()
            win.flip()
            win.close()
            core.quit()
            return
        '''
        # Give information about the break,
        break_text = visual.TextStim(win, text='Please take a short break. Press space to continue.', pos=(0, 0))
        break_text.draw()
        win.flip()

        #plot histogram of blink durations
        plt.hist(blink_durations, bins=5)
        plt.show()

        # Wait for spacebar press to continue
        event.waitKeys(keyList=['space'])
        win.flip()

        # Replay condition
        tr_event_data, tr_response_data = true_replay_condition(win, bc_event_data)
        # Save natural blink durations
        tr_event_data.to_csv(os.path.join(folder_path, 'tr_event_data.csv'))
        tr_response_data.to_csv(os.path.join(folder_path, 'tr_response_data.csv'))

        video.pause()
        video.autoDraw = False

        background.draw()

        # Give information about the break,
        break_text = visual.TextStim(win, text='Please take a short break. Press space to continue.', pos=(0, 0))
        break_text.draw()
        win.flip()

        # Wait for spacebar press to continue
        event.waitKeys(keyList=['space'])
        win.flip()

        # Random replay condition
        rr_event_data, rr_response_data = random_replay_condition(win, bc_event_data)
        rr_event_data.to_csv(os.path.join(folder_path, 'rr_event_data.csv'))   
        rr_response_data.to_csv(os.path.join(folder_path, 'rr_response_data.csv'))
    
        # thank participant for participating
        end_text = visual.TextStim(win, text='Thank you for participating in this experiment. Press space to exit.', pos=(0, 0))
        end_text.draw()
        win.flip()

    except KeyboardInterrupt:
        bc_event_data.to_csv(os.path.join(folder_path, 'bc_event_data.csv'))
        bc_response_data.to_csv(os.path.join(folder_path, 'bc_response_data.csv'))
        win.close()
        core.quit()


# Run the main experiment
main_experiment(win)

# Clean up
win.close()
core.quit()
