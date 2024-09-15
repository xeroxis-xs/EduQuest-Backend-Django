from celery import shared_task
from django.utils import timezone
from django.db.models import Max

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
            return  # Do not process private quests

        if not attempt.submitted:
            return  # Attempt is not submitted yet

        user = attempt.student

        # Check if the user has any "First Attempt" badge
        has_badge = UserQuestBadge.objects.filter(
            quest_attempted__student=user,
            badge__name="First Attempt"
        ).exists()

        if not has_badge:
            # Award the "First Attempt" badge
            badge = Badge.objects.get(name="First Attempt")
            user_quest_badge, created = UserQuestBadge.objects.get_or_create(
                badge=badge,
                quest_attempted=attempt
            )
            if created:
                print(f"[First Attempt] Badge awarded to user: {user.username}")
            else:
                print(f"[First Attempt] User: {user.username} already has the badge")
        else:
            print(f"[First Attempt] User: {user.username} already has the badge")

    except UserQuestAttempt.DoesNotExist:
        print(f"[First Attempt] UserQuestAttempt with id {user_quest_attempt_id} does not exist.")
    except Badge.DoesNotExist:
        print("[First Attempt] Badge 'First Attempt' does not exist.")

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
            return  # Do not process private quests

        if not attempt.submitted:
            return  # Attempt is not submitted yet

        # Calculate the total max score for the quest
        quest_max_score = quest.total_max_score()
        total_score_achieved = attempt.total_score_achieved

        if total_score_achieved == quest_max_score:
            # Award the "Perfectionist" badge
            badge = Badge.objects.get(name="Perfectionist")
            user_quest_badge, created = UserQuestBadge.objects.get_or_create(
                badge=badge,
                quest_attempted=attempt
            )
            if created:
                print(f"[Perfectionist] Badge awarded to user: {attempt.student.username}")
            else:
                print(f"[Perfectionist] User: {attempt.student.username} already has the badge for this quest")
        else:
            print(f"[Perfectionist] User: {attempt.student.username} did not achieve full marks")

    except UserQuestAttempt.DoesNotExist:
        print(f"[Perfectionist] UserQuestAttempt with id {user_quest_attempt_id} does not exist.")
    except Badge.DoesNotExist:
        print("[Perfectionist] Badge 'Perfectionist' does not exist.")
    except Quest.DoesNotExist:
        print(f"[Perfectionist] Quest for UserQuestAttempt with id {user_quest_attempt_id} does not exist.")


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
            return  # Do not process private quests

        # Get all user quest attempts with a score greater than 0
        user_quest_attempts = UserQuestAttempt.objects.filter(
            quest=quest,
            total_score_achieved__gt=0
        ).exclude(first_attempted_date=None, last_attempted_date=None)

        if not user_quest_attempts.exists():
            print(f"[Speedster] No eligible attempts for quest: {quest.name}")
            return

        # Filter out attempts with zero or negative time_taken
        filtered_attempts = [
            attempt for attempt in user_quest_attempts if attempt.time_taken > 0
        ]

        if not filtered_attempts:
            print(f"[Speedster] No attempts with valid time_taken for quest: {quest.name}")
            return

        # Find the fastest attempt
        fastest_attempt = min(filtered_attempts, key=lambda x: x.time_taken)
        fastest_attempt_score = fastest_attempt.total_score_achieved

        print(f"[Speedster] Fastest attempt for quest: {quest.name} is by user: {fastest_attempt.student.username} with score: {fastest_attempt_score}")

        # Get top three unique scores
        unique_scores = user_quest_attempts.values_list('total_score_achieved', flat=True).distinct().order_by('-total_score_achieved')[:3]
        top_three_scores = list(unique_scores)

        print(f"[Speedster] Top three scores for quest: {quest.name} are: {top_three_scores}")

        if fastest_attempt_score in top_three_scores:
            badge, created = UserQuestBadge.objects.get_or_create(
                badge=Badge.objects.get(name="Speedster"),
                quest_attempted=fastest_attempt
            )
            if created:
                print(f"[Speedster] Badge awarded to user: {fastest_attempt.student.username}")
            else:
                print(f"[Speedster] User: {fastest_attempt.student.username} already has the badge.")
        else:
            print(f"[Speedster] Fastest user is not among the top three scorers for quest: {quest.name}")

    except Quest.DoesNotExist:
        print(f"[Speedster] Quest with id {quest_id} does not exist.")


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
            return  # Do not process private quests

        if quest.status != "Expired":
            return  # Quest is not expired yet

        # Get all user quest attempts for the quest
        user_quest_attempts = UserQuestAttempt.objects.filter(quest=quest)

        if not user_quest_attempts.exists():
            print(f"[Expert] No attempts found for quest: {quest.name}")
            return

        # Find the highest score
        highest_score = user_quest_attempts.aggregate(
            max_score=Max('total_score_achieved')
        )['max_score'] or 0

        if highest_score <= 0:
            print(f"[Expert] No user scored above 0 for quest: {quest.name}")
            return

        # Get all attempts with the highest score
        top_attempts = user_quest_attempts.filter(total_score_achieved=highest_score)

        badge = Badge.objects.get(name="Expert")
        print(f"[Expert] Highest score for quest: {quest.name} is: {highest_score}")

        if top_attempts.count() == 0:
            print(f"[Expert] No attempts with the highest score for quest: {quest.name}")
            return

        for attempt in top_attempts:
            user_quest_badge, created = UserQuestBadge.objects.get_or_create(
                badge=badge,
                quest_attempted=attempt
            )
            if created:
                print(f"[Expert] Badge awarded to user: {attempt.student.username}")
            else:
                print(f"[Expert] User: {attempt.student.username} already has the badge for this quest")

    except Quest.DoesNotExist:
        print(f"[Expert] Quest with id {quest_id} does not exist.")
    except Badge.DoesNotExist:
        print("[Expert] Badge 'Expert' does not exist.")


