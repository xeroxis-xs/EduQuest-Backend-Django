import os
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.text import slugify
from .utils import split_full_name
from django.db.models import Sum, Max, F, Subquery, OuterRef
from storages.backends.azure_storage import AzureStorage


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
        return f"{self.id}"

    def save(self, *args, **kwargs):
        if not self.pk:  # Only set default nickname on initial creation
            self.nickname = self.username.replace("#", "")
            self.first_name, self.last_name = split_full_name(self.nickname)
        super().save(*args, **kwargs)


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
        return f"{self.user.username} enrolled in {self.course_group.course.code} - {self.course_group.name}"


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
    # tutorial_date = models.DateTimeField(null=True, blank=True)
    expiration_date = models.DateTimeField(null=True, blank=True)
    max_attempts = models.PositiveIntegerField(default=1)
    organiser = models.ForeignKey(EduquestUser, on_delete=models.CASCADE, related_name='quests_organised')
    image = models.ForeignKey(Image, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.name} from {self.from_course_group.course.code} - {self.from_course_group.name}"

    # Calculate the total max score for all questions in a quest
    def total_max_score(self):
        return self.questions.aggregate(total_max_score=Sum('max_score'))['total_max_score'] or 0

    # Calculate the total number of questions in a quest
    def total_questions(self):
        return self.questions.count()


class Question(models.Model):
    from_quest = models.ForeignKey(Quest, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField()
    number = models.PositiveIntegerField()
    max_score = models.FloatField(default=1)

    def __str__(self):
        return f"{self.text} from quest {self.from_quest}"


class Answer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers')
    text = models.TextField()
    is_correct = models.BooleanField(default=False)
    reason = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.text} for Question ID {self.question.id}"


class UserQuestAttempt(models.Model):
    """
    This model is used to record the user's attempt for each quest
    If there is no quest attempt, the user will not have a record in this model
    """
    user = models.ForeignKey(EduquestUser, on_delete=models.CASCADE, related_name='attempted_quests')
    quest = models.ForeignKey(Quest, on_delete=models.CASCADE, related_name='attempted_by')
    # When the user first attempted the quest, automatically populate the date and time
    all_questions_submitted = models.BooleanField(default=False)
    first_attempted_on = models.DateTimeField(blank=True, null=True)
    last_attempted_on = models.DateTimeField(blank=True, null=True)
    total_score_achieved = models.FloatField(default=0)

    def __str__(self):
        return f"{self.id} {self.user.username} - {self.quest.name} - First attempt on {self.first_attempted_on}"

    # Calculate the total score achieved by the user for all questions in a quest
    def calculate_total_score_achieved(self):
        return self.question_attempts.aggregate(total_score_achieved=Sum('score_achieved'))['total_score_achieved'] or 0

    def time_taken(self):
        if not self.first_attempted_on or not self.last_attempted_on:
            return 0
        # Calculate the total time taken by subtracting the first_attempted_on from the last_attempted_on
        time_difference = self.last_attempted_on - self.first_attempted_on
        # If negative return 0
        if time_difference.total_seconds() < 0:
            return 0
        return time_difference.total_seconds() * 1000  # Convert to milliseconds


class UserQuestQuestionAttempt(models.Model):
    """
    This model is used to record the user's attempt for each question in a quest
    This model will always be created for every question in a quest
    """
    user_quest_attempt = models.ForeignKey(UserQuestAttempt, on_delete=models.CASCADE, related_name='question_attempts')
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='attempts')
    submitted = models.BooleanField(default=False)
    # The score_achieved will be calculated after user submission
    score_achieved = models.FloatField(default=0)
    # time_taken = models.PositiveIntegerField()  # in milliseconds
    # attempted_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user_quest_attempt.user.username} - {self.question.text} - score: {self.score_achieved}"


class AttemptAnswerRecord(models.Model):
    """
    This model is used to record the answers selected by the user for each question attempt
    """
    user_quest_question_attempt = models.ForeignKey(UserQuestQuestionAttempt, on_delete=models.CASCADE, related_name='selected_answers')
    answer = models.ForeignKey(Answer, on_delete=models.CASCADE, related_name='user_attempts')
    is_selected = models.BooleanField(default=False)


    def __str__(self):
        return f"{self.user_quest_question_attempt.user_quest_attempt.user.username} - {self.answer.text}"


class Badge(models.Model):
    name = models.CharField(max_length=50)
    description = models.TextField()
    type = models.CharField(max_length=50)  # Course Type or Quest Type
    condition = models.CharField(max_length=250)  # Condition to be met to earn the badge
    image = models.ForeignKey(Image, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.name}"


class UserCourseBadge(models.Model):
    # user = models.ForeignKey(EduquestUser, on_delete=models.CASCADE, related_name='badges_earned_from_courses')
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE, related_name='awarded_to_course_completion')
    course_completed = models.ForeignKey(UserCourseGroupEnrollment, on_delete=models.CASCADE, related_name='earned_course_badges')
    awarded_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Earned {self.badge} from completing Course {self.course_completed} "


class UserQuestBadge(models.Model):
    # user = models.ForeignKey(EduquestUser, on_delete=models.CASCADE, related_name='badges_earned_from_quests')
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE, related_name='awarded_to_quest_attempt')
    quest_attempted = models.ForeignKey(UserQuestAttempt, on_delete=models.CASCADE, related_name='earned_quest_badges')
    awarded_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Earned {self.badge} from attempting Quest {self.quest_attempted}"


class Document(models.Model):
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

            # Check if file with the same name exists
            while storage.exists(unique_file_name):
                unique_file_name = f"{file_name}_{slugify(self.uploaded_by.username)}_{self.pk or ''}{file_extension}"

            self.file.name = unique_file_name

        super(Document, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        storage = AzureStorage()
        if storage.exists(self.file.name):
            storage.delete(self.file.name)
        super(Document, self).delete(*args, **kwargs)

    def __str__(self):
        return self.name
