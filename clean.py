import os
import shutil
from typing import Optional, Any
from pathlib import Path

import pandas as pd
from tqdm.auto import tqdm

from src.config import cfg
from src.model_mappings import whisper_mapp
from src.transcribe import TranscribeAlignDiarize  # TODO: Rename to pipe
from src.concat_srt import concatenate_transcriptions
from src.ffmpgeg_burn import add_subtitles

from src.utils import (
    YoutubeDownloder,
    SplitWavAudioMubin,
    convert_video_to_audio,
    srt_to_csv_with_pandas,
    dataframe_to_srt,
)

from src.translate import Translator


class Name:
    def __init__(
        self, burn_srt: bool = False, delete_intermediate: bool = False
    ) -> None:
        self.video_path = None
        self.video_dir = None
        self.audio_pth = None
        self.chunks_dir = None
        self.delete_intermediate = delete_intermediate
        self.burn_srt = burn_srt

    def get_available_languages(self):
        return list(whisper_mapp.keys())

    def convert_audio_to_chunks(self):
        chunks_dir = Path(self.video_dir).joinpath("chunks")
        chunks_dir.mkdir(exist_ok=True, parents=True)
        audio_splitter = SplitWavAudioMubin(
            save_folder=str(chunks_dir), filename=self.audio_pth
        )
        audio_splitter.multiple_split(min_per_split=cfg.audio.split_length_minutes)
        self.chunks_dir = chunks_dir

    def __call__(
        self, path, source_language, destination_language: Optional["str"] = None
    ) -> Any:
        assert (
            source_language in self.get_available_languages()
        ), f"Language {source_language} not in supported list."

        # Check if it's a file path
        if os.path.isfile(path):
            print(f"Path detected")
            self.video_dir = str(Path(path).parent)
            self.video_path = path

        else:
            yt = YoutubeDownloder(save_folder="youtube", file_type="video")
            # download youtube video
            self.video_dir, self.video_path = yt.download_youtube(url=path)

        # step 1 : convert video to audio ...
        self.audio_pth = convert_video_to_audio(
            video_path=str(self.video_path), save_pth=str(self.video_dir)
        )

        # step 2 : split audio to chunks
        self.convert_audio_to_chunks()

        # step 3: start the conversion process
        trans_align_diarize = TranscribeAlignDiarize(
            device=cfg.model.device,
            batch_size=cfg.model.batch_size,
            compute_type=cfg.model.compute_type,
            HF_TOKEN=cfg.model.HF_TOKEN,
            result_dir=self.video_dir,
        )

        chunk_pths = list(self.chunks_dir.glob("*.wav"))

        for i, chunk_pth in tqdm(enumerate(chunk_pths)):
            trans_align_diarize.pipe(
                audio_path=str(chunk_pth),
                source_lang=whisper_mapp[str(source_language)],
                model_="faster_whisper",
            )

        # Merge all timestamps
        srt_save_pth = Path(self.video_dir).joinpath(
            cfg.result.transcribe_result_dir_name
        )
        self.srt_pth = concatenate_transcriptions(
            srt_save_dir=srt_save_pth, seconds=cfg.audio.split_length_seconds
        )

        df_pth = Path(self.srt_pth).parent.joinpath("result.csv")
        srt_to_csv_with_pandas(
            srt_file_path=self.srt_pth,
            csv_file_path=df_pth,
        )

        if self.delete_intermediate:
            shutil.rmtree(self.chunks_dir)
            shutil.rmtree(srt_save_pth)

        if destination_language:
            translator = Translator()

            tranlated_csv = translator.translate_csv(
                csv_pth=df_pth,
                source_language=source_language,
                destination_language=destination_language,
            )
            srt_content = dataframe_to_srt(df=pd.read_csv(tranlated_csv))

            translated_srt_pth = str(Path(tranlated_csv).with_suffix(".srt"))

            with open(translated_srt_pth, "w") as f:
                f.write(srt_content)

            if self.burn_srt:
                burned_vid_pth = Path(self.video_dir).joinpath("subtitled.mp4")
                add_subtitles(
                    video_path=self.video_path,
                    srt_path=translated_srt_pth,
                    font_name="Futura",
                    fontsize=12,
                    output_file=burned_vid_pth,
                )

        if destination_language == None and self.burn_srt:
            add_subtitles(
                video_path=self.video_path,
                srt_path=self.srt_pth,
                font_name="Futura",
                fontsize=14,
                output_file=Path(self.video_dir).joinpath("subtitled.mp4"),
            )


if __name__ == "__main__":
    ns = Name(burn_srt=True)
    # print(ns.get_available_languages())
    ns(
        path="https://www.youtube.com/watch?v=RX288fIu8YQ",
        source_language="english",
        destination_language="hindi",
    )
