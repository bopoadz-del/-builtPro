"""Learning feedback API."""

from __future__ import annotations

from datetime import datetime
import json
import os
from pathlib import Path
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.backend.db import get_db
from backend.learning.models import Feedback, FeedbackLabel, FeedbackReview

router = APIRouter(prefix="/learning")


def _evaluate_pdp(*args: Any, **kwargs: Any) -> None:  # noqa: ANN401
    return None


@router.post("/feedback", status_code=201)
def create_feedback(payload: Dict[str, Any], db: Session = Depends(get_db)):
    _evaluate_pdp()
    feedback = Feedback(
        workspace_id=payload["workspace_id"],
        user_id=payload["user_id"],
        source=payload.get("source", "ui"),
        input_text=payload.get("input_text", ""),
        output_text=payload.get("output_text", ""),
        metadata_json=payload.get("metadata", {}),
    )
    db.add(feedback)
    db.commit()
    db.refresh(feedback)
    return {"feedback_id": feedback.id}


@router.post("/feedback/{feedback_id}/label")
def add_label(feedback_id: int, payload: Dict[str, Any], db: Session = Depends(get_db)):
    feedback = db.query(Feedback).filter(Feedback.id == feedback_id).first()
    if feedback is None:
        raise HTTPException(status_code=404, detail="Feedback not found")
    label = FeedbackLabel(
        feedback_id=feedback_id,
        label_type=payload["label_type"],
        label_data_json=payload.get("label_data", {}),
    )
    db.add(label)
    db.commit()
    return {"label_id": label.id}


@router.post("/feedback/{feedback_id}/review")
def add_review(feedback_id: int, payload: Dict[str, Any], db: Session = Depends(get_db)):
    feedback = db.query(Feedback).filter(Feedback.id == feedback_id).first()
    if feedback is None:
        raise HTTPException(status_code=404, detail="Feedback not found")
    review = FeedbackReview(
        feedback_id=feedback_id,
        reviewer_id=payload["reviewer_id"],
        status=payload.get("status", "pending"),
        notes=payload.get("notes"),
    )
    db.add(review)
    db.commit()
    return {"review_id": review.id}


@router.post("/export-dataset/{dataset_name}")
def export_dataset(dataset_name: str, payload: Dict[str, Any], db: Session = Depends(get_db)):
    workspace_id = payload.get("workspace_id")
    export_dir = Path(os.getenv("LEARNING_EXPORT_DIR", "/tmp/learning_exports"))
    export_dir.mkdir(parents=True, exist_ok=True)

    feedbacks = (
        db.query(Feedback)
        .filter(Feedback.workspace_id == workspace_id)
        .all()
    )

    records = []
    for feedback in feedbacks:
        label = next((lbl for lbl in feedback.labels if lbl.label_type == dataset_name), None)
        if label is None:
            continue
        approved = any(review.status == "approved" for review in feedback.reviews)
        if not approved:
            continue
        records.append(
            {
                "input_text": feedback.input_text,
                "output_text": feedback.output_text,
                "label": label.label_data_json,
            }
        )

    dataset_path = export_dir / f"{dataset_name}-{workspace_id}.jsonl"
    with dataset_path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record))
            handle.write("\n")

    manifest_path = export_dir / f"{dataset_name}-{workspace_id}-manifest.json"
    manifest = {
        "dataset_name": dataset_name,
        "workspace_id": workspace_id,
        "record_count": len(records),
        "generated_at": datetime.utcnow().isoformat(),
        "dataset_path": str(dataset_path),
    }
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    return {
        "dataset_path": str(dataset_path),
        "manifest_path": str(manifest_path),
        "record_count": len(records),
    }
