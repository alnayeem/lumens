from __future__ import annotations

from typing import Dict, Iterable, Optional


def make_content_id(record: Dict) -> Optional[str]:
    vid = record.get("video_id")
    if not vid:
        return None
    return f"yt:{vid}"


def write_firestore_content(records: Iterable[Dict], project_id: str, collection: str = "content") -> int:
    """Write records to Firestore Native as documents in collection.

    Each record is stored under doc id `yt:{VIDEOID}` with the record fields.
    Requires `google-cloud-firestore` and ADC credentials (`gcloud auth application-default login`).
    """
    try:
        from google.cloud import firestore  # type: ignore
    except Exception as e:
        raise RuntimeError(
            "google-cloud-firestore is required. Install via `pip install google-cloud-firestore`"
        ) from e

    client = firestore.Client(project=project_id)
    written = 0
    batch = client.batch()
    BATCH_LIMIT = 400  # leave headroom under Firestore 500 ops limit
    ops = 0
    for rec in records:
        cid = make_content_id(rec)
        if not cid:
            continue
        doc_ref = client.collection(collection).document(cid)
        batch.set(doc_ref, rec, merge=True)
        ops += 1
        written += 1
        if ops >= BATCH_LIMIT:
            batch.commit()
            batch = client.batch()
            ops = 0
    if ops:
        batch.commit()
    return written

