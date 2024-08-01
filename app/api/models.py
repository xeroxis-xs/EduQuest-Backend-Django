from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from .utils import split_full_name
from django.db.models import Sum


class EduquestUser(AbstractUser):
    nickname = models.CharField(max_length=100, blank=True, null=True, editable=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    # Custom validator example: Allow letters, numbers, and selected special characters
    # username_validator = RegexValidator(
    #     regex=r'^[\w.@+#\s-]+$',
    #     message="Enter a valid username. This value may contain only letters, numbers, spaces, and @/./+/-/_/# characters."
    # )
    # username = models.CharField(
    #     max_length=150,
    #     unique=True,
    #     validators=[username_validator],  # Apply the custom validator
    #     error_messages={
    #         'unique': "A user with that username already exists.",
    #     },
    # )

    def __str__(self):
        return f"{self.id}"

    def save(self, *args, **kwargs):
        if not self.pk:  # Only set default nickname on initial creation
            self.nickname = self.username.replace("#", "")
            self.first_name, self.last_name = split_full_name(self.nickname)
        super().save(*args, **kwargs)


class Image(models.Model):
    name = models.CharField(max_length=100)
    filename = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class AcademicYear(models.Model):
    start_year = models.PositiveIntegerField()
    end_year = models.PositiveIntegerField()

    def __str__(self):
        return f"AY{self.start_year}-{self.end_year}"


class Term(models.Model):
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name='terms')
    name = models.CharField(max_length=50)
    start_date = models.DateField()
    end_date = models.DateField()

    def __str__(self):
        return f"{self.academic_year} - {self.name} ({self.start_date} to {self.end_date})"


class Course(models.Model):
    term = models.ForeignKey(Term, on_delete=models.CASCADE, related_name='courses')
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=100, null=True, blank=True)
    type = models.CharField(max_length=100)  # Eduquest, Private
    description = models.TextField()
    status = models.CharField(max_length=100) # Active, Inactive
    image = models.ForeignKey(Image, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.term} - {self.code}"


class UserCourse(models.Model):
    user = models.ForeignKey(EduquestUser, on_delete=models.CASCADE, related_name='enrolled_courses')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrolled_users')
    enrolled_on = models.DateTimeField(auto_now_add=True)
    completed_on = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} enrolled {self.course.name}"


class Quest(models.Model):
    from_course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='quests')
    name = models.CharField(max_length=100)
    description = models.TextField()
    type = models.CharField(max_length=50)  # EduQuest MCQ, Kahoot!, WooClap, Private
    status = models.CharField(max_length=50)  # Active, Expired
    expiration_date = models.DateTimeField(null=True, blank=True)
    max_attempts = models.PositiveIntegerField(default=1)
    organiser = models.ForeignKey(EduquestUser, on_delete=models.CASCADE, related_name='quests_organised')
    image = models.ForeignKey(Image, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.name} from {self.from_course.code}"

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
    first_attempted_on = models.DateTimeField(auto_now_add=True)
    last_attempted_on = models.DateTimeField()

    def __str__(self):
        return f"{self.user.username} - {self.quest.name} - First attempt on {self.first_attempted_on}"

    # Calculate the total score achieved by the user for all questions in a quest
    def total_score_achieved(self):
        return self.question_attempts.aggregate(total_score_achieved=Sum('score_achieved'))['total_score_achieved'] or 0

    def time_taken(self):
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
    course_completed = models.ForeignKey(UserCourse, on_delete=models.CASCADE, related_name='earned_course_badges')
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
