from sqlalchemy import delete

from app.db.session import SessionLocal
from app.models.document import Document
from app.models.document_version import DocumentVersion
from app.repositories.document_repository import DocumentRepository


def test_document_repository():

    db = SessionLocal()

    try:
        repository = DocumentRepository(db)

        document = Document(
            title="Repository Test Document",
            description="Test compliance document",
            file_name="test_policy.pdf",
            file_type="application/pdf",
            status="uploaded",
            uploaded_by=10,
        )

        created_document = repository.create_document(document)

        assert created_document.id is not None
        assert created_document.uploaded_by == 10

        found_document = repository.get_document_by_id(created_document.id)

        assert found_document is not None
        assert found_document.id == created_document.id

        version_1 = DocumentVersion(
            document_id=created_document.id,
            version_number=1,
            file_name="test_policy.pdf",
            storage_path="storage/documents/1/v1/test_policy.pdf",
            file_hash="a" * 64,
        )

        created_version_1 = repository.create_document_version(version_1)

        assert created_version_1.id is not None
        assert created_version_1.version_number == 1

        version_2 = DocumentVersion(
            document_id=created_document.id,
            version_number=2,
            file_name="test_policy_v2.pdf",
            storage_path="storage/documents/1/v2/test_policy_v2.pdf",
            file_hash="b" * 64,
        )

        created_version_2 = repository.create_document_version(version_2)

        assert created_version_2.id is not None
        assert created_version_2.version_number == 2

        versions = repository.get_document_versions(created_document.id)

        assert len(versions) == 2
        assert versions[0].version_number == 1
        assert versions[1].version_number == 2

        latest_version = repository.get_latest_version(created_document.id)

        assert latest_version is not None
        assert latest_version.version_number == 2

    finally:
        if "created_document" in locals():
            db.execute(
                delete(DocumentVersion).where(
                    DocumentVersion.document_id == created_document.id
                )
            )

            db.execute(delete(Document).where(Document.id == created_document.id))

            db.commit()

        db.close()
