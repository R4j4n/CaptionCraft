import sys
import subprocess


def add_subtitles(video_path, srt_path, font_name, fontsize, output_file):
    command = [
        "ffmpeg",
        "-i",
        video_path,
        "-vf",
        f"subtitles={srt_path}:force_style='Fontname={font_name},Fontsize={fontsize},PrimaryColour=&hFF'",
        output_file,
        "-y",
    ]

    subprocess.run(command)
