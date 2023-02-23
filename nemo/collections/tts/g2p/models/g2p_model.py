# Copyright (c) 2022, NVIDIA CORPORATION & AFFILIATES.  All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
from abc import ABC
from typing import List, Optional

import torch
from omegaconf import DictConfig
from tqdm import tqdm

from nemo.core.classes import ModelPT
from nemo.utils import logging, model_utils

__all__ = ["G2PModel"]


class G2PModel(ModelPT, ABC):
    @torch.no_grad()
    def convert_graphemes_to_phonemes(
        self,
        manifest_filepath: str,
        output_manifest_filepath: str,
        grapheme_field: str = "text_graphemes",
        batch_size: int = 32,
        num_workers: int = 0,
        pred_field: Optional[str] = "pred_text",
    ) -> List[str]:

        """
        Main function for Inference. Converts grapheme entries from the manifest "graheme_field" to phonemes
        Args:
            manifest_filepath: Path to .json manifest file
            output_manifest_filepath: Path to .json manifest file to save predictions, will be saved in "target_field"
            grapheme_field: name of the field in manifest_filepath for input grapheme text
            pred_field:  name of the field in the output_file to save predictions
            batch_size: int = 32 # Batch size to use for inference
            num_workers: int = 0 # Number of workers to use for DataLoader during inference

        Returns: Predictions generated by the model
        """
        config = {
            "manifest_filepath": manifest_filepath,
            "grapheme_field": grapheme_field,
            "drop_last": False,
            "shuffle": False,
            "batch_size": batch_size,
            "num_workers": num_workers,
        }

        all_preds = self._infer(DictConfig(config))
        with open(manifest_filepath, "r") as f_in:
            with open(output_manifest_filepath, 'w', encoding="utf-8") as f_out:
                for i, line in tqdm(enumerate(f_in)):
                    line = json.loads(line)
                    line[pred_field] = all_preds[i]
                    f_out.write(json.dumps(line, ensure_ascii=False) + "\n")

        logging.info(f"Predictions saved to {output_manifest_filepath}.")
        return all_preds

    @classmethod
    def list_available_models(cls) -> 'List[PretrainedModelInfo]':
        """
        This method returns a list of pre-trained model which can be instantiated directly from NVIDIA's NGC cloud.
        Returns:
            List of available pre-trained models.
        """
        # recursively walk the subclasses to generate pretrained model info
        list_of_models = model_utils.resolve_subclass_pretrained_model_info(cls)
        return list_of_models