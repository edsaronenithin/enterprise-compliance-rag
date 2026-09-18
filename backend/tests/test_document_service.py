import hashlib
from pathlib import Path

from sqlalchemy import delete

from app.db.session import SessionLocal
from app.models.document import Document
from app.models.document_version import DocumentVersion
from app.services.document_service import upload_document
import pytest


@pytest.mark.anyio
async def test_upload_document():

    db = SessionLocal()

    test_file_path = Path("storage/documents/999999/v1/test_policy.txt")

    try:
        test_content = b"This is a test compliance document."

        # Create an UploadFile-like object
        from fastapi import UploadFile
        from io import BytesIO

        file = UploadFile(
            file=BytesIO(test_content),
            filename="test_policy.txt",
        )

        # Set content type
        file.headers = {"content-type": "text/plain"}

        # Upload document
        document = await upload_document(
            db=db,
            file=file,
            title="Service Test Document",
            description="Testing document upload service",
            user_id=10,
        )

        # ---------------------------------------------
        # Verify document
        # ---------------------------------------------

        assert document.id is not None
        assert document.title == "Service Test Document"
        assert document.uploaded_by == 10
        assert document.status == "uploaded"

        # ---------------------------------------------
        # Verify version
        # ---------------------------------------------

        version = (
            db.query(DocumentVersion)
            .filter(DocumentVersion.document_id == document.id)
            .first()
        )

        assert version is not None
        assert version.version_number == 1
        assert version.file_name == "test_policy.txt"

        # ---------------------------------------------
        # Verify physical file
        # ---------------------------------------------

        saved_file = Path(version.storage_path)

        assert saved_file.exists()

        # ---------------------------------------------
        # Verify SHA-256
        # ---------------------------------------------

        actual_hash = hashlib.sha256(saved_file.read_bytes()).hexdigest()

        assert version.file_hash == actual_hash

        expected_hash = hashlib.sha256(test_content).hexdigest()

        assert version.file_hash == expected_hash

    finally:
        # Delete versions
        if "document" in locals():
            db.execute(
                delete(DocumentVersion).where(
                    DocumentVersion.document_id == document.id
                )
            )

            # Delete document
            db.execute(delete(Document).where(Document.id == document.id))

            db.commit()

            # Delete uploaded file
            if "version" in locals():
                saved_file = Path(version.storage_path)

                if saved_file.exists():
                    saved_file.unlink()

                # Remove empty directories
                version_directory = saved_file.parent
                document_directory = version_directory.parent

                if version_directory.exists():
                    version_directory.rmdir()

                if document_directory.exists():
                    document_directory.rmdir()

        db.close()
