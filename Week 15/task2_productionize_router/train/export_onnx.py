"""
Exports the trained LSTM (artifacts/model.pt) to ONNX, verifies numerical
parity against the PyTorch model, and applies dynamic int8 quantization for
faster CPU inference. Run after train_lstm.py:

    python export_onnx.py
"""
import json
import time
from pathlib import Path

import numpy as np
import onnxruntime as ort
import torch
import torch.nn as nn
from onnxruntime.quantization import QuantType, quantize_dynamic

ARTIFACTS_DIR = Path(__file__).resolve().parent.parent / "artifacts"


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


def main():
    ckpt = torch.load(ARTIFACTS_DIR / "model.pt", map_location="cpu")
    model = SimpleLSTM(
        ckpt["vocab_size"], ckpt["embed_dim"], ckpt["hidden_dim"], ckpt["num_classes"], ckpt["pad_idx"]
    )
    model.load_state_dict(ckpt["model_state_dict"])
    model.eval()

    dummy_input = torch.randint(0, ckpt["vocab_size"], (1, 16), dtype=torch.int64)
    onnx_path = ARTIFACTS_DIR / "model.onnx"

    torch.onnx.export(
        model,
        (dummy_input,),
        str(onnx_path),
        input_names=["input_ids"],
        output_names=["logits"],
        dynamic_axes={"input_ids": {0: "batch", 1: "seq_len"}, "logits": {0: "batch"}},
        opset_version=17,
    )
    print(f"Exported ONNX model to {onnx_path}")

    # Verify parity between PyTorch and ONNX Runtime on a fresh random batch.
    test_input = torch.randint(0, ckpt["vocab_size"], (4, 24), dtype=torch.int64)
    with torch.no_grad():
        torch_out = model(test_input).numpy()

    session = ort.InferenceSession(str(onnx_path), providers=["CPUExecutionProvider"])
    onnx_out = session.run(None, {"input_ids": test_input.numpy()})[0]

    max_diff = np.abs(torch_out - onnx_out).max()
    print(f"Max abs difference between PyTorch and ONNX outputs: {max_diff:.6f}")
    assert max_diff < 1e-3, "ONNX export does not match PyTorch model output"

    # Dynamic int8 quantization -- weight-only, no calibration data needed, and
    # is well supported for the LSTM/Linear ops this model uses.
    quantized_path = ARTIFACTS_DIR / "model.quant.onnx"
    quantize_dynamic(str(onnx_path), str(quantized_path), weight_type=QuantType.QInt8)
    print(f"Quantized ONNX model saved to {quantized_path} "
          f"({onnx_path.stat().st_size/1e6:.1f}MB -> {quantized_path.stat().st_size/1e6:.1f}MB)")

    # Quick latency comparison: PyTorch eager vs. ONNX Runtime vs. quantized ONNX Runtime.
    quant_session = ort.InferenceSession(str(quantized_path), providers=["CPUExecutionProvider"])
    single_input = torch.randint(0, ckpt["vocab_size"], (1, 20), dtype=torch.int64)

    def bench(fn, n=50):
        for _ in range(5):
            fn()
        t0 = time.time()
        for _ in range(n):
            fn()
        return (time.time() - t0) / n * 1000

    torch_ms = bench(lambda: model(single_input))
    onnx_ms = bench(lambda: session.run(None, {"input_ids": single_input.numpy()}))
    quant_ms = bench(lambda: quant_session.run(None, {"input_ids": single_input.numpy()}))

    print(f"Avg latency (batch=1, seq_len=20): PyTorch={torch_ms:.2f}ms | "
          f"ONNX={onnx_ms:.2f}ms | ONNX-int8={quant_ms:.2f}ms")

    with open(ARTIFACTS_DIR / "metrics.json") as f:
        metrics = json.load(f)
    metrics.update({
        "onnx_export_max_diff": float(max_diff),
        "latency_ms_pytorch": torch_ms,
        "latency_ms_onnx_fp32": onnx_ms,
        "latency_ms_onnx_int8": quant_ms,
        "onnx_size_mb": onnx_path.stat().st_size / 1e6,
        "onnx_quant_size_mb": quantized_path.stat().st_size / 1e6,
    })
    with open(ARTIFACTS_DIR / "metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)


if __name__ == "__main__":
    main()
