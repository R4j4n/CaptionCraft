import os
import gc
import torch
from pathlib import Path
from typing import Literal

import whisperx
import pandas as pd
from src.config import cfg
from rich.console import Console
from whisperx.utils import get_writer
from faster_whisper import WhisperModel

console = Console()


class TranscribeAlignDiarize:
    def __init__(
        self,
        device: str,
        batch_size: int,
        HF_TOKEN: str,
        result_dir: str,
        compute_type: str = Literal["float16", "int8"],
        diarization_model: str = "pyannote/speaker-diarization-3.0",
    ) -> None:
        self.HF_TOKEN = HF_TOKEN
        self.device: str = device
        self.batch_size: int = batch_size
        self.compute_type: str = compute_type
        self.diarization_model = diarization_model
        self.result_dir = Path(result_dir)

    def perform_transcribe(self, audio_path, source_language):
        with console.status(
            f":rocket:[bold red] Loading the {self.compute_type} whisper model."
        ):
            model = whisperx.load_model(
                "large-v2", self.device, compute_type=self.compute_type
            )

        audio = whisperx.load_audio(audio_path)

        result = model.transcribe(
            audio,
            batch_size=self.batch_size,
            print_progress=True,
            language=source_language,
        )

        gc.collect()
        torch.cuda.empty_cache()
        del model

        return result

    def perform_transcribe_fast_whisper(self, audio_path, source_language):
        audio_file = self.add_text_before_extension(audio_path, "_monoChannel")
        os.system(
            f'ffmpeg -i "{audio_path}" -ar 16000 -ac 1 -c:a pcm_s16le -y "{audio_file}"'
        )
        with console.status(
            f":rocket:[bold red] Loading the {self.compute_type} whisper model."
        ):
            model = WhisperModel(
                "large-v2", device=self.device, compute_type=self.compute_type
            )

        options = dict(language=source_language, beam_size=10, best_of=10)

        transcribe_options = dict(task="transcribe", **options)
        segments_raw, info = model.transcribe(audio_file, **transcribe_options)

        segments = []

        i = 0
        for segment_chunk in segments_raw:
            chunk = {}
            chunk["start"] = segment_chunk.start
            chunk["end"] = segment_chunk.end
            chunk["text"] = segment_chunk.text
            segments.append(chunk)
            i += 1

        result = {}
        result["segments"] = segments
        result["language"] = source_language

        gc.collect()
        torch.cuda.empty_cache()
        del model
        os.remove(audio_file)
        return result

    def perform_alignment(self, whisper_response, audio_path):
        align_model, metadata = whisperx.load_align_model(
            language_code=whisper_response["language"], device=self.device
        )
        with console.status(f":rocket:[bold red] Performing Alignment."):
            result = whisperx.align(
                whisper_response["segments"],
                align_model,
                metadata,
                audio_path,
                self.device,
                interpolate_method="nearest",
                return_char_alignments=True,
            )

        gc.collect()
        torch.cuda.empty_cache()
        del align_model

        return result

    def perform_diarize(self, alignment_result, audio_path):
        with console.status(f":rocket:[bold red] Performing Diarization."):
            diarize_model = whisperx.DiarizationPipeline(
                model_name=self.diarization_model,
                use_auth_token=self.HF_TOKEN,
                device=self.device,
            )

            diarize_segments = diarize_model(
                audio_path, min_speakers=2, max_speakers=10
            )
            result = whisperx.assign_word_speakers(diarize_segments, alignment_result)

            gc.collect()
            torch.cuda.empty_cache()
            del diarize_model

        return result

    # TODO : Delete if srt is working
    def write_csv(self, result, audio_path, save_dir):
        filename = Path(audio_path).stem

        start, end, speaker, text = [], [], [], []

        for i, records in enumerate(result["segments"]):
            speaker.append(records["speaker"])
            text.append(records["text"])
            start.append(records["start"])
            end.append(records["end"])

        # Converting to DataFrame
        df = pd.DataFrame(
            {"Start": start, "End": end, "Speaker": speaker, "Text": text}
        )
        df.to_csv(save_dir.joinpath(f"{filename}.csv"))

    def pipe(
        self, audio_path, source_lang, model_=Literal["whisperx", "faster_whisper"]
    ):
        if model_ == "whisperx":
            whiser_resposne = self.perform_transcribe(
                audio_path=audio_path, source_language=source_lang
            )

        if model_ == "faster_whisper":
            whiser_resposne = self.perform_transcribe_fast_whisper(
                audio_path=audio_path, source_language=source_lang
            )

        alligned_response = self.perform_alignment(
            whisper_response=whiser_resposne, audio_path=audio_path
        )

        diarization_result = self.perform_diarize(
            alignment_result=alligned_response, audio_path=audio_path
        )
        diarization_result["language"] = source_lang

        result_dir = self.result_dir.joinpath(cfg.result.transcribe_result_dir_name)
        result_dir.mkdir(parents=True, exist_ok=True)

        # self.write_csv(
        #     result=diarization_result, audio_path=audio_path, save_dir=result_dir
        # )
        writer = get_writer(output_format="srt", output_dir=result_dir)

        writer(
            diarization_result,
            audio_path,
            {"highlight_words": False, "max_line_count": 500, "max_line_width": None},
        )

    @staticmethod
    def add_text_before_extension(path, text):
        # Split the path into root and extension
        root, ext = os.path.splitext(path)

        # Add the text before the extension and return
        return f"{root}{text}{ext}"


# if __name__ == "__main__":
#     audio_pth = "/home/ml/rajan/speech/whisperx_custom/cleaned_pipe/results/Anarchy explained_ Power and humiliation _ John Mearsheimer and Lex Fridman/Anarchy explained_ Power and humiliation _ John Mearsheimer and Lex Fridman.mp3"
#     transcriber = TranscribeAlignDiarize(
#         device="cuda",
#         batch_size=32,
#         compute_type="float16",
#         HF_TOKEN="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",
#         result_dir="/home/ml/rajan/speech/whisperx_custom/cleaned_pipe/results/Anarchy explained_ Power and humiliation _ John Mearsheimer and Lex Fridman",
#         # diarization_model="pyannote/speaker-diarization@2.1",
#     )

#     transcriber.pipe(audio_path=audio_pth, source_lang="en")