@shared_task
def award_completionist_badge(user_course_group_enrollment_id):
    """
    Award the "Completionist" badge to a user who has completed the course group.
    Triggered after UserCourseGroupEnrollment.completed_on is set.
    """
    from .models import UserCourseGroupEnrollment, Badge, UserCourseBadge
    try:
        user_course_group_enrollment = UserCourseGroupEnrollment.objects.get(id=user_course_group_enrollment_id)
        user = user_course_group_enrollment.student
        course_group = user_course_group_enrollment.course_group

        if user_course_group_enrollment.completed_on is None:
            return  # Enrollment is not completed yet

        # Award the "Completionist" badge
        badge = Badge.objects.get(name="Completionist")
        user_course_badge, created = UserCourseBadge.objects.get_or_create(
            badge=badge,
            user_course_group_enrollment=user_course_group_enrollment
        )
        if created:
            print(f"[Completionist] Badge awarded to user: {user.username} for completing course group: {course_group.name}")
        else:
            print(f"[Completionist] User: {user.username} already has the badge for course group: {course_group.name}")
    except UserCourseGroupEnrollment.DoesNotExist:
        print(f"[Completionist] UserCourseGroupEnrollment with id {user_course_group_enrollment_id} does not exist.")
    except Badge.DoesNotExist:
        print("[Completionist] Badge 'Completionist' does not exist.")
    except Exception as e:
        print(f"[Completionist] Error: {e}")


@shared_task
def check_course_completion_and_update_enrollment(user_quest_attempt_id):
    """
    Check if the user has completed all quests in the course group.
    If so, update UserCourseGroupEnrollment.completed_on date to current date.
    """
    from django.utils import timezone
    from .models import UserQuestAttempt, Quest, UserCourseGroupEnrollment
    try:
        attempt = UserQuestAttempt.objects.get(id=user_quest_attempt_id)
        quest = attempt.quest

        if quest.type == "Private":
            return  # Do not process private quests

        if not attempt.submitted:
            return  # Attempt is not submitted yet

        course_group = quest.course_group
        user = attempt.student

        # Get or create the UserCourseGroupEnrollment
        user_course_group_enrollment, created = UserCourseGroupEnrollment.objects.get_or_create(
            student=user,
            course_group=course_group
        )

        # If completed_on is already set, no need to proceed
        if user_course_group_enrollment.completed_on:
            return

        # Get all non-private quests under the course group
        quests_in_group = Quest.objects.filter(
            course_group=course_group
        ).exclude(type="Private")

        # Check if there are any quests to complete
        if not quests_in_group.exists():
            return

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
            print(f"[Course Completion Check] User {user.username} has completed the course group {course_group.name}")
        else:
            print(f"[Course Completion Check] User {user.username} has not yet completed all quests in course group {course_group.name}")
    except Exception as e:
        print(f"[Course Completion Check] Error in check_course_completion_and_update_enrollment: {e}")

@shared_task
def update_user_quest_attempt_score_and_points_task(user_quest_attempt_id):
    """
    Task to calculate total score achieved for a quest attempt and update the user's total points.
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
                print(f"[Update User Points] User {instance.student.username} earned {points_to_add} points for quest attempt {instance.id}")

    except UserQuestAttempt.DoesNotExist:
        print(f"[Error] UserQuestAttempt with id {user_quest_attempt_id} does not exist.")
    except Exception as e:
        print(f"[Error] Failed to update score and points for UserQuestAttempt {user_quest_attempt_id}: {e}")
