from typing import List, Any
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession

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
    Bulk upload scanned answer sheets for an offline exam.
    """
    if current_user.role not in [UserRole.TEACHER, UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    results = []
    
    for file in files:
        # Process each file
        result = await BulkGradingService.process_bulk_upload(db, exam_id, file)
        results.append(result)
        
    return results
