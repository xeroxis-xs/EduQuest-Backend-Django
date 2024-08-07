from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db.models import signals, Sum
from .models import (
    EduquestUser,
    Image,
    AcademicYear,
    Term,
    Course,
    Quest,
    UserQuestAttempt,
    UserQuestQuestionAttempt,
    UserCourse,
    Badge,
    UserQuestBadge,
    UserCourseBadge,
)
from django.utils import timezone


@receiver(post_save, sender=UserQuestAttempt)
def award_perfectionist_quest_badges(sender, instance, created, **kwargs):
    if not created:
        if instance.all_questions_submitted:
            print(f"[Perfectionist] Quest attempt: {instance.id} has been submitted")
            # Check if the user has obtained full marks for the quest attempt
            quest = Quest.objects.get(id=instance.quest.id)
            if quest.type != "Private":
                quest_max_score = quest.total_max_score()
                print(f"[Perfectionist] Quest attempt score: {instance.total_score_achieved()} / {quest_max_score}")
                if instance.total_score_achieved() == quest_max_score:
                    # Award a badge to the user for obtaining full marks the quest
                    # If the user has already been awarded the badge for the same quest, do not award again
                    user_quest_badge, created = UserQuestBadge.objects.get_or_create(
                        badge=Badge.objects.get(name="Perfectionist"),
                        quest_attempted=instance
                    )
                    if created:
                        print(f"[Perfectionist] Badge awarded to user: {instance.user.username} for completing quest attempt: {instance.id}")
                    else:
                        print(f"[Perfectionist] User: {instance.user.username} has already earned the Badge for quest: {instance.quest.name}")
                else:
                    print(f"[Perfectionist] User: {instance.user.username} did not obtain full marks for quest: {instance.quest.name}")


@receiver(post_save, sender=UserCourse)
def award_completionist_course_badges(sender, instance, created, **kwargs):
    if not created:
        if instance.completed_on and instance.course.type != "Private":
            print(f"[Completionist] User: {instance.user.username} has completed course: {instance.course.name}")
            # Award a badge to the user for completing the course
            # If the user has already been awarded the badge for the same course, do not award again
            user_course_badge, created = UserCourseBadge.objects.get_or_create(
                badge=Badge.objects.get(name="Completionist"),
                course_completed=instance
            )
            if created:
                print(f"[Completionist] Badge awarded to user: {instance.user.username} for completing course: {instance.course.name}")
            else:
                print(f"[Completionist] User: {instance.user.username} has already earned the Badge for course: {instance.course.name}")


@receiver(post_save, sender=UserQuestAttempt)
def award_first_attempt_quest_badge(sender, instance, created, **kwargs):
    if not created:
        if instance.all_questions_submitted:
            print(f"[First Attempt] Quest attempt: {instance.id} has been submitted")
            quest = Quest.objects.get(id=instance.quest.id)
            if quest.type != "Private":

                user = EduquestUser.objects.get(id=instance.user.id)
                # Check if the user has earned any First Attempt badge before
                user_quest_badges = UserQuestBadge.objects.filter(quest_attempted__user=user, badge__name="First Attempt")
                if user_quest_badges.count() == 0:
                    # Award a badge to the user for completing a quest for the first time
                    # If the user has already been awarded the badge, do not award again
                    user_quest_badge, created = UserQuestBadge.objects.get_or_create(
                        badge=Badge.objects.get(name="First Attempt"),
                        quest_attempted=instance
                    )
                    if created:
                        print(f"[First Attempt] Badge awarded to user: {instance.user.username} for completing quest attempt: {instance.id}")
                    else:
                        print(f"[First Attempt] User: {instance.user.username} has already earned the Badge before")
                else:
                    print(f"[First Attempt] User: {instance.user.username} has already earned the Badge before")


@receiver(post_save, sender=Quest)
def award_expert_quest_badge(sender, instance, created, **kwargs):
    # Scenario 2: When the instructor manually marks the quest as expired
    # Scenario 1: When a quest has ended based on the expiry date, it will be marked as expired
    if not created:
        if instance.status == "Expired" and instance.type != "Private":
            print(f"[Expert] Quest: {instance.name} has ended and expired")
            # Award a badge to the user for achieving the highest score on the quest
            # If the user has already been awarded the badge for the same quest, do not award again
            # If the highest is 0, do not award the badge
            user_quest_attempts = UserQuestAttempt.objects.filter(quest=instance)
            highest_score = 0
            highest_score_attempt = None
            for attempt in user_quest_attempts:
                if attempt.total_score_achieved() > highest_score:
                    highest_score = attempt.total_score_achieved()
                    highest_score_attempt = attempt
            if highest_score > 0:
                if highest_score_attempt:
                    user_quest_badge, created = UserQuestBadge.objects.get_or_create(
                        badge=Badge.objects.get(name="Expert"),
                        quest_attempted=highest_score_attempt
                    )
                    if created:
                        print(f"[Expert] Badge awarded to user: {highest_score_attempt.user.username} for scoring the highest in quest: {instance.name}")
                    else:
                        print(f"[Expert] User: {highest_score_attempt.user.username} has already earned the Badge for quest: {instance.name}")
            else:
                print(f"[Expert] No user has scored above 0 for quest: {instance.name}")


@receiver(post_save, sender=Quest)
def award_speedster_quest_badge(sender, instance, created, **kwargs):
    # Scenario 2: When the instructor manually marks the quest as expired
    # Scenario 1: When a quest has ended based on the expiry date, it will be marked as expired
    if not created:
        if instance.status == "Expired" and instance.type != "Private":
            print(f"[Speedster] Quest: {instance.name} has ended and expired")
            # Award a badge to the user with the shortest overall time
            # The user also has to be among the top three scorers to get this badge
            # If the user is the fastest but not in the top three scorers, do not award the badge
            # If the user has already been awarded the badge for the same quest, do not award again
            # If the user gets 0 score, do not award the badge
            user_quest_attempts = UserQuestAttempt.objects.filter(quest=instance, question_attempts__score_achieved__gt=0).distinct()

            if user_quest_attempts.exists():
                # Get the shortest overall time attempt
                # Sort by time_taken ascending
                sorted_by_time_taken_attempts = sorted(user_quest_attempts, key=lambda x: (x.time_taken()))
                fastest_attempt = sorted_by_time_taken_attempts[0]
                fastest_attempt_score = fastest_attempt.total_score_achieved()

                print(f"[Speedster] Fastest user: {fastest_attempt.user.id} with time: {fastest_attempt.time_taken()}ms "
                      f"and score: {fastest_attempt_score}")
                # Sort by score taken descending
                sorted_by_score_attempts = sorted(user_quest_attempts, key=lambda x: (-x.total_score_achieved()))
                print(f"[Speedster] All scores: {[attempt.total_score_achieved() for attempt in sorted_by_score_attempts]}")
                attempts_unique_scores = sorted(set([attempt.total_score_achieved() for attempt in sorted_by_score_attempts]), reverse=True)
                top_three_scores = attempts_unique_scores[:3]
                print(f"[Speedster] Top three unique scores: {top_three_scores}")

                # Check if the fastest user is among the top 3 scorers
                if fastest_attempt_score in top_three_scores:
                    user_quest_badge, created = UserQuestBadge.objects.get_or_create(
                        badge=Badge.objects.get(name="Speedster"),
                        quest_attempted=fastest_attempt
                    )
                    if created:
                        print(f"[Speedster] Badge awarded to user: {fastest_attempt.user.username} for being the fastest while remaining in the top three in quest: {instance.name}")
                    else:
                        print(f"[Speedster] User: {fastest_attempt.user.username} has already earned the Badge for quest: {instance.name}")
                else:
                    print(f"[Speedster] The fastest user is not among the top three scorers for quest: {instance.name}")
            else:
                print(f"[Speedster] No user has scored above 0 for quest: {instance.name}")


@receiver(post_save, sender=UserQuestAttempt)
def set_course_completion (sender, instance, created, **kwargs):
    if not created:
        if instance.all_questions_submitted and instance.quest.type != "Private":
            print(f"[Course Completion] User: {instance.user.username} has completed quest: {instance.quest.name}")
            # Check if the user has at least submitted one attempt for each quest within the course associated
            course = Course.objects.get(id=instance.quest.from_course.id)
            quests = course.quests.all()
            # Iterate through each quest in the course
            for quest in quests:
                user_quest_attempts = UserQuestAttempt.objects.filter(user=instance.user, quest=quest, all_questions_submitted=True)
                if user_quest_attempts.count() == 0:
                    print(f"[Course Completion] User: {instance.user.username} has not submitted any attempts in quest: {quest.name}")
                    return
            print(f"[Course Completion] User: {instance.user.username} has completed all quests in course: {course.name}")
            # Set the user course as completed with the last attempted date for the quest
            user_course = UserCourse.objects.get(user=instance.user, course=course)
            user_course.completed_on = instance.last_attempted_on
            user_course.save(update_fields=['completed_on'])


@receiver(post_save, sender=UserQuestQuestionAttempt)
def calculate_score_for_a_question(sender, instance, created, **kwargs):
    if not created:
        if instance.submitted:
            correct_answer_count = 0
            max_score = instance.question.max_score
            answer_count = instance.question.answers.count()

            # Calculate the number of correct answers based on the condition
            for selected_answer in instance.selected_answers.all():
                if selected_answer.is_selected == selected_answer.answer.is_correct:
                    correct_answer_count += 1

            # Calculate the score achieved
            if answer_count > 0:
                score_achieved = (correct_answer_count / answer_count) * max_score
            else:
                score_achieved = 0

            instance.score_achieved = score_achieved

            # Temporarily disconnect the signal to prevent recursion
            signals.post_save.disconnect(receiver=calculate_score_for_a_question, sender=UserQuestQuestionAttempt)
            instance.save(update_fields=['score_achieved'])
            # Reconnect the signal
            signals.post_save.connect(receiver=calculate_score_for_a_question, sender=UserQuestQuestionAttempt)


@receiver(post_save, sender=EduquestUser)
def create_private_course(sender, instance, created, **kwargs):
    if created:
        private_year, _ = AcademicYear.objects.get_or_create(
            start_year=0,
            end_year=0
        )
        private_term, _ = Term.objects.get_or_create(
            academic_year=private_year,
            name="Private Term",
            start_date=None,
            end_date=None
        )
        private_course = Course.objects.create(
            term=private_term,
            name="Private Course",
            code=f"PRIVATE {instance.id}",
            type="Private",
            description="This is a private Course created for you to generate Quests for your own use.",
            status="Active",
            image=Image.objects.get(name="Private Course")
        )
        UserCourse.objects.create(
            user=instance,
            course=private_course,
            enrolled_on=timezone.now()
        )
