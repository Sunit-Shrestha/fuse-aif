"""ONNX Runtime-backed inference for the AG_NEWS topic-classifier LSTM.

Deliberately has no PyTorch/transformers dependency -- the backend container
only needs onnxruntime, keeping the production image lean (torch stays in
train/, which never ships to production).
"""
import json
import re
from typing import List

import numpy as np
import onnxruntime as ort

from . import config


def tokenizer(text: str) -> List[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


class RouterModel:
    def __init__(self):
        with open(config.VOCAB_PATH) as f:
            vocab = json.load(f)
        self.stoi = vocab["stoi"]
        self.unk_idx = vocab["unk_idx"]
        self.pad_idx = vocab["pad_idx"]
        self.class_names = vocab["class_names"]
        self.session = ort.InferenceSession(str(config.ONNX_MODEL_PATH), providers=["CPUExecutionProvider"])

    def _numericalize(self, text: str) -> List[int]:
        return [self.stoi.get(tok, self.unk_idx) for tok in tokenizer(text)] or [self.unk_idx]

    def _pad_batch(self, sequences: List[List[int]]) -> np.ndarray:
        max_len = max(len(s) for s in sequences)
        return np.array(
            [s + [self.pad_idx] * (max_len - len(s)) for s in sequences], dtype=np.int64
        )

    def predict_one(self, text: str) -> dict:
        return self.predict_batch([text])[0]

    def predict_batch(self, texts: List[str]) -> List[dict]:
        sequences = [self._numericalize(t) for t in texts]
        batch = self._pad_batch(sequences)
        logits = self.session.run(None, {"input_ids": batch})[0]
        probs = _softmax(logits)
        results = []
        for row in probs:
            idx = int(np.argmax(row))
            results.append({
                "category": self.class_names[idx],
                "confidence": float(row[idx]),
                "probabilities": {c: float(p) for c, p in zip(self.class_names, row)},
            })
        return results


def _softmax(logits: np.ndarray) -> np.ndarray:
    exp = np.exp(logits - logits.max(axis=-1, keepdims=True))
    return exp / exp.sum(axis=-1, keepdims=True)
