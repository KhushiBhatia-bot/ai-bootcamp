import io
import re
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Request
from sqlalchemy.orm import Session
from pypdf import PdfReader
import docx

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.chat import Chat
from app.models.user import User

router = APIRouter(prefix="/api/v1/documents", tags=["Documents"])


def unicode_safe(text: str) -> str:
    """
    Remove characters that cause JSON serialization issues in JavaScript:
    - Lone surrogates (\\uD800–\\uDFFF) that are unpaired
    - Null bytes (\\x00)
    This prevents JSON.stringify() failures in the browser when PDF text
    is embedded into a message payload.
    """
    if not text:
        return text
    # Remove null bytes
    text = text.replace("\x00", "")
    # Remove lone surrogates using encode/decode trick
    try:
        text = text.encode("utf-16", "surrogatepass").decode("utf-16", "ignore")
    except Exception:
        # Fallback: re-encode as ASCII-safe
        text = text.encode("utf-8", "replace").decode("utf-8", "replace")
    return text


@router.post("/upload")
async def upload_document(
    request: Request,
    file: Optional[UploadFile] = File(None),
    current_user: User = Depends(get_current_user),
):
    # Fallback to inspecting multipart form if field name varied
    if file is None:
        try:
            form = await request.form()
            for key in ["file", "document", "upload", "doc"]:
                if key in form:
                    candidate = form[key]
                    if hasattr(candidate, "filename") and candidate.filename:
                        file = candidate
                        break
        except Exception:
            pass

    if file is None or not getattr(file, "filename", None):
        raise HTTPException(
            status_code=400,
            detail="No file provided. Please choose a PDF, DOCX, TXT, MD, or CSV file to upload.",
        )

    filename = file.filename or "uploaded_doc"
    try:
        contents = await file.read()
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Could not read uploaded file: {str(e)}",
        )

    if not contents:
        raise HTTPException(
            status_code=400,
            detail="The uploaded file is empty.",
        )

    extracted_text = ""

    try:
        filename_lower = filename.lower()
        if filename_lower.endswith(".pdf"):
            pdf_file = io.BytesIO(contents)
            reader = PdfReader(pdf_file)
            pages_text = []
            for i, page in enumerate(reader.pages):
                try:
                    page_str = page.extract_text() or ""
                    if page_str.strip():
                        pages_text.append(f"--- Page {i+1} ---\n{page_str.strip()}")
                except Exception:
                    continue
            extracted_text = "\n\n".join(pages_text)

        elif filename_lower.endswith(".docx"):
            docx_file = io.BytesIO(contents)
            doc = docx.Document(docx_file)
            extracted_text = "\n".join([p.text for p in doc.paragraphs if p.text.strip()])

        elif filename_lower.endswith((".txt", ".md", ".csv", ".json", ".py", ".js", ".html")):
            extracted_text = contents.decode("utf-8", errors="ignore")

        else:
            raise HTTPException(
                status_code=400,
                detail="Unsupported file format. Please upload PDF, DOCX, TXT, MD, or CSV files.",
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to process document: {str(e)}",
        )

    # Clean up any problematic Unicode that would break JSON.stringify in the browser
    extracted_text = unicode_safe(extracted_text)

    if not extracted_text.strip():
        raise HTTPException(
            status_code=400,
            detail="The uploaded document contains no readable text.",
        )

    # Trim to 35,000 characters if extraordinarily long to fit context window comfortably
    trimmed = False
    if len(extracted_text) > 35000:
        extracted_text = extracted_text[:35000] + "\n\n...[Document content truncated for context limit]..."
        trimmed = True

    return {
        "filename": filename,
        "char_count": len(extracted_text),
        "text": extracted_text,
        "trimmed": trimmed,
    }
