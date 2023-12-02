import os
import glob
import pandas as pd
from pathlib import Path
from src.config import cfg


def time_from_seconds(seconds):
    # Split the input into whole seconds and milliseconds
    whole_seconds = int(seconds)
    milliseconds = int((seconds - whole_seconds) * 1000)

    # Constants for time conversion
    SECONDS_PER_MINUTE = 60
    MINUTES_PER_HOUR = 60

    # Calculate hours, minutes, and seconds
    hours = whole_seconds // (SECONDS_PER_MINUTE * MINUTES_PER_HOUR)
    whole_seconds -= hours * (SECONDS_PER_MINUTE * MINUTES_PER_HOUR)

    minutes = whole_seconds // SECONDS_PER_MINUTE
    whole_seconds -= minutes * SECONDS_PER_MINUTE

    # Format the time string
    time_str = f"{hours:02}:{minutes:02}:{whole_seconds:02},{milliseconds:03}"
    return time_str


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


def merge_csv(result_dir: str):
    # glob all the files
    csv_pths = glob.glob(os.path.join(str(result_dir), "*.csv"))

    # sort the csvs based on created date
    csv_pths = sorted(csv_pths, key=os.path.getmtime)

    dfs = []
    for i, csv_pth in enumerate(csv_pths):
        # read csv and perform conversion
        df = pd.read_csv(csv_pth)

        df["Start"] = df["Start"].apply(time_from_seconds)
        df["End"] = df["End"].apply(time_from_seconds)

        df["Start"] = df["Start"].apply(
            lambda x: sum_seconds(x, i * cfg.audio.split_length_seconds)
        )
        df["End"] = df["End"].apply(
            lambda x: sum_seconds(x, i * cfg.audio.split_length_seconds)
        )

        dfs.append(df)

    df = pd.concat(dfs, ignore_index=True)
    df = df.loc[:, ~df.columns.str.contains("^Unnamed")]
    final_result_pth = Path(result_dir).parent.joinpath(cfg.result.file_name)
    df.to_csv(final_result_pth)

    return final_result_pth

