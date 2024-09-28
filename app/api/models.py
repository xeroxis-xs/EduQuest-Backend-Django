from datetime import datetime
import os

from celery import chain
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import AbstractUser
from django.utils.text import slugify
from .utils import split_full_name
from django.db.models import Sum
from storages.backends.azure_storage import AzureStorage
from django.core.exceptions import ValidationError

class EduquestUser(AbstractUser):
    """
    Custom User model for EduQuest
    is_staff: True if user is an instructor
    """
    nickname = models.CharField(max_length=100, blank=True, null=True, editable=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    total_points = models.FloatField(default=0)

    def __str__(self):
        return f"{self.id} - {self.username}"

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        if is_new:
            self.nickname = self.username.replace("#", "")
            self.first_name, self.last_name = split_full_name(self.nickname)
        super().save(*args, **kwargs)
        if is_new and not self.is_superuser:
            # Enroll the user in the private course group
            from .models import CourseGroup, UserCourseGroupEnrollment
            private_course_group = CourseGroup.objects.get(name="Private Course Group")
            UserCourseGroupEnrollment.objects.create(student=self, course_group=private_course_group)
            print(f"[Enroll Private Course Group] User: {self.username} has been enrolled in the Private course group")


class Image(models.Model):
    """
    Model to store images for courses, quests, and badges
    The image files are stored in Next.js public folder
    """
    name = models.CharField(max_length=100)
    filename = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class AcademicYear(models.Model):
    """
    Model to store academic years
    e.g. AY2021-2022
    """
    start_year = models.PositiveIntegerField()
    end_year = models.PositiveIntegerField()

    def __str__(self):
        return f"AY{self.start_year}-{self.end_year}"


class Term(models.Model):
    """
    Model to store terms for each academic year
    e.g. Term 1, Term 2, Term 3
    """
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name='terms')
    name = models.CharField(max_length=50)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.academic_year} - {self.name} ({self.start_date} to {self.end_date})"


class Course(models.Model):
    """
    Model to store courses for each term
    e.g. Term 1 - SC1000, SC2000
    e.g. Term 2 - SC1000
    e.g. Term 2 - SC2000
    One course can have many course groups
    Many coordinators can coordinate many courses
    e.g. SC1000 coordinators: instructor1, instructor2
    e.g. SC2000 coordinators: instructor2, instructor3
    """
    term = models.ForeignKey(Term, on_delete=models.CASCADE, related_name='courses')
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=100, null=True, blank=True)
    type = models.CharField(max_length=100)  # System-enroll, Self-enroll, Private
    description = models.TextField()
    status = models.CharField(max_length=100)  # Active, Expired
    image = models.ForeignKey(Image, on_delete=models.SET_NULL, null=True, blank=True)
    coordinators = models.ManyToManyField(EduquestUser, related_name='coordinated_courses')

    def clean(self):
        super().clean()
        # Remove the following block to prevent ValidationError during creation
        # if not self.pk and not self.coordinators.exists():
        #     raise ValidationError("A course must have at least one coordinator.")

    def save(self, *args, **kwargs):
        is_new_instance = self.pk is None
        old_status_value = None
        if not is_new_instance:
            old_instance = Course.objects.get(pk=self.pk)
            old_status_value = old_instance.status

        self.full_clean()  # Call the clean method
        super(Course, self).save(*args, **kwargs)

        # After saving the instance, check if 'status' changed from Active to Expired
        if old_status_value == 'Active' and self.status == 'Expired':
            # Import tasks locally to avoid circular import
            from .tasks import check_course_completion_and_award_completionist_badge
            # Trigger all tasks
            check_course_completion_and_award_completionist_badge.delay(self.id)

            # Recursively set all quests in all course groups to 'Expired'
            for course_group in self.groups.all():
                for quest in course_group.quests.all():
                    quest.status = 'Expired'
                    quest.save()

    def total_students_enrolled(self):
        return UserCourseGroupEnrollment.objects.filter(course_group__course=self).count()

    def __str__(self):
        return f"Term {self.term.name} - {self.code}"



class CourseGroup(models.Model):
    """
    Model to store course groups for each course
    This is similar to how course index works in NTU
    e.g. SC1000 - TEL1, SCS1
    e.g. SC2000 - TEL2, SCS2
    """
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='groups')
    name = models.CharField(max_length=100) # Group name: e.g. TEL1, SWLA, SCSJ
    session_day = models.CharField(max_length=10, null=True, blank=True)  # e.g. Monday, Tuesday, Wednesday
    session_time = models.CharField(max_length=100, null=True, blank=True)  # e.g. 10:00 AM - 12:00 PM, 2:30 PM - 4:30 PM
    instructor = models.ForeignKey(EduquestUser, on_delete=models.CASCADE, related_name='instructed_course_groups')

    def total_students_enrolled(self):
        return UserCourseGroupEnrollment.objects.filter(course_group=self).count()

    def __str__(self):
        return f"Group {self.name} from {self.course.code}"


