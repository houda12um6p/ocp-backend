from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from ..core.database import get_db
from ..services.webhook_service import WebhookService
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/webhooks", tags=["webhooks"])


class WebhookResponse(BaseModel):
    status: str
    message: str = ""
@router.post("/github/push", response_model=WebhookResponse)
async def github_push_webhook(request: Request, db: Session = Depends(get_db)):
    try:
        payload = await request.json()
        
        webhook_service = WebhookService(db)
        result = await webhook_service.handle_github_push(payload)
        
        if result["status"] == "success":
            return WebhookResponse(
                status="success",
                message=f"Processed {result.get('commits_processed', 0)} commits"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("message", "Unknown error")
            )
    except Exception as e:
        logger.error(f"GitHub push webhook error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Webhook processing failed: {str(e)}"
        )


@router.post("/github/pull-request", response_model=WebhookResponse)
async def github_pull_request_webhook(request: Request, db: Session = Depends(get_db)):
    try:
        payload = await request.json()
        
        webhook_service = WebhookService(db)
        result = await webhook_service.handle_github_pull_request(payload)
        
        if result["status"] == "success":
            return WebhookResponse(
                status="success",
                message=f"Processed PR #{result.get('pr_id')} - {result.get('action')}"
            )
        elif result["status"] == "ignored":
            return WebhookResponse(
                status="ignored",
                message=f"Action {result.get('action')} ignored"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("message", "Unknown error")
            )
    except Exception as e:
        logger.error(f"GitHub PR webhook error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Webhook processing failed: {str(e)}"
        )


@router.post("/github/review-comment", response_model=WebhookResponse)
async def github_review_comment_webhook(request: Request, db: Session = Depends(get_db)):
    try:
        payload = await request.json()
        
        webhook_service = WebhookService(db)
        result = await webhook_service.handle_github_review_comment(payload)
        
        if result["status"] == "success":
            return WebhookResponse(
                status="success",
                message=f"Processed comment - {result.get('action')} - Problem detected: {result.get('is_problem_detected')}"
            )
        elif result["status"] == "ignored":
            return WebhookResponse(
                status="ignored",
                message=f"Action {result.get('action')} ignored"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("message", "Unknown error")
            )
    except Exception as e:
        logger.error(f"GitHub review comment webhook error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Webhook processing failed: {str(e)}"
        )


@router.post("/jira/issue-updated", response_model=WebhookResponse)
async def jira_issue_webhook(request: Request, db: Session = Depends(get_db)):
    try:
        payload = await request.json()
        
        webhook_service = WebhookService(db)
        result = await webhook_service.handle_jira_issue_updated(payload)
        
        if result["status"] == "success":
            return WebhookResponse(
                status="success",
                message=f"Processed Jira issue {result.get('jira_key')} - {result.get('action')}"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("message", "Unknown error")
            )
    except Exception as e:
        logger.error(f"Jira issue webhook error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Webhook processing failed: {str(e)}"
        )
