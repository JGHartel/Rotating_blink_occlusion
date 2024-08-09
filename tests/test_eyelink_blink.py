from psychopy import visual, core, event
import pylink
from EyeLinkCoreGraphicsPsychoPy import EyeLinkCoreGraphicsPsychoPy

# Create a window
win = visual.Window(fullscr=True, units='height')
win_height = win.size[1]
text = visual.TextStim(
    win,
    text='Blink count:\n0',
    height=.05
)

tracker = pylink.EyeLink('100.1.1.1')

tracker.openDataFile('test.edf')
tracker.setOfflineMode()
tracker.sendCommand('sample_rate 1000')

# Send screen size to exp.tracker
tracker.sendCommand("screen_pixel_coords = 0 0 %d %d" % (win.size[0] - 1, win.size[1] - 1))
tracker.sendMessage("DISPLAY_COORDS 0 0 %d %d" % (win.size[0] - 1, win.size[1] - 1))

# Instantiate a graphics environment (genv) for calibration
genv = EyeLinkCoreGraphicsPsychoPy(tracker, win)

# Set background and foreground colors for calibration
genv.setCalibrationColors((-1, -1, -1), win.color)
genv.setTargetType('circle')
genv.setTargetSize(win_height*0.015)
genv.setCalibrationSounds('off', 'off', 'off')
tracker.sendCommand(f"calibration_type = HV9")
pylink.openGraphicsEx(genv)

# Start tracker setup
setup_text = visual.TextStim(
    win,
    text='STARTING EYE TRACKER SETUP\nPRESS C TO START CALIBRATION',
    units='height',
    height=0.05
    )
setup_text.draw()
win.flip()
tracker.doTrackerSetup()
tracker.startRecording(1, 1, 1, 1)
core.wait(5)

clock = core.Clock()
text.autoDraw = True
while clock.getTime() < 15:
    win.flip()
    if event.getKeys(['escape']):
        break

tracker.stopRecording()
tracker.setOfflineMode()
tracker.closeDataFile()
tracker.receiveDataFile('test.edf', 'test.edf')
tracker.close()
win.close()
pylink.closeGraphics()
core.quit()