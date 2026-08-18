"""
Trains the AG_NEWS topic-classifier LSTM (same architecture as Week 13's
SimpleLSTM) on the FULL training split instead of a 5k-row toy subset, with a
min-frequency-filtered vocabulary so the model is worth productionizing.

Saves two artifacts into ../artifacts/:
  - model.pt    (state_dict + architecture hyperparams)
  - vocab.json  (stoi mapping + special-token indices + model hyperparams)
"""
import json
import re
import time
from collections import Counter
from pathlib import Path

import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from datasets import load_dataset

ARTIFACTS_DIR = Path(__file__).resolve().parent.parent / "artifacts"
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
CLASS_NAMES = ["World", "Sports", "Business", "Sci/Tech"]

EMBED_DIM = 64
HIDDEN_DIM = 128
MIN_FREQ = 3
MAX_VOCAB_SIZE = 30000
BATCH_SIZE = 64
EPOCHS = 8
LR = 0.001
GRAD_CLIP_NORM = 1.0


def tokenizer(text):
    return re.findall(r"[a-z0-9]+", text.lower())


class SimpleLSTM(nn.Module):
    def __init__(self, vocab_size, embed_dim, hidden_dim, num_classes, pad_idx):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, embed_dim, padding_idx=pad_idx)
        self.lstm = nn.LSTM(embed_dim, hidden_dim, batch_first=True)
        self.fc = nn.Linear(hidden_dim, num_classes)

    def forward(self, text):
        embedded = self.embedding(text)
        _, (hidden, _) = self.lstm(embedded)
        return self.fc(hidden[-1])


def build_vocab(train_data, min_freq, max_size):
    counter = Counter()
    for example in train_data:
        counter.update(tokenizer(example["text"]))
    # Keep the most frequent tokens that clear min_freq, capped at max_size.
    kept = [w for w, c in counter.most_common() if c >= min_freq][:max_size]
    itos = ["<unk>", "<pad>"] + kept
    stoi = {w: i for i, w in enumerate(itos)}
    return stoi, len(itos)


def main():
    print(f"Using device: {DEVICE}")
    t0 = time.time()

    ag_news = load_dataset("fancyzhx/ag_news")
    train_data, test_data = ag_news["train"], ag_news["test"]
    print(f"Train rows: {len(train_data)} | Test rows: {len(test_data)} ({time.time()-t0:.1f}s)")

    stoi, vocab_size = build_vocab(train_data, MIN_FREQ, MAX_VOCAB_SIZE)
    unk_idx, pad_idx = stoi["<unk>"], stoi["<pad>"]
    print(f"Vocab size (min_freq={MIN_FREQ}, cap={MAX_VOCAB_SIZE}): {vocab_size:,}")

    def numericalize(text):
        return [stoi.get(tok, unk_idx) for tok in tokenizer(text)]

    def collate_batch(batch):
        labels = torch.tensor([ex["label"] for ex in batch], dtype=torch.int64)
        texts = [torch.tensor(numericalize(ex["text"]), dtype=torch.int64) for ex in batch]
        padded = nn.utils.rnn.pad_sequence(texts, batch_first=True, padding_value=pad_idx)
        return padded, labels

    train_loader = DataLoader(train_data, batch_size=BATCH_SIZE, shuffle=True, collate_fn=collate_batch)
    test_loader = DataLoader(test_data, batch_size=BATCH_SIZE, shuffle=False, collate_fn=collate_batch)

    model = SimpleLSTM(vocab_size, EMBED_DIM, HIDDEN_DIM, len(CLASS_NAMES), pad_idx).to(DEVICE)
    print(f"Model parameters: {sum(p.numel() for p in model.parameters()):,}")

    optimizer = torch.optim.Adam(model.parameters(), lr=LR)
    criterion = nn.CrossEntropyLoss()

    for epoch in range(EPOCHS):
        model.train()
        epoch_start = time.time()
        total_loss, correct, total = 0.0, 0, 0
        for texts, labels in train_loader:
            texts, labels = texts.to(DEVICE), labels.to(DEVICE)
            optimizer.zero_grad()
            preds = model(texts)
            loss = criterion(preds, labels)
            loss.backward()
            # LSTMs are prone to exploding gradients early in training, which manifests
            # as the loss/accuracy plateauing near chance for several epochs before an
            # unstable jump -- clipping keeps updates well-behaved from the first step.
            torch.nn.utils.clip_grad_norm_(model.parameters(), GRAD_CLIP_NORM)
            optimizer.step()
            total_loss += loss.item()
            correct += (preds.argmax(1) == labels).sum().item()
            total += labels.size(0)
        train_acc = correct / total

        model.eval()
        val_correct, val_total = 0, 0
        with torch.no_grad():
            for texts, labels in test_loader:
                texts, labels = texts.to(DEVICE), labels.to(DEVICE)
                preds = model(texts)
                val_correct += (preds.argmax(1) == labels).sum().item()
                val_total += labels.size(0)
        val_acc = val_correct / val_total
        print(f"Epoch {epoch+1}/{EPOCHS} | Train Acc: {train_acc:.1%} | Test Acc: {val_acc:.1%} "
              f"| {time.time()-epoch_start:.1f}s")

    torch.save({
        "model_state_dict": model.state_dict(),
        "vocab_size": vocab_size,
        "embed_dim": EMBED_DIM,
        "hidden_dim": HIDDEN_DIM,
        "num_classes": len(CLASS_NAMES),
        "pad_idx": pad_idx,
    }, ARTIFACTS_DIR / "model.pt")

    with open(ARTIFACTS_DIR / "vocab.json", "w") as f:
        json.dump({
            "stoi": stoi,
            "unk_idx": unk_idx,
            "pad_idx": pad_idx,
            "class_names": CLASS_NAMES,
        }, f)

    with open(ARTIFACTS_DIR / "metrics.json", "w") as f:
        json.dump({"final_test_accuracy": val_acc, "vocab_size": vocab_size,
                    "epochs": EPOCHS, "total_train_seconds": time.time() - t0}, f, indent=2)

    print(f"Saved model.pt, vocab.json, metrics.json to {ARTIFACTS_DIR} ({time.time()-t0:.1f}s total)")


if __name__ == "__main__":
    main()
