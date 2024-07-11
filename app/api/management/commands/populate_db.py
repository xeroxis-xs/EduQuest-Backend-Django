import random
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from faker import Faker
from ...models import EduquestUser, AcademicYear, Term, Course, Quest, Question, Answer, UserQuestAttempt, \
    UserQuestQuestionAttempt, UserCourseCompletion, Badge

User = get_user_model()
fake = Faker()


class Command(BaseCommand):
    help = 'Populate the database with random data'

    def handle(self, *args, **kwargs):
        self.clear_db()
        self.create_users()
        self.create_academic_years_terms_courses_quests_questions()
        self.create_attempts()
        self.create_badges()

    def clear_db(self):
        eduquestUsers = EduquestUser.objects.filter(id__gt=1)
        eduquestUsers.delete()
        AcademicYear.objects.all().delete()
        print("Cleared all tables")

    def create_users(self):
        for _ in range(5):
            user = EduquestUser.objects.create(
                username=f"#{fake.name().upper()}#",
                email=f"{fake.user_name().upper()}@e.ntu.edu.sg",
                password='password',
                nickname=fake.first_name(),
                is_active=True,
                is_staff=False
            )
            print(f"Created user: {user.username}")

    def create_academic_years_terms_courses_quests_questions(self):
        for year in range(2023, 2025):
            academic_year = AcademicYear.objects.create(start_year=year, end_year=year + 1)
            for term_name in ["Semester 1", "Semester 2", "Special Term 1", "Special Term 2"]:
                start_date = timezone.make_aware(fake.date_time_this_decade())
                term = Term.objects.create(
                    academic_year=academic_year,
                    name=term_name,
                    start_date=start_date,
                    end_date=start_date + timezone.timedelta(days=90)
                )
                for course_num in range(1000, random.randint(1000, 1006)):
                    course = Course.objects.create(
                        term=term,
                        name=f"Course {fake.company()}",
                        code=f"CS{course_num}",
                        description=fake.text(max_nb_chars=150),
                        status="Active"
                    )
                    for quest_num in range(0, random.randint(1, 5)):
                        quest = Quest.objects.create(
                            from_course=course,
                            name=f"Quest {quest_num}",
                            description=fake.text(),
                            type="Quiz",
                            status="Active",
                            organiser=random.choice(User.objects.all())
                        )
                        number = 1
                        for question_num in range(1, random.randint(1, 4)):
                            question = Question.objects.create(
                                from_quest=quest,
                                text=fake.sentence(),
                                number=number,
                                max_score=10
                            )
                            number += 1
                            for _ in range(4):
                                Answer.objects.create(
                                    question=question,
                                    text=fake.word(),
                                    is_correct=random.choice([True, False])
                                )
            print(f"Created academic year: {academic_year.start_year}-{academic_year.end_year}")

    def create_attempts(self):
        for user in User.objects.filter(id__gt=1):
            for quest in Quest.objects.all():
                total_time_taken = 0
                user_quest_attempt = UserQuestAttempt.objects.create(
                    user=user,
                    quest=quest,
                    is_first_attempt=True,
                    is_perfect_score=random.choice([True, False])
                )
                for question in quest.questions.all():
                    time_taken = random.randint(10000, 30000)
                    total_time_taken += time_taken
                    UserQuestQuestionAttempt.objects.create(
                        user_quest_attempt=user_quest_attempt,
                        question=question,
                        score=random.randint(0, question.max_score),
                        time_taken=time_taken
                    )
                user_quest_attempt.total_time_taken = total_time_taken
                user_quest_attempt.save()
                print(f"Created attempt for user: {user.username}, quest: {quest.name}")

    def create_badges(self):
        badge_types = [
            ('First Attempt', 'Awarded upon completing any quest for the first time.'),
            ('Completionist', 'Awarded upon completing all quests within a course.'),
            ('Expert', 'Awarded for achieving the highest score on a Quest.'),
            ('Speedster', 'Awarded for achieving the highest score on a Quest AND shortest overall time.'),
            ('Perfectionist', 'Awarded for achieving a perfect score on a quiz.'),
        ]
        for badge_type in badge_types:
            for user in User.objects.filter(id__gt=1):
                if random.choice([True, False]):
                    course = random.choice(Course.objects.all())
                    quest = random.choice(Quest.objects.all())
                    badge = Badge.objects.create(
                        name=badge_type[0],
                        description=badge_type[1],
                        type="Quest" if badge_type[0] in ["First Attempt", "Expert", "Speedster",
                                                          "Perfectionist"] else "Course",
                        course=course if badge_type[0] == "Completionist" else None,
                        quest=quest if badge_type[0] in ["First Attempt", "Expert", "Speedster",
                                                         "Perfectionist"] else None,
                    )
                    badge.earned_by.add(user)
                    print(f"Created badge: {badge.name} for user: {user.username}")