class UserCourseGroupEnrollment(models.Model):
    """
    Model to store the user's enrollment in a course group
    One course group can have many course group enrollment records
    One enrollment only stores one course group and one student
    """
    student = models.ForeignKey(EduquestUser, related_name='enrolled_course_groups', on_delete=models.CASCADE)
    course_group = models.ForeignKey(CourseGroup, related_name='enrolled_students', on_delete=models.CASCADE)
    enrolled_on = models.DateTimeField(auto_now_add=True)
    completed_on = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.student.username} enrolled in {self.course_group.course.code} - {self.course_group.name}"


class Quest(models.Model):
    """
    Model to store quests for each course group
    One course group can have many quests
    """
    course_group = models.ForeignKey(CourseGroup, on_delete=models.CASCADE, related_name='quests')
    name = models.CharField(max_length=100)
    description = models.TextField()
    type = models.CharField(max_length=50)  # EduQuest MCQ, Kahoot!, WooClap, Private
    status = models.CharField(max_length=50, default="Active")  # Active, Expired
    tutorial_date = models.DateTimeField(null=True, blank=True)
    expiration_date = models.DateTimeField(null=True, blank=True)
    max_attempts = models.PositiveIntegerField(default=1)
    organiser = models.ForeignKey(EduquestUser, on_delete=models.CASCADE, related_name='quests_organised')
    image = models.ForeignKey(Image, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.name} from Group {self.course_group.course.name} {self.course_group.course.code}"

    # Calculate the total max score for all questions in a quest
    def total_max_score(self):
        return self.questions.aggregate(total_max_score=Sum('max_score'))['total_max_score'] or 0

    # Calculate the total number of questions in a quest
    def total_questions(self):
        return self.questions.count()

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        previous_status = None
        if not is_new:
            previous = Quest.objects.get(pk=self.pk)
            previous_status = previous.status

        super(Quest, self).save(*args, **kwargs)
        # If the quest status changed from Active to Expired
        if previous_status == "Active" and self.status == "Expired":
            self.expiration_date = timezone.now()
            super(Quest, self).save(update_fields=['expiration_date'])

            from .tasks import award_speedster_badge, award_expert_badge
            award_expert_badge.delay(self.id)
            award_speedster_badge.delay(self.id)


