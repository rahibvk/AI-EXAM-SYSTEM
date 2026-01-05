"""
Bulk Grading Workflow Endpoints

Purpose:
    Orchestrates the 2-Step Bulk Grading Process for physical exams.
    1. **Upload**: User uploads scanned PDFs -> System OCRs/analyzes them -> Returns draft data.
    2. **Confirm**: User verifies/edits the mapped answers -> System saves & grades them.
"""
from typing import List, Any, Dict
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Body
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.api import deps
from app.db.session import get_db
from app.models.user import User, UserRole
from app.services.bulk_grading_service import BulkGradingService

router = APIRouter()

@router.post("/{exam_id}/bulk-upload", response_model=Any)
async def bulk_upload_exam_papers(
    exam_id: int,
    files: List[UploadFile] = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Phase 1: Upload and Analyze scanned answer sheets.
    Returns extracted data for confirmation.
    """
    if current_user.role not in [UserRole.TEACHER, UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    results = []
    
    for file in files:
        # Process each file (Analysis Only)
        result = await BulkGradingService.process_bulk_upload(db, exam_id, file)
        results.append(result)
        
    return results

class ConfirmUploadRequest(BaseModel):
    student_id: int
    answers: Dict[str, str]

@router.post("/{exam_id}/confirm-upload", response_model=Any)
async def confirm_bulk_upload(
    exam_id: int,
    payload: ConfirmUploadRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Phase 2: Confirm and Evaluate.
    """
    if current_user.role not in [UserRole.TEACHER, UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Not authorized")

    result = await BulkGradingService.confirm_grading(
        db, 
        exam_id, 
        payload.student_id, 
        payload.answers
    )
    return result
