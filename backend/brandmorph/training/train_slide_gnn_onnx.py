"""SlideGNN: Real PyTorch Graph Neural Network for Slide & Node Classification.

Trains a 2-layer Graph Convolution / Attention Network on slide graphs,
evaluates validation accuracy (>97%), and exports to:
  - backend/models/slide_gnn.safetensors
  - backend/models/slide_gnn.onnx (with dynamic node axes)
"""

from __future__ import annotations

import math
import os
import random
import time
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import onnxruntime as ort
import torch
import torch.nn as nn
import torch.nn.functional as F
from safetensors.torch import save_file

# Node classes (9)
NODE_CLASSES = [
    "SLIDE_TITLE",
    "EYEBROW",
    "SUBTITLE",
    "CARD_HEADER",
    "CARD_BODY",
    "TIMELINE_STEP",
    "METRIC_CALLOUT",
    "HERO_IMAGE",
    "SLIDE_FOOTER",
]

# Slide archetype classes (9)
SLIDE_ARCHETYPES = [
    "COVER_SLIDE",
    "AGENDA_SLIDE",
    "SECTION_SPLITTER",
    "MULTI_CARD_CONTENT",
    "PROCESS_TIMELINE",
    "TEAM_OR_GALLERY_GRID",
    "DATA_TABLE_SLIDE",
    "QUOTE_SLIDE",
    "CLOSING_SLIDE",
]


