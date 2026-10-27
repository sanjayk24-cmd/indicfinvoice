#!/usr/bin/env python3
"""
nlu/model.py - JointNLU Model with Intent and Slot Classification Heads.

Base model: ai4bharat/indic-bert (or configurable encoder).
Architecture:
  - Base Transformer Encoder (e.g., AlbertModel for IndicBERT)
  - Dropout layer (default 0.1)
  - Intent Head: Linear(hidden_size, num_intents) applied to the CLS token (token 0)
  - Slot Head: Linear(hidden_size, num_tags) applied to every token representation
"""

import json
import os
from typing import Optional, Tuple
import torch
import torch.nn as nn
from transformers import AutoConfig, AutoModel


class JointNLU(nn.Module):
    """
    Joint Intent Classification and Slot Filling model.
    """

    def __init__(
        self,
        base_model_name_or_path: str = "ai4bharat/indic-bert",
        num_intents: int = 5,
        num_tags: int = 8,
        dropout_rate: float = 0.1,
    ):
        super().__init__()
        self.base_model_name_or_path = base_model_name_or_path
        self.num_intents = num_intents
        self.num_tags = num_tags
        self.dropout_rate = dropout_rate

        self.encoder = AutoModel.from_pretrained(base_model_name_or_path)
        self.hidden_size = self.encoder.config.hidden_size

        self.dropout = nn.Dropout(dropout_rate)
        self.intent_head = nn.Linear(self.hidden_size, num_intents)
        self.slot_head = nn.Linear(self.hidden_size, num_tags)

    def forward(
        self,
        input_ids: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None,
        token_type_ids: Optional[torch.Tensor] = None,
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Forward pass.
        Args:
            input_ids: (batch_size, seq_len)
            attention_mask: (batch_size, seq_len)
            token_type_ids: (batch_size, seq_len) optional
        Returns:
            intent_logits: (batch_size, num_intents)
            slot_logits: (batch_size, seq_len, num_tags)
        """
        encoder_kwargs = {}
        if token_type_ids is not None:
            # Only pass token_type_ids if the underlying model supports it
            if "token_type_ids" in getattr(self.encoder, "forward", lambda: None).__code__.co_varnames:
                encoder_kwargs["token_type_ids"] = token_type_ids

        outputs = self.encoder(
            input_ids=input_ids,
            attention_mask=attention_mask,
            **encoder_kwargs,
        )

        # sequence_output: (batch_size, seq_len, hidden_size)
        sequence_output = outputs[0]
        sequence_output = self.dropout(sequence_output)

        # CLS token representation is at index 0
        cls_token = sequence_output[:, 0, :]
        intent_logits = self.intent_head(cls_token)

        # Slot classification on all tokens
        slot_logits = self.slot_head(sequence_output)

        return intent_logits, slot_logits

    def save_pretrained(self, save_directory: str) -> None:
        """
        Saves model weights and configuration to save_directory.
        """
        os.makedirs(save_directory, exist_ok=True)
        config = {
            "base_model_name_or_path": self.base_model_name_or_path,
            "num_intents": self.num_intents,
            "num_tags": self.num_tags,
            "dropout_rate": self.dropout_rate,
            "hidden_size": self.hidden_size,
        }
        config_path = os.path.join(save_directory, "model_config.json")
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)

        weights_path = os.path.join(save_directory, "pytorch_model.bin")
        torch.save(self.state_dict(), weights_path)

    @classmethod
    def from_pretrained(cls, save_directory: str) -> "JointNLU":
        """
        Loads JointNLU from save_directory.
        """
        config_path = os.path.join(save_directory, "model_config.json")
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)

        model = cls(
            base_model_name_or_path=config["base_model_name_or_path"],
            num_intents=config["num_intents"],
            num_tags=config["num_tags"],
            dropout_rate=config.get("dropout_rate", 0.1),
        )

        weights_path = os.path.join(save_directory, "pytorch_model.bin")
        if not os.path.exists(weights_path):
            raise FileNotFoundError(f"Model weights not found: {weights_path}")

        state_dict = torch.load(weights_path, map_location="cpu")
        model.load_state_dict(state_dict)
        return model
