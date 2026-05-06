"""
Storage Service
───────────────
Handles all Azure Storage interactions:
  - Blob Storage  : storing/retrieving raw PDF files
  - Table Storage : persisting and querying document metadata/results

The connection string is read from environment variables.
When the connection string is empty (local dev without Azure), operations
are silently skipped and a warning is logged so the rest of the pipeline
still works.
"""
from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime
from typing import Optional

from backend.config import get_settings
from backend.models.document import (
    AnalyticsSummary,
    DocumentRecord,
    DocumentStatus,
    RemedialClassification,
)

logger = logging.getLogger(__name__)


# ── Lazy client helpers ───────────────────────────────────────────────────────

def _get_blob_service_client():
    """Return an Azure BlobServiceClient or None if not configured."""
    try:
        from azure.storage.blob import BlobServiceClient  # type: ignore
        settings = get_settings()
        if not settings.azure_storage_connection_string:
            logger.warning("AZURE_STORAGE_CONNECTION_STRING not set – blob storage disabled")
            return None
        return BlobServiceClient.from_connection_string(settings.azure_storage_connection_string)
    except ImportError:
        logger.warning("azure-storage-blob not installed – blob storage disabled")
        return None


def _get_table_client(table_name: str):
    """Return an Azure TableClient or None if not configured."""
    try:
        from azure.data.tables import TableServiceClient  # type: ignore
        settings = get_settings()
        if not settings.azure_storage_connection_string:
            logger.warning("AZURE_STORAGE_CONNECTION_STRING not set – table storage disabled")
            return None
        service = TableServiceClient.from_connection_string(settings.azure_storage_connection_string)
        # Create table if it doesn't exist
        try:
            service.create_table_if_not_exists(table_name)
        except Exception:
            pass
        return service.get_table_client(table_name)
    except ImportError:
        logger.warning("azure-data-tables not installed – table storage disabled")
        return None


# ── Blob operations ───────────────────────────────────────────────────────────

def upload_pdf_to_blob(pdf_bytes: bytes, filename: str) -> tuple[str, str]:
    """
    Upload a PDF to Blob Storage.
    Returns (document_id, blob_url).
    """
    document_id = str(uuid.uuid4())
    settings = get_settings()
    blob_name = f"{document_id}/{filename}"

    client = _get_blob_service_client()
    if client is None:
        logger.warning("Blob upload skipped (no client) – document_id=%s", document_id)
        return document_id, ""

    container = client.get_container_client(settings.azure_blob_container_name)
    try:
        container.create_container()
    except Exception:
        pass  # Already exists

    blob_client = container.get_blob_client(blob_name)
    try:
        blob_client.upload_blob(pdf_bytes, overwrite=True)
        blob_url = blob_client.url
        logger.info("Uploaded blob: %s", blob_url)
    except Exception as exc:
        logger.warning("Blob upload failed (storage may be unreachable): %s – continuing without blob", exc)
        blob_url = ""

    return document_id, blob_url


def get_pdf_from_blob(document_id: str, filename: str) -> Optional[bytes]:
    """Download a PDF from Blob Storage. Returns None if not found."""
    settings = get_settings()
    blob_name = f"{document_id}/{filename}"

    client = _get_blob_service_client()
    if client is None:
        return None

    blob_client = client.get_blob_client(
        container=settings.azure_blob_container_name, blob=blob_name
    )
    try:
        stream = blob_client.download_blob()
        return stream.readall()
    except Exception as exc:
        logger.error("Blob download failed for %s: %s", blob_name, exc)
        return None


def get_pdf_from_blob_url(blob_url: str) -> Optional[bytes]:
    """Download a PDF directly using its full Azure Blob Storage URL."""
    try:
        from azure.storage.blob import BlobClient  # type: ignore
        blob_client = BlobClient.from_blob_url(blob_url)
        stream = blob_client.download_blob()
        return stream.readall()
    except ImportError:
        logger.warning("azure-storage-blob not installed – cannot fetch by URL")
        return None
    except Exception as exc:
        logger.error("Blob download by URL failed for %s: %s", blob_url, exc)
        return None


