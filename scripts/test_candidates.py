import sys
import os
sys.path.insert(0, ".")
sys.path.insert(0, "engine")
from engine.main import resolve_youtube_stream_url
import cv2

candidates = [
    ("traffic_1", "https://www.youtube.com/watch?v=1EiC9bvVGnk"),
    ("traffic_2", "https://www.youtube.com/watch?v=lfYYtQ1Ah04"),
    ("parking_1", "https://www.youtube.com/watch?v=U7HRKjlXK-Y"),
    ("parking_2", "https://www.youtube.com/watch?v=gteUhJz4v2I"),
    ("retail_1", "https://www.youtube.com/watch?v=-ZG3gM6vTBE"),
    ("retail_2", "https://www.youtube.com/watch?v=5rkwqp6nnr4"),
    ("retail_3", "https://www.youtube.com/watch?v=KMJS66jBtVQ"),
    ("pedestrian_1", "https://www.youtube.com/watch?v=Od6EeCWytZo"),
    ("pedestrian_2", "https://www.youtube.com/watch?v=Bi61ue_cpMY"),
    ("pedestrian_3", "https://www.youtube.com/watch?v=t9G_aG8LFh8"),
    ("gym_1", "https://www.youtube.com/watch?v=Ae3SPjsXETc"),
    ("gym_2", "https://www.youtube.com/watch?v=gcNh17Ckjgg"),
    ("gym_3", "https://www.youtube.com/watch?v=xqvCmoLULNY"),
    ("workshop_1", "https://www.youtube.com/watch?v=2QBEPQIRygI"),
    ("workshop_2", "https://www.youtube.com/watch?v=h3suLIhonb8"),
    ("warehouse_1", "https://www.youtube.com/watch?v=vm33YAT3Soo"),
    ("warehouse_2", "https://www.youtube.com/watch?v=dQKr-4N533k"),
    ("warehouse_3", "https://www.youtube.com/watch?v=4smBCzqA_vo"),
    ("safety_1", "https://www.youtube.com/watch?v=Tv7rgE_dSg0"),
    ("safety_2", "https://www.youtube.com/watch?v=q6dS6Wuqyo4"),
    ("bottling_1", "https://www.youtube.com/watch?v=RTqNpMo2IX0"),
    ("bottling_2", "https://www.youtube.com/watch?v=7fZkeRojRNQ"),
    ("barcode_1", "https://www.youtube.com/watch?v=b3Gh2tffHxE"),
    ("barcode_2", "https://www.youtube.com/watch?v=lze4XzfNykY"),
    ("dashcam_1", "https://www.youtube.com/watch?v=ToEWlyM-n8s"),
    ("dashcam_2", "https://www.youtube.com/watch?v=HeGKRSIo7u4"),
]

print(f"Testing {len(candidates)} candidate videos...")
for tag, url in candidates:
    try:
        s_url, is_live, title = resolve_youtube_stream_url(url, "720p")
        cap = cv2.VideoCapture(s_url)
        ret, frame = cap.read()
        cap.release()
        if ret and frame is not None and frame.size > 0:
            h, w = frame.shape[:2]
            print(f"PASS: {tag:<14} | {w}x{h} | {title[:40]} | {url}")
        else:
            print(f"FAIL (no frame): {tag:<14} | {title[:40]} | {url}")
    except Exception as e:
        print(f"ERROR: {tag:<14} | {e} | {url}")
