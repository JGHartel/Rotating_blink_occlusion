'''
- check the exit and wrap up functions
- check response_data collection
- check ordering in blink_event data
'''

import os
import random
import numpy as np
import pandas as pd
from scipy.stats import norm
from matplotlib import pyplot as plt
from psychopy import core, visual, event, gui, data
from psychopy.hardware import keyboard

import pylink
from EyeLinkCoreGraphicsPsychoPy import EyeLinkCoreGraphicsPsychoPy


class Experiment:
    def __init__(self, eye = True, tracker_ip = '100.1.1.1'):
        self.initialize_window()
        self.initialize_video()
        self.initialize_keyboard()
        self.get_subject_id()
        self.initialize_variables()
        self.initialize_quest()
        self.initialize_data()
        
        self.initialize_eye_tracking(eye, tracker_ip)
        
        
    def initialize_keyboard(self):
        self.kb=keyboard.Keyboard()
        self.keys = self.kb.getKeys()
        
    def initialize_video(self):
        self.video_folder = './materials'
        self.video_path = './materials/man_2_downsampled.avi'
        self.data_path = './data'

        self.video = visual.MovieStim3(self.win, self.video_path, size=(self.win.size[0], self.win.size[1]), flipVert=False, flipHoriz=False, loop=True, interpolate=True)

        self.occluder = visual.Rect(self.win, width=self.win.size[0], height=self.win.size[1], fillColor='black')

    def initialize_window(self):
        self.win = visual.Window(fullscr=True, units='pix', screen=0, color='black')


    def initialize_variables(self):
        self.main_start_time = core.getTime()
        self.max_condition_duration = 300
        self.max_cycles = 1000
        self.duration = 0.3
        self.is_occlusion = True
        self.is_forward = True
        self.is_jump = True
        self.is_detected = False
        self.in_blink = False
        self.cycle_number = 0
        self.occ_end_time = 0
        self.space_click_time = 0 
        self.blink_durations = [] 
        self.total_blinks = 0
        self.max_blinks = 1000

    def initialize_data(self):
      
        self.host_edf='jgh_test.edf'

        self.event_data = pd.DataFrame(columns=['event_type', 'onset', 'duration', 'trial_jump'])
        self.blink_data = self.event_data.copy()
        self.response_data = pd.DataFrame(columns=['time', 'video_jump', 'response_speed', 'response_type', 'quest_type', 'quest_threshold', 'quest_sd'])
            
    def initialize_eye_tracking( self, eye = True, tracker_ip = ''):
        self.eye = eye

        if eye:
            self.eye_dir  = os.path.join(self.sub, 'eyetrack')
            if not os.path.exists(self.eye_dir):
                os.makedirs(self.eye_dir)
    
            self.tracker_ip = tracker_ip
            self.tracker    = pylink.EyeLink(tracker_ip)
        else:
            self.tracker = None

    def initialize_quest(self):
            self.video_jump_start = 0.5

            self.quest_forward = data.QuestHandler(startVal=0.5, startValSd=0.5, pThreshold=0.75, gamma=0.5, 
                                           nTrials=50, minVal=0.0, maxVal=1.0, beta=3.5, delta=0.1)
            
            self.quest_backward = data.QuestHandler(startVal=0.5, startValSd=0.5, pThreshold=0.75, gamma=0.5, 
                                           nTrials=50, minVal=0.0, maxVal=1.0, beta=3.5, delta=0.1)
            
            self.video_jump_forward = self.video_jump_start
            self.video_jump_backward = -self.video_jump_start 
            self.video_jump = self.video_jump_start

            

    def tracker_setup(self, calibration_type='HV9'):

        if not self.eye:
            raise ValueError("Eye tracking is disabled. `exp.eye` must be set to True to run tracker_setup()")

        win_height = self.win.size[1]

        self.tracker.openDataFile(self.host_edf)
        self.tracker.setOfflineMode()
        self.tracker.sendCommand('sample_rate 1000')

        # Send screen size to exp.tracker
        self.tracker.sendCommand("screen_pixel_coords = 0 0 %d %d" % (self.win.size[0] - 1, self.win.size[1] - 1))
        self.tracker.sendMessage("DISPLAY_COORDS 0 0 %d %d" % (self.win.size[0] - 1, self.win.size[1] - 1))

        # Instantiate a graphics environment (genv) for calibration
        genv = EyeLinkCoreGraphicsPsychoPy(self.tracker, self.win)

        # Set background and foreground colors for calibration
        genv.setCalibrationColors((1, 1, 1), self.win.color)
        genv.setTargetType('circle')
        genv.setTargetSize(win_height*0.015)
        genv.setCalibrationSounds('off', 'off', 'off')
        self.tracker.sendCommand(f"calibration_type = {calibration_type}")
        self.tracker.sendCommand("link_event_filter = LEFT,RIGHT,FIXATION,FIXUPDATE,SACCADE,BLINK,BUTTON,INPUT")
        self.tracker.sendCommand("file_sample_data = LEFT,RIGHT,GAZE,AREA,GAZERES,STATUS")
                   
        pylink.openGraphicsEx(genv)

        # Start tracker setup
        setup_text = visual.TextStim(self.win,
                                    text='STARTING EYE TRACKER SETUP\nPRESS C TO START CALIBRATION',
                                    units='height',
                                    height=0.05)
        setup_text.draw()
        self.win.flip()
        self.tracker.doTrackerSetup()
        self.tracker.startRecording(1,1,1,1)
        core.wait(1)
        
    def jump(self):
        start_time = core.getTime()
        end_time = core.getTime()
        event_type = 'empty'

        if not self.is_jump:
            end_time = core.getTime()
            event_type = 'no_jump'
            pass

        else:
            if self.is_occlusion:
                self.occluder.autoDraw = True
                self.video.autoDraw = False
                self.win.flip()

            self.video.pause()
            if self.is_forward:
                self.video.seek((self.video.getCurrentFrameTime() + self.video_jump_forward) % self.video.duration)
                self.video_jump = self.video_jump_forward
                event_type = 'occluded_forward_jump' if self.is_occlusion else 'forward_jump'
            else:
                self.video.seek((self.video.getCurrentFrameTime() + self.video_jump_backward) % self.video.duration)
                self.video_jump = self.video_jump_backward 
                event_type = 'occluded_backward_jump' if self.is_occlusion else 'backward_jump'

            self.video.play()

            if self.is_occlusion:
                self.ocfcluder.autoDraw = False
                core.wait(core.getTime() + self.duration - start_time)

            end_time = core.getTime()
            self.video.autoDraw = True
            self.win.flip()

        self.occ_end_time = end_time

        new_data = pd.DataFrame({'event_type': event_type, 'onset': start_time, 'duration': end_time - start_time, 'trial_jump': self.video_jump}, index=[0])
        self.event_data = pd.concat([self.event_data, new_data], ignore_index=True)
        return

    def check_response(self):
        mean = 0
        sd = 0
        response = 0
        response_type = ''
        quest_type = ''

        if self.cycle_number > 0 and not self.is_change:

            video_jump_old = self.video_jump
            
            response_speed = self.space_click_time - self.occ_end_time

            if self.is_jump:
                if self.is_detected:
                    response_type = 'correct'
                    response=1
                if not self.is_detected:
                    response_type = 'missed'
                    response=0
                self.cycle_number += 1
                
                if self.is_forward:
                    self.quest_forward.addResponse(response)
                    mean=self.quest_forward.mean()
                    sd=self.quest_forward.sd()
                    self.video_jump_forward = next(self.quest_forward)
                else: 
                    self.quest_backward.addResponse(response)
                    mean=self.quest_backward.mean()
                    sd=self.quest_backward.sd()
                    self.video_jump_backward = -next(self.quest_backward)

            else:
                response_type = 'false positive' if self.is_detected else 'correct rejection'
                mean = self.quest_forward.mean() if self.is_forward else self.quest_backward.mean()
                sd = self.quest_forward.sd() if self.is_forward else self.quest_backward.sd()
                quest_type = 'forward' if self.is_forward else 'backward'
   
            self.response_data = pd.concat([self.response_data, pd.DataFrame({'time': self.space_click_time, 'video_jump': video_jump_old, 'response_speed': response_speed, 'response_type': response_type, 'quest_threshold': mean, 'quest_sd': sd, 'quest_type': quest_type}, index=[0])], ignore_index=True)
        
        if self.is_change:
            self.cycle_number += 1
            self.is_change = False 
            if self.is_detected:
                response_type = 'caught change'
            if not self.is_detected:
                response_type = 'missed change'

            self.response_data = pd.concat([self.response_data, pd.DataFrame({'time': self.space_click_time, 'video_jump': 0, 'response_speed': response_speed, 'response_type': response_type}, index=[0])], ignore_index=True)        
        
        else:
            self.cycle_number += 1

        return

    def reset_parameters(self):
        self.is_occlusion = True
        self.is_forward = True
        self.is_jump = True
        self.is_detected = False
        self.occ_end_time = 0
        self.space_click_time = 0
        self.video_jump = self.video_jump_start
        self.cycle_number = 0
        
        #jump to start of video
        self.video.seek(0)

        self.event_data = pd.DataFrame(columns=self.event_data.columns)
        self.response_data = pd.DataFrame(columns=self.response_data.columns)

        #re-initialize the QuestHandler
        self.quest_forward = data.QuestHandler(startVal=0.5, startValSd=0.5, pThreshold=0.75, gamma=0.5, 
                                       nTrials=50, minVal=0.0, maxVal=1.0, beta=3.5, delta=0.1)
        self.quest_backward = data.QuestHandler(startVal=0.5, startValSd=0.5, pThreshold=0.75, gamma=0.5, 
                                       nTrials=50, minVal=0.0, maxVal=1.0, beta=3.5, delta=0.1)

        return
    
    def pseudo_blink_condition(self):
        
        self.reset_parameters()

        self.video.autoDraw = True
        self.video.play()
        self.win.flip()

        self.condition_start_time = core.getTime()

        self.blink_text = visual.TextStim(self.win, text=f'BLINK_{self.total_blinks}', pos=(0, 0), color='white', height=40)

        self.event_data = pd.concat([self.event_data, pd.DataFrame({'event_type': 'condition_start', 'onset': self.condition_start_time}, index=[0])], ignore_index=True)

        while True:
            self.keys = self.kb.getKeys()

            #change the blink text to the current blink number
            self.blink_text.text = f'BLINK_{self.total_blinks}'

            if 'b' in self.keys:

                if not self.in_blink:
                    blink_start = core.getTime()
                    self.in_blink = True

                    self.blink_text.autoDraw = True 

                    self.is_occlusion = False
                    self.jump_choice()

                elif self.in_blink:
                    blink_end = core.getTime()
                    self.in_blink = False

                    self.event_data = pd.concat([self.event_data, pd.DataFrame({'event_type': 'blink', 'onset': blink_start, 'duration': blink_end - blink_start}, index=[0])], ignore_index=True)
                    self.blink_durations.append(blink_end - blink_start)

                    self.blink_text.autoDraw = False
                    self.check_response()

                    self.total_blinks += 1

            self.win.flip()

            if 'space' in self.keys and self.cycle_number > 0 and self.is_detected == False:
                self.space_click_time = core.getTime()
                self.response_time = self.space_click_time - self.occ_end_time
                if self.response_time < 2 and self.response_time > 0:
                    self.is_detected = True

            if 'escape' in self.keys or 'q' in self.keys or self.total_blinks >= self.max_blinks or core.getTime() - self.condition_start_time > self.max_condition_duration:
                end_type = 'max_blinks' if self.total_blinks >= self.max_blinks else 'max_duration' if core.getTime() - self.condition_start_time > self.max_condition_duration else 'escape' if 'escape' in self.keys else 'q' if 'q' in self.keys else 'unknown'
                self.event_data = pd.concat([self.event_data, pd.DataFrame({'event_type': 'condition_end', 'onset': core.getTime(), 'end_type': end_type}, index=[0])], ignore_index=True)
                self.blink_data = self.event_data
                self.wrap_up('pseudo_blink_condition', 'blink')
                break

        return

    
    def blink_condition(self):
        
        self.reset_parameters()

        self.video.autoDraw = True
        self.video.play()
        self.win.flip()
        blink_start=0.0

        condition_start_time = core.getTime()

        self.event_data = pd.concat([self.event_data, pd.DataFrame({'event_type': 'condition_start', 'onset': condition_start_time}, index=[0])], ignore_index=True)
        print('blink condition started')

        while True:        
            self.keys = self.kb.getKeys()


            event_code = self.detect_blink_from_pupil_size()
                
            if event_code == pylink.STARTBLINK:
                blink_start = core.getTime()
                self.is_occlusion = False
                self.jump_choice()
            
            elif event_code == pylink.ENDBLINK:
                blink_end = core.getTime()
                
                self.event_data = pd.concat(
                            [self.event_data,
                            pd.DataFrame({'event_type': 'blink',
                                        'onset': blink_start,
                                        'duration': blink_end - blink_start
                                        }, index=[0])],
                                            ignore_index=True)
                    
                self.blink_durations.append(blink_end - blink_start)

                self.check_response()

                self.total_blinks += 1
                    

            self.win.flip()

            if 'space' in self.keys and self.cycle_number > 0 and self.is_detected == False:
                self.space_click_time = core.getTime()
                self.response_time = self.space_click_time - self.occ_end_time
                if self.response_time < 2 and self.response_time > 0:
                    self.is_detected = True

            if 'escape' in self.keys or 'q' in self.keys or self.total_blinks >= self.max_blinks:
                self.wrap_up('pseudo_blink_condition', 'blink')
                break

        self.blink_data = self.event_data

        self.wrap_up('blink_condition', 'blink')

        return
    
    def analyze_blink_condition(self):
        # calculate the mean and standard deviation of the blink durations
        self.blink_durations = np.array(self.blink_data[self.blink_data['event_type'] == 'blink']['duration'])
        self.dur_mu, self.dur_std = norm.fit(self.blink_durations)

        #get the condition start time
        condition_start_time = self.blink_data[self.blink_data['event_type'] == 'condition_start']['onset'].iloc[0]

        # calculate the mean and standard deviation of the blink distances
        self.blink_starts = np.array(self.blink_data[self.blink_data['event_type'] == 'blink']['onset'])-condition_start_time
        self.blink_ends = self.blink_starts + self.blink_durations 

        self.blink_distances = self.blink_starts[1:] - self.blink_ends[:-1]
        self.dis_mu, self.dis_std = norm.fit(self.blink_distances)

        return

    def random_replay_condition(self):

        self.reset_parameters()

        self.analyze_blink_condition()
        self.duration = np.random.normal(self.dur_mu, self.dur_std)
        distance = np.random.normal(self.dis_mu, self.dis_std)

        condition_start_time = core.getTime()

        self.event_data = pd.concat([self.event_data, pd.DataFrame({'event_type': 'condition_start', 'onset': condition_start_time}, index=[0])], ignore_index=True)

        self.video.autoDraw = True
        self.video.play()

        while True:
            self.keys = self.kb.getKeys()
            
            time_since_last_blink = core.getTime() - self.occ_end_time

            if time_since_last_blink > distance:
                self.check_response()

                self.is_occlusion = True

                self.jump_choice()

                self.duration = np.random.normal(self.dur_mu, self.dur_std)
                distance = np.random.normal(self.dis_mu, self.dis_std)


            if 'space' in self.keys:
                self.space_click_time = core.getTime()
                if self.space_click_time - self.occ_end_time < 2:
                    self.is_detected = True

            if 'escape' in self.keys or 'q' in self.keys or self.cycle_number >= np.size(self.blink_durations):
                break
        
            self.win.flip()

        self.wrap_up('random_replay_condition', 'rr')

        return
    
    def jump_choice(self):
        random_number = random.random()
        self.is_detected = False
        self.is_change = False
        
        if random_number < 0.25:
            self.is_jump = True
            self.is_forward = True
            self.jump()
        elif random_number < 0.5:
            self.is_jump = True
            self.is_forward = False
            self.jump()
        elif random_number > 0.95:
            self.is_jump = False
            self.Is_Forward = True
            self.is_change = True
            self.change_video()
        else:
            self.is_jump = False

    def change_video(self):
        #pick a differnt video from video folder
        video_list = os.listdir(self.video_folder)
        video_list.remove(self.video_path)
        self.video_path = os.path.join(self.video_folder, random.choice(video_list))

        # get the current position in video
        current_time = self.video.getCurrentFrameTime()

        self.video.autoDraw = False
        self.video = visual.MovieStim3(self.win, self.video_path, size=(self.win.size[0], self.win.size[1]), flipVert=False, flipHoriz=False, loop=True, interpolate=True)
        self.video.seek(current_time)

        self.event_data = pd.concat([self.event_data, pd.DataFrame({'event_type': 'video_change', 'onset': core.getTime(), 'new_video': f'{self.video_path}'}, index=[0])], ignore_index=True)
                        
        self.video.autoDraw = True
        self.video.play()


    def true_replay_condition(self):
        
        self.reset_parameters()

        self.analyze_blink_condition()

        condition_start_time = core.getTime()
        new_data = pd.DataFrame({'event_type': 'condition_start', 'onset': condition_start_time}, index=[0])
        self.event_data = pd.concat([self.event_data, new_data], ignore_index=True)

        self.video.autoDraw = True
        self.video.play()

        while True:
            self.keys = self.kb.getKeys()
            self.video.draw()

            if core.getTime() - condition_start_time >= self.blink_starts[self.cycle_number] and not self.in_blink:
                self.Duration= self.blink_durations[self.cycle_number]
                self.is_occlusion = True
                self.in_blink = True

                self.check_response()

                self.jump_choice()

                # override cycle number to progress even if there was no jump
                self.cycle_number += 1

            elif core.getTime() - condition_start_time >= self.blink_ends[self.cycle_number] and self.in_blink:
                self.in_blink = False

            self.win.flip()

            if 'space' in self.keys and self.cycle_number > 1:
                space_click_time = core.getTime() 
                if space_click_time - self.occ_end_time < 2:
                    self.is_detected = True

            if 'escape' in self.keys or 'q' in self.keys:
                break
            if self.cycle_number >= np.size(self.blink_durations):
                break

        self.wrap_up('true_replay_condition', 'tr')
        return

    def wrap_up(self, condition_name, condition_prefix):
        #show wrap up message
        self.video.autoDraw = False
        
        self.show_message('Wrapping up, please wait... ')
        self.win.flip()
        # Save the experiment data in a dedicated folder for the specified experimental condition
        data_path = os.path.join(self.beh_dir, condition_name)
        if not os.path.exists(data_path):
            os.makedirs(data_path)
        
        self.event_data.to_csv(os.path.join(data_path, f'{condition_prefix}_event_data.csv'))
        self.response_data.to_csv(os.path.join(data_path, f'{condition_prefix}_response_data.csv'))

        self.show_message('Wrap up complete. Press space to continue.')
        self.win.flip()

        event.waitKeys(keyList=['space'])
        self.win.flip()

        return

    def get_subject_id(self):
        participant_data = {'participant_id': ''}
        dlg = gui.DlgFromDict(dictionary=participant_data, title="Participant Data")

        self.sub = participant_data['participant_id']
        self.sub_sub = f'sub-{self.sub}'

        if dlg.OK:
            print("Participant Data:", participant_data)
        else:
            print("User cancelled")
            return
        
        # Subject folders
        self.sub_dir = os.path.join('data', self.sub_sub)
        if not os.path.exists(self.sub_dir):
            os.makedirs(self.sub_dir)
        
        self.beh_dir = os.path.join(self.sub_dir, 'beh')
        if not os.path.exists(self.beh_dir):
            os.makedirs(self.beh_dir)

    def run(self):

        self.get_subject_id()

        if self.eye:
            self.tracker_setup()

        self.show_message('In this experiment, you will see a rotating object. Press the spacebar whenever you feel like there are discontinuities in its movement.')

        # Blink condition
        self.blink_condition()

        # True replay condition
        #self.true_replay_condition()  

        #self.random_replay_condition()
    
        self.show_message('Thank you for participating in this experiment. Press space to exit.')
        self.win.flip()

        event.waitKeys(keyList=['space'])
        self.win.flip()

        self.win.close()
        core.quit()

    def show_message(self, text):
        background = visual.Rect(self.win, width=1920, height=1080, fillColor='black')
        background.draw()
        info_text = visual.TextStim(self.win, text=text, pos=(0, 0))
        info_text.draw()
        self.win.flip()

    def eyelink_detect_event(self, event_type='blink_start'):
        """Check if an event has occurred on the Eyelink tracker and compute the delay.
        THIS FUNCTION HAS BEEN DEPRECATED DUE TO INSUFFICIENT SAMPLING RATE DURING VIDEOP RESENTATION
        """
        event_dict = {
            pylink.STARTBLINK: 'blink_start',
            pylink.ENDBLINK: 'blink_end',
            pylink.STARTSACC: 'saccade_start',
            pylink.ENDSACC: 'saccade_end',
            pylink.STARTFIX: 'fixation_start',
            pylink.ENDFIX: 'fixation_end'
        }

        data = self.tracker.getNextData()
        event_code = f'{data}'
        if data in event_dict:
            event_code = event_dict[data]
        
            
        if data != 0:
            current_time = self.tracker.trackerTime()
            float_time = self.tracker.getFloatData()
            #event_time = float_time.getTime()
            print(f'Time: {current_time}, Code: {event_code}')

            self.event_data = pd.concat(
                [self.event_data,
                 pd.DataFrame(
                     {'event_type': event_code,
                      'onset': current_time
                      }, index=[0])
                      ], ignore_index=True)

            if event_code == event_type:
                return True, current_time          
            
            return False, current_time
        
        return False, None

    def detect_blink_from_pupil_size(self):
        """Update whether eyes are closed (pupil size = 0) and return the pylink event code for the blink.
        `self.in_blink` True -> True: Eyes are still closed
        `self.in_blink` False -> True: Start of a blink
        `self.in_blink` True -> False: End of a blink
        `self.in_blink` False -> False: Eyes are still open
        """
        sample = self.tracker.getNewestSample()
        if sample is None:
            pupil_size = None
            return self.in_blink, None
        elif sample.isRightSample():
            pupil_size = sample.getRightEye().getPupilSize()
        elif sample.isLeftSample():
            pupil_size = sample.getLeftEye().getPupilSize()
        elif sample.isBinocularSample():
            pupil_size = sample.getBinocularEye().getPupilSize()
        else:
            raise ValueError("Cannot determine which eye is being tracked.")
        
        if pupil_size == 0: # Eyes closed this frame
            if self.in_blink: # Eyes still closed in the middle of a blink
                event_code = None
            else: # Start of a blink
                event_code = pylink.STARTBLINK
            self.in_blink = True
        else: # Eyes open this frame
            if self.in_blink: # End of a blink
                event_code = pylink.ENDBLINK
            else: # Eyes still open
                event_code = None
            self.in_blink = False

        return event_code

    def pseudo_blink_detection(self, event_type='pseudo_blink'):  
        # Pseudo-blink detection when no valid coordinates are found
        sample = self.tracker.getNewestSample()
        if sample is not None:
            

            left_eye = sample.getLeftEye()
            right_eye = sample.getRightEye()
            print(f"left: {left_eye}, right: {right_eye}")
            
            if (left_eye is None or left_eye.getGaze() == (-32768, -32768)) and (right_eye is None or right_eye.getGaze() == (-32768, -32768)):
                # Pseudo-blink detected
                pseudo_blink_time = self.tracker.trackerTime()
                print(f"Pseudo-blink detected at: {pseudo_blink_time}")

                self.event_data = pd.concat(
                    [self.event_data,
                     pd.DataFrame(
                         {'event_type': 'pseudo_blink',
                          'onset': [pseudo_blink_time]
                          })], ignore_index=True)

                
                return True, pseudo_blink_time

        return False, None
                                   

experiment = Experiment()
experiment.run()

