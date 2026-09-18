from pathlib import Path
import hashlib

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.document_version import DocumentVersion
from app.repositories.document_repository import DocumentRepository


UPLOAD_DIRECTORY = Path("storage/documents")

ALLOWED_FILE_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/plain",
}

MAX_FILE_SIZE = 25 * 1024 * 1024  # 25 MB


def validate_file(file: UploadFile) -> None:
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File name is required",
        )

    if file.content_type not in ALLOWED_FILE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file type",
        )


async def upload_document(
    db: Session,
    file: UploadFile,
    title: str,
    description: str | None,
    user_id: int,
) -> Document:

    validate_file(file)

    repository = DocumentRepository(db)

    document = Document(
        title=title,
        description=description,
        file_name=file.filename,
        file_type=file.content_type,
        status="uploaded",
        uploaded_by=user_id,
    )

    version_number = 1

    storage_path: Path | None = None

    try:
        # 1. Add document and generate its ID
        repository.add_document(document)

        # 2. Create storage directory
        document_directory = UPLOAD_DIRECTORY / str(document.id) / f"v{version_number}"

        document_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        # 3. Create file path
        storage_path = document_directory / Path(file.filename).name

        # 4. Save file and calculate SHA-256
        sha256 = hashlib.sha256()
        total_size = 0

        with storage_path.open("wb") as buffer:
            while chunk := await file.read(1024 * 1024):
                total_size += len(chunk)

                if total_size > MAX_FILE_SIZE:
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail="File size exceeds the 25 MB limit",
                    )

                sha256.update(chunk)
                buffer.write(chunk)

        file_hash = sha256.hexdigest()

        # 5. Create document version
        document_version = DocumentVersion(
            document_id=document.id,
            version_number=version_number,
            file_name=file.filename,
            storage_path=str(storage_path),
            file_hash=file_hash,
        )

        repository.add_document_version(document_version)

        # 6. Commit document + version together
        repository.commit()

        # 7. Refresh document
        db.refresh(document)

        return document

    except Exception:
        # Roll back database transaction
        db.rollback()

        # Remove file if it was created
        if storage_path is not None:
            storage_path.unlink(missing_ok=True)

        raise
