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
        self.mouse = event.Mouse(win=self.win)
        self.video_path = './materials/David.avi'
        self.video = visual.MovieStim3(self.win, self.video_path, size=(1920, 1200), flipVert=False, flipHoriz=False, loop=True)
        self.occluder = visual.Rect(self.win, width=1920, height=1200, fillColor='black')
        self.quest = data.QuestHandler(startVal=0.3, startValSd=0.2, pThreshold=0.75, gamma=0.5, 
                                       nTrials=50, minVal=0.0, maxVal=1.0, beta=3.5, delta=0.1)
        self.main_start_time = core.getTime()
        self.max_cycles = 10
        self.video_jump_start = 0.5

    def occluder_jump(self, duration=0.3, video_jump=1):
        start_time = core.getTime()

        self.occluder.autoDraw = True
        self.video.autoDraw = False  
        self.win.flip()

        self.video.pause()
        self.video.seek((self.video.getCurrentFrameTime() + video_jump) % self.video.duration)
        self.video.play()
        self.occluder.autoDraw = False

        core.wait(core.getTime() + duration - start_time)
        end_time = core.getTime()

        self.video.autoDraw = True
        self.win.flip()

        return start_time, end_time

    def blink_jump(self, duration=0.3, video_jump=1):
        start_time = core.getTime()

        self.video.pause()
        self.video.seek((self.video.getCurrentFrameTime() + video_jump) % self.video.duration)
        self.video.play()

        core.wait(core.getTime() + duration - start_time)
        end_time = core.getTime()
        self.win.flip()

        return start_time, end_time

    def check_response(self, cycle_number, space_click_time, occ_end_time, is_jump, is_detected, response_data):
        if cycle_number > 0:
            video_jump_old = self.video_jump_start

            for value in self.quest:
                video_jump = value
                break

            response_speed = space_click_time - occ_end_time
            if is_jump and is_detected:
                response_type = 'correct'
                self.quest.addResponse(1)
            elif is_jump and not is_detected:
                response_type = 'missed'
                self.quest.addResponse(0)
            elif not is_jump and is_detected:
                response_type = 'false positive'
                self.quest.addResponse(0)
            else:  # not is_jump and not is_detected
                response_type = 'correct rejection'
                self.quest.addResponse(1)

            response_data = response_data._append({'time': core.getTime() - self.main_start_time, 'video_jump': video_jump_old, 'response_speed': response_speed, 'response_type': response_type, 'quest_threshold': self.quest.mean(), 'quest_sd': self.quest.sd()}, ignore_index=True)

        cycle_number += 1
        return cycle_number, response_data

    def blink_condition(self):
        event_data = pd.DataFrame(columns=['event_type', 'time'])
        response_data = pd.DataFrame(columns=['time', 'video_jump', 'response_speed', 'response_type', 'quest_threshold', 'quest_sd'])

        occ_end_time = 0
        blink_durations = []
        cycle_number = 0
        space_click_time = 0
        is_jump = False
        is_detected = False
        video_jump = self.video_jump_start

        self.video.autoDraw = True
        self.video.play()

        blinking = False
        condition_start_time = core.getTime()
        event_data = event_data._append({'event_type': 'condition_start', 'time': condition_start_time - self.main_start_time}, ignore_index=True)

        while True:
            keys = event.getKeys()

            if 'b' in keys:
                if not blinking:
                    blink_start = core.getTime()
                    blinking = True

                    blink_text = visual.TextStim(self.win, text='BLINK', pos=(-0.9, 0.9))
                    blink_text.draw()
                    blink_text.autoDraw = True

                    if random.random() < 0.5:
                        is_detected = False
                        is_jump = True
                        occ_start_time, occ_end_time = self.blink_jump(video_jump=video_jump)
                    else:
                        is_detected = False
                        is_jump = False
                        occ_start_time, occ_end_time = self.blink_jump(video_jump=0)

                    event_data = event_data._append({'event_type': 'occlusion_start', 'time': occ_start_time - self.main_start_time}, ignore_index=True)
                    event_data = event_data._append({'event_type': 'occlusion_end', 'time': occ_end_time - self.main_start_time}, ignore_index=True)
                    event_data = event_data._append({'event_type': 'blink_start', 'time': blink_start - self.main_start_time}, ignore_index=True)

                elif blinking:
                    blink_end = core.getTime()
                    blinking = False

                    event_data = event_data._append({'event_type': 'blink_end', 'time': blink_end - self.main_start_time}, ignore_index=True)
                    blink_durations.append(blink_end - blink_start)

                    blink_text.autoDraw = False

                    cycle_number, response_data = self.check_response(cycle_number, space_click_time, occ_end_time, is_jump, is_detected, response_data)
            
            self.win.flip()

            if 'space' in keys and cycle_number > 0:
                space_click_time = core.getTime() - self.main_start_time
                if space_click_time - occ_end_time < 2:
                    is_detected = True

            if 'escape' in keys or 'q' in keys or cycle_number >= self.max_cycles:
                break

        return event_data, response_data, blink_durations

    def random_replay_condition(self, blink_data):
        event_data = pd.DataFrame(columns=['event_type', 'time'])
        response_data = pd.DataFrame(columns=['time', 'video_jump', 'response_speed', 'response_type', 'quest_threshold', 'quest_sd'])

        blink_start = np.array(blink_data[blink_data['event_type'] == 'blink_start']['time'])
        blink_end = np.array(blink_data[blink_data['event_type'] == 'blink_end']['time'])

        blink_durations = blink_end - blink_start
        blink_distance = blink_start[1:] - blink_end[:-1]

        space_click_time = 0
        occ_end_time = 0

        dur_mu, dur_std = norm.fit(blink_durations)
        dis_mu, dis_std = norm.fit(blink_distance)

        is_jump = False
        is_detected = False
        cycle_number = 0

        self.video.autoDraw = True
        self.video.play()

        duration = np.random.normal(dur_mu, dur_std)
        distance = np.random.normal(dis_mu, dis_std)

        condition_start_time = core.getTime()
        event_data = event_data._append({'event_type': 'condition_start', 'time': condition_start_time - self.main_start_time}, ignore_index=True)

        while True:
            self.video.draw()

            time_since_last_blink = core.getTime() - occ_end_time

            if time_since_last_blink > distance:
                cycle_number, response_data = self.check_response(cycle_number, space_click_time, occ_end_time, is_jump, is_detected, response_data)

                if random.random() < 0.5:
                    is_detected = False
                    is_jump = True
                    occ_start_time, occ_end_time = self.occluder_jump(video_jump=self.video_jump_start, duration=duration)
                else:
                    is_detected = False
                    is_jump = False
                    occ_start_time, occ_end_time = self.occluder_jump(video_jump=0, duration=duration)

                event_data = event_data._append({'event_type': 'occluder_start', 'time': occ_start_time - self.main_start_time}, ignore_index=True)
                event_data = event_data._append({'event_type': 'occluder_end', 'time': occ_end_time - self.main_start_time}, ignore_index=True)

                duration = np.random.normal(dur_mu, dur_std)
                distance = np.random.normal(dis_mu, dis_std)

            self.win.flip()
            keys = event.getKeys()

            if 'space' in keys:
                space_click_time = core.getTime() - self.main_start_time
                if space_click_time - occ_end_time < 2:
                    is_detected = True

            if 'escape' in keys or 'q' in keys or cycle_number >= np.size(blink_durations):
                break

        return event_data, response_data

    def true_replay_condition(self, blink_data):
        event_data = pd.DataFrame(columns=['event_type', 'time'])
        response_data = pd.DataFrame(columns=['time', 'video_jump', 'response_speed', 'response_type', 'quest_threshold', 'quest_sd'])

        blink_start = np.array(blink_data[blink_data['event_type'] == 'blink_start']['time'])
        blink_end = np.array(blink_data[blink_data['event_type'] == 'blink_end']['time'])

        blink_durations = blink_end - blink_start
        space_click_time = 0
        occ_end_time = 0

        is_jump = False
        is_detected = False
        cycle_number = 0

        self.video.autoDraw = True
        self.video.play()

        condition_start_time = core.getTime()
        event_data = event_data._append({'event_type': 'condition_start', 'time': condition_start_time - self.main_start_time}, ignore_index=True)

        for dur in blink_durations:
            cycle_number, response_data = self.check_response(cycle_number, space_click_time, occ_end_time, is_jump, is_detected, response_data)

            if random.random() < 0.5:
                is_detected = False
                is_jump = True
                occ_start_time, occ_end_time = self.occluder_jump(video_jump=self.video_jump_start, duration=dur)
            else:
                is_detected = False
                is_jump = False
                occ_start_time, occ_end_time = self.occluder_jump(video_jump=0, duration=dur)

            event_data = event_data._append({'event_type': 'occluder_start', 'time': occ_start_time - self.main_start_time}, ignore_index=True)
            event_data = event_data._append({'event_type': 'occluder_end', 'time': occ_end_time - self.main_start_time}, ignore_index=True)

            self.win.flip()
            keys = event.getKeys()

            if 'space' in keys:
                space_click_time = core.getTime() - self.main_start_time
                if space_click_time - occ_end_time < 2:
                    is_detected = True

            if 'escape' in keys or 'q' in keys:
                break

        return event_data, response_data

    def run(self):
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

        self.show_instructions('In this experiment, you will see a rotating object. Press the spacebar whenever you feel like there are discontinuities in its movement.')

        # Blink condition
        bc_event_data, bc_response_data, blink_durations = self.blink_condition()
        self.save_data(folder_path, 'bc_event_data.csv', bc_event_data)
        self.save_data(folder_path, 'bc_response_data.csv', bc_response_data)
        self.video.pause()

        self.show_message('Please take a short break. Press space to continue.')
        self.show_histogram(blink_durations)

        # True replay condition
        tr_event_data, tr_response_data = self.true_replay_condition(bc_event_data)
        self.save_data(folder_path, 'tr_event_data.csv', tr_event_data)
        self.save_data(folder_path, 'tr_response_data.csv', tr_response_data)
        self.video.pause()

        self.show_message('Please take a short break. Press space to continue.')

        # Random replay condition
        rr_event_data, rr_response_data = self.random_replay_condition(bc_event_data)
        self.save_data(folder_path, 'rr_event_data.csv', rr_event_data)
        self.save_data(folder_path, 'rr_response_data.csv', rr_response_data)

        self.show_message('Thank you for participating in this experiment. Press space to exit.')

        self.win.close()
        core.quit()

    def show_instructions(self, text):
        background = visual.Rect(self.win, width=1920, height=1200, fillColor='gray')
        background.draw()
        info_text = visual.TextStim(self.win, text=text, pos=(0, 0))
        info_text.draw()
        self.win.flip()
        event.waitKeys(keyList=['space'])
        self.win.flip()

    def show_message(self, text):
        message_text = visual.TextStim(self.win, text=text, pos=(0, 0))
        message_text.draw()
        self.win.flip()
        event.waitKeys(keyList=['space'])
        self.win.flip()

    def show_histogram(self, data):
        plt.hist(data, bins=5)
        plt.show()

    def save_data(self, folder_path, file_name, data):
        data.to_csv(os.path.join(folder_path, file_name))


if __name__ == "__main__":
    experiment = Experiment()
    experiment.run()
