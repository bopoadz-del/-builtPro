"""Hydration pipeline stub."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import json
from typing import Any, Dict, Iterable

from backend.reasoning.db_models import DocumentEntity, DocumentLink

from .models import Document, DocumentVersion, HydrationRun, HydrationRunItem, SourceType, WorkspaceSource


@dataclass
class HydrationOptions:
    dry_run: bool = False


class HydrationPipeline:
    def __init__(
        self,
        db_session,
        indexing_client: Any | None = None,
        ule_hook: Any | None = None,
        connectors: Dict[SourceType, Any] | None = None,
    ) -> None:
        self.db_session = db_session
        self.indexing_client = indexing_client
        self.ule_hook = ule_hook
        self.connectors = connectors or {}

    def hydrate_workspace(self, workspace_id: str, options: HydrationOptions) -> None:
        sources = (
            self.db_session.query(WorkspaceSource)
            .filter(WorkspaceSource.workspace_id == workspace_id, WorkspaceSource.is_enabled.is_(True))
            .all()
        )
        run = HydrationRun(workspace_id=workspace_id, started_at=datetime.utcnow(), status="running")
        self.db_session.add(run)
        self.db_session.commit()

        files_seen = 0
        for source in sources:
            source_type = self._coerce_source_type(source.source_type)
            if source_type is None:
                continue
            connector_cls = self.connectors.get(source_type)
            if connector_cls is None:
                continue
            config = json.loads(source.config_json)
            connector = connector_cls(config, secrets_ref=None)
            connector.validate_config()
            items, cursor = connector.list_changes(source.cursor_json)
            for item in items:
                files_seen += 1
                metadata = connector.get_metadata(item)
                document = (
                    self.db_session.query(Document)
                    .filter(
                        Document.workspace_id == workspace_id,
                        Document.source_document_id == metadata["source_document_id"],
                    )
                    .first()
                )
                if document is None:
                    document = Document(
                        workspace_id=workspace_id,
                        source_document_id=metadata["source_document_id"],
                        name=metadata["name"],
                    )
                    self.db_session.add(document)
                    self.db_session.commit()

                checksum = metadata.get("checksum") or ""
                existing = (
                    self.db_session.query(DocumentVersion)
                    .filter(DocumentVersion.document_id == document.id, DocumentVersion.checksum == checksum)
                    .first()
                )
                if existing is None:
                    version = DocumentVersion(document_id=document.id, checksum=checksum)
                    self.db_session.add(version)
                    self.db_session.commit()

                    content = connector.download(item)
                    text = content.decode("utf-8") if isinstance(content, (bytes, bytearray)) else str(content)
                    chunks = self._chunk_text(text)

                    if self.indexing_client is not None:
                        self.indexing_client.index_chunks(workspace_id, document.id, version.id, chunks)

                    self._run_ule_hook(workspace_id, document.id, document.name, text)

                run_item = HydrationRunItem(run_id=run.id, source_id=source.id, document_id=document.id)
                self.db_session.add(run_item)
                self.db_session.commit()

            source.cursor_json = cursor
            self.db_session.commit()

        run.files_seen = files_seen
        run.status = "completed"
        self.db_session.commit()

    def _chunk_text(self, text: str) -> Iterable[str]:
        for line in text.splitlines():
            if line.strip():
                yield line

    def _coerce_source_type(self, raw: str) -> SourceType | None:
        if raw in SourceType._value2member_map_:
            return SourceType(raw)
        if raw.startswith("SourceType."):
            key = raw.split(".", 1)[1]
            if key in SourceType.__members__:
                return SourceType[key]
        if raw in SourceType.__members__:
            return SourceType[raw]
        return None

    def _run_ule_hook(self, workspace_id: str, document_id: int, document_name: str, text: str) -> None:
        if self.ule_hook is not None:
            self.ule_hook.run(self.db_session, workspace_id, document_id, document_name, text)
            return

        entity = DocumentEntity(workspace_id=workspace_id, document_id=document_id, name=document_name)
        self.db_session.add(entity)
        self.db_session.commit()
        link = DocumentLink(document_id=document_id, entity_id=entity.id, link_type="mentions")
        self.db_session.add(link)
        self.db_session.commit()
