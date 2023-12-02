import torch
from easydict import EasyDict as edict

c = edict()

# audio
c.audio = edict()
c.audio.split_length_minutes = 5
c.audio.split_length_seconds = 300


# model
c.model = edict()
c.model.device = "cuda" if torch.cuda.is_available() else "cpu"
c.model.batch_size = 32
c.model.compute_type = "float16"
c.model.HF_TOKEN = "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"


# result
c.result = edict()
c.result.file_name = "result.srt"
c.result.transcribe_result_dir_name = "transcribe_results"


# ui
c.ui = edict()
c.ui.uploaded_save_pth = "uploaded"
cfg = c
