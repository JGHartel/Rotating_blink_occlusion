import os
import random
import numpy as np
import pandas as pd
from scipy.stats import norm
from matplotlib import pyplot as plt
from psychopy import core, visual, event, gui, data


class Experiment:
    def __init__(self):
        self.win = visual.Window(size=[1920, 1200], fullscr=True, units='pix', screen=1)
        self.video_path = './materials/David.avi'
        self.data_path = './data'
        self.video = visual.MovieStim3(self.win, self.video_path, size=(1920, 1200), flipVert=False, flipHoriz=False, loop=True)
        self.win_width, self.win_height = 1920
        self.occluder = visual.Rect(self.win, width=1920, height=1080, fillColor='black')

        self.main_start_time = core.getTime()
        self.max_cycles = 10
        self.video_jump_start = 0.5

        self.quest_forward = data.QuestHandler(startVal=0.5, startValSd=0.5, pThreshold=0.75, gamma=0.5, 
                                       nTrials=50, minVal=0.0, maxVal=1.0, beta=3.5, delta=0.1)
        
        self.quest_backward = data.QuestHandler(startVal=-0.5, startValSd=0.5, pThreshold=-0.75, gamma=0.5, 
                                       nTrials=50, minVal=-1.0, maxVal=1.0, beta=3.5, delta=0.1)
        
        self.video_jump_forward = self.video_jump_start
        self.video_jump_backward = -self.video_jump_start 

        self.duration = 0.3
        self.IsOcclusion = True
        self.IsForward = True
        self.IsJump = True
        self.IsDetected = False
        self.IsBlink = False
        self.cycle_number = 0
        self.occ_end_time = 0
        self.space_click_time = 0 
        self.blink_durations = [] 
        
        self.keys = event.getKeys()
        
            # create an event data frame with generic bids template

        self.event_data = pd.DataFrame(columns=['event_type', 'onset', 'duration', 'trial_jump'])
        self.response_data = pd.DataFrame(columns=['time', 'video_jump', 'response_speed', 'response_type', 'quest_threshold', 'quest_sd'])

    def jump(self):
        start_time = core.getTime()

        if not self.IsJump:
            end_time = core.getTime()
            event_type = 'no_jump'
            pass
        else:
            if self.IsOcclusion:
                self.occluder.autoDraw = True
                self.video.autoDraw = False
                self.win.flip()

            self.video.pause()
            if self.IsForward:
                self.video.seek((self.video.getCurrentFrameTime() + self.video_jump_forward) % self.video.duration)
            else:
                self.video.seek((self.video.getCurrentFrameTime() + self.video_jump_backward) % self.video.duration)
            self.video.play()

            if self.IsOcclusion:
                self.occluder.autoDraw = False
                core.wait(core.getTime() + self.duration - start_time)

            end_time = core.getTime()
            self.video.autoDraw = True
            self.win.flip()

            if self.IsOcclusion and self.IsForward:
                event_type = 'occluded_forward_jump'
            elif self.IsOcclusion and not self.IsForward:
                event_type = 'occluded_backward_jump'
            elif not self.IsOcclusion and self.IsForward:
                event_type = 'forward_jump'

        self.occ_end_time = end_time
        self.event_data = self.event_data._append({'event_type': event_type, 'onset': start_time, 'duration': end_time - start_time, 'trial_jump': self.video_jump}, ignore_index=True)
        return

    def check_response(self):
        if self.cycle_number > 0:
            video_jump_old = self.video_jump
            
            response_speed = self.space_click_time - self.occ_end_time

            if self.IsJump:
                if self.IsDetected:
                    response_type = 'correct'
                    response=1
                elif not self.IsDetected:
                    response_type = 'missed'
                    response=0
                self.cycle_number += 1
                
                if self.IsForward:
                    self.quest_forward.update(response)
                    mean=self.quest_forward.mean()
                    sd=self.quest_forward.sd()
                    for value in self.quest_forward:
                        self.video_jump_forward = value
                        break
                else: 
                    self.quest_backward.update(response)
                    mean=self.quest_forward.mean()
                    sd=self.quest_forward.sd()
                    for value in self.quest_backward:
                        self.video_jump_backward= value
                        break

            elif not self.IsJump and self.IsDetected:
                response_type = 'false positive'
            else: 
                response_type = 'correct rejection'
   
            self.response_data = self.response_data._append({'time': self.space_click_time, 'video_jump': video_jump_old, 'response_speed': response_speed, 'response_type': response_type, 'quest_threshold': mean, 'quest_sd': sd}, ignore_index=True)

        return

    def reset_parameters(self):
        self.IsOcclusion = True
        self.IsForward = True
        self.IsJump = True
        self.IsDetected = False
        self.occ_end_time = 0
        self.space_click_time = 0
        self.video_jump = self.video_jump_start

        #jump to start of video
        self.video.seek(0)

        self.event_data = self.event_data.clear()
        self.response_data = self.response_data.clear()

        #re-initialize the QuestHandler
        self.quest_forward = data.QuestHandler(startVal=0.5, startValSd=0.5, pThreshold=0.75, gamma=0.5, 
                                       nTrials=50, minVal=0.0, maxVal=1.0, beta=3.5, delta=0.1)
        self.quest_backward = data.QuestHandler(startVal=-0.5, startValSd=0.5, pThreshold=-0.75, gamma=0.5, 
                                       nTrials=50, minVal=-1.0, maxVal=1.0, beta=3.5, delta=0.1)

        return
    
    def blink_condition(self):
        
        self.reset_parameters()

        self.video.autoDraw = True
        self.video.play()

        condition_start_time = core.getTime()
        self.event_data = self.event_data._append({'event_type': 'condition_start', 'onset': condition_start_time}, ignore_index=True)

        while True:
            if 'b' in self.keys:
                if not self.IsBlink:
                    blink_start = core.getTime()
                    self.IsBlink = True

                    blink_text = visual.TextStim(self.win, text='BLINK', pos=(-self.win_width/2, self.win_height/2))
                    blink_text.draw()
                    blink_text.autoDraw = True

                    self.IsOcclusion = False
                    self.jump_choice()

 
                elif self.IsBlink:
                    blink_end = core.getTime()
                    self.IsBlink = False

                    event_data = event_data._append({'event_type': 'blink', 'onset': blink_start, 'duration': blink_end - blink_start}, ignore_index=True)
                    self.blink_durations.append(blink_end - blink_start)

                    blink_text.autoDraw = False
                    self.check_response()

            self.win.flip()

            if 'space' in self.keys and self.cycle_number > 0:
                self.space_click_time = core.getTime()
                if self.space_click_time - self.occ_end_time < 2:
                    self.IsDetected = True

            if 'escape' or 'q' in self.keys or self.cycle_number >= self.max_cycles:
                break

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
        self.blink_ends = self.lbink_starts + self.blink_durations 

        self.blink_distances = self.blink_starts[1:] - self.blink_ends[:-1]
        self.dis_mu, self.dis_std = norm.fit(self.blink_distance)


        return

    def random_replay_condition(self):

        self.reset_parameters()

        self.analyze_blink_condition()
        self.duration = np.random.normal(self.dur_mu, self.dur_std)
        distance = np.random.normal(self.dis_mu, self.dis_std)

        condition_start_time = core.getTime()
    
        event_data = event_data.append({'event_type': 'condition_start', 'onset': condition_start_time}, ignore_index=True)

        self.video.autoDraw = True
        self.video.play()

        while True:
            self.video.draw()
            time_since_last_blink = core.getTime() - self.occ_end_time

            if time_since_last_blink > distance:
                self.check_response()

                self.IsOcclusion = True

                self.jump_choice()

                self.duration = np.random.normal(self.dur_mu, self.dur_std)
                distance = np.random.normal(self.dis_mu, self.dis_std)

            self.win.flip()
            self.keys = event.getKeys()

            if 'space' in self.keys:
                self.space_click_time = core.getTime()
                if self.space_click_time - self.occ_end_time < 2:
                    self.IsDetected = True

            if 'escape' or'q' in self.keys or self.cycle_number >= np.size(self.blink_durations):
                break

        self.wrap_up('random_replay_condition', 'rr')

        return
    
    def jump_choice(self):
        random_number = random.random()
        self.IsDetected = False
        
        if random_number < 0.25:
            self.IsJump = True
            self.IsForward = True
            self.jump()
        elif random_number < 0.5:
            self.IsJump = True
            self.IsForward = False
            self.jump()
        else:
            self.IsJump = False

    def true_replay_condition(self):
        
        self.reset_parameters()

        self.analyze_blink_condition()

        condition_start_time = core.getTime()
        event_data = event_data.append({'event_type': 'condition_start', 'onset': condition_start_time}, ignore_index=True)

        self.video.autoDraw = True
        self.video.play()

        while True:
            self.video.draw()

            if core.getTime() - condition_start_time > self.blink_starts[self.cycle_number] and not self.IsBlink:
                self.Duration= self.blink_durations[self.cycle_number]
                self.IsOcclusion = True
                self.IsBlink = True

                self.check_response()

                self.jump_choice()

                # override cycle number to progress even if there was no jump
                self.cycle_number += 1

            elif core.getTime() - condition_start_time > self.blink_ends[cycle_number] and Blinked:
                Blinked = False

            self.win.flip()

            if 'space' in self.keys and self.cycle_number > 1:
                space_click_time = core.getTime() 
                if space_click_time - self.occ_end_time < 2:
                    IsDetected = True

            if 'escape' in self.keys or 'q' in self.keys:
                break
            if self.cycle_number > np.size(self.blink_durations-1):
                break

        self.wrap_up('true_replay_condition', 'tr')
        return

    def wrap_up(self, condition_name, condition_prefix):
        #show wrap up message
        self.video.autoDraw = False
        
        self.show_message('Wrapping up, please wait... ')

        # Transfer data
        self.tr_data = self.event_data  
        self.tr_response_data = self.response_data
        
        # Save the experiment data in a dedicated folder for the specified experimental condition
        data_path = os.path.join(self.data_path, 'behavioral', condition_name)
        if not os.path.exists(data_path):
            os.makedirs(data_path)
        
        # Use the prefix for file names
        self.save_data(data_path, f'{condition_prefix}_event_data.csv', self.blink_data)
        self.save_data(data_path, f'{condition_prefix}_response_data.csv', self.blink_response_data)


        self.show_message('Wrap up complete. Press space to continue.')
        event.waitKeys(keyList=['space'])
        self.win.flip()

    def run(self):

        participant_data = {'participant_id': ''}
        dlg = gui.DlgFromDict(dictionary=participant_data, title="Participant Data")

        if dlg.OK:
            print("Participant Data:", participant_data)
        else:
            print("User cancelled")
            return

        self.data_path = os.path.join('data', participant_data['participant_id'])
        if not os.path.exists(self.data_path):
            os.makedirs(self.data_path)

        self.show_instructions('In this experiment, you will see a rotating object. Press the spacebar whenever you feel like there are discontinuities in its movement.')

        # Blink condition
        self.blink_condition()

        # True replay condition
        self.true_replay_condition()

        self.random_replay_condition()
    
        self.show_message('Thank you for participating in this experiment. Press space to exit.')

        event.waitKeys(keyList=['space'])
        self.win.flip()

        self.win.close()
        core.quit()

    def show_message(self, text):
        background = visual.Rect(self.win, width=1920, height=1200, fillColor='gray')
        background.draw()
        info_text = visual.TextStim(self.win, text=text, pos=(0, 0))
        info_text.draw()
        self.win.flip()


if __name__ == "__main__":
    experiment = Experiment()
    experiment.run()


