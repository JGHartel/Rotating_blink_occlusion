import time
from collections import deque
import nest_asyncio
import numpy as np
from pupil_labs.realtime_api.simple import Device
from blink_detector.blink_detector import blink_detection_pipeline
from blink_detector.helper import (
    stream_images_and_timestamps,
    update_array,
    compute_blink_rate,
    plot_blink_rate,
)

nest_asyncio.apply()

ADDRESS = "192.168.144.127"
PORT = "8080"

# Setup functions
def setup_device(address=ADDRESS, port=PORT):
    device = Device(address=address, port=port)
    return device



print(f"Phone IP address: {device.phone_ip}")
print(f"Phone name: {device.phone_name}")