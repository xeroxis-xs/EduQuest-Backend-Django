from django.db import models
from django.contrib.auth.models import AbstractUser
from .utils import split_full_name


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
    code = models.CharField(max_length=100)
    description = models.TextField()
    status = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.term} - {self.code}"


class Quest(models.Model):
    from_course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='quests')
    name = models.CharField(max_length=100)
    description = models.TextField()
    type = models.CharField(max_length=50)  # Quiz
    status = models.CharField(max_length=50)  # Ongoing, Upcoming, Completed
    organiser = models.ForeignKey(EduquestUser, on_delete=models.CASCADE, related_name='quests_organised')
    participants = models.ManyToManyField(EduquestUser, related_name='quests_participated')

    def __str__(self):
        return f"{self.name} from {self.from_course.code}"


class Question(models.Model):
    from_quest = models.ForeignKey(Quest, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField()
    correct_answer = models.TextField()
    max_score = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.text} in Quest ID {self.from_quest.name.id}"


class Answer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers')
    text = models.TextField()
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.text} for Question ID {self.question.id}"


class UserQuestAttempt(models.Model):
    user = models.ForeignKey(EduquestUser, on_delete=models.CASCADE, related_name='attempted_quests')
    quest = models.ForeignKey(Quest, on_delete=models.CASCADE, related_name='attempted_by')
    first_attempted_on = models.DateTimeField(auto_now_add=True)
    is_first_attempt = models.BooleanField(default=False)
    is_perfect_score = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} - {self.quest.name} - First attempt on {self.first_attempted_on}"


class UserQuestQuestionAttempt(models.Model):
    user_quest_attempt = models.ForeignKey(UserQuestAttempt, on_delete=models.CASCADE, related_name='question_attempts')
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='attempts')
    selected_answers = models.ManyToManyField(Answer, related_name='selected_by')
    score = models.PositiveIntegerField()
    time_taken = models.PositiveIntegerField()  # in milliseconds
    attempted_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user_quest_attempt.user.username} - {self.question.text} - took {self.time_taken} ms"


class UserCourseCompletion(models.Model):
    user = models.ForeignKey(EduquestUser, on_delete=models.CASCADE, related_name='completed_courses')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='completed_by')
    date_completed = models.DateTimeField(auto_now_add=True)

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
