import sys
import pysrt
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip


def time_to_seconds(time_obj):
    return (
        time_obj.hours * 3600
        + time_obj.minutes * 60
        + time_obj.seconds
        + time_obj.milliseconds / 1000
    )


def create_subtitle_clips(
    subtitles,
    videosize,
    language,
    fontsize=40,
    font="Arial",
    color="yellow",
    debug=False,
):
    subtitle_clips = []

    if language in ["hi", "ne"]:
        font = "Lohit-Devanagari"

    for subtitle in subtitles:
        start_time = time_to_seconds(subtitle.start)
        end_time = time_to_seconds(subtitle.end)
        duration = end_time - start_time

        video_width, video_height = videosize

        text_clip = (
            TextClip(
                subtitle.text,
                fontsize=fontsize,
                font=font,
                color=color,
                bg_color="black",
                size=(video_width * 3 / 4, None),
                method="f",
            )
            .set_start(start_time)
            .set_duration(duration)
        )
        subtitle_x_position = "center"
        subtitle_y_position = video_height * 4 / 5

        text_position = (subtitle_x_position, subtitle_y_position)
        subtitle_clips.append(text_clip.set_position(text_position))

    return subtitle_clips


def burn(video_path, srt_path, language):
    # Load video and SRT file
    video = VideoFileClip(video_path)
    subtitles = pysrt.open(srt_path)

    begin, end = video_path.split(".mp4")
    output_video_file = begin + "_subtitled" + ".mp4"

    # Create subtitle clips
    subtitle_clips = create_subtitle_clips(subtitles, video.size, language=language)

    # Add subtitles to the video
    final_video = CompositeVideoClip([video] + subtitle_clips)

    # Write output video file
    final_video.write_videofile(output_video_file)


# burn(
#     video_path="/home/ml/rajan/speech/whisperx_custom/cleaned_pipe/results/why_china_wont_attack_taiwan__john_mearsheimer_and_lex_fridman/why_china_wont_attack_taiwan__john_mearsheimer_and_lex_fridman.mp4",
#     srt_path="/home/ml/rajan/speech/whisperx_custom/cleaned_pipe/results/why_china_wont_attack_taiwan__john_mearsheimer_and_lex_fridman/result.srt",
#     language="en",
# )
