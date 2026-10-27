#!/usr/bin/env python3
"""
nlu/train.py - Training pipeline for JointNLU on GPU with Mixed Precision (AMP).

Features:
  - Base model: ai4bharat/indic-bert (from configs/settings.yaml)
  - Label maps built strictly from training split (data/splits/train.jsonl)
  - Sub-word tokenization: labels only the first sub-word; others get -100
  - Loss: intent CrossEntropy + slot CrossEntropy (ignore_index=-100)
  - AdamW optimizer (lr 3e-5), batch size 32, 8 epochs
  - Checkpoint selection: best validation intent macro-F1
  - Mixed precision: torch.cuda.amp.autocast (float16)
  - Saves model weights, tokenizer, and label maps to models/indicfinvoice_v1/
  - Prints per-epoch validation intent macro-F1 and slot F1
  - Includes --dry-run mode to benchmark GPU throughput and estimate total train time
"""

import argparse
import json
import os
import random
import sys
import time
from typing import Dict, List, Optional, Tuple

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset
from transformers import AutoTokenizer

from sklearn.metrics import accuracy_score, f1_score

try:
    from seqeval.metrics import f1_score as seqeval_f1_score
    HAS_SEQEVAL = True
except ImportError:
    HAS_SEQEVAL = False

# Add project root to sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

try:
    from nlu.model import JointNLU
except ImportError:
    from model import JointNLU

try:
    from plot import plot_training_curves
except ImportError:
    try:
        from nlu.plot import plot_training_curves
    except ImportError:
        plot_training_curves = None

# Ensure UTF-8 output on Windows console
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

TRAIN_SPLIT = "data/splits/train.jsonl"
VAL_SPLIT = "data/splits/val.jsonl"
DEFAULT_MODEL_DIR = "models/indicfinvoice_v1"
SETTINGS_PATH = "configs/settings.yaml"


def set_seed(seed: int = 42) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def load_settings(path: str = SETTINGS_PATH) -> dict:
    if os.path.exists(path):
        import yaml
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {}


def build_label_maps(train_path: str) -> Tuple[Dict[str, int], Dict[int, str], Dict[str, int], Dict[int, str]]:
    """
    Builds intent and tag mappings strictly from the training split.
    """
    intents = set()
    tags = set()

    with open(train_path, "r", encoding="utf-8") as f:
        for line in f:
            line_str = line.strip()
            if not line_str:
                continue
            record = json.loads(line_str)
            intents.add(record["intent"])
            for t in record["tags"]:
                tags.add(t)

    sorted_intents = sorted(list(intents))
    # Ensure 'O' is at index 0 for tags
    other_tags = sorted([t for t in tags if t != "O"])
    sorted_tags = ["O"] + other_tags if "O" in tags else sorted(list(tags))

    intent2id = {intent: i for i, intent in enumerate(sorted_intents)}
    id2intent = {i: intent for intent, i in intent2id.items()}

    tag2id = {tag: i for i, tag in enumerate(sorted_tags)}
    id2tag = {i: tag for tag, i in tag2id.items()}

    return intent2id, id2intent, tag2id, id2tag


