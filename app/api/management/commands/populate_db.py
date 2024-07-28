import random
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from faker import Faker
from ...models import (
    EduquestUser,
    Image,
    AcademicYear,
    Term,
    Course,
    UserCourse,
    Quest,
    Question,
    Answer,
    UserQuestAttempt,
    UserQuestQuestionAttempt,
    AttemptAnswerRecord,
    Badge,
    UserQuestBadge,
    UserCourseBadge
)

User = get_user_model()
fake = Faker()


class Command(BaseCommand):
    help = 'Populate the database with random data'

    def handle(self, *args, **kwargs):
        self.clear_db()
        self.create_users()
        self.create_images()
        self.create_badges()
        self.create_academic_years_terms_courses_quests_questions()
        self.create_attempts()


    def clear_db(self):
        eduquestUsers = EduquestUser.objects.filter(id__gt=2)
        eduquestUsers.delete()
        Image.objects.all().delete()
        AcademicYear.objects.all().delete()
        Badge.objects.all().delete()
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
                       "Database", "Multiple Choice", "Wooclap", "Kahoot", "First Attempt Badge", "Completionist Badge",
                       "Expert Badge", "Speedster Badge", "Perfectionist Badge"]
        image_filenames = ["cloud_computing.svg", "data_science.svg", "machine_learning_and_ai.svg",
                           "computer_architecture.svg", "cyber_security.svg", "data_structure_and_algorithm.svg",
                           "database.svg", "multiple_choice.svg", "wooclap.svg", "kahoot.svg", "first_attempt_badge.svg",
                           "completionist_badge.svg", "expert_badge.svg", "speedster_badge.svg", "perfectionist_badge.svg"]
        for i in range(len(image_names)):
            Image.objects.create(name=image_names[i], filename=image_filenames[i])

    def create_badges(self):
        badge_name_description_type = [
            {
                "name": "First Attempt",
                "description": "Awarded upon completing any quest for the first time.",
                "type": "Quest",
                "image": "first_attempt_badge.svg"
            },
            {
                "name": "Completionist",
                "description": "Awarded upon completing all quests within a course.",
                "type": "Course",
                "image": "completionist_badge.svg"
            },
            {
                "name": "Expert",
                "description": "Awarded for achieving the highest score on a quest.",
                "type": "Quest",
                "image": "expert_badge.svg"
            },
            {
                "name": "Speedster",
                "description": "Awarded for achieving the highest score on a quest and shortest overall time.",
                "type": "Quest",
                "image": "speedster_badge.svg"
            },
            {
                "name": "Perfectionist",
                "description": "Awarded for achieving a perfect score on a quiz.",
                "type": "Quest",
                "image": "perfectionist_badge.svg"
            }
        ]
        for badge in badge_name_description_type:
            Badge.objects.create(
                name=badge["name"],
                description=badge["description"],
                type=badge["type"],
                image=Image.objects.get(filename=badge["image"])
            )

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
                    for user in User.objects.filter(id__gt=1):
                        if random.choice([True, False]):
                            UserCourse.objects.create(
                                user=user,
                                course=course,
                                enrolled_on=timezone.make_aware(fake.date_time_this_month())
                            )
                    # Continue with quest and question creation
                    for quest_num in range(0, random.randint(1, 3)):
                        quest = Quest.objects.create(
                            from_course=course,
                            name=f"Quest {quest_num}",
                            description=fake.text(),
                            type="Multiple Choice",
                            status="Active",
                            max_attempts=random.randint(1, 4),
                            organiser=User.objects.get(id=1),
                            image=Image.objects.get(name="Multiple Choice")
                        )
                        for question_num in range(1, random.randint(2, 5)):
                            question = Question.objects.create(
                                from_quest=quest,
                                text=fake.sentence(),
                                number=question_num,
                                max_score=random.randint(1, 5)
                            )
                            for _ in range(4):
                                Answer.objects.create(
                                    question=question,
                                    text=fake.word(),
                                    is_correct=random.choice([True, False])
                                )
            print(f"Created academic year: {academic_year.start_year}-{academic_year.end_year}")

    def create_attempts(self):
        # Iterate through all users except the superuser
        for user in User.objects.filter(id__gt=1):
            # Iterate through all courses the user is enrolled in
            for user_course in UserCourse.objects.filter(user=user):
                # Iterate through all quests in the course enrolled in
                for quest in Quest.objects.filter(from_course=user_course.course):
                    # Randomly create some attempts for a quest
                    for i in range(random.randint(1, 3)):
                        user_quest_attempt = UserQuestAttempt.objects.create(
                            user=user,
                            quest=quest,
                            first_attempted_on=timezone.make_aware(fake.date_time_this_month()),
                            last_attempted_on=timezone.make_aware(fake.date_time_this_month() + timezone.timedelta(days=random.randint(1, 7))),
                            all_questions_submitted=False
                        )
                        # For each user quest attempt, randomly attempt some questions
                        for question in Question.objects.filter(from_quest=user_quest_attempt.quest):
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
                        print(f"Created attempt for user: {user.username}, course: {user_course.course} - quest: {quest.name}")