def save_document_text(document_id: str, text: str) -> None:
    """Store the extracted plain text of a document as {document_id}/document_text.txt."""
    settings = get_settings()
    blob_name = f"{document_id}/document_text.txt"

    client = _get_blob_service_client()
    if client is None:
        logger.warning("Text save skipped (no blob client) – document_id=%s", document_id)
        return

    container = client.get_container_client(settings.azure_blob_container_name)
    try:
        container.create_container()
    except Exception:
        pass

    try:
        container.get_blob_client(blob_name).upload_blob(
            text.encode("utf-8"), overwrite=True
        )
        logger.info("Saved document text blob: %s", blob_name)
    except Exception as exc:
        logger.warning("Text save failed for %s: %s – continuing", blob_name, exc)


def get_document_text(document_id: str) -> Optional[str]:
    """Retrieve the stored plain text for a document. Returns None if not found."""
    settings = get_settings()
    blob_name = f"{document_id}/document_text.txt"

    client = _get_blob_service_client()
    if client is None:
        return None

    blob_client = client.get_blob_client(
        container=settings.azure_blob_container_name, blob=blob_name
    )
    try:
        return blob_client.download_blob().readall().decode("utf-8")
    except Exception as exc:
        logger.warning("Text retrieval failed for %s: %s", blob_name, exc)
        return None


# ── Table operations ──────────────────────────────────────────────────────────

def _record_to_entity(record: DocumentRecord) -> dict:
    """Convert a DocumentRecord to an Azure Table entity dict."""
    # Flat queryable columns – avoids deserialising JSON just to list/filter
    ef = record.extracted_fields
    cs = record.confidence_score
    rr = record.remedial_result
    ins = record.insights

    entity: dict = {
        "PartitionKey": "documents",
        "RowKey": record.document_id,
        "filename": record.filename,
        "blob_url": record.blob_url or "",
        "status": record.status.value if isinstance(record.status, DocumentStatus) else str(record.status),
        "uploaded_at": record.uploaded_at.isoformat(),
        "processed_at": record.processed_at.isoformat() if record.processed_at else "",
        # ── Flat queryable columns (populated after processing) ──────────────
        "site_name": (ef.site_name or "") if ef else "",
        "inspection_date": (ef.inspection_date or "") if ef else "",
        "next_service_date": (ef.next_service_date or "") if ef else "",
        "inspector_name": (ef.inspector_name or "") if ef else "",
        "vendor_name": (ef.vendor_name or "") if ef else "",
        "document_type": (ef.document_type or "") if ef else "",
        "overall_outcome": (ef.overall_outcome or "") if ef else "",
        "certificate_number": (ef.certificate_number or "") if ef else "",
        "overall_confidence": cs.overall_score if cs else 0.0,
        "remedial_classification": (rr.classification.value if rr and rr.classification else ""),
        "compliance_status": (ins.compliance_status or "") if ins else "",
        "risk_level": (ins.risk_level or "") if ins else "",
        "is_overdue": ins.is_overdue if ins else False,
        # ── Full JSON blobs (for detail view) ────────────────────────────────
        "metadata_json": record.metadata.model_dump_json() if record.metadata else "",
        "extracted_fields_json": record.extracted_fields.model_dump_json() if record.extracted_fields else "",
        "validation_result_json": record.validation_result.model_dump_json() if record.validation_result else "",
        "remedial_result_json": record.remedial_result.model_dump_json() if record.remedial_result else "",
        "confidence_score_json": record.confidence_score.model_dump_json() if record.confidence_score else "",
        "agent_state_json": record.agent_state.model_dump_json() if record.agent_state else "",
        "insights_json": record.insights.model_dump_json() if record.insights else "",
        # ── Officer override ─────────────────────────────────────────────────
        "override_by": record.override_by or "",
        "override_reason": record.override_reason or "",
        "overridden_at": record.overridden_at.isoformat() if record.overridden_at else "",
    }
    return entity


def _normalise_status(raw: str) -> str:
    """Strip legacy 'DocumentStatus.' prefix stored by old code."""
    if isinstance(raw, str) and raw.startswith("DocumentStatus."):
        raw = raw.split(".", 1)[1].lower()
    return raw