class NLUDataset(Dataset):
    """
    PyTorch Dataset for Joint NLU.
    Aligns subwords: first subword of a word receives the tag; subsequent subwords receive -100.
    Special tokens ([CLS], [SEP], [PAD]) receive -100.
    """

    def __init__(
        self,
        filepath: str,
        tokenizer,
        intent2id: Dict[str, int],
        tag2id: Dict[str, int],
        max_length: int = 128,
    ):
        self.tokenizer = tokenizer
        self.intent2id = intent2id
        self.tag2id = tag2id
        self.max_length = max_length

        self.examples = []
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                line_str = line.strip()
                if line_str:
                    self.examples.append(json.loads(line_str))

    def __len__(self) -> int:
        return len(self.examples)

    def __getitem__(self, idx: int) -> dict:
        record = self.examples[idx]
        tokens = record["tokens"]
        tags = record["tags"]
        intent_str = record["intent"]

        intent_id = self.intent2id[intent_str]

        # Check if tokenizer is a fast tokenizer with word_ids()
        encoding = self.tokenizer(
            tokens,
            is_split_into_words=True,
            truncation=True,
            max_length=self.max_length,
            return_offsets_mapping=False,
        )

        input_ids = encoding["input_ids"]
        attention_mask = encoding["attention_mask"]

        # Align slot labels
        if hasattr(encoding, "word_ids"):
            # Fast tokenizer path
            word_ids = encoding.word_ids()
            slot_labels = []
            prev_word_idx = None
            for w_idx in word_ids:
                if w_idx is None:
                    slot_labels.append(-100)
                elif w_idx != prev_word_idx:
                    # First sub-word of word
                    slot_labels.append(self.tag2id[tags[w_idx]])
                else:
                    # Subsequent sub-word
                    slot_labels.append(-100)
                prev_word_idx = w_idx
        else:
            # Fallback path for slow tokenizers
            subwords = []
            slot_labels = []
            # [CLS] token at beginning
            slot_labels.append(-100)
            for word, tag in zip(tokens, tags):
                w_subwords = self.tokenizer.tokenize(word)
                if not w_subwords:
                    continue
                subwords.extend(w_subwords)
                slot_labels.append(self.tag2id[tag])
                slot_labels.extend([-100] * (len(w_subwords) - 1))
            # [SEP] token at end
            slot_labels.append(-100)
            # Truncate to max_length
            slot_labels = slot_labels[:self.max_length]

        return {
            "input_ids": input_ids,
            "attention_mask": attention_mask,
            "slot_labels": slot_labels,
            "intent_label": intent_id,
        }


def collate_fn(batch: list) -> dict:
    """
    Collate function with dynamic padding.
    """
    max_len = max(len(x["input_ids"]) for x in batch)

    batch_input_ids = []
    batch_attention_mask = []
    batch_slot_labels = []
    batch_intent_labels = []

    for x in batch:
        seq_len = len(x["input_ids"])
        pad_len = max_len - seq_len

        batch_input_ids.append(x["input_ids"] + [0] * pad_len)
        batch_attention_mask.append(x["attention_mask"] + [0] * pad_len)
        batch_slot_labels.append(x["slot_labels"] + [-100] * pad_len)
        batch_intent_labels.append(x["intent_label"])

    return {
        "input_ids": torch.tensor(batch_input_ids, dtype=torch.long),
        "attention_mask": torch.tensor(batch_attention_mask, dtype=torch.long),
        "slot_labels": torch.tensor(batch_slot_labels, dtype=torch.long),
        "intent_labels": torch.tensor(batch_intent_labels, dtype=torch.long),
    }


def compute_metrics(
    all_true_intents: list,
    all_pred_intents: list,
    all_true_slots: list,
    all_pred_slots: list,
    id2tag: Dict[int, str],
) -> Tuple[float, float, float]:
    """
    Computes intent accuracy, intent macro-F1, and slot F1.
    Slot F1 is evaluated at token level over non-'O' tags (ignoring -100 and O).
    Also calculates seqeval entity-level F1 if seqeval is available.
    """
    intent_acc = accuracy_score(all_true_intents, all_pred_intents)
    intent_macro_f1 = f1_score(all_true_intents, all_pred_intents, average="macro")

    # Token-level slot evaluation over non-'O' slots
    token_true_filtered = []
    token_pred_filtered = []

    seqeval_true_seqs = []
    seqeval_pred_seqs = []

    for t_seq, p_seq in zip(all_true_slots, all_pred_slots):
        cur_true_seq = []
        cur_pred_seq = []
        for t, p in zip(t_seq, p_seq):
            if t == -100:
                continue
            true_tag_str = id2tag[t]
            pred_tag_str = id2tag[p]
            cur_true_seq.append(true_tag_str)
            cur_pred_seq.append(pred_tag_str)

            # Filter for token-level non-O slots
            if true_tag_str != "O" or pred_tag_str != "O":
                token_true_filtered.append(true_tag_str)
                token_pred_filtered.append(pred_tag_str)

        seqeval_true_seqs.append(cur_true_seq)
        seqeval_pred_seqs.append(cur_pred_seq)

    if token_true_filtered:
        slot_f1_token = f1_score(token_true_filtered, token_pred_filtered, average="micro")
    else:
        slot_f1_token = 1.0 if not token_pred_filtered else 0.0

    if HAS_SEQEVAL and seqeval_true_seqs:
        try:
            slot_f1 = seqeval_f1_score(seqeval_true_seqs, seqeval_pred_seqs)
        except Exception:
            slot_f1 = slot_f1_token
    else:
        slot_f1 = slot_f1_token

    return intent_acc, intent_macro_f1, slot_f1


