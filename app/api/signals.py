from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db.models import signals
from .models import (
    EduquestUser,
    Image,
    AcademicYear,
    Term,
    Course,
    Quest,
    Question,
    Answer,
    UserQuestAttempt,
    UserQuestQuestionAttempt,
    AttemptAnswerRecord,
    UserCourse,
    Badge,
    UserQuestBadge,
    UserCourseBadge,
)


@receiver(post_save, sender=UserQuestAttempt)
def award_perfectionist_quest_badges(sender, instance, created, **kwargs):
    if not created:
        pass
        if instance.all_questions_submitted:
            # Check if the user has obtained full marks for the quest attempt
            quest = Quest.objects.get(id=instance.quest.id)
            quest_max_score = quest.total_max_score()
            print(f"Quest attempt score: {instance.total_score_achieved()} / {quest_max_score}")
            if instance.total_score_achieved() == quest_max_score:
                # Award a badge to the user for obtaining full marks the quest
                UserQuestBadge.objects.get_or_create(
                    badge=Badge.objects.get(name="Perfectionist"),
                    quest_attempted=instance
                )
                print(f"Perfectionist Badge awarded to user: {instance.user.username} for completing quest attempt: {instance.id}")


@receiver(post_save, sender=UserCourse)
def award_completionist_course_badges(sender, instance, created, **kwargs):
    if not created:
        if instance.completed_on:
            # Award a badge to the user for completing the course
            UserCourseBadge.objects.get_or_create(
                badge=Badge.objects.get(name="Completionist"),
                course_completed=instance
            )
            print(f"Completionist Badge awarded to user: {instance.user.username} for completing course: {instance.course.name}")



@receiver(post_save, sender=UserQuestAttempt)
def set_course_completion (sender, instance, created, **kwargs):
    if not created:
        if instance.all_questions_submitted:
            print(f"User: {instance.user.username} has completed quest: {instance.quest.name}")
            # Check if the user has at least submitted one attempt for each quest within the course associated
            course = Course.objects.get(id=instance.quest.from_course.id)
            quests = course.quests.all()
            print(f"quests: {quests}")
            # Iterate through each quest in the course
            for quest in quests:
                user_quest_attempts = UserQuestAttempt.objects.filter(user=instance.user, quest=quest, all_questions_submitted=True)
                if user_quest_attempts.count() == 0:
                    print(f"User: {instance.user.username} has not submitted any attempts in quest: {quest.name}")
                    return
            print(f"User: {instance.user.username} has completed all quests in course: {course.name}")
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