class Question(models.Model):
    """
    Model to store questions for each quest
    One quest can have many questions
    """
    quest = models.ForeignKey(Quest, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField()
    number = models.PositiveIntegerField()
    max_score = models.FloatField(default=1)

    def __str__(self):
        return f"{self.number} from Quest ID {self.quest.id}"


class Answer(models.Model):
    """
    Model to store answer options for each question
    """
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers')
    text = models.TextField()
    is_correct = models.BooleanField(default=False)
    reason = models.TextField(blank=True, null=True)  # Explanation for the correct answer, only for generated quest

    def __str__(self):
        return f"{self.text} for Question ID {self.question.id}"


class UserQuestAttempt(models.Model):
    """
    Model to store the user's attempt for each quest
    When the user starts a quest attempt, a record will be created
    """
    student = models.ForeignKey(EduquestUser, on_delete=models.CASCADE, related_name='attempted_quests')
    quest = models.ForeignKey(Quest, on_delete=models.CASCADE, related_name='attempted_by')
    submitted = models.BooleanField(default=False)
    first_attempted_date = models.DateTimeField(blank=True, null=True)  # blank for imported quests
    last_attempted_date = models.DateTimeField(blank=True, null=True)  # blank for imported quests
    total_score_achieved = models.FloatField(default=0)

    def __str__(self):
        return f"{self.student.username} attempted {self.quest.name}"

    def calculate_total_score_achieved(self):
        """
        Calculate the total score achieved by the user for the quest
        Set the score_achieved for each answer attempt.
        """
        total_score = 0
        user_answer_attempts_to_update = []
        questions = self.quest.questions.all()

        for question in questions:
            answers = question.answers.all()
            num_options = answers.count()

            if num_options == 0:
                continue  # Avoid division by zero

            weight_per_option = question.max_score / num_options
            user_answers = self.answer_attempts.filter(question=question)
            question_score = 0

            for ua in user_answers:
                if ua.is_selected == ua.answer.is_correct:
                    ua.score_achieved = weight_per_option
                    question_score += weight_per_option
                else:
                    ua.score_achieved = 0
                user_answer_attempts_to_update.append(ua)

            total_score += question_score

        # Bulk update all UserAnswerAttempt instances' score_achieved fields
        UserAnswerAttempt.objects.bulk_update(user_answer_attempts_to_update, ['score_achieved'])

        return total_score

    @property
    def time_taken(self):
        if not self.first_attempted_date or not self.last_attempted_date:
            return 0
        # Calculate the total time taken by subtracting the first_attempted_date from the last_attempted_date
        time_difference = self.last_attempted_date - self.first_attempted_date
        # If negative, return 0
        if time_difference.total_seconds() < 0:
            return 0
        return int(time_difference.total_seconds() * 1000)  # Convert to milliseconds


    def save(self, *args, **kwargs):
        is_new_instance = self.pk is None
        old_submitted_value = None
        if not is_new_instance:
            old_instance = UserQuestAttempt.objects.get(pk=self.pk)
            old_submitted_value = old_instance.submitted

        super(UserQuestAttempt, self).save(*args, **kwargs)

        # After saving the instance, check if 'submitted' changed from False to True
        if old_submitted_value == False and self.submitted == True:
            # Import tasks locally to avoid circular import
            from .tasks import (award_first_attempt_badge, calculate_score_and_issue_points)
            # Trigger all tasks
            calculate_score_and_issue_points.delay(self.id)
            award_first_attempt_badge.delay(self.id)


class UserAnswerAttempt(models.Model):
    """
    Model to store the user's selected answer options for each question attempt
    """
    user_quest_attempt = models.ForeignKey(UserQuestAttempt, on_delete=models.CASCADE, related_name='answer_attempts')
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='user_answer_attempts')
    answer = models.ForeignKey(Answer, on_delete=models.CASCADE)
    is_selected = models.BooleanField(default=False)
    score_achieved = models.FloatField(default=0)

    def __str__(self):
        return f"{self.user_quest_attempt.student.username} selected {self.answer.text} for question {self.question.number}"


class Badge(models.Model):
    """
    Model to store badges that can be earned by users
    """
    name = models.CharField(max_length=50)
    description = models.TextField()
    type = models.CharField(max_length=50)  # Course Type or Quest Type
    condition = models.CharField(max_length=250)  # Condition to be met to earn the badge
    image = models.ForeignKey(Image, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.name}"


class UserCourseBadge(models.Model):
    """
    Model to store the user's earned badges from completing courses
    These badges are awarded based on 'course' related conditions
    """
    badge = models.ForeignKey(
        Badge,
        on_delete=models.CASCADE,
        related_name='awarded_to_course_completion'
    )
    user_course_group_enrollment = models.ForeignKey(
        UserCourseGroupEnrollment,
        on_delete=models.CASCADE,
        related_name='earned_course_badges'
    )
    awarded_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return (f"{self.user_course_group_enrollment.student.username} earned {self.badge.name} from Course "
                f"{self.user_course_group_enrollment.course_group.course.code} - "
                f"{self.user_course_group_enrollment.course_group.name}")


class UserQuestBadge(models.Model):
    """
    Model to store the user's earned badges from attempting quests
    These badges are awarded based on 'quest' related conditions
    """
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE, related_name='awarded_to_quest_attempt')
    user_quest_attempt = models.ForeignKey(UserQuestAttempt, on_delete=models.CASCADE, related_name='earned_quest_badges')
    awarded_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return (f"{self.user_quest_attempt.student.username} earned {self.badge.name} from Quest "
                f"{self.user_quest_attempt.quest.name}")


class Document(models.Model):
    """
    Model to store documents and their records uploaded by users
    """
    name = models.CharField(max_length=255)
    file = models.FileField(upload_to='documents/')
    size = models.FloatField()
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(EduquestUser, on_delete=models.CASCADE, related_name='uploaded_documents')

    def save(self, *args, **kwargs):
        if self.file:
            storage = AzureStorage()
            file_name, file_extension = os.path.splitext(self.file.name)
            unique_file_name = self.file.name

            # Save the instance to generate a primary key
            if not self.pk:
                super(Document, self).save(*args, **kwargs)

            # Check if file with the same name exists
            while storage.exists(unique_file_name):
                unique_file_name = f"{file_name}_{self.pk}{file_extension}"

            self.file.name = unique_file_name

        super(Document, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        storage = AzureStorage()
        if storage.exists(self.file.name):
            storage.delete(self.file.name)
        super(Document, self).delete(*args, **kwargs)

    def __str__(self):
        return self.name



