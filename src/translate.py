from pathlib import Path

import pandas as pd
from tqdm.auto import tqdm
from transformers import MBartForConditionalGeneration, MBart50TokenizerFast

from src.config import cfg
from src.model_mappings import mbart_mapp


class Translator:
    def __init__(self) -> None:
        self.model = MBartForConditionalGeneration.from_pretrained(
            "facebook/mbart-large-50-many-to-many-mmt"
        ).to(cfg.model.device)
        self.tokenizer = MBart50TokenizerFast.from_pretrained(
            "facebook/mbart-large-50-many-to-many-mmt"
        )

    def translate_csv(self, csv_pth, source_language, destination_language):
        assert source_language in list(
            mbart_mapp.keys()
        ), f"Source Language {source_language} cannot be converted to {destination_language}"

        assert destination_language in list(
            mbart_mapp.keys()
        ), f"{source_language} cannot be converted to {destination_language}"

        self.tokenizer.src_lang = mbart_mapp[source_language]

        df = pd.read_csv(csv_pth)

        translated_ = []

        source_text = df["Text"].to_list()

        for x in tqdm(source_text):
            encoded_source = self.tokenizer(x, return_tensors="pt").to(cfg.model.device)

            generated_tokens = self.model.generate(
                **encoded_source,
                forced_bos_token_id=self.tokenizer.lang_code_to_id[
                    str(mbart_mapp[destination_language])
                ],
            )
            result = self.tokenizer.batch_decode(
                generated_tokens, skip_special_tokens=True
            )

            translated_.append(result[-1])

        df["Text"] = translated_

        translated_csv_pth = Path(csv_pth).parent.joinpath(
            f"result_{mbart_mapp[destination_language]}.csv"
        )
        df.drop(df.filter(regex="Unnamed"), axis=1, inplace=True)
        df.to_csv(translated_csv_pth)

        return translated_csv_pth
