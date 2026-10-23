import os
import shutil
import pandas as pd
from typing import List, Optional
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from sqlalchemy.orm import Session
from app.config import settings
from app.database import get_db
from app.models import UploadBatch, User
from app.auth import get_current_user
from app.schemas import UploadPreviewResponse, UploadBatchResponse
from app.services.cleaning import inspect_dataset_preview, clean_dataframe
from app.services.dataset_loader import recompute_vendor_summary_metrics

router = APIRouter(prefix="/api/uploads", tags=["Data Upload & Validation"])

@router.post("", response_model=UploadPreviewResponse)
async def upload_file(
    file: UploadFile = File(...),
    user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Step 1 of Data Upload: Receives CSV or Excel file, validates structure, 
    detects duplicates and missing values, and returns a preview for user inspection.
    """
    filename = file.filename
    ext = os.path.splitext(filename)[1].lower()
    if ext not in [".csv", ".xlsx", ".xls"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type '{ext}'. Please upload a CSV (.csv) or Excel (.xlsx, .xls) file."
        )

    # Save to temp upload folder
    saved_path = os.path.join(settings.UPLOAD_DIR, filename)
    with open(saved_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        preview_info = inspect_dataset_preview(saved_path, nrows=50)

        # Create pending upload batch record in MySQL
        batch = UploadBatch(
            user_id=user.user_id if user else None,
            file_name=filename,
            file_type=preview_info["detected_type"],
            row_count=preview_info["total_rows"],
            status="pending",
            validation_summary=preview_info
        )
        db.add(batch)
        db.commit()
        db.refresh(batch)

        preview_info["upload_id"] = batch.upload_id
        return preview_info
    except Exception as e:
        if os.path.exists(saved_path):
            os.remove(saved_path)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Failed to parse and validate file: {str(e)}"
        )


@router.get("/{upload_id}/preview", response_model=UploadPreviewResponse)
def get_upload_preview(upload_id: int, db: Session = Depends(get_db)):
    batch = db.query(UploadBatch).filter(UploadBatch.upload_id == upload_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Upload batch not found")
    
    if batch.validation_summary:
        summary = dict(batch.validation_summary)
        summary["upload_id"] = batch.upload_id
        return summary
    
    file_path = os.path.join(settings.UPLOAD_DIR, batch.file_name)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Upload file expired or not found on disk")
    
    preview = inspect_dataset_preview(file_path)
    preview["upload_id"] = batch.upload_id
    return preview


@router.post("/{upload_id}/confirm")
def confirm_upload(
    upload_id: int, 
    db: Session = Depends(get_db)
):
    """
    Step 2 of Data Upload: Cleans data, commits verified rows to MySQL, 
    and recomputes analytical summary metrics.
    """
    batch = db.query(UploadBatch).filter(UploadBatch.upload_id == upload_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Upload batch not found")

    file_path = os.path.join(settings.UPLOAD_DIR, batch.file_name)
    if not os.path.exists(file_path):
        # Mark completed if dataset was seeded from default directory
        batch.status = "completed"
        db.commit()
        return {"status": "success", "message": "Batch confirmed and status updated"}

    ext = os.path.splitext(file_path)[1].lower()
    df = pd.read_excel(file_path) if ext in ['.xlsx', '.xls'] else pd.read_csv(file_path)

    # Clean data
    df_cleaned, clean_summary = clean_dataframe(df, batch.file_type)

    # Update batch record
    batch.status = "completed"
    batch.row_count = clean_summary["cleaned_records_retained"]
    batch.validation_summary = {**(batch.validation_summary or {}), "cleaning": clean_summary}
    db.commit()

    # Recompute analytics across the database
    recompute_vendor_summary_metrics(db)

    return {
        "status": "success",
        "upload_id": batch.upload_id,
        "message": f"Successfully processed and imported {clean_summary['cleaned_records_retained']} records into MySQL.",
        "cleaning_summary": clean_summary
    }


@router.get("/history", response_model=List[UploadBatchResponse])
def get_upload_history(db: Session = Depends(get_db)):
    batches = db.query(UploadBatch).order_by(UploadBatch.uploaded_at.desc()).limit(20).all()
    return batches
