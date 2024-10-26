import logging
from celery import shared_task
from django.utils import timezone
from django.db.models import Max

# Configure the logger
logger = logging.getLogger(__name__)

@shared_task
def test_task():
    """
    A test task to check if Celery is working.
    Alternatively, use "env | grep CELERY" inside the celery container to check if the environment variables are set.
    """
    logger.info("Test task is being processed.")
    return "Task Completed"


@shared_task
def check_expired_quest():
    """
    Check for expired quests and update their status to 'Expired'.
    """
    from .models import Quest
    now = timezone.now()
    expired_quests = Quest.objects.filter(expiration_date__lt=now, status='Active')
    expired_quests_ids = [quest.id for quest in expired_quests]
    if not expired_quests:
        return "[Expired Quest Check] No expired quests found that need to be updated"

    for quest in expired_quests:
        quest.status = 'Expired'
        quest.save()
    return f"[Expired Quest Check] {len(expired_quests)} expired quests: {expired_quests_ids}"


@shared_task
def calculate_score_and_issue_points(user_quest_attempt_id):
    """
    Task update the user's total points.
    """
    from django.db import transaction
    from django.db.models import Max
    from .models import UserQuestAttempt

    try:
        # Retrieve the UserQuestAttempt instance
        instance = UserQuestAttempt.objects.get(id=user_quest_attempt_id)

        # Update the total score achieved and user's total points
        with transaction.atomic():
            # Calculate the total score achieved
            total_score_achieved = instance.calculate_total_score_achieved()
            instance.total_score_achieved = total_score_achieved
            instance.save(update_fields=['total_score_achieved'])

            # Async tasks to award badges
            award_perfectionist_badge.delay(user_quest_attempt_id)

            # Get the user's highest score achieved for this quest, excluding the current attempt
            highest_score_achieved = UserQuestAttempt.objects.filter(
                student=instance.student,
                quest=instance.quest,
                submitted=True
            ).exclude(pk=instance.pk).aggregate(
                max_score=Max('total_score_achieved')
            )['max_score'] or 0

            # Update the user's total points if the new score is higher
            if total_score_achieved > highest_score_achieved and instance.quest.type != 'Private':
                points_to_add = total_score_achieved - highest_score_achieved
                instance.student.total_points += points_to_add
                instance.student.save(update_fields=['total_points'])
                return f"[Update User Points] User {instance.student.username} earned {points_to_add} points for quest attempt {instance.id}"

            return f"[Update User Points] User {instance.student.username} did not earn any points for quest attempt {instance.id}"

    except UserQuestAttempt.DoesNotExist:
        return f"[Error] UserQuestAttempt with id {user_quest_attempt_id} does not exist."
    except Exception as e:
        return f"[Error] Failed to update score and points for UserQuestAttempt {user_quest_attempt_id}: {e}"


@shared_task
def award_first_attempt_badge(user_quest_attempt_id):
    """
    Award the "First Attempt" badge to a user who has attempted a quest for the first time.
    Triggered after a user quest attempt is submitted.
    """
    from .models import UserQuestAttempt, Badge, UserQuestBadge
    try:
        attempt = UserQuestAttempt.objects.get(id=user_quest_attempt_id)
        quest = attempt.quest

        if quest.type == "Private":
            return f"[First Attempt] Skipping private quest: {quest.name}"

        if not attempt.submitted:
            return f"[First Attempt] Attempt for quest: {quest.name} is not submitted yet"

        user = attempt.student

        # Check if the user has any "First Attempt" badge
        has_badge = UserQuestBadge.objects.filter(
            user_quest_attempt__student=user,
            badge__name="First Attempt"
        ).exists()

        if not has_badge:
            # Award the "First Attempt" badge
            badge = Badge.objects.get(name="First Attempt")
            user_quest_badge, created = UserQuestBadge.objects.get_or_create(
                badge=badge,
                user_quest_attempt=attempt
            )
            if created:
                return f"[First Attempt] Badge awarded to user: {user.username}"
            else:
                return f"[First Attempt] User: {user.username} already has the badge"
        return f"[First Attempt] User: {user.username} already has the badge"

    except UserQuestAttempt.DoesNotExist:
        return f"[First Attempt] UserQuestAttempt with id {user_quest_attempt_id} does not exist."
    except Badge.DoesNotExist:
        return "[First Attempt] Badge 'First Attempt' does not exist."

