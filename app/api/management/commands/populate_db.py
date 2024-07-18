import random
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from faker import Faker
from ...models import EduquestUser, Image, AcademicYear, Term, Course, Quest, Question, Answer, UserQuestAttempt, \
    UserQuestQuestionAttempt, AttemptAnswerRecord, UserCourseCompletion, Badge

User = get_user_model()
fake = Faker()


class Command(BaseCommand):
    help = 'Populate the database with random data'

    def handle(self, *args, **kwargs):
        self.clear_db()
        self.create_users()
        self.create_images()
        self.create_academic_years_terms_courses_quests_questions()
        self.create_attempts()
        self.create_badges()

    def clear_db(self):
        eduquestUsers = EduquestUser.objects.filter(id__gt=2)
        eduquestUsers.delete()
        Image.objects.all().delete()
        AcademicYear.objects.all().delete()
        print("Cleared all tables")

    def create_users(self):
        for _ in range(4):
            user = EduquestUser.objects.create(
                username=f"#{fake.name().upper()}#",
                email=f"{fake.user_name().upper()}@e.ntu.edu.sg",
                password='password',
                nickname=fake.first_name(),
                is_active=True,
                is_staff=False
            )
            print(f"Created user: {user.username}")

    def create_images(self):
        image_names = ["Cloud Computing", "Data Science", "Machine Learning and AI",
                       "Computer Architecture", "Cyber Security", "Data Structure and Algorithm",
                       "Database", "Multiple Choice"]
        image_filenames = ["cloud_computing.svg", "data_science.svg", "machine_learning_and_ai.svg",
                           "computer_architecture.svg", "cyber_security.svg", "data_structure_and_algorithm.svg",
                           "database.svg", "multiple_choice.svg"]
        for i in range(len(image_names)):
            Image.objects.create(name=image_names[i], filename=image_filenames[i])

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
                for course_name in ["Cloud Computing", "Data Science", "Machine Learning and AI",
                                    "Computer Architecture", "Cyber Security", "Data Structure and Algorithm",
                                    "Database"]:
                    course = Course.objects.create(
                        term=term,
                        name=f"{course_name}",
                        code=f"CS{random.randint(1000, 1006)}",
                        description=fake.text(max_nb_chars=150),
                        status="Active",
                        image=Image.objects.get(name=course_name)
                    )
                    # Enroll users in the course
                    all_users = list(EduquestUser.objects.all())
                    num_users_to_enroll = random.randint(1, len(all_users))  # Decide how many users to enroll
                    users_to_enroll = random.sample(all_users, num_users_to_enroll)
                    for user in users_to_enroll:
                        course.enrolled_users.add(user)
                    # Continue with quest and question creation
                    for quest_num in range(0, random.randint(1, 5)):
                        quest = Quest.objects.create(
                            from_course=course,
                            name=f"Quest {quest_num}",
                            description=fake.text(),
                            type="Multiple Choice",
                            status="Active",
                            organiser=User.objects.get(id=1),
                            image=Image.objects.get(name="Multiple Choice")
                        )
                        number = 1
                        for question_num in range(1, random.randint(1, 6)):
                            question = Question.objects.create(
                                from_quest=quest,
                                text=fake.sentence(),
                                number=number,
                                max_score=random.randint(1, 5)
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
            for course in Course.objects.all():
                if user in course.enrolled_users.all():
                    for quest in Quest.objects.filter(from_course=course):
                        # Check if an attempt for this quest by this user already exists
                        attempt_exists = UserQuestAttempt.objects.filter(user=user, quest=quest).exists()
                        if not attempt_exists and random.choice([True, False]):
                            # Create a new attempt for a quest
                            first_attempted_on = timezone.make_aware(fake.date_time_this_month())
                            last_attempted_on = first_attempted_on + timezone.timedelta(days=random.randint(1, 7))
                            user_quest_attempt = UserQuestAttempt.objects.create(
                                user=user,
                                quest=quest,
                                first_attempted_on=first_attempted_on,
                                last_attempted_on=last_attempted_on,
                                submitted=False,
                                time_taken=(last_attempted_on - first_attempted_on).total_seconds()*1000
                            )
                            # For each question in the quest, create a question attempt
                            for question in quest.questions.all():
                                user_quest_question_attempt = UserQuestQuestionAttempt.objects.create(
                                    user_quest_attempt=user_quest_attempt,
                                    question=question,
                                    submitted=False,
                                    score_achieved=0
                                )
                                for answer in question.answers.all():
                                    # Create answer record for every answer
                                    AttemptAnswerRecord.objects.create(
                                        user_quest_question_attempt=user_quest_question_attempt,
                                        answer=answer,
                                        is_selected=random.choice([True, False])
                                    )
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