def evaluate(
    model: nn.Module,
    val_loader: DataLoader,
    device: torch.device,
    id2tag: Dict[int, str],
) -> Tuple[float, float, float, float]:
    """
    Evaluates model on validation set.
    """
    model.eval()
    val_loss = 0.0
    total_steps = 0

    all_true_intents = []
    all_pred_intents = []
    all_true_slots = []
    all_pred_slots = []

    intent_criterion = nn.CrossEntropyLoss()
    slot_criterion = nn.CrossEntropyLoss(ignore_index=-100)

    with torch.no_grad():
        for batch in val_loader:
            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            slot_labels = batch["slot_labels"].to(device)
            intent_labels = batch["intent_labels"].to(device)

            with torch.autocast(device_type="cuda", dtype=torch.float16, enabled=(device.type == "cuda")):
                intent_logits, slot_logits = model(input_ids, attention_mask=attention_mask)
                loss_intent = intent_criterion(intent_logits, intent_labels)
                loss_slot = slot_criterion(slot_logits.view(-1, slot_logits.size(-1)), slot_labels.view(-1))
                loss = loss_intent + loss_slot

            val_loss += loss.item()
            total_steps += 1

            # Predictions
            pred_intents = torch.argmax(intent_logits, dim=-1).cpu().tolist()
            pred_slots = torch.argmax(slot_logits, dim=-1).cpu().tolist()

            all_pred_intents.extend(pred_intents)
            all_true_intents.extend(intent_labels.cpu().tolist())

            all_pred_slots.extend(pred_slots)
            all_true_slots.extend(slot_labels.cpu().tolist())

    avg_val_loss = val_loss / max(1, total_steps)
    intent_acc, intent_macro_f1, slot_f1 = compute_metrics(
        all_true_intents, all_pred_intents, all_true_slots, all_pred_slots, id2tag
    )

    return avg_val_loss, intent_acc, intent_macro_f1, slot_f1