@shared_task
def award_perfectionist_badge(user_quest_attempt_id):
    """
    Award the "Perfectionist" badge to a user who has achieved full marks for a quest.
    Triggered after a user quest attempt is submitted.
    """
    from .models import Quest, UserQuestAttempt, UserQuestBadge, Badge
    try:
        attempt = UserQuestAttempt.objects.get(id=user_quest_attempt_id)
        quest = attempt.quest

        if quest.type == "Private":
            return f"[Perfectionist] Skipping private quest: {quest.name}"

        if quest.total_max_score() == 0:
            return f"[Perfectionist] Skipping Quest: {quest.name} only has open-ended / mcq with no correct ans questions"

        if not attempt.submitted:
            return f"[Perfectionist] Attempt for quest: {quest.name} is not submitted yet"

        # Calculate the total max score for the quest
        quest_max_score = quest.total_max_score()
        total_score_achieved = attempt.total_score_achieved

        if total_score_achieved == quest_max_score:
            # Award the "Perfectionist" badge
            badge = Badge.objects.get(name="Perfectionist")
            user_quest_badge, created = UserQuestBadge.objects.get_or_create(
                badge=badge,
                user_quest_attempt=attempt
            )
            if created:
                return f"[Perfectionist] Badge awarded to user: {attempt.student.username}"
            else:
                return f"[Perfectionist] User: {attempt.student.username} already has the badge for this quest"
        else:
            return f"[Perfectionist] User: {attempt.student.username} did not achieve full marks: ({total_score_achieved}/{quest_max_score})"

    except UserQuestAttempt.DoesNotExist:
        return f"[Perfectionist] UserQuestAttempt with id {user_quest_attempt_id} does not exist."
    except Badge.DoesNotExist:
        return "[Perfectionist] Badge 'Perfectionist' does not exist."
    except Quest.DoesNotExist:
        return f"[Perfectionist] Quest for UserQuestAttempt with id {user_quest_attempt_id} does not exist."


@shared_task
def award_speedster_badge(quest_id):
    """
    Award the "Speedster" badge to the fastest user who has completed a quest.
    Triggered after a quest status is changed from Active to Expired.
    """
    from .models import Quest, UserQuestAttempt, UserQuestBadge, Badge
    try:
        quest = Quest.objects.get(id=quest_id)
        if quest.type == "Private":
            return f"[Speedster] Skipping private quest: {quest.name}"

        if quest.total_max_score() == 0:
            return f"[Speedster] Skipping Quest: {quest.name} only has open-ended / mcq with no correct ans questions"

        # Get all user quest attempts with a score greater than 0
        user_quest_attempts = UserQuestAttempt.objects.filter(
            quest=quest,
            total_score_achieved__gt=0
        ).exclude(first_attempted_date=None, last_attempted_date=None)

        if not user_quest_attempts.exists():
            return f"[Speedster] No eligible attempts for quest: {quest.name}"

        # Filter out attempts with zero or negative time_taken
        filtered_attempts = [
            attempt for attempt in user_quest_attempts if attempt.time_taken > 0
        ]

        if not filtered_attempts:
            return f"[Speedster] No attempts with valid time_taken for quest: {quest.name}"

        # Find the fastest attempt
        fastest_attempt = min(filtered_attempts, key=lambda x: x.time_taken)
        fastest_attempt_score = fastest_attempt.total_score_achieved

        logger.info(f"[Speedster] Fastest attempt for quest: {quest.name} is by user: {fastest_attempt.student.username} with score: {fastest_attempt_score}")

        # Get top three unique scores
        unique_scores = user_quest_attempts.values_list('total_score_achieved', flat=True).distinct().order_by('-total_score_achieved')[:3]
        top_three_scores = list(unique_scores)

        logger.info(f"[Speedster] Top three scores for quest: {quest.name} are: {top_three_scores}")

        if fastest_attempt_score in top_three_scores:
            badge, created = UserQuestBadge.objects.get_or_create(
                badge=Badge.objects.get(name="Speedster"),
                user_quest_attempt=fastest_attempt
            )
            if created:
                return f"[Speedster] Badge awarded to user: {fastest_attempt.student.username}"
            else:
                return f"[Speedster] User: {fastest_attempt.student.username} already has the badge."
        else:
            return f"[Speedster] Fastest user is not among the top three scorers for quest: {quest.name}"

    except Quest.DoesNotExist:
        return f"[Speedster] Quest with id {quest_id} does not exist."


