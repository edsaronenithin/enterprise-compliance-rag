from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.document_version import DocumentVersion


class DocumentRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_document(self, document: Document) -> Document:
        self.db.add(document)
        self.db.commit()
        self.db.refresh(document)

        return document

    def get_document_by_id(self, document_id: int) -> Document | None:
        statement = select(Document).where(Document.id == document_id)

        return self.db.scalar(statement)

    def get_documents(self) -> list[Document]:
        statement = select(Document).order_by(Document.created_at.desc())

        return list(self.db.scalars(statement).all())

    def create_document_version(
        self,
        document_version: DocumentVersion,
    ) -> DocumentVersion:
        self.db.add(document_version)
        self.db.commit()
        self.db.refresh(document_version)

        return document_version

    def get_document_versions(
        self,
        document_id: int,
    ) -> list[DocumentVersion]:
        statement = (
            select(DocumentVersion)
            .where(DocumentVersion.document_id == document_id)
            .order_by(DocumentVersion.version_number.asc())
        )

        return list(self.db.scalars(statement).all())

    def get_latest_version(
        self,
        document_id: int,
    ) -> DocumentVersion | None:
        statement = (
            select(DocumentVersion)
            .where(DocumentVersion.document_id == document_id)
            .order_by(DocumentVersion.version_number.desc())
        )

        return self.db.scalars(statement).first()

    def create_document_with_version(
        self,
        document: Document,
        document_version: DocumentVersion,
    ) -> tuple[Document, DocumentVersion]:

        self.db.add(document)

        self.db.flush()

        document_version.document_id = document.id

        self.db.add(document_version)

        self.db.commit()

        self.db.refresh(document)
        self.db.refresh(document_version)

        return document, document_version

    def add_document(self, document: Document) -> Document:
        self.db.add(document)
        self.db.flush()
        return document

    def add_document_version(
        self,
        document_version: DocumentVersion,
    ) -> DocumentVersion:
        self.db.add(document_version)
        self.db.flush()
        return document_version

    def commit(self) -> None:
        self.db.commit()
