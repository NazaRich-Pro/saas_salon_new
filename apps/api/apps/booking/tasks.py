"""Celery tasks for booking app - to be implemented in Stage 13"""
from celery import shared_task


@shared_task
def archive_old_appointments():
    """Archive appointments older than 60 days"""
    # Will be implemented in Stage 13
    pass
