import factory
import pytz
from ..models import (
    EduquestUser,
    Image,
    AcademicYear,
    Term,
    Course,
    CourseGroup,
    UserCourseGroupEnrollment,
    Quest,
    Question,
    Answer,
    UserQuestAttempt,
    UserAnswerAttempt,
    Badge,
    UserQuestBadge,
    UserCourseBadge,
    Document
)


# Factory Definitions
class EduquestUserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = EduquestUser

    username = factory.Sequence(lambda n: f"user{n}")
    email = factory.LazyAttribute(lambda obj: f"{obj.username}@example.com")
    is_staff = False


class ImageFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Image

    name = factory.Sequence(lambda n: f"Image {n}")
    filename = factory.Sequence(lambda n: f"image_{n}.svg")


class AcademicYearFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = AcademicYear

    start_year = 2021
    end_year = 2022


class TermFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Term

    name = factory.Sequence(lambda n: f"Term {n}")
    start_date = factory.Faker('date_between', start_date='-2y', end_date='today')
    end_date = factory.Faker('date_between', start_date='today', end_date='+1y')
    academic_year = factory.SubFactory(AcademicYearFactory)


class CourseFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Course

    name = factory.Sequence(lambda n: f"Course {n}")
    code = factory.Sequence(lambda n: f"CS{n}")
    type = 'System-enroll'
    description = factory.Faker('text')
    status = 'Active'
    term = factory.SubFactory(TermFactory)
    image = factory.SubFactory(ImageFactory)


class CourseGroupFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = CourseGroup

    course = factory.SubFactory(CourseFactory)
    instructor = factory.SubFactory(EduquestUserFactory)
    name = factory.Sequence(lambda n: f"Group {n}")
    session_day = factory.Faker('day_of_week')
    session_time = factory.Faker('time')


class UserCourseGroupEnrollmentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = UserCourseGroupEnrollment

    course_group = factory.SubFactory(CourseGroupFactory)
    student = factory.SubFactory(EduquestUserFactory)


class QuestFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Quest

    name = factory.Sequence(lambda n: f"Quest {n}")
    description = factory.Faker('text')
    type = 'EduQuest MCQ'
    status = 'Active'
    tutorial_date = factory.Faker('date_time', tzinfo=pytz.UTC)
    expiration_date = factory.Faker('date_time', tzinfo=pytz.UTC)
    max_attempts = 3
    course_group = factory.SubFactory(CourseGroupFactory)
    organiser = factory.SubFactory(EduquestUserFactory)
    image = factory.SubFactory(ImageFactory)


class QuestionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Question

    quest = factory.SubFactory(QuestFactory)
    text = factory.Faker('text')
    number = factory.Sequence(lambda n: n)
    max_score = 5.0


class AnswerFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Answer

    question = factory.SubFactory(QuestionFactory)
    text = factory.Faker('text')
    is_correct = False
    reason = factory.Faker('text')


class UserQuestAttemptFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = UserQuestAttempt

    student = factory.SubFactory(EduquestUserFactory)
    quest = factory.SubFactory(QuestFactory)


class UserAnswerAttemptFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = UserAnswerAttempt

    user_quest_attempt = factory.SubFactory(UserQuestAttemptFactory)
    question = factory.SubFactory(QuestionFactory)
    answer = factory.SubFactory(AnswerFactory)


class BadgeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Badge

    name = factory.Sequence(lambda n: f"Badge {n}")
    description = factory.Faker('text')
    type = 'Course Type'
    condition = factory.Faker('text')
    image = factory.SubFactory(ImageFactory)


class UserQuestBadgeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = UserQuestBadge

    user_quest_attempt = factory.SubFactory(UserQuestAttemptFactory)
    badge = factory.SubFactory(BadgeFactory)
    awarded_date = factory.Faker('date_time', tzinfo=pytz.UTC)


class UserCourseBadgeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = UserCourseBadge

    user_course_group_enrollment = factory.SubFactory(UserCourseGroupEnrollmentFactory)
    badge = factory.SubFactory(BadgeFactory)
    awarded_date = factory.Faker('date_time', tzinfo=pytz.UTC)


class DocumentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Document

    name = factory.Sequence(lambda n: f"Document {n}")
    file = factory.django.FileField(filename='test.pdf')
    size = 100.0
    uploaded_by = factory.SubFactory(EduquestUserFactory)