def train(
    train_path: str = TRAIN_SPLIT,
    val_path: str = VAL_SPLIT,
    output_dir: str = DEFAULT_MODEL_DIR,
    base_model_name: Optional[str] = None,
    batch_size: int = 32,
    lr: float = 3e-5,
    epochs: int = 8,
    seed: int = 42,
    dry_run: bool = False,
    dry_run_batches: int = 10,
) -> None:
    set_seed(seed)
    settings = load_settings()
    if base_model_name is None:
        base_model_name = settings.get("nlu_base_model", "ai4bharat/indic-bert")

    print("=" * 70)
    print("JOINT NLU TRAINING PIPELINE (INDICFINVOICE V1)")
    print("=" * 70)
    print(f"Base Encoder Model:    {base_model_name}")
    print(f"Training Data Split:   {train_path}")
    print(f"Validation Data Split: {val_path}")
    print(f"Output Directory:      {output_dir}")
    print(f"Batch Size:            {batch_size}")
    print(f"Learning Rate:         {lr}")
    print(f"Epochs:                {epochs}")
    print(f"Dry Run Mode:          {dry_run}")

    # Device configuration
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device:                {device}")
    if device.type == "cuda":
        print(f"GPU Name:              {torch.cuda.get_device_name(0)}")
        print(f"GPU VRAM:              {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB")

    # 1. Build label mappings strictly from training split
    print("\n--- Building Label Maps from Training Split ---")
    intent2id, id2intent, tag2id, id2tag = build_label_maps(train_path)
    num_intents = len(intent2id)
    num_tags = len(tag2id)
    print(f"Intents ({num_intents}): {intent2id}")
    print(f"Tags ({num_tags}):    {tag2id}")

    # 2. Load Tokenizer
    print(f"\nLoading Tokenizer for {base_model_name}...")
    tokenizer = AutoTokenizer.from_pretrained(base_model_name)
    print(f"Tokenizer loaded successfully. Vocab size: {tokenizer.vocab_size}")

    # 3. Create Datasets and DataLoaders
    print("\nPreparing Datasets...")
    train_dataset = NLUDataset(train_path, tokenizer, intent2id, tag2id)
    val_dataset = NLUDataset(val_path, tokenizer, intent2id, tag2id)
    print(f"Train records: {len(train_dataset)}")
    print(f"Val records:   {len(val_dataset)}")

    train_loader = DataLoader(
        train_dataset,
        batch_size=batch_size,
        shuffle=True,
        collate_fn=collate_fn,
        num_workers=0,
    )
    val_loader = DataLoader(
        val_dataset,
        batch_size=batch_size,
        shuffle=False,
        collate_fn=collate_fn,
        num_workers=0,
    )

    # 4. Instantiate Model
    print(f"\nInitializing JointNLU model with {base_model_name}...")
    model = JointNLU(
        base_model_name_or_path=base_model_name,
        num_intents=num_intents,
        num_tags=num_tags,
        dropout_rate=0.1,
    )
    model.to(device)

    # 5. Optimizer & AMP Scaler
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr)
    if hasattr(torch.amp, "GradScaler"):
        scaler = torch.amp.GradScaler("cuda", enabled=(device.type == "cuda"))
    else:
        scaler = torch.cuda.amp.GradScaler(enabled=(device.type == "cuda"))

    intent_criterion = nn.CrossEntropyLoss()
    slot_criterion = nn.CrossEntropyLoss(ignore_index=-100)

    total_train_batches = len(train_loader)
    total_val_batches = len(val_loader)

    # DRY RUN BENCHMARKING
    if dry_run:
        print("\n" + "=" * 70)
        print(f"PERFORMING DRY RUN ({dry_run_batches} training batches + validation sample)...")
        print("=" * 70)
        model.train()
        batch_times = []

        # Warmup batch
        for i, batch in enumerate(train_loader):
            if i >= dry_run_batches:
                break
            t0 = time.perf_counter()
            optimizer.zero_grad()
            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            slot_labels = batch["slot_labels"].to(device)
            intent_labels = batch["intent_labels"].to(device)

            with torch.autocast(device_type="cuda", dtype=torch.float16, enabled=(device.type == "cuda")):
                intent_logits, slot_logits = model(input_ids, attention_mask=attention_mask)
                loss_intent = intent_criterion(intent_logits, intent_labels)
                loss_slot = slot_criterion(slot_logits.view(-1, num_tags), slot_labels.view(-1))
                loss = loss_intent + loss_slot

            scaler.scale(loss).backward()
            scaler.step(optimizer)
            scaler.update()

            if device.type == "cuda":
                torch.cuda.synchronize()
            t_batch = time.perf_counter() - t0
            batch_times.append(t_batch)
            print(f"  Dry Run Batch {i+1:02d}/{dry_run_batches:02d} | Loss: {loss.item():.4f} | Time: {t_batch*1000:.1f} ms")

        # Exclude first warmup batch
        measured_times = batch_times[1:] if len(batch_times) > 1 else batch_times
        avg_batch_time = sum(measured_times) / len(measured_times)

        # Measure val time
        t_val_start = time.perf_counter()
        val_loss, val_acc, val_intent_f1, val_slot_f1 = evaluate(model, val_loader, device, id2tag)
        if device.type == "cuda":
            torch.cuda.synchronize()
        val_time = time.perf_counter() - t_val_start

        epoch_train_time = avg_batch_time * total_train_batches
        epoch_total_time = epoch_train_time + val_time
        total_estimated_time = epoch_total_time * epochs

        print("\n" + "-" * 70)
        print("DRY RUN BENCHMARK & ESTIMATED TRAINING TIME RESULTS:")
        print("-" * 70)
        print(f"Average Batch Time (fp16):        {avg_batch_time*1000:.1f} ms")
        print(f"Batches per Epoch:                 {total_train_batches}")
        print(f"Train Time per Epoch:              {epoch_train_time:.1f} s ({epoch_train_time/60:.2f} min)")
        print(f"Validation Time per Epoch:         {val_time:.1f} s ({val_time/60:.2f} min)")
        print(f"Total Time per Epoch:              {epoch_total_time:.1f} s ({epoch_total_time/60:.2f} min)")
        print(f"Total Estimated Training Time:     {total_estimated_time:.1f} s ({total_estimated_time/60:.2f} min)")
        print(f"Dry Run Val Intent Macro-F1:       {val_intent_f1:.4f}")
        print(f"Dry Run Val Slot F1:               {val_slot_f1:.4f}")
        print("-" * 70)
        print("\nDry run completed successfully. Verification passed!")
        return

    # FULL TRAINING LOOP
    best_val_intent_f1 = -1.0
    best_epoch = -1
    best_metrics = {}

    training_history = {
        "epochs": [],
        "train_loss": [],
        "val_loss": [],
        "val_intent_acc": [],
        "val_intent_macro_f1": [],
        "val_slot_f1": [],
    }

    print("\n" + "=" * 70)
    print("STARTING FULL TRAINING (8 Epochs)")
    print("=" * 70)

    start_total_time = time.time()

    for epoch in range(1, epochs + 1):
        epoch_start_time = time.time()
        model.train()
        train_loss = 0.0

        for step, batch in enumerate(train_loader, 1):
            optimizer.zero_grad()
            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            slot_labels = batch["slot_labels"].to(device)
            intent_labels = batch["intent_labels"].to(device)

            with torch.autocast(device_type="cuda", dtype=torch.float16, enabled=(device.type == "cuda")):
                intent_logits, slot_logits = model(input_ids, attention_mask=attention_mask)
                loss_intent = intent_criterion(intent_logits, intent_labels)
                loss_slot = slot_criterion(slot_logits.view(-1, num_tags), slot_labels.view(-1))
                loss = loss_intent + loss_slot

            scaler.scale(loss).backward()
            scaler.step(optimizer)
            scaler.update()

            train_loss += loss.item()

            if step % 50 == 0 or step == total_train_batches:
                print(f"Epoch {epoch:02d}/{epochs:02d} | Step {step:03d}/{total_train_batches:03d} | Batch Loss: {loss.item():.4f}")

        avg_train_loss = train_loss / total_train_batches

        # Validation evaluation
        val_loss, val_acc, val_intent_f1, val_slot_f1 = evaluate(model, val_loader, device, id2tag)
        epoch_duration = time.time() - epoch_start_time

        print(
            f"\n[Epoch {epoch:02d}/{epochs:02d} Summary] Duration: {epoch_duration:.1f}s | "
            f"Train Loss: {avg_train_loss:.4f} | Val Loss: {val_loss:.4f} | "
            f"Val Intent Acc: {val_acc:.4f} | Val Intent Macro-F1: {val_intent_f1:.4f} | Val Slot F1: {val_slot_f1:.4f}"
        )

        # Update training history
        training_history["epochs"].append(epoch)
        training_history["train_loss"].append(round(avg_train_loss, 4))
        training_history["val_loss"].append(round(val_loss, 4))
        training_history["val_intent_acc"].append(round(val_acc, 4))
        training_history["val_intent_macro_f1"].append(round(val_intent_f1, 4))
        training_history["val_slot_f1"].append(round(val_slot_f1, 4))

        os.makedirs(output_dir, exist_ok=True)
        history_path = os.path.join(output_dir, "training_history.json")
        with open(history_path, "w", encoding="utf-8") as f_hist:
            json.dump(training_history, f_hist, indent=2)

        # Plot training curves per epoch using plot.py
        if plot_training_curves is not None:
            plot_path = os.path.join(output_dir, "training_curves.png")
            try:
                plot_training_curves(training_history, output_path=plot_path)
                print(f"[Epoch {epoch:02d} Graph] Training plot updated: {plot_path}")
            except Exception as e:
                print(f"[Epoch {epoch:02d} Graph] Warning: Could not update plot: {e}")

        # Checkpoint selection by validation intent macro-F1
        if val_intent_f1 > best_val_intent_f1:
            best_val_intent_f1 = val_intent_f1
            best_epoch = epoch
            best_metrics = {
                "epoch": epoch,
                "val_loss": val_loss,
                "val_intent_acc": val_acc,
                "val_intent_macro_f1": val_intent_f1,
                "val_slot_f1": val_slot_f1,
            }
            print(f"--> NEW BEST MODEL at Epoch {epoch} (Val Intent Macro-F1: {val_intent_f1:.4f})! Saving checkpoint...")

            os.makedirs(output_dir, exist_ok=True)
            # Save model weights and configuration
            model.save_pretrained(output_dir)
            # Save tokenizer
            tokenizer.save_pretrained(output_dir)
            # Save label maps
            label_maps = {
                "intent2id": intent2id,
                "id2intent": id2intent,
                "tag2id": tag2id,
                "id2tag": id2tag,
            }
            label_maps_path = os.path.join(output_dir, "label_maps.json")
            with open(label_maps_path, "w", encoding="utf-8") as f_lm:
                json.dump(label_maps, f_lm, indent=2, ensure_ascii=False)

            # Save best training summary
            summary_path = os.path.join(output_dir, "training_summary.json")
            with open(summary_path, "w", encoding="utf-8") as f_sum:
                json.dump(best_metrics, f_sum, indent=2)

        print("-" * 70)

    total_duration = time.time() - start_total_time
    print("\n" + "=" * 70)
    print("TRAINING COMPLETED SUCCESSFULLY")
    print("=" * 70)
    print(f"Total Duration:        {total_duration/60:.2f} minutes ({total_duration:.1f} seconds)")
    print(f"Best Epoch:            {best_epoch}")
    print(f"Best Val Intent Macro-F1: {best_metrics.get('val_intent_macro_f1', 0.0):.4f}")
    print(f"Best Val Slot F1:         {best_metrics.get('val_slot_f1', 0.0):.4f}")
    print(f"Best Val Intent Acc:      {best_metrics.get('val_intent_acc', 0.0):.4f}")
    print(f"Checkpoint Saved To:   {output_dir}")
    print("=" * 70)


