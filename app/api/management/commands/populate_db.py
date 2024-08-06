import random
import pytz
import datetime
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
from .template import *

User = get_user_model()
fake = Faker()


class Command(BaseCommand):
    help = 'Populate the database with random data'

    def handle(self, *args, **kwargs):
        self.clear_db()
        self.create_images()
        self.create_users()
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

    def create_images(self):
        for image_item in image_list:
            Image.objects.create(
                name=image_item["name"],
                filename=image_item["filename"]
            )
            print(f"Created image: {image_item['name']}")

    def create_users(self):
        for _ in range(6):
            user = EduquestUser.objects.create(
                username=f"#{fake.name().upper()}#",
                email=f"{fake.user_name().upper()}@e.ntu.edu.sg",
                password='password',
                nickname=fake.first_name(),
                is_active=True,
                is_staff=False
            )
            print(f"Created user: {user.username}")

    def create_badges(self):
        for badge in badge_list:
            Badge.objects.create(
                name=badge["name"],
                description=badge["description"],
                type=badge["type"],
                condition=badge["condition"],
                image=Image.objects.get(filename=badge["image"])
            )

    def create_academic_years_terms_courses_quests_questions(self):
        for year in year_list:
            academic_year = AcademicYear.objects.create(
                start_year=year["start_year"],
                end_year=year["end_year"]
            )

            for term_item in term_list:
                term = Term.objects.create(
                    academic_year=academic_year,
                    name=term_item["name"],
                    start_date=term_item["start_date"],
                    end_date=term_item["end_date"]
                )

                for course_item in course_list:
                    course = Course.objects.create(
                        term=term,
                        name=f"{course_item['name']}",
                        code=course_item["code"],
                        type="Public",
                        description=course_item["description"],
                        status="Active",
                        image=Image.objects.get(name=course_item["name"])
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
                    for quest_num in range(1, random.randint(2, 4)):
                        expired_date = random.choice([None, timezone.make_aware(
                            fake.date_time_between_dates(term_item["start_date"], term_item["end_date"]).replace(hour=23, minute=59, second=59, microsecond=999999)
                            + timezone.timedelta(days=random.randint(1, 7))
                        )])
                        status = "Active"
                        if expired_date:
                            if expired_date < timezone.now():
                                status = "Expired"
                        quest = Quest.objects.create(
                            from_course=course,
                            name=f"Quest {quest_num}",
                            description=fake.text(),
                            type="Eduquest MCQ",
                            expiration_date=expired_date,
                            status=status,
                            max_attempts=random.randint(1, 5),
                            organiser=User.objects.get(id=1),
                            image=Image.objects.get(name="Multiple Choice")
                        )
                        for question_num in range(1, random.randint(3, 5)):
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
                    for i in range(random.randint(1, quest.max_attempts)):
                        first_attempted_on = timezone.make_aware(fake.date_time_this_month())
                        last_attempted_on = first_attempted_on + timezone.timedelta(days=random.randint(1, 7))
                        user_quest_attempt = UserQuestAttempt.objects.create(
                            user=user,
                            quest=quest,
                            first_attempted_on=first_attempted_on,
                            last_attempted_on=last_attempted_on,
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

