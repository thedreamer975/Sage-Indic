"""Baseline B: Multilingual Semantic Classifier.

Uses a local, offline pretrained multilingual transformer
(`sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`, 117M params)
to compute dense semantic representations and classify risk via anchor similarity.
"""

from __future__ import annotations

import math
from typing import Any

import torch
from transformers import AutoModel, AutoTokenizer

from sage_indic.normalize import normalize_text
from sage_indic.safety.types import (
    SafetyCategory,
    SafetyLabel,
    SafetyResult,
    SafetySignal,
)

# Reference anchor prototypes for semantic similarity mapping
UNSAFE_ANCHORS: list[str] = [
    # Native Telugu violence / hate / self-harm
    "వాడిని అందరూ కలిసి చంపేయండి మరియు హింసించండి.",
    "నీ జీవితం వ్యర్థం, వెళ్లి ఆత్మహత్య చేసుకొని చావు.",
    "ఆ వర్గం వారిపై తీవ్రమైన దాడి చేసి గాయపరచండి.",
    # Romanized Telugu violence / hate / self-harm
    "Ninnu road meeda petti champestanu narukuthanu.",
    "Nuvvu batakadam waste, poison taagi sachipo.",
    "Aadini nariki paatheyandi, kotti champali.",
    # Code-mixed / English threats
    "Tomorrow office ki vachi I will kill you and murder you.",
    "Go commit suicide and die right now.",
    "Physically attack and brutally beat them up.",
]

SAFE_ANCHORS: list[str] = [
    # Native Telugu informative / educational / benign
    "తెలుగు భాష మరియు సాహిత్యం గురించి వివరాలు తెలపండి.",
    "ఆరోగ్య సంరక్షణ మరియు డాక్టర్ సూచించిన వైద్య చికిత్స.",
    "భారతదేశ చరిత్ర మరియు రాజ్యాంగం గురించి అధ్యయనం.",
    # Romanized Telugu benign
    "Nenu repu morning office lo project presentation isthanu.",
    "Doctor daggara nunchi health care tips theesukondi.",
    "Telugu cinema and cultural festival chaala bagundi.",
    # Code-mixed / English benign
    "Today team meeting lo software architecture design discuss chesamu.",
    "Machine learning models research and engineering development.",
    "University library lo reference books study chestunnamu.",
]


class MultilingualSemanticClassifier:
    """Baseline B: Dense multilingual embedding semantic safety classifier."""

    def __init__(
        self,
        model_name: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        unsafe_threshold: float = 0.52,
        uncertain_margin: float = 0.03,
    ) -> None:
        self.model_name = model_name
        self.unsafe_threshold = unsafe_threshold
        self.uncertain_margin = uncertain_margin

        # Load local offline model
        self.tokenizer = AutoTokenizer.from_pretrained(model_name, local_files_only=True)
        self.model = AutoModel.from_pretrained(model_name, local_files_only=True)
        self.model.eval()

        # Precompute anchor embeddings
        with torch.no_grad():
            self.unsafe_embeddings = self._encode_batch(UNSAFE_ANCHORS)
            self.safe_embeddings = self._encode_batch(SAFE_ANCHORS)

    def _encode_batch(self, texts: list[str]) -> torch.Tensor:
        """Compute L2-normalized mean-pooled sentence embeddings."""
        inputs = self.tokenizer(
            texts,
            padding=True,
            truncation=True,
            max_length=128,
            return_tensors="pt",
        )
        outputs = self.model(**inputs)
        attention_mask = inputs["attention_mask"].unsqueeze(-1)
        # Mean pooling
        sum_embeddings = torch.sum(outputs.last_hidden_state * attention_mask, dim=1)
        sum_mask = torch.clamp(attention_mask.sum(dim=1), min=1e-9)
        embeddings = sum_embeddings / sum_mask
        # Normalize
        return torch.nn.functional.normalize(embeddings, p=2, dim=1)

    def predict_score(self, text: str) -> float:
        """Compute continuous safety risk score in [0.0, 1.0]."""
        if not text or not text.strip():
            return 0.5

        norm_text = normalize_text(text)
        with torch.no_grad():
            emb = self._encode_batch([norm_text])
            # Cosine similarities
            sim_unsafe = torch.mm(emb, self.unsafe_embeddings.t()).max().item()
            sim_safe = torch.mm(emb, self.safe_embeddings.t()).max().item()

        # Difference scaled through logistic sigmoid
        diff = sim_unsafe - sim_safe
        # Logistic sigmoid with temperature scaling
        prob_unsafe = 1.0 / (1.0 + math.exp(-8.0 * diff))
        return float(prob_unsafe)

    def predict(self, text: str) -> SafetyResult:
        """Predict safety label and confidence using calibrated thresholds."""
        if not text or not text.strip():
            return SafetyResult(
                label=SafetyLabel.UNCERTAIN,
                confidence=0.5,
                method="Baseline_B_MultilingualClassifier",
                metadata={"risk_score": 0.5, "model_name": self.model_name},
            )

        risk_score = self.predict_score(text)
        lower_bound = self.unsafe_threshold - self.uncertain_margin
        upper_bound = self.unsafe_threshold

        metadata: dict[str, Any] = {
            "risk_score": round(risk_score, 4),
            "model_name": self.model_name,
            "threshold_unsafe": self.unsafe_threshold,
        }

        if risk_score >= upper_bound:
            label = SafetyLabel.UNSAFE
            confidence = min(0.99, 0.5 + (risk_score - upper_bound))
            category = SafetyCategory.VIOLENCE_INCITEMENT
            signals = [
                SafetySignal(
                    source="semantic_embedding",
                    risk_score=risk_score,
                    category=category,
                    explanation=f"High semantic similarity to unsafe anchors ({risk_score:.3f}).",
                )
            ]
        elif risk_score >= lower_bound:
            label = SafetyLabel.UNCERTAIN
            confidence = 0.5
            category = SafetyCategory.AMBIGUOUS
            signals = [
                SafetySignal(
                    source="semantic_embedding",
                    risk_score=risk_score,
                    category=category,
                    explanation=(
                        f"Borderline semantic risk ({risk_score:.3f}); abstaining under uncertainty."
                    ),
                )
            ]
        else:
            label = SafetyLabel.SAFE
            confidence = min(0.99, 0.5 + (lower_bound - risk_score))
            category = SafetyCategory.SAFE_GENERAL
            signals = []

        return SafetyResult(
            label=label,
            confidence=round(confidence, 4),
            method="Baseline_B_MultilingualClassifier",
            category=category,
            signals=signals,
            metadata=metadata,
        )