def _entity_to_record(entity: dict) -> DocumentRecord:
    """Convert an Azure Table entity dict back to a DocumentRecord."""
    from backend.models.document import (  # local import to avoid circular
        ConfidenceScore,
        DocumentMetadata,
        ExtractedFields,
        RemedialResult,
        ValidationResult,
    )

    def _parse(json_str: str, model):
        if not json_str:
            return None
        try:
            return model.model_validate_json(json_str)
        except Exception:
            return None

    from backend.models.document import AgentState, DocumentInsights  # avoid circular

    return DocumentRecord(
        document_id=entity["RowKey"],
        filename=entity.get("filename", ""),
        blob_url=entity.get("blob_url") or None,
        status=_normalise_status(entity.get("status", "pending")),
        uploaded_at=datetime.fromisoformat(entity["uploaded_at"]),
        processed_at=datetime.fromisoformat(entity["processed_at"]) if entity.get("processed_at") else None,
        metadata=_parse(entity.get("metadata_json", ""), DocumentMetadata),
        extracted_fields=_parse(entity.get("extracted_fields_json", ""), ExtractedFields),
        validation_result=_parse(entity.get("validation_result_json", ""), ValidationResult),
        remedial_result=_parse(entity.get("remedial_result_json", ""), RemedialResult),
        confidence_score=_parse(entity.get("confidence_score_json", ""), ConfidenceScore),
        agent_state=_parse(entity.get("agent_state_json", ""), AgentState),
        insights=_parse(entity.get("insights_json", ""), DocumentInsights),
        override_by=entity.get("override_by") or None,
        override_reason=entity.get("override_reason") or None,
        overridden_at=datetime.fromisoformat(entity["overridden_at"]) if entity.get("overridden_at") else None,
    )


def save_document(record: DocumentRecord) -> None:
    """Upsert a DocumentRecord to Table Storage."""
    settings = get_settings()
    client = _get_table_client(settings.azure_table_name)
    if client is None:
        logger.warning("Table save skipped (no client) – document_id=%s", record.document_id)
        return
    entity = _record_to_entity(record)
    try:
        client.upsert_entity(entity)
        logger.info("Saved document to table: %s [%s]", record.document_id, record.status)
    except Exception as exc:
        logger.warning("Table save failed (storage may be unreachable): %s – continuing", exc)


def get_document(document_id: str) -> Optional[DocumentRecord]:
    """Fetch a single DocumentRecord by ID. Returns None if not found."""
    settings = get_settings()
    client = _get_table_client(settings.azure_table_name)
    if client is None:
        return None
    try:
        entity = client.get_entity(partition_key="documents", row_key=document_id)
        return _entity_to_record(entity)
    except Exception as exc:
        logger.error("get_document failed for %s: %s", document_id, exc)
        return None


def _load_dashboard_defaults() -> list[DocumentRecord]:
    """Load fallback document list from backend/data/dashboard_defaults.json."""
    import json
    import os

    defaults_path = os.path.join(os.path.dirname(__file__), "..", "data", "dashboard_defaults.json")
    try:
        with open(defaults_path, encoding="utf-8-sig") as f:
            data = json.load(f)
        return [DocumentRecord.model_validate(item) for item in data]
    except Exception as exc:
        logger.warning("Failed to load dashboard defaults: %s", exc)
        return []


def list_documents(
    status_filter: Optional[str] = None,
    limit: int = 100,
) -> list[DocumentRecord]:
    """Return a list of documents, optionally filtered by status."""
    settings = get_settings()
    client = _get_table_client(settings.azure_table_name)
    if client is None:
        # Fallback to defaults JSON when Azure Storage is not configured
        records = _load_dashboard_defaults()
        if status_filter:
            records = [r for r in records if r.status == status_filter]
        records.sort(key=lambda r: r.uploaded_at, reverse=True)
        return records[:limit]

    query_filter = "PartitionKey eq 'documents'"
    if status_filter:
        query_filter += f" and status eq '{status_filter}'"

    try:
        entities = list(client.query_entities(query_filter, results_per_page=limit))
        records = [_entity_to_record(e) for e in entities]
        # Sort by uploaded_at descending
        records.sort(key=lambda r: r.uploaded_at, reverse=True)
        return records[:limit]
    except Exception as exc:
        logger.error("list_documents failed: %s", exc)
        return []


