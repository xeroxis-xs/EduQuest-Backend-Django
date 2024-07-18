from django.db import models
from django.contrib.auth.models import AbstractUser
from .utils import split_full_name
from django.db.models import Sum


class EduquestUser(AbstractUser):
    nickname = models.CharField(max_length=100, blank=True, null=True, editable=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    def __str__(self):
        return self.username

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
    enrolled_users = models.ManyToManyField(EduquestUser, related_name='enrolled_courses', blank=True)
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=100)
    description = models.TextField()
    status = models.CharField(max_length=100)
    image = models.ForeignKey(Image, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.term} - {self.code}"


class Quest(models.Model):
    from_course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='quests')
    name = models.CharField(max_length=100)
    description = models.TextField()
    type = models.CharField(max_length=50)  # Quiz
    status = models.CharField(max_length=50)  # Ongoing, Upcoming, Completed
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
        return f"{self.text} in Quest ID {self.from_quest.name.id}"


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
    first_attempted_on = models.DateTimeField(auto_now_add=True)
    last_attempted_on = models.DateTimeField(null=True, blank=True)
    # If the user has submitted the quest from clicking the submit button, this will be set to True
    submitted = models.BooleanField(default=False)
    time_taken = models.PositiveIntegerField(default=0)  # in milliseconds

    def __str__(self):
        return f"{self.user.username} - {self.quest.name} - First attempt on {self.first_attempted_on}"

    # Calculate the total score achieved by the user for all questions in a quest
    def total_score_achieved(self):
        return self.question_attempts.aggregate(total_score_achieved=Sum('score_achieved'))['total_score_achieved'] or 0

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
        return f"{self.user_quest_question_attempt.user_quest_attempt.user.username} - {self.answer.text} - {self.is_correct}"


class UserCourseCompletion(models.Model):
    user = models.ForeignKey(EduquestUser, on_delete=models.CASCADE, related_name='completed_courses')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='completed_by')
    completed_on = models.DateTimeField(null=True, blank=True)
    enrolled_on = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('user', 'course')

    def __str__(self):
        return f"{self.user.username} - {self.course.name}"


class Badge(models.Model):
    BADGE_TYPES = [
        ('First Attempt', 'First Attempt Badge'),
        ('Completionist', 'Completionist Badge'),
        ('Expert', 'Expert Badge'),
        ('Speedster', 'Speedster Badge'),
        ('Perfectionist', 'Perfectionist Badge'),
    ]

    name = models.CharField(max_length=50, choices=BADGE_TYPES)
    description = models.TextField()
    type = models.CharField(max_length=50)  # Course Type or Quest Type
    earned_by = models.ManyToManyField(EduquestUser, related_name='badges_earned')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, null=True, blank=True, related_name='badges_awarded')
    quest = models.ForeignKey(Quest, on_delete=models.CASCADE, null=True, blank=True, related_name='badges_awarded')
    awarded_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.quest:
            return f"{self.name} - Quest: {self.quest.name}"
        else:
            return f"{self.name} - Course: {self.course.name}"




# class UserEarnBadgeQuest(models.Model):
#     user = models.ForeignKey(EduquestUser, on_delete=models.CASCADE, related_name='badges_earned_from_quests')
#     badge = models.ForeignKey(Badge, on_delete=models.CASCADE, related_name='awarded_to')
#     quest = models.ForeignKey(Quest, on_delete=models.CASCADE, related_name='earned_badges')
#     awarded_date = models.DateTimeField(auto_now_add=True)
#
#     def __str__(self):
#         return f"{self.user.username} - earned {self.badge} from Quest {self.quest} on {self.awarded_date}"
#
#
# class UserEarnBadgeCourse(models.Model):
#     user = models.ForeignKey(EduquestUser, on_delete=models.CASCADE, related_name='badges_earned_from_courses')
#     badge = models.ForeignKey(Badge, on_delete=models.CASCADE, related_name='awarded_to')
#     course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='earned_badges')
#     awarded_date = models.DateTimeField(auto_now_add=True)
#
#     def __str__(self):
#         return f"{self.user.username} - earned {self.badge} from Course {self.course} on {self.awarded_date}"
