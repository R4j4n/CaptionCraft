import os
import shutil
from typing import Optional, Any
from pathlib import Path
import pandas as pd
from tqdm.auto import tqdm
from src.config import cfg
from src.model_mappings import whisper_mapp, mbart_mapp
from src.transcribe import TranscribeAlignDiarize
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


class Pipe:
    def __init__(
        self,
        delete_intermediate: bool = False,
    ):
        self.video_path = None
        self.video_dir = None
        self.audio_path = None
        self.chunks_dir = None
        self.delete_intermediate = delete_intermediate
        self.df_pth = None
        self.srt_pth = None

    def get_transcribe_languages(self):
        return list(whisper_mapp.keys())

    def get_translate_languages(self):
        return list(mbart_mapp.keys())

    def convert_audio_to_chunks(self):
        self.chunks_dir = Path(self.video_dir).joinpath("chunks")
        self.chunks_dir.mkdir(exist_ok=True, parents=True)
        audio_splitter = SplitWavAudioMubin(
            save_folder=str(self.chunks_dir), filename=self.audio_path
        )
        audio_splitter.multiple_split(min_per_split=cfg.audio.split_length_minutes)

    def process_video_path(self, path):
        if os.path.isfile(path):
            print("Path detected")
            self.video_dir = str(Path(path).parent)
            self.video_path = path
        else:
            yt = YoutubeDownloder(save_folder="youtube", file_type="video")
            self.video_dir, self.video_path = yt.download_youtube(url=path)

    def transcribe_audio_chunks(self, source_language):
        trans_align_diarize = TranscribeAlignDiarize(
            device=cfg.model.device,
            batch_size=cfg.model.batch_size,
            compute_type=cfg.model.compute_type,
            HF_TOKEN=cfg.model.HF_TOKEN,
            result_dir=self.video_dir,
        )
        chunk_paths = list(self.chunks_dir.glob("*.wav"))
        for chunk_path in tqdm(chunk_paths):
            trans_align_diarize.pipe(
                audio_path=str(chunk_path),
                source_lang=whisper_mapp[str(source_language)],
                model_="faster_whisper",
            )

    def burn_subtitle_to_video(self):
        burned_video_path = Path(self.video_dir).joinpath("subtitled.mp4")
        add_subtitles(
            video_path=self.video_path,
            srt_path=self.srt_path,
            font_name="Futura",
            fontsize=14,
            output_file=burned_video_path,
        )

        return True

    def handle_transcription_result(self):
        srt_save_path = Path(self.video_dir).joinpath(
            cfg.result.transcribe_result_dir_name
        )
        self.srt_path = concatenate_transcriptions(
            srt_save_dir=srt_save_path, seconds=cfg.audio.split_length_seconds
        )
        df_path = Path(self.srt_path).parent.joinpath("result.csv")
        srt_to_csv_with_pandas(srt_file_path=self.srt_path, csv_file_path=df_path)
        if self.delete_intermediate:
            shutil.rmtree(self.chunks_dir)
            shutil.rmtree(srt_save_path)
        return df_path

    def translate(self, df_path, source_language, destination_language):
        translator = Translator()
        translated_csv = translator.translate_csv(
            csv_pth=df_path,
            source_language=source_language,
            destination_language=destination_language,
        )
        srt_content = dataframe_to_srt(df=pd.read_csv(translated_csv))
        translated_srt_path = str(Path(translated_csv).with_suffix(".srt"))
        with open(translated_srt_path, "w") as file:
            file.write(srt_content)

        return translated_srt_path, translated_csv

    def remap_speakers(self, mapp):
        # Read the dataframe from the csv file
        df = pd.read_csv(self.df_pth)

        # Replace the 'Speaker' values based on the mapping
        df["Speaker"] = df["Speaker"].replace(mapp)

        # Optionally, you can save the modified dataframe back to the same file
        df.to_csv(self.df_pth, index=False)

        srt_content = dataframe_to_srt(df=df)
        os.remove(self.srt_path)
        with open(self.srt_path, "w") as file:
            file.write(srt_content)

    def __call__(
        self, path, source_language, destination_language: Optional[str] = None
    ):
        if source_language not in self.get_transcribe_languages():
            raise ValueError(f"Language {source_language} not in supported list.")

        else:
            try:
                self.process_video_path(path)
                self.audio_path = convert_video_to_audio(
                    video_path=str(self.video_path), save_pth=str(self.video_dir)
                )

                self.convert_audio_to_chunks()
                self.transcribe_audio_chunks(source_language)
                self.df_pth = self.handle_transcription_result()

                if destination_language:
                    self.srt_path, self.df_pth = self.translate(
                        df_path=self.df_pth,
                        source_language=source_language,
                        destination_language=destination_language,
                    )

                return True
            except Exception as e:
                raise f"Cannot Process : {e}"


# processor = Pipe(delete_intermediate=True)
# processor(
#     path="https://www.youtube.com/watch?v=w9NkqdoIH5A",
#     source_language="english",
#     destination_language="hindi",
# )
# processor.remap_speakers({"SPEAKER_01": "Lex", "SPEAKER_00": "Elon"})
# processor.burn_subtitle_to_video()