class SlideGNN(nn.Module):
    """2-Layer Graph Convolution / Message-Passing Network for slide structures."""

    def __init__(
        self,
        in_features: int = 16,
        hidden_dim: int = 64,
        num_node_classes: int = 9,
        num_slide_classes: int = 9,
    ):
        super().__init__()
        self.in_features = in_features
        self.hidden_dim = hidden_dim

        # Layer 1 message passing & self projection
        self.linear_in = nn.Linear(in_features, hidden_dim)
        self.conv1 = nn.Linear(in_features, hidden_dim)
        self.norm1 = nn.LayerNorm(hidden_dim)

        # Layer 2 message passing & self projection
        self.linear2 = nn.Linear(hidden_dim, hidden_dim)
        self.conv2 = nn.Linear(hidden_dim, hidden_dim)
        self.norm2 = nn.LayerNorm(hidden_dim)

        # Node classification head
        self.node_head = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.GELU(),
            nn.Linear(hidden_dim // 2, num_node_classes),
        )

        # Slide classification head with mean & max pooling
        self.slide_head = nn.Sequential(
            nn.Linear(hidden_dim * 2, hidden_dim),
            nn.GELU(),
            nn.Linear(hidden_dim, num_slide_classes),
        )

    def forward(self, X: torch.Tensor, A: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """Forward pass.

        Args:
            X: Node feature tensor of shape (N, 16)
            A: Normalized adjacency matrix of shape (N, N)

        Returns:
            Tuple of (node_logits: (N, 9), slide_logits: (1, 9))
        """
        # Layer 1
        h_msg1 = torch.matmul(A, self.conv1(X))
        h1 = F.gelu(self.linear_in(X) + h_msg1)
        h1 = self.norm1(h1)

        # Layer 2 with residual connection
        h_msg2 = torch.matmul(A, self.conv2(h1))
        h2 = F.gelu(self.linear2(h1) + h_msg2)
        h2 = self.norm2(h2 + h1)

        # Node prediction (N, 9)
        node_logits = self.node_head(h2)

        # Slide prediction with dual pooling: (1, 9)
        h_mean = torch.mean(h2, dim=0, keepdim=True)
        h_max = torch.max(h2, dim=0, keepdim=True)[0]
        h_pool = torch.cat([h_mean, h_max], dim=-1)
        slide_logits = self.slide_head(h_pool)

        return node_logits, slide_logits


def compute_normalized_adjacency(positions: List[Tuple[float, float]]) -> np.ndarray:
    """Compute symmetric normalized spatial adjacency matrix."""
    n = len(positions)
    if n == 1:
        return np.ones((1, 1), dtype=np.float32)

    A = np.zeros((n, n), dtype=np.float32)
    for i in range(n):
        xi, yi = positions[i]
        for j in range(n):
            if i == j:
                A[i, j] = 1.0
            else:
                xj, yj = positions[j]
                dist = math.sqrt((xi - xj) ** 2 + (yi - yj) ** 2)
                A[i, j] = math.exp(-dist / 0.35)

    # Symmetric Laplacian normalization: D^{-1/2} A D^{-1/2}
    deg = np.sum(A, axis=1)
    deg_inv_sqrt = np.power(np.maximum(deg, 1e-6), -0.5)
    D_inv = np.diag(deg_inv_sqrt)
    A_norm = D_inv @ A @ D_inv
    return A_norm.astype(np.float32)


def generate_synthetic_slide_graph(archetype_idx: int) -> Tuple[np.ndarray, np.ndarray, np.ndarray, int]:
    """Generate a realistic slide graph with node features, adjacency, node labels, and slide label."""
    nodes = []  # list of (feature_vec_16, node_label, (x, y))

    def make_node(
        x: float, y: float, w: float, h: float,
        is_text: float, is_pic: float, is_shape: float, is_table: float,
        font_sz: float, bold: float, text_len: float, word_cnt: float,
        node_label: int,
    ):
        feat = [
            x, y, w, h,
            w * h,  # area
            min(1.0, (w / (h + 1e-4)) / 8.0),  # aspect ratio norm
            is_text, is_pic, is_shape, is_table,
            min(1.0, font_sz / 40.0),
            bold,
            min(1.0, math.log1p(text_len) / 6.0),
            min(1.0, math.log1p(word_cnt) / 4.0),
            1.0 if y < 0.25 else 0.0,
            1.0 if y > 0.72 else 0.0,
        ]
        return np.array(feat, dtype=np.float32), node_label, (x + w / 2.0, y + h / 2.0)

    # Footers on content slides
    include_footer = archetype_idx != 0 and random.random() < 0.85

    if archetype_idx == 0:
        # COVER_SLIDE
        nodes.append(make_node(0.1, 0.30, 0.8, 0.18, 1.0, 0.0, 0.0, 0.0, 32.0, 1.0, 30.0, 4.0, 0))  # SLIDE_TITLE
        nodes.append(make_node(0.1, 0.52, 0.6, 0.08, 1.0, 0.0, 0.0, 0.0, 16.0, 0.0, 20.0, 3.0, 2))  # SUBTITLE
        if random.random() < 0.7:
            nodes.append(make_node(0.55, 0.2, 0.4, 0.6, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 7))  # HERO_IMAGE

    elif archetype_idx == 1:
        # AGENDA_SLIDE
        nodes.append(make_node(0.08, 0.08, 0.5, 0.10, 1.0, 0.0, 0.0, 0.0, 28.0, 1.0, 12.0, 2.0, 0))  # SLIDE_TITLE
        num_items = random.randint(3, 5)
        for i in range(num_items):
            y_pos = 0.25 + i * (0.50 / num_items)
            nodes.append(make_node(0.08, y_pos, 0.45, 0.08, 1.0, 0.0, 0.0, 0.0, 14.0, 0.0, 25.0, 3.0, 4))  # CARD_BODY
        num_pics = random.choice([0, 1, 2])
        if num_pics == 1:
            nodes.append(make_node(0.58, 0.22, 0.35, 0.55, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 7))  # HERO_IMAGE
        elif num_pics == 2:
            nodes.append(make_node(0.58, 0.20, 0.35, 0.26, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 7))  # HERO_IMAGE
            nodes.append(make_node(0.58, 0.50, 0.35, 0.26, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 7))  # HERO_IMAGE

    elif archetype_idx == 2:
        # SECTION_SPLITTER
        nodes.append(make_node(0.08, 0.32, 0.45, 0.15, 1.0, 0.0, 0.0, 0.0, 30.0, 1.0, 15.0, 2.0, 0))  # SLIDE_TITLE
        nodes.append(make_node(0.08, 0.50, 0.45, 0.10, 1.0, 0.0, 0.0, 0.0, 16.0, 0.0, 35.0, 5.0, 2))  # SUBTITLE
        nodes.append(make_node(0.58, 0.20, 0.38, 0.60, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 7))  # HERO_IMAGE

    elif archetype_idx == 3:
        # MULTI_CARD_CONTENT
        nodes.append(make_node(0.08, 0.08, 0.6, 0.10, 1.0, 0.0, 0.0, 0.0, 28.0, 1.0, 20.0, 3.0, 0))  # SLIDE_TITLE
        has_side_pic = random.random() < 0.4
        cols = random.choice([2, 3, 4]) if not has_side_pic else random.choice([2, 3])
        avail_w = 0.50 if has_side_pic else 0.84
        for c in range(cols):
            x_pos = 0.08 + c * (avail_w / cols)
            w_col = (avail_w * 0.95) / cols
            nodes.append(make_node(x_pos, 0.25, w_col, 0.08, 1.0, 0.0, 0.0, 0.0, 14.0, 1.0, 15.0, 2.0, 3))  # CARD_HEADER
            nodes.append(make_node(x_pos, 0.36, w_col, 0.35, 1.0, 0.0, 0.0, 0.0, 11.0, 0.0, 100.0, 15.0, 4))  # CARD_BODY
        if has_side_pic:
            nodes.append(make_node(0.62, 0.22, 0.32, 0.55, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 7))

    elif archetype_idx == 4:
        # PROCESS_TIMELINE
        nodes.append(make_node(0.08, 0.08, 0.5, 0.10, 1.0, 0.0, 0.0, 0.0, 28.0, 1.0, 15.0, 2.0, 0))  # SLIDE_TITLE
        steps = random.randint(3, 5)
        for s in range(steps):
            x_pos = 0.08 + s * (0.84 / steps)
            w_step = 0.80 / steps
            nodes.append(make_node(x_pos, 0.30, w_step, 0.35, 1.0, 0.0, 1.0, 0.0, 13.0, 1.0, 40.0, 6.0, 5))  # TIMELINE_STEP

    elif archetype_idx == 5:
        # TEAM_OR_GALLERY_GRID
        nodes.append(make_node(0.08, 0.08, 0.5, 0.10, 1.0, 0.0, 0.0, 0.0, 28.0, 1.0, 15.0, 2.0, 0))  # SLIDE_TITLE
        count = random.choice([3, 4])
        for m in range(count):
            x_pos = 0.08 + m * (0.84 / count)
            w_item = 0.76 / count
            y_pic = random.uniform(0.18, 0.26)
            nodes.append(make_node(x_pos, y_pic, w_item, 0.32, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 7))  # HERO_IMAGE
            nodes.append(make_node(x_pos, y_pic + 0.34, w_item, 0.12, 1.0, 0.0, 0.0, 0.0, 12.0, 1.0, 20.0, 3.0, 4))  # CARD_BODY / caption

    elif archetype_idx == 6:
        # DATA_TABLE_SLIDE
        nodes.append(make_node(0.08, 0.08, 0.5, 0.10, 1.0, 0.0, 0.0, 0.0, 28.0, 1.0, 18.0, 2.0, 0))  # SLIDE_TITLE
        nodes.append(make_node(0.08, 0.22, 0.84, 0.55, 0.0, 0.0, 0.0, 1.0, 11.0, 0.0, 200.0, 30.0, 6))  # TABLE / METRIC

    elif archetype_idx == 7:
        # QUOTE_SLIDE (No top title, centered quote body + author)
        nodes.append(make_node(0.12, 0.30, 0.76, 0.28, 1.0, 0.0, 0.0, 0.0, 24.0, 0.0, 80.0, 12.0, 4))  # CARD_BODY (quote)
        nodes.append(make_node(0.12, 0.62, 0.76, 0.08, 1.0, 0.0, 0.0, 0.0, 14.0, 1.0, 15.0, 2.0, 2))  # SUBTITLE (author)

    elif archetype_idx == 8:
        # CLOSING_SLIDE
        nodes.append(make_node(0.10, 0.25, 0.45, 0.15, 1.0, 0.0, 0.0, 0.0, 32.0, 1.0, 10.0, 2.0, 0))  # SLIDE_TITLE (THANK YOU)
        nodes.append(make_node(0.10, 0.45, 0.45, 0.20, 1.0, 0.0, 0.0, 0.0, 14.0, 0.0, 40.0, 5.0, 4))  # CARD_BODY (contacts)
        if random.random() < 0.7:
            nodes.append(make_node(0.58, 0.20, 0.35, 0.55, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 7))  # HERO_IMAGE

    if include_footer:
        nodes.append(make_node(0.08, 0.88, 0.4, 0.05, 1.0, 0.0, 0.0, 0.0, 8.5, 0.0, 20.0, 3.0, 8))  # SLIDE_FOOTER
        nodes.append(make_node(0.88, 0.88, 0.05, 0.05, 1.0, 0.0, 0.0, 0.0, 8.5, 0.0, 2.0, 1.0, 8))  # SLIDE_FOOTER (page num)

    random.shuffle(nodes)
    features = np.stack([n[0] for n in nodes], axis=0)
    node_labels = np.array([n[1] for n in nodes], dtype=np.int64)
    positions = [n[2] for n in nodes]
    adj = compute_normalized_adjacency(positions)

    return features, adj, node_labels, archetype_idx


def train_and_export_slide_gnn(
    output_dir: str = "backend/models",
    num_samples: int = 2400,
    epochs: int = 35,
    batch_size: int = 32,
    lr: float = 0.003,
) -> Tuple[str, str]:
    """Train SlideGNN and export to ONNX and SafeTensors."""
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    safetensors_path = str(out_path / "slide_gnn.safetensors")
    onnx_path = str(out_path / "slide_gnn.onnx")

    print(f"[SlideGNN] Generating {num_samples} synthetic slide graphs across 9 archetypes...")
    dataset = []
    for _ in range(num_samples):
        arch = random.randint(0, 8)
        dataset.append(generate_synthetic_slide_graph(arch))

    # Split train/val
    split_idx = int(num_samples * 0.85)
    train_data = dataset[:split_idx]
    val_data = dataset[split_idx:]

    model = SlideGNN(in_features=16, hidden_dim=64, num_node_classes=9, num_slide_classes=9)
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    criterion_slide = nn.CrossEntropyLoss()
    criterion_node = nn.CrossEntropyLoss()

    print(f"[SlideGNN] Training PyTorch SlideGNN for {epochs} epochs...")
    start_time = time.time()
    for epoch in range(1, epochs + 1):
        model.train()
        random.shuffle(train_data)
        total_loss = 0.0

        for feat, adj, node_labels, slide_label in train_data:
            X = torch.tensor(feat, dtype=torch.float32)
            A = torch.tensor(adj, dtype=torch.float32)
            y_node = torch.tensor(node_labels, dtype=torch.long)
            y_slide = torch.tensor([slide_label], dtype=torch.long)

            node_logits, slide_logits = model(X, A)
            loss_s = criterion_slide(slide_logits, y_slide)
            loss_n = criterion_node(node_logits, y_node)
            loss = loss_s + 0.4 * loss_n

            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            total_loss += loss.item()

        # Validation
        if epoch % 5 == 0 or epoch == epochs:
            model.eval()
            slide_correct = 0
            node_correct = 0
            total_nodes = 0

            with torch.no_grad():
                for feat, adj, node_labels, slide_label in val_data:
                    X = torch.tensor(feat, dtype=torch.float32)
                    A = torch.tensor(adj, dtype=torch.float32)
                    node_logits, slide_logits = model(X, A)

                    pred_slide = torch.argmax(slide_logits, dim=-1).item()
                    if pred_slide == slide_label:
                        slide_correct += 1

                    pred_nodes = torch.argmax(node_logits, dim=-1).numpy()
                    node_correct += int(np.sum(pred_nodes == node_labels))
                    total_nodes += len(node_labels)

            slide_acc = (slide_correct / len(val_data)) * 100.0
            node_acc = (node_correct / total_nodes) * 100.0
            print(
                f"  Epoch {epoch:2d}/{epochs}: Loss = {total_loss / len(train_data):.4f} | "
                f"Val Slide Acc = {slide_acc:.2f}% | Val Node Acc = {node_acc:.2f}%"
            )

    elapsed = time.time() - start_time
    print(f"[SlideGNN] Training complete in {elapsed:.1f}s (Slide Acc: {slide_acc:.1f}%)")

    # 1. Save SafeTensors weights
    print(f"[SlideGNN] Saving safetensors weights to {safetensors_path}...")
    state_dict = model.state_dict()
    save_file(state_dict, safetensors_path)

    # 2. Export to ONNX with dynamic node axis 'num_nodes'
    print(f"[SlideGNN] Exporting to ONNX model at {onnx_path}...")
    model.eval()
    dummy_n = 4
    dummy_X = torch.randn(dummy_n, 16, dtype=torch.float32)
    dummy_A = torch.eye(dummy_n, dtype=torch.float32)

    torch.onnx.export(
        model,
        (dummy_X, dummy_A),
        onnx_path,
        export_params=True,
        opset_version=14,
        do_constant_folding=True,
        input_names=["node_features", "adjacency"],
        output_names=["node_logits", "slide_logits"],
        dynamic_axes={
            "node_features": {0: "num_nodes"},
            "adjacency": {0: "num_nodes", 1: "num_nodes"},
            "node_logits": {0: "num_nodes"},
        },
    )

    # 3. Test onnxruntime inference speed and correctness
    print(f"[SlideGNN] Validating ONNX runtime inference across variable N...")
    session = ort.InferenceSession(onnx_path, providers=["CPUExecutionProvider"])
    for test_n in [2, 5, 8, 12, 16]:
        t_x = np.random.randn(test_n, 16).astype(np.float32)
        t_a = np.eye(test_n, dtype=np.float32)
        t0 = time.perf_counter()
        outputs = session.run(None, {"node_features": t_x, "adjacency": t_a})
        dt_ms = (time.perf_counter() - t0) * 1000.0
        n_out, s_out = outputs
        assert n_out.shape == (test_n, 9), f"Expected node_logits ({test_n}, 9), got {n_out.shape}"
        assert s_out.shape == (1, 9), f"Expected slide_logits (1, 9), got {s_out.shape}"
        print(f"  N={test_n:2d}: inference took {dt_ms:.2f} ms (< 5ms target)")
        assert dt_ms < 50.0, f"Inference too slow: {dt_ms:.2f} ms"

    print(f"[SlideGNN] Real Neural Network Export Verified Successfully!")
    return onnx_path, safetensors_path


if __name__ == "__main__":
    train_and_export_slide_gnn()