@shared_task
def award_expert_badge(quest_id):
    """
    Award the "Expert" badge to the user who has scored the highest for a quest.
    Triggered after a quest status is changed from Active to Expired.
    """
    from .models import Quest, UserQuestAttempt, UserQuestBadge, Badge
    try:
        quest = Quest.objects.get(id=quest_id)

        if quest.type == "Private":
            return f"[Expert] Skipping private quest: {quest.name}"

        if quest.total_max_score() == 0:
            return f"[Expert] Skipping Quest: {quest.name} only has open-ended / mcq with no correct ans questions"

        if quest.status != "Expired":
            return f"[Expert] Quest: {quest.name} is not expired yet"

        # Get all user quest attempts for the quest
        user_quest_attempts = UserQuestAttempt.objects.filter(quest=quest)

        if not user_quest_attempts.exists():
            return f"[Expert] No attempts found for quest: {quest.name}"

        # Find the highest score
        highest_score = user_quest_attempts.aggregate(
            max_score=Max('total_score_achieved')
        )['max_score'] or 0

        if highest_score <= 0:
            return f"[Expert] No user scored above 0 for quest: {quest.name}"

        # Get all attempts with the highest score
        top_attempts = user_quest_attempts.filter(total_score_achieved=highest_score)

        badge = Badge.objects.get(name="Expert")
        logger.info(f"[Expert] Highest score for quest: {quest.name} is: {highest_score}")

        if top_attempts.count() == 0:
            return f"[Expert] No attempts with the highest score for quest: {quest.name}"

        users_awarded = []
        for attempt in top_attempts:
            UserQuestBadge.objects.get_or_create(
                badge=badge,
                user_quest_attempt=attempt
            )
            users_awarded.append(attempt.student.username)

        return f"[Expert] Badge awarded to users: {users_awarded} with the highest score: {highest_score} for quest: {quest.name}"

    except Quest.DoesNotExist:
        return f"[Expert] Quest with id {quest_id} does not exist."
    except Badge.DoesNotExist:
        return f"[Expert] Badge 'Expert' does not exist."


# @shared_task
# def award_completionist_badge(user_course_group_enrollment):
#     """
#     Award the "Completionist" badge to a user who has completed the course group.
#     Triggered after a course status is changed from Active to Expired.
#     """
#     from .models import UserCourseGroupEnrollment, Badge, UserCourseBadge
#     try:
#         # Award the "Completionist" badge
#         badge = Badge.objects.get(name="Completionist")
#         user_course_badge, created = UserCourseBadge.objects.get_or_create(
#             badge=badge,
#             user_course_group_enrollment=user_course_group_enrollment
#         )
#         awarded_users.append(user.username)
#             # if created:
#             #     return f"[Completionist] Badge awarded to user: {user.username} for completing course group: {course_group.name}"
#             # else:
#             #     return f"[Completionist] User: {user.username} already has the badge for course group: {course_group.name}"
#         return f"[Completionist] Badge awarded to users: {awarded_users} for completing course group: {course_group.name}"
#     except UserCourseGroupEnrollment.DoesNotExist:
#         return f"[Completionist] UserCourseGroupEnrollment with course id {course_id} does not exist."
#     except Badge.DoesNotExist:
#         return "[Completionist] Badge 'Completionist' does not exist."
#     except Exception as e:
#         return f"[Completionist] Error: {e}"


@shared_task
def check_course_completion_and_award_completionist_badge(course_id):
    """
    Check if the user has completed all quests in the course group.
    If so, update UserCourseGroupEnrollment.completed_on date to current date
    and issue the "Completionist" badge.
    Triggered after a course status is changed from Active to Expired.
    """
    from django.utils import timezone
    from .models import UserQuestAttempt, Quest, UserCourseGroupEnrollment, Badge, UserCourseBadge
    try:

        user_course_group_enrollments = UserCourseGroupEnrollment.objects.filter(course_group__course_id=course_id)

        if not user_course_group_enrollments.exists():
            return f"[Course Completion Check] No user enrollments found for course: {course_id}"

        awarded_users = []
        for user_course_group_enrollment in user_course_group_enrollments:
            course_group = user_course_group_enrollment.course_group
            user = user_course_group_enrollment.student

            # Get all non-private quests under the course group
            quests_in_group = Quest.objects.filter(
                course_group=course_group
            ).exclude(type="Private")

            # Check if there are any quests to complete
            if not quests_in_group.exists():
                logger.info(f"[Course Completion Check] No quests found in course group {course_group.name}")
                continue

            # Get IDs of all quests in the course group
            quests_in_group_ids = set(quests_in_group.values_list('id', flat=True))

            # Get IDs of quests the user has submitted attempts for
            user_attempts_in_group = set(
                UserQuestAttempt.objects.filter(
                    student=user,
                    quest__in=quests_in_group,
                    submitted=True
                ).values_list('quest_id', flat=True)
            )
            # Check if the user has submitted attempts for all quests
            if quests_in_group_ids == user_attempts_in_group:
                # User has completed all quests
                user_course_group_enrollment.completed_on = timezone.now()
                user_course_group_enrollment.save()

                # Award the "Completionist" badge
                badge = Badge.objects.get(name="Completionist")
                UserCourseBadge.objects.get_or_create(
                    badge=badge,
                    user_course_group_enrollment=user_course_group_enrollment
                )
                awarded_users.append(user_course_group_enrollment.student.username)

        return f"[Course Completion Check] Badge awarded to users: {awarded_users} for completing course group: {course_group}"

    except UserCourseGroupEnrollment.DoesNotExist:
        return f"[Course Completion Check] UserCourseGroupEnrollment with course id {course_id} does not exist."