def _load_analytics_defaults() -> dict:
    """Load fallback chart data from backend/data/analytics_defaults.json."""
    import json
    import os

    defaults_path = os.path.join(os.path.dirname(__file__), "..", "data", "analytics_defaults.json")
    try:
        with open(defaults_path, encoding="utf-8-sig") as f:
            return json.load(f)
    except Exception:
        return {
            "processing_buckets": [],
            "confidence_distribution": [],
            "site_breakdown": [],
            "ppm_distribution": [],
        }


def _init_accumulators(defaults: dict) -> tuple[dict[str, int], dict[str, int], dict, dict]:
    """
    Return zero-initialised accumulators for chart computation, with bucket
    keys sourced directly from analytics_defaults.json:
      (hour_buckets, conf_buckets, site_map, ppm_map)
    """
    hour_buckets: dict[str, int] = {
        entry["time"]: 0 for entry in defaults.get("processing_buckets", [])
    }
    conf_buckets: dict[str, int] = {
        entry["range"]: 0 for entry in defaults.get("confidence_distribution", [])
    }
    site_map: dict[str, dict[str, int]] = {}
    ppm_map: dict[str, int] = {}
    return hour_buckets, conf_buckets, site_map, ppm_map


def get_analytics_summary() -> AnalyticsSummary:
    """Compute aggregate analytics from all stored documents."""
    records = list_documents(limit=1000)

    defaults = _load_analytics_defaults()
    hour_buckets, conf_buckets, site_map, ppm_map = _init_accumulators(defaults)

    # When no real documents exist, return the defaults directly
    if not records:
        return AnalyticsSummary(
            total_documents=defaults.get("total_documents", 0),
            auto_approved=defaults.get("auto_approved", 0),
            manual_review=defaults.get("manual_review", 0),
            requires_attention=defaults.get("requires_attention", 0),
            approved=defaults.get("approved", 0),
            rejected=defaults.get("rejected", 0),
            avg_confidence=defaults.get("avg_confidence", 0.0),
            remedial_pass=defaults.get("remedial_pass", 0),
            remedial_minor=defaults.get("remedial_minor", 0),
            remedial_critical=defaults.get("remedial_critical", 0),
            auto_approval_rate=defaults.get("auto_approval_rate", 0.0),
            avg_processing_time_seconds=defaults.get("avg_processing_time_seconds", 0.0),
            processing_buckets=defaults.get("processing_buckets", []),
            confidence_distribution=defaults.get("confidence_distribution", []),
            site_breakdown=defaults.get("site_breakdown", []),
            ppm_distribution=defaults.get("ppm_distribution", []),
        )

    summary = AnalyticsSummary(total_documents=len(records))
    confidence_sum = 0.0
    confidence_count = 0
    processing_time_sum = 0.0
    processing_time_count = 0

    now_utc = datetime.utcnow()

    for rec in records:
        # ── Status counters ────────────────────────────────────────────
        s = rec.status
        if s == DocumentStatus.AUTO_APPROVED:
            summary.auto_approved += 1
        elif s == DocumentStatus.MANUAL_REVIEW:
            summary.manual_review += 1
        elif s == DocumentStatus.REQUIRES_ATTENTION:
            summary.requires_attention += 1
        elif s == DocumentStatus.APPROVED:
            summary.approved += 1
        elif s == DocumentStatus.REJECTED:
            summary.rejected += 1

        # ── Confidence ────────────────────────────────────────────────
        if rec.confidence_score:
            score = rec.confidence_score.overall_score
            confidence_sum += score
            confidence_count += 1

            if score <= 20:
                conf_buckets["0-20"] += 1
            elif score <= 40:
                conf_buckets["20-40"] += 1
            elif score <= 60:
                conf_buckets["40-60"] += 1
            elif score <= 80:
                conf_buckets["60-80"] += 1
            else:
                conf_buckets["80-100"] += 1

        # ── Remedial ──────────────────────────────────────────────────
        if rec.remedial_result:
            clf = rec.remedial_result.classification
            if clf == RemedialClassification.PASS:
                summary.remedial_pass += 1
            elif clf == RemedialClassification.REMEDIAL_MINOR:
                summary.remedial_minor += 1
            elif clf == RemedialClassification.REMEDIAL_CRITICAL:
                summary.remedial_critical += 1

        # ── Processing time ───────────────────────────────────────────
        if rec.processed_at and rec.uploaded_at:
            delta = (rec.processed_at - rec.uploaded_at).total_seconds()
            if delta >= 0:
                processing_time_sum += delta
                processing_time_count += 1

        # ── Processing-time 24h bucket ────────────────────────────────
        try:
            uploaded = rec.uploaded_at
            age_hours = (now_utc - uploaded).total_seconds() / 3600
            if age_hours <= 24:
                hour = uploaded.hour
                if hour < 4:
                    hour_buckets["00:00"] += 1
                elif hour < 8:
                    hour_buckets["04:00"] += 1
                elif hour < 12:
                    hour_buckets["08:00"] += 1
                elif hour < 16:
                    hour_buckets["12:00"] += 1
                elif hour < 20:
                    hour_buckets["16:00"] += 1
                else:
                    hour_buckets["20:00"] += 1
        except Exception:
            pass

        # ── Site breakdown ────────────────────────────────────────────
        site = (
            (rec.extracted_fields.site_name if rec.extracted_fields else None)
            or (rec.metadata.expected_site_name if rec.metadata else None)
            or "Unknown"
        )
        if site not in site_map:
            site_map[site] = {"approved": 0, "review": 0, "remedial": 0}
        if s in (DocumentStatus.AUTO_APPROVED, DocumentStatus.APPROVED):
            site_map[site]["approved"] += 1
        elif rec.remedial_result and rec.remedial_result.classification in (
            RemedialClassification.REMEDIAL_MINOR,
            RemedialClassification.REMEDIAL_CRITICAL,
        ):
            site_map[site]["remedial"] += 1
        else:
            site_map[site]["review"] += 1

        # ── PPM distribution ──────────────────────────────────────────
        ppm = (
            (rec.extracted_fields.document_type if rec.extracted_fields else None)
            or (rec.metadata.expected_ppm_type if rec.metadata else None)
            or "Other"
        )
        ppm_map[ppm] = ppm_map.get(ppm, 0) + 1

    # ── Finalise scalar fields ─────────────────────────────────────────
    if confidence_count:
        summary.avg_confidence = round(confidence_sum / confidence_count, 2)

    if processing_time_count:
        summary.avg_processing_time_seconds = round(
            processing_time_sum / processing_time_count, 1
        )

    auto_and_approved = summary.auto_approved + summary.approved
    if summary.total_documents:
        summary.auto_approval_rate = round(
            auto_and_approved / summary.total_documents * 100, 2
        )

    # ── Build chart lists (fall back to defaults when empty) ──────────
    any_in_24h = any(v > 0 for v in hour_buckets.values())
    summary.processing_buckets = (
        [{"time": k, "count": v} for k, v in hour_buckets.items()]
        if any_in_24h
        else defaults.get("processing_buckets", [])
    )

    any_conf = any(v > 0 for v in conf_buckets.values())
    summary.confidence_distribution = (
        [{"range": k, "count": v} for k, v in conf_buckets.items()]
        if any_conf
        else defaults.get("confidence_distribution", [])
    )

    summary.site_breakdown = (
        [{"site": k, **v} for k, v in site_map.items() if k != "Unknown"]
        if site_map
        else defaults.get("site_breakdown", [])
    )

    summary.ppm_distribution = (
        sorted(
            [{"type": k, "count": v} for k, v in ppm_map.items()],
            key=lambda x: x["count"],
            reverse=True,
        )
        if ppm_map
        else defaults.get("ppm_distribution", [])
    )

    return summary
