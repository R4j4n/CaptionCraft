# source : https://raw.githubusercontent.com/maximofn/subtify/main/concat_transcriptions.py


import os
import re
import glob
from tqdm import tqdm
from pathlib import Path

from src.config import cfg


def sum_seconds(time, seconds):
    # Get time in seconds
    time = time.split(",")
    time_milisecons = time[1]
    time_milisecons = int(time_milisecons) / 1000
    time = time[0].split(":")
    time = int(time[0]) * 3600 + int(time[1]) * 60 + int(time[2])

    # Get integer and decimal part of seconds
    seconds, seconds_miliseconds = divmod(seconds, 1)
    seconds = int(seconds)
    seconds_miliseconds = round(seconds_miliseconds, 3)

    # Add seconds
    time = time + seconds
    time_milisecons = time_milisecons + seconds_miliseconds
    if time_milisecons >= 1:
        time = time + 1
        time_milisecons = time_milisecons - 1
        time_milisecons = round(time_milisecons, 3)

    # Get time in hh:mm:ss,mmm format
    hours = int(time) // 3600
    minutes = (int(time) % 3600) // 60
    seconds = (int(time) % 3600) % 60
    time_milisecons = str(time_milisecons).split(".")[1]
    time = f"{hours:02d}:{minutes:02d}:{seconds:02d},{time_milisecons}"

    return time


def hmsms_to_seconds(time):
    # Get time in seconds
    time = time.split(",")
    milisecons = time[1]
    time = time[0].split(":")
    time = int(time[0]) * 3600 + int(time[1]) * 60 + int(time[2])
    time = time + int(milisecons) / 1000

    return time


def concatenate_transcriptions(srt_save_dir, seconds):
    # Concatenate transcriptions
    transcription = ""
    num_transcriptions = 1

    files = glob.glob(os.path.join(str(srt_save_dir), "*.srt"))
    # sort the csvs based on created date
    files = sorted(files, key=os.path.getmtime)

    progress_bar = tqdm(total=len(files), desc="Concatenating transcriptions progress")
    for i, file in enumerate(files):
        with open(file, "r") as f:
            transcription_chunk = f.read().splitlines()
        for line in transcription_chunk:
            # if line is dd:dd:dd,ddd --> dd:dd:dd,ddd
            if re.match(r"\d\d:\d\d:\d\d,\d\d\d --> \d\d:\d\d:\d\d,\d\d\d", line):
                # Get start time (dd:dd:dd,ddd) and end time (dd:dd:dd,ddd)
                start, end = line.split(" --> ")
                # Add seconds to start and end time
                start = sum_seconds(start, i * seconds)
                end = sum_seconds(end, i * seconds)
                # Add to transcription
                transcription += f"{start} --> {end}\n"

            # if line is a number and carriage return --> number
            elif re.match(r"\d+$", line):
                transcription += f"{num_transcriptions}\n"
                num_transcriptions += 1

            else:
                transcription += f"{line}\n"
        progress_bar.update(1)

    srt_save_pth = Path(srt_save_dir).parent.joinpath(cfg.result.file_name)
    with open(srt_save_pth, "w") as f:
        f.write(transcription)

    return srt_save_pth
