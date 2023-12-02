import re
import os
import math
from pathlib import Path
from typing import Any, Literal

import moviepy.editor
import pandas as pd
from pytube import YouTube
from pydub import AudioSegment
from rich.console import Console
from rich.progress import Progress
from pytube.exceptions import VideoUnavailable


console = Console()


class SplitWavAudioMubin:
    def __init__(self, save_folder, filename):
        self.folder = save_folder
        self.filename = filename
        self.filepath = filename
        _, self.file_extension = os.path.splitext(self.filename)

        if self.file_extension == ".mp3":
            self.audio = AudioSegment.from_mp3(self.filepath)

        if self.file_extension == ".wav":
            self.audio = AudioSegment.from_wav(self.filepath)

    def get_duration(self):
        return self.audio.duration_seconds

    def single_split(self, from_min, to_min, split_filename):
        t1 = from_min * 60 * 1000
        t2 = to_min * 60 * 1000
        split_audio = self.audio[t1:t2]
        split_audio.export(self.folder + "/" + split_filename, format="wav")

    def multiple_split(self, min_per_split):
        total_mins = math.ceil(self.get_duration() / 60)

        with Progress() as progress:
            task = progress.add_task(
                "[green]Splitting...", total=total_mins // min_per_split
            )

            for i in range(0, total_mins, min_per_split):
                split_fn = f"{i}_{i}{self.file_extension}"
                self.single_split(i, i + min_per_split, split_fn)

                progress.update(task, advance=1)

                if i >= total_mins - min_per_split:
                    print("All split successfully")


class YoutubeDownloder:
    def __init__(self, save_folder: str, file_type=Literal["video", "audio"]) -> None:
        self.save_folder = save_folder
        self.file_type = file_type

        if self.file_type == "video":
            self.download_format = "mp4"
        else:
            self.download_format = "mp3"

    def sanitize_title(self, title: str) -> str:
        """Sanitize the title to be used as a filename."""
        sanitized_title = re.sub(r"[^a-z0-9 ]", "", title.lower())
        return "_".join(sanitized_title.split(" "))

    def __download_youtube_video(self, url):
        yt = YouTube(url)

        file_name = self.sanitize_title(title=str(yt.title))

        self.save_pth = Path(self.save_folder).joinpath(file_name)
        # self.save_pth.mkdir(parents=True, exist_ok=True)

        save_video_dir = self.save_pth.joinpath(f"{file_name}.{self.download_format}")
        print(f"Passed save path {save_video_dir}")

        if os.path.exists(str(save_video_dir)):
            console.print("Video already downloaded.", style="bold green")
            return str(self.save_pth), str(save_video_dir)

        else:
            command = f"yt-dlp -o '{str(save_video_dir)}' -f 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]' '{url}'"
            os.system(command)
            return str(self.save_pth), str(save_video_dir)

    def __download_youtube_audio(self, url):
        yt = YouTube(url)

        file_name = self.sanitize_title(title=str(yt.title))

        self.save_pth = Path(self.save_folder).joinpath(file_name)
        # self.save_pth.mkdir(parents=True, exist_ok=True)

        save_video_audio = self.save_pth.joinpath(f"{file_name}.{self.download_format}")

        if os.path.exists(save_video_audio):
            console.print("Audio already downloaded.", style="bold green")

            return str(self.save_pth), str(save_video_audio)
        else:
            command = f"yt-dlp '{url}' -o '{str(save_video_audio)}' --extract-audio --audio-format mp3 --audio-quality 0"
            os.system(command)
            return str(self.save_pth), str(save_video_audio)

    def download_youtube(self, url):
        if self.file_type == "video":
            return self.__download_youtube_video(url)

        elif self.file_type == "audio":
            return self.__download_youtube_audio(url)


def dataframe_to_srt(df):
    srt_format = ""
    for index, row in df.iterrows():
        start = row["Start"].replace(",", ".")
        end = row["End"].replace(",", ".")
        speaker = row["Speaker"]
        text = f"{speaker}: {row['Text']}"
        srt_format += f"{index+1}\n{start} --> {end}\n{text}\n\n"
    return srt_format