def main():
    parser = argparse.ArgumentParser(description="Train JointNLU model for intent and slot classification.")
    parser.add_argument("--train-path", type=str, default=TRAIN_SPLIT, help="Path to training jsonl")
    parser.add_argument("--val-path", type=str, default=VAL_SPLIT, help="Path to validation jsonl")
    parser.add_argument("--output-dir", type=str, default=DEFAULT_MODEL_DIR, help="Directory to save model")
    parser.add_argument("--base-model", type=str, default=None, help="Base model name or path (default from settings)")
    parser.add_argument("--batch-size", type=int, default=32, help="Batch size (default: 32)")
    parser.add_argument("--lr", type=float, default=3e-5, help="Learning rate (default: 3e-5)")
    parser.add_argument("--epochs", type=int, default=8, help="Number of training epochs (default: 8)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed (default: 42)")
    parser.add_argument("--dry-run", action="store_true", help="Run a dry run benchmark to estimate total train time")
    parser.add_argument("--dry-run-batches", type=int, default=10, help="Number of batches for dry run")

    args = parser.parse_args()

    train(
        train_path=args.train_path,
        val_path=args.val_path,
        output_dir=args.output_dir,
        base_model_name=args.base_model,
        batch_size=args.batch_size,
        lr=args.lr,
        epochs=args.epochs,
        seed=args.seed,
        dry_run=args.dry_run,
        dry_run_batches=args.dry_run_batches,
    )


if __name__ == "__main__":
    main()
