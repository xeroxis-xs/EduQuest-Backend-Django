from celery import shared_task
from django.utils import timezone
from .models import Quest


@shared_task
def check_expired_quest():
    now = timezone.now()
    expired_quests = Quest.objects.filter(expiration_date__lt=now, status='Active')
    expired_quests_ids = [quest.id for quest in expired_quests]
    if not expired_quests:
        return "[Celery] No expired quests found that need to be updated"

    for quest in expired_quests:
        quest.status = 'Expired'
        quest.save()
    return f"[Celery]  {len(expired_quests)} expired quests: {expired_quests_ids}"