def convert_video_to_audio(video_path: str, save_pth):
    filename = "".join(os.path.basename(video_path).split(".")[:-1])

    # Load the Video
    video = moviepy.editor.VideoFileClip(video_path)

    # Extract the Audio
    audio = video.audio

    # Export the Audio
    save_pth_ = os.path.join(save_pth, f"{filename}.wav")
    audio.write_audiofile(save_pth_)

    return save_pth_


import pandas as pd
import re


def srt_to_csv_with_pandas(srt_file_path, csv_file_path):
    # Read the SRT file
    with open(srt_file_path, "r", encoding="utf-8") as file:
        srt_content = file.read()

    # Split the content into blocks
    blocks = re.split(r"\n\n", srt_content.strip())

    # Process each block
    data = []
    for block in blocks:
        lines = block.split("\n")
        if len(lines) >= 3:
            # Extract time and text
            time_info, text = lines[1], " ".join(lines[2:])
            start_time, end_time = time_info.split(" --> ")

            # Extract and include the full speaker text
            speaker_match = re.search(r"\[([^\]]+)\]", text)
            speaker = speaker_match.group(1) if speaker_match else "Unknown"

            # Clean text
            text = re.sub(r"\[[^\]]+\]: ", "", text)

            # Append to data list
            data.append([start_time, end_time, speaker, text])

    # Create a DataFrame
    df = pd.DataFrame(data, columns=["Start", "End", "Speaker", "Text"])

    # Write DataFrame to a CSV file with index
    df.to_csv(csv_file_path, index=True, encoding="utf-8")

    return df


# class YouTubeDownloader:
#     def __init__(
#         self,
#         download_dir,
#         quality=Literal["480p", "720p", "1080p"],
#         merge: bool = False,
#     ) -> None:
#         self.download_dir = Path(download_dir)
#         self.quality = quality
#         self.merge = merge

#     def sanitize_title(self, title: str) -> str:
#         """Sanitize the title to be used as a filename."""
#         # Replace invalid file name characters with an underscore
#         sanitized_title = re.sub(r'[\\/*?:"<>|]', "_", title)
#         return sanitized_title

#     def __call__(self, URL: str) -> Any:
#         yt = YouTube(URL)

#         try:
#             sanitized_title = self.sanitize_title(yt.title)
#             vid_name = "_".join(sanitized_title.split())
#             dload_dir = self.download_dir.joinpath(vid_name)
#             dload_dir.mkdir(parents=True, exist_ok=True)

#             with console.status(
#                 "[bold green] Downloading audio and video..."
#             ) as status:
#                 # Download video
#                 video_stream = yt.streams.filter(
#                     file_extension="mp4", resolution=self.quality
#                 ).first()

#                 video_filename = video_stream.download(
#                     output_path=str(dload_dir),
#                     filename=f"{vid_name}.mp4",
#                     skip_existing=True,
#                 )

#                 # Download Audio
#                 audio_stream = yt.streams.filter(only_audio=True).first()
#                 audio_filename = audio_stream.download(
#                     output_path=str(dload_dir),
#                     filename=f"{vid_name}.mp3",
#                     skip_existing=True,
#                 )

#             if self.merge:
#                 video_clip = VideoFileClip(video_filename)
#                 audio_clip = AudioFileClip(audio_filename)
#                 final_clip = video_clip.set_audio(audio_clip)

#                 os.remove(path=video_filename)

#                 final_clip.write_videofile(video_filename, threads=16)

#                 return dload_dir

#             else:
#                 return dload_dir, video_filename, audio_filename

#         except VideoUnavailable as e:
#             raise Exception(f"{e} : Cannot Download the video.")


# if __name__ == "__main__":
#     URL = "https://youtu.be/LQnFpHIcAXg?si=5H8YQUIsEPVA0zg6"
#     yt = YouTubeDownloader(
#         download_dir="/home/ml/rajan/speech/whisperx_custom/cleaned_pipe/src/results",
#         quality="1080p",
#         merge=True,
#     )
#     save_pth = yt(URL=URL)
