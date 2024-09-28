from django.test import TestCase
from unittest.mock import patch

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

from ..serializers import (
    EduquestUserSerializer,
    EduquestUserSummarySerializer,
    ImageSerializer,
    AcademicYearSerializer,
    TermSerializer,
    CourseSerializer,
    CourseGroupSerializer,
    UserCourseGroupEnrollmentSerializer,
    QuestSerializer,
    QuestionSerializer,
    AnswerSerializer,
    UserQuestAttemptSerializer,
    UserAnswerAttemptSerializer,
    BadgeSerializer,
    UserQuestBadgeSerializer,
    UserCourseBadgeSerializer,
    DocumentSerializer

)

from .factory import (
    EduquestUserFactory,
    ImageFactory,
    AcademicYearFactory,
    TermFactory,
    CourseFactory,
    CourseGroupFactory,
    UserCourseGroupEnrollmentFactory,
    QuestFactory,
    QuestionFactory,
    AnswerFactory,
    UserQuestAttemptFactory,
    UserAnswerAttemptFactory,
    BadgeFactory,
    UserQuestBadgeFactory,
    UserCourseBadgeFactory,
)


class EduquestUserSerializerTest(TestCase):

    def test_serializer_fields(self):
        """
        Test that the serializer returns the correct fields.
        """
        user = EduquestUser.objects.create_user(
            username='#Bob Builder#',
            email='bob@example.com',
            first_name='Bob',
            last_name='Builder',
            nickname='bobbuilder',
            is_staff=True
        )

        serializer = EduquestUserSerializer(user)
        data = serializer.data

        expected_fields = [
            'id', 'first_name', 'last_name', 'username', 'email', 'nickname',
            'last_login', 'updated_at', 'is_superuser', 'is_active',
            'is_staff', 'total_points'
        ]

        for field in expected_fields:
            self.assertIn(field, data)

    @patch('api.models.split_full_name')
    def test_read_only_fields(self, mock_split_full_name):
        """
        Test that read-only fields are not updated.
        """
        mock_split_full_name.return_value = ('Chris', 'Brown')

        user = EduquestUser.objects.create_user(
            username='#Chris Brown#',
            email='chris@example.com',
            is_superuser=True
        )

        data = {
            'username': '#NewFirstName NewLastName#',
            'first_name': 'NewFirstName',
            'last_name': 'NewLastName',
            'email': 'newemail@example.com',
            'nickname': 'newnickname',
            'is_superuser': False
        }

        serializer = EduquestUserSerializer(user, data=data, partial=True)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        updated_user = serializer.save()

        # Read-only fields should not be updated
        self.assertEqual(updated_user.username, '#Chris Brown#')
        self.assertEqual(updated_user.first_name, 'Chris')
        self.assertEqual(updated_user.last_name, 'Brown')
        self.assertEqual(updated_user.is_superuser, True)

        # Updatable fields should be updated
        self.assertEqual(updated_user.email, 'newemail@example.com')
        self.assertEqual(updated_user.nickname, 'newnickname')


class ImageSerializerTest(TestCase):

    def test_serializer_fields(self):
        """
        Test that the serializer returns the correct fields.
        """
        image = Image.objects.create(
            name='Test Image',
            filename='test.jpg'
        )
        serializer = ImageSerializer(image)
        data = serializer.data
        expected_fields = [
            'id', 'name', 'filename'
        ]
        for field in expected_fields:
            self.assertIn(field, data)


class AcademicYearSerializerTest(TestCase):
    def test_serializer_create(self):
        """
        Test that the serializer creates an AcademicYear instance
        """
        data = {
            'start_year': 2022,
            'end_year': 2023
        }
        serializer = AcademicYearSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        ay = serializer.save()
        self.assertEqual(ay.start_year, 2022)
        self.assertEqual(ay.end_year, 2023)

    def test_serializer_invalid_data(self):
        """
        Test that the serializer rejects invalid data
        """
        data = {
            'start_year': 'invalid',  # Should be an integer
            'end_year': 2023
        }
        serializer = AcademicYearSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('start_year', serializer.errors)


class TermSerializerTest(TestCase):
    def setUp(self):
        self.ay = AcademicYearFactory()

    def test_serializer_create(self):
        """
        Test that the serializer creates a Term instance
        """
        data = {
            'name': 'Term 1',
            'start_date': '2021-08-01',
            'end_date': '2021-12-15',
            'academic_year_id': self.ay.id
        }
        serializer = TermSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        term = serializer.save()
        self.assertEqual(term.name, 'Term 1')
        self.assertEqual(term.academic_year, self.ay)
        self.assertEqual(str(term.start_date), '2021-08-01')

    def test_serializer_read(self):
        """
        Test that the serializer returns the correct data
        """
        term = Term.objects.create(
            academic_year=self.ay,
            name="Term 2",
            start_date="2022-01-10",
            end_date="2022-05-20"
        )
        serializer = TermSerializer(term)
        data = serializer.data
        self.assertEqual(data['name'], 'Term 2')
        self.assertEqual(data['academic_year']['id'], self.ay.id)
        self.assertEqual(data['academic_year']['start_year'], 2021)

    def test_serializer_update(self):
        """
        Test that the serializer updates an existing Term instance
        """
        term = Term.objects.create(
            academic_year=self.ay,
            name="Term 3",
            start_date="2022-06-01",
            end_date="2022-10-15"
        )
        new_ay = AcademicYear.objects.create(start_year=2022, end_year=2023)
        data = {
            'name': 'Updated Term 3',
            'academic_year_id': new_ay.id
        }
        serializer = TermSerializer(instance=term, data=data, partial=True)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        updated_term = serializer.save()
        self.assertEqual(updated_term.name, 'Updated Term 3')
        self.assertEqual(updated_term.academic_year, new_ay)


class CourseSerializerTest(TestCase):
    def setUp(self):
        # Create test users (coordinators)
        self.coordinator_one = EduquestUserFactory()
        self.coordinator_two = EduquestUserFactory()
        # Create a test term
        self.term = TermFactory()
        # Create a test image
        self.image = ImageFactory()

    def test_create_course_success(self):
        """
        Test that the serializer successfully creates a Course instance with valid data.
        """
        data = {
            'name': 'Introduction to Testing',
            'code': 'CS1000',
            'type': 'System-enroll',
            'description': 'A course on testing in software development.',
            'status': 'Active',
            'term_id': self.term.id,
            'image_id': self.image.id,
            'coordinators': [self.coordinator_one.id, self.coordinator_two.id]
        }
        serializer = CourseSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        course = serializer.save()

        # Assertions
        self.assertEqual(course.name, 'Introduction to Testing')
        self.assertEqual(course.code, 'CS1000')
        self.assertEqual(course.type, 'System-enroll')
        self.assertEqual(course.description, 'A course on testing in software development.')
        self.assertEqual(course.status, 'Active')
        self.assertEqual(course.term, self.term)
        self.assertEqual(course.image, self.image)
        self.assertQuerysetEqual(
            course.coordinators.all(),
            [repr(self.coordinator_one), repr(self.coordinator_two)],
            transform=repr,
            ordered=False
        )

    def test_create_course_without_coordinators(self):
        """
        Test that the serializer raises a validation error when no coordinators are provided.
        """
        data = {
            'name': 'Advanced Testing',
            'code': 'CS2000',
            'type': 'Private',
            'description': 'An advanced course on testing methodologies.',
            'status': 'Active',
            'term_id': self.term.id,
            'image_id': self.image.id,
            'coordinators': []  # Empty list should trigger validation error
        }
        serializer = CourseSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('coordinators', serializer.errors)
        self.assertEqual(
            serializer.errors['coordinators'][0],
            'At least one coordinator must be assigned to the course.'
        )

    def test_update_course_success(self):
        """
        Test that the serializer successfully updates an existing Course instance.
        """
        # Create initial course
        course = Course.objects.create(
            name='Basic Course',
            code='CS0001',
            type='System-enroll',
            description='Basic course description.',
            status='Active',
            term=self.term,
            image=self.image
        )
        course.coordinators.set([self.coordinator_one])

        # New data for update
        new_data = {
            'name': 'Updated Course Name',
            'code': 'CS0002',
            'coordinators': [self.coordinator_two.id]
        }
        serializer = CourseSerializer(instance=course, data=new_data, partial=True)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        updated_course = serializer.save()

        # Assertions
        self.assertEqual(updated_course.name, 'Updated Course Name')
        self.assertEqual(updated_course.code, 'CS0002')
        self.assertQuerysetEqual(
            updated_course.coordinators.all(),
            [repr(self.coordinator_two)],
            transform=repr,
            ordered=False
        )

    def test_update_course_remove_all_coordinators(self):
        """
        Test that the serializer raises a validation error when attempting to remove all coordinators.
        """
        # Create initial course
        course = Course.objects.create(
            name='Basic Course',
            code='CS0001',
            type='System-enroll',
            description='Basic course description.',
            status='Active',
            term=self.term,
            image=self.image
        )
        course.coordinators.set([self.coordinator_one, self.coordinator_two])

        # Attempt to remove all coordinators
        new_data = {
            'coordinators': []
        }
        serializer = CourseSerializer(instance=course, data=new_data, partial=True)
        self.assertFalse(serializer.is_valid())
        self.assertIn('coordinators', serializer.errors)
        self.assertEqual(
            serializer.errors['coordinators'][0],
            'At least one coordinator must be assigned to the course.'
        )


class CourseGroupSerializerTest(TestCase):
    def setUp(self):
        # Create test coordinators
        self.coordinator_one = EduquestUserFactory()
        self.coordinator_two = EduquestUserFactory()
        # Create a test term
        self.term = TermFactory()
        # Create a test course
        self.course = CourseFactory(term=self.term)
        self.course.coordinators.set([self.coordinator_one, self.coordinator_two])

        # Create an image
        self.image = ImageFactory()

    def test_create_course_group_success(self):
        """
        Test that the serializer successfully creates a CourseGroup instance with valid data.
        """
        data = {
            'course_id': self.course.id,
            'instructor_id': self.coordinator_one.id,
            'name': 'Group A',
            'session_day': 'Monday',
            'session_time': '10:00 AM'
        }
        serializer = CourseGroupSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        course_group = serializer.save()

        # Assertions
        self.assertEqual(course_group.name, 'Group A')
        self.assertEqual(course_group.course, self.course)
        self.assertEqual(course_group.instructor, self.coordinator_one)
        self.assertEqual(course_group.session_day, 'Monday')
        self.assertEqual(course_group.session_time, '10:00 AM')
        self.assertEqual(course_group.total_students_enrolled(), 0)

    def test_update_course_group_success(self):
        """
        Test that the serializer successfully updates an existing CourseGroup instance.
        """
        # Create initial CourseGroup
        course_group = CourseGroup.objects.create(
            course=self.course,
            instructor=self.coordinator_one,
            name='Group B',
            session_day='Tuesday',
            session_time='2:00 PM'
        )

        # Update data
        data = {
            'name': 'Updated Group B',
            'session_day': 'Wednesday',
            'instructor_id': self.coordinator_two.id
        }
        serializer = CourseGroupSerializer(instance=course_group, data=data, partial=True)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        updated_course_group = serializer.save()

        # Assertions
        self.assertEqual(updated_course_group.name, 'Updated Group B')
        self.assertEqual(updated_course_group.session_day, 'Wednesday')
        self.assertEqual(updated_course_group.instructor, self.coordinator_two)

    def test_update_course_group_change_course(self):
        """
        Test updating the course of a CourseGroup.
        """
        # Create a second course
        second_course = Course.objects.create(
            name='Advanced Testing',
            code='CS2000',
            type='Private',
            description='An advanced course on testing methodologies.',
            status='Active',
            term=self.term,
            image_id=self.image.id
        )
        second_course.coordinators.set([self.coordinator_two])

        # Create initial CourseGroup
        course_group = CourseGroup.objects.create(
            course=self.course,
            instructor=self.coordinator_one,
            name='Group C',
            session_day='Thursday',
            session_time='4:00 PM'
        )

        # Update data to change course
        data = {
            'course_id': second_course.id,
            'name': 'Group C Updated'
        }
        serializer = CourseGroupSerializer(instance=course_group, data=data, partial=True)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        updated_course_group = serializer.save()

        # Assertions
        self.assertEqual(updated_course_group.course, second_course)
        self.assertEqual(updated_course_group.name, 'Group C Updated')

    def test_create_course_group_missing_required_fields(self):
        """
        Test that the serializer raises a validation error when required fields are missing.
        """
        data = {
            'course_id': self.course.id,
            # 'instructor_id' is missing
            'name': 'Group D',
            'session_day': 'Friday',
            'session_time': '1:00 PM'
        }
        serializer = CourseGroupSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('instructor_id', serializer.errors)

    def test_create_course_group_invalid_course(self):
        """
        Test that the serializer raises a validation error when an invalid course_id is provided.
        """
        data = {
            'course_id': 999,  # Assuming this ID does not exist
            'instructor_id': self.coordinator_one.id,
            'name': 'Group E',
            'session_day': 'Saturday',
            'session_time': '3:00 PM'
        }
        serializer = CourseGroupSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('course_id', serializer.errors)


class UserCourseGroupEnrollmentSerializerTest(TestCase):
    def setUp(self):
        # Create test users
        self.student_one = EduquestUser.objects.create_user(
            username='#Student One#',
            email='student_one@example.com',
        )
        self.student_two = EduquestUser.objects.create_user(
            username='#Student Two#',
            email='student_two@example.com',
            password='password123'
        )
        self.instructor = EduquestUser.objects.create_user(
            username='#Instructor#',
            email='instructor@example.com',
        )
        # Create a term and academic year
        self.ay = AcademicYear.objects.create(start_year=2021, end_year=2022)
        self.term = Term.objects.create(
            name='Term 1',
            start_date='2021-08-01',
            end_date='2021-12-15',
            academic_year=self.ay
        )
        # Create a course
        self.course = Course.objects.create(
            name='Introduction to Testing',
            code='CS1000',
            type='System-enroll',
            description='A course on testing in software development.',
            status='Active',
            term=self.term,
            image_id=1  # Assuming Image with ID 1 exists
        )
        self.course.coordinators.set([self.instructor])
        # Create course groups
        self.course_group_a = CourseGroup.objects.create(
            course=self.course,
            instructor=self.instructor,
            name='Group A',
            session_day='Monday',
            session_time='10:00 AM'
        )
        self.course_group_b = CourseGroup.objects.create(
            course=self.course,
            instructor=self.instructor,
            name='Group B',
            session_day='Wednesday',
            session_time='2:00 PM'
        )

    def test_create_enrollment_success(self):
        """
        Test that the serializer successfully creates a UserCourseGroupEnrollment instance.
        """
        data = {
            'course_group_id': self.course_group_a.id,
            'student_id': self.student_one.id
        }
        serializer = UserCourseGroupEnrollmentSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        enrollment = serializer.save()

        # Assertions
        self.assertEqual(enrollment.course_group, self.course_group_a)
        self.assertEqual(enrollment.student, self.student_one)
        self.assertIsNotNone(enrollment.enrolled_on)
        self.assertIsNone(enrollment.completed_on)

    def test_create_duplicate_enrollment_same_group(self):
        """
        Test that the serializer raises a validation error when enrolling a student in the same course group twice.
        """
        # First enrollment
        UserCourseGroupEnrollment.objects.create(
            course_group=self.course_group_a,
            student=self.student_one
        )

        # Attempt duplicate enrollment
        data = {
            'course_group_id': self.course_group_a.id,
            'student_id': self.student_one.id
        }
        serializer = UserCourseGroupEnrollmentSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('enrollment', serializer.errors)
        self.assertEqual(
            serializer.errors['enrollment'][0],
            'This student is already enrolled in this course group.'
        )

    def test_create_enrollment_same_course_different_group(self):
        """
        Test that the serializer prevents a student from enrolling in multiple groups within the same course.
        """
        # First enrollment in Group A
        UserCourseGroupEnrollment.objects.create(
            course_group=self.course_group_a,
            student=self.student_one
        )

        # Attempt enrollment in Group B (same course)
        data = {
            'course_group_id': self.course_group_b.id,
            'student_id': self.student_one.id
        }
        serializer = UserCourseGroupEnrollmentSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('enrollment', serializer.errors)
        self.assertEqual(
            serializer.errors['enrollment'][0],
            'This student is already enrolled in another course group within the same course.'
        )

    def test_create_enrollment_different_course(self):
        """
        Test that a student can enroll in course groups of different courses.
        """
        # Create a second course
        second_course = Course.objects.create(
            name='Advanced Testing',
            code='CS2000',
            type='Private',
            description='An advanced course on testing methodologies.',
            status='Active',
            term=self.term,
            image_id=1
        )
        second_course.coordinators.set([self.instructor])

        # Create a course group for the second course
        course_group_c = CourseGroup.objects.create(
            course=second_course,
            instructor=self.instructor,
            name='Group C',
            session_day='Friday',
            session_time='4:00 PM'
        )

        # Enroll student in Group A (Course 1)
        UserCourseGroupEnrollment.objects.create(
            course_group=self.course_group_a,
            student=self.student_one
        )

        # Attempt enrollment in Group C (Course 2)
        data = {
            'course_group_id': course_group_c.id,
            'student_id': self.student_one.id
        }
        serializer = UserCourseGroupEnrollmentSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        enrollment = serializer.save()

        # Assertions
        self.assertEqual(enrollment.course_group, course_group_c)
        self.assertEqual(enrollment.student, self.student_one)

    def test_update_enrollment_success(self):
        """
        Test that the serializer successfully updates a UserCourseGroupEnrollment instance.
        """
        # Create initial enrollment in Group A
        enrollment = UserCourseGroupEnrollment.objects.create(
            course_group=self.course_group_a,
            student=self.student_one
        )

        # Update data to change course group to Group B
        data = {
            'course_group_id': self.course_group_b.id
        }
        serializer = UserCourseGroupEnrollmentSerializer(instance=enrollment, data=data, partial=True)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        updated_enrollment = serializer.save()

        # Assertions
        self.assertEqual(updated_enrollment.course_group, self.course_group_b)

    def test_update_enrollment_to_duplicate(self):
        """
        Test that updating a UserCourseGroupEnrollment to a duplicate enrollment raises a validation error.
        """
        # Create two enrollments
        enrollment_a = UserCourseGroupEnrollment.objects.create(
            course_group=self.course_group_a,
            student=self.student_one
        )
        enrollment_b = UserCourseGroupEnrollment.objects.create(
            course_group=self.course_group_b,
            student=self.student_two
        )

        # Attempt to update enrollment_b to have the same course_group and student as enrollment_a
        data = {
            'course_group_id': self.course_group_a.id,
            'student_id': self.student_one.id
        }
        serializer = UserCourseGroupEnrollmentSerializer(instance=enrollment_b, data=data, partial=True)
        self.assertFalse(serializer.is_valid())
        self.assertIn('enrollment', serializer.errors)
        self.assertEqual(
            serializer.errors['enrollment'][0],
            'This student is already enrolled in this course group.'
        )


class QuestSerializerTest(TestCase):
    def setUp(self):
        # Create test user (organiser)
        self.organiser = EduquestUserFactory()

        # Create a course
        self.course = CourseFactory()
        self.course.coordinators.set([self.organiser])

        # Create a course group
        self.course_group = CourseGroupFactory(course=self.course, instructor=self.organiser)

        # Create an image
        self.image = ImageFactory()

    def test_create_quest_success(self):
        """
        Test that the serializer successfully creates a Quest instance with valid data.
        """
        data = {
            'name': 'Quest 1',
            'description': 'First quest for testing.',
            'type': 'EduQuest MCQ',
            'status': 'Active',
            'tutorial_date': '2021-08-05T10:00:00Z',
            'expiration_date': '2021-08-12T10:00:00Z',
            'max_attempts': 3,
            'course_group_id': self.course_group.id,
            'organiser_id': self.organiser.id,
            'image_id': self.image.id
        }
        serializer = QuestSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        quest = serializer.save()

        # Assertions
        self.assertEqual(quest.name, 'Quest 1')
        self.assertEqual(quest.description, 'First quest for testing.')
        self.assertEqual(quest.type, 'EduQuest MCQ')
        self.assertEqual(quest.status, 'Active')
        self.assertEqual(str(quest.tutorial_date), '2021-08-05 10:00:00+00:00')
        self.assertEqual(str(quest.expiration_date), '2021-08-12 10:00:00+00:00')
        self.assertEqual(quest.max_attempts, 3)
        self.assertEqual(quest.course_group, self.course_group)
        self.assertEqual(quest.organiser, self.organiser)
        self.assertEqual(quest.image, self.image)
        self.assertEqual(quest.total_max_score(), 0)
        self.assertEqual(quest.total_questions(), 0)

    def test_create_quest_missing_required_fields(self):
        """
        Test that the serializer raises a validation error when required fields are missing.
        """
        data = {
            # 'name' is missing
            'description': 'Missing name field.',
            'type': 'EduQuest MCQ',
            'status': 'Active',
            'tutorial_date': '2021-08-05T10:00:00Z',
            'expiration_date': '2021-08-12T10:00:00Z',
            'max_attempts': 3,
            'course_group_id': self.course_group.id,
            'organiser_id': self.organiser.id,
            'image_id': self.image.id
        }
        serializer = QuestSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('name', serializer.errors)

    def test_update_quest_success(self):
        """
        Test that the serializer successfully updates an existing Quest instance.
        """
        # Create initial Quest
        quest = Quest.objects.create(
            name='Quest 2',
            description='Second quest description.',
            type='Kahoot!',
            status='Active',
            tutorial_date='2021-08-06T10:00:00Z',
            expiration_date='2021-08-13T10:00:00Z',
            max_attempts=2,
            course_group=self.course_group,
            organiser=self.organiser,
            image=self.image
        )

        # Update data
        data = {
            'name': 'Updated Quest 2',
            'max_attempts': 4
        }
        serializer = QuestSerializer(instance=quest, data=data, partial=True)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        updated_quest = serializer.save()

        # Assertions
        self.assertEqual(updated_quest.name, 'Updated Quest 2')
        self.assertEqual(updated_quest.max_attempts, 4)

    def test_serializer_read(self):
        """
        Test that the serializer returns the correct data for reading operations.
        """
        # Create a Quest instance
        quest = Quest.objects.create(
            name='Quest 3',
            description='Third quest description.',
            type='EduQuest MCQ',
            status='Active',
            tutorial_date='2021-08-07T10:00:00Z',
            expiration_date='2021-08-14T10:00:00Z',
            max_attempts=1,
            course_group=self.course_group,
            organiser=self.organiser,
            image=self.image
        )

        serializer = QuestSerializer(quest)
        data = serializer.data

        # Assertions
        self.assertEqual(data['name'], 'Quest 3')
        self.assertEqual(data['description'], 'Third quest description.')
        self.assertEqual(data['type'], 'EduQuest MCQ')
        self.assertEqual(data['status'], 'Active')
        self.assertEqual(data['tutorial_date'], '2021-08-07T10:00:00Z')
        self.assertEqual(data['expiration_date'], '2021-08-14T10:00:00Z')
        self.assertEqual(data['max_attempts'], 1)
        self.assertEqual(data['course_group']['id'], self.course_group.id)
        self.assertEqual(data['organiser']['id'], self.organiser.id)
        self.assertEqual(data['image']['id'], self.image.id)
        self.assertEqual(data['total_max_score'], 0)
        self.assertEqual(data['total_questions'], 0)


class QuestionSerializerTest(TestCase):
    def setUp(self):
        # Create organiser
        self.organiser = EduquestUserFactory()
        # Create course and course group
        self.course = CourseFactory()
        self.course.coordinators.set([self.organiser])
        self.course_group = CourseGroupFactory(course=self.course, instructor=self.organiser)
        # Create a quest
        self.quest = QuestFactory(course_group=self.course_group, organiser=self.organiser)

    def test_create_question_with_answers_success(self):
        """
        Test that the serializer successfully creates a Question with associated Answers.
        """
        data = {
            'quest_id': self.quest.id,
            'text': 'What is unit testing?',
            'number': 1,
            'max_score': 5.0,
            'answers': [
                {'text': 'Testing individual components.', 'is_correct': True, 'reason': 'Correct definition.'},
                {'text': 'Testing the entire system.', 'is_correct': False, 'reason': 'System testing.'},
            ]
        }
        serializer = QuestionSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        question = serializer.save()

        # Assertions
        self.assertEqual(question.text, 'What is unit testing?')
        self.assertEqual(question.number, 1)
        self.assertEqual(question.max_score, 5.0)
        self.assertEqual(question.quest, self.quest)
        self.assertEqual(question.answers.count(), 2)

        correct_answer = question.answers.get(is_correct=True)
        self.assertEqual(correct_answer.text, 'Testing individual components.')
        self.assertEqual(correct_answer.reason, 'Correct definition.')

        incorrect_answer = question.answers.get(is_correct=False)
        self.assertEqual(incorrect_answer.text, 'Testing the entire system.')
        self.assertEqual(incorrect_answer.reason, 'System testing.')

    def test_create_question_missing_required_fields(self):
        """
        Test that the serializer raises a validation error when required fields are missing.
        """
        data = {
            # 'quest_id' is missing
            'text': 'What is integration testing?',
            'number': 2,
            'max_score': 5.0,
            'answers': [
                {'text': 'Testing interactions between components.', 'is_correct': True, 'reason': 'Correct.'},
                {'text': 'Testing individual units.', 'is_correct': False, 'reason': 'Unit testing.'},
            ]
        }
        serializer = QuestionSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('quest_id', serializer.errors)

    def test_bulk_create_questions_success(self):
        """
        Test that the serializer can handle bulk creation of multiple Questions.
        """
        data = [
            {
                'quest_id': self.quest.id,
                'text': 'What is integration testing?',
                'number': 2,
                'max_score': 5.0,
                'answers': [
                    {'text': 'Testing interactions between components.', 'is_correct': True, 'reason': 'Correct.'},
                    {'text': 'Testing individual units.', 'is_correct': False, 'reason': 'Unit testing.'},
                ]
            },
            {
                'quest_id': self.quest.id,
                'text': 'What is system testing?',
                'number': 3,
                'max_score': 5.0,
                'answers': [
                    {'text': 'Testing the entire system as a whole.', 'is_correct': True, 'reason': 'Correct.'},
                    {'text': 'Testing individual components.', 'is_correct': False, 'reason': 'Unit testing.'},
                ]
            }
        ]
        serializer = QuestionSerializer(data=data, many=True)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        questions = serializer.save()

        # Assertions
        self.assertEqual(len(questions), 2)
        self.assertEqual(Question.objects.count(), 2)
        self.assertEqual(Answer.objects.count(), 4)

    def test_bulk_create_questions_with_invalid_data(self):
        """
        Test that the serializer raises validation errors when bulk creating with invalid data.
        """
        data = [
            {
                'quest_id': self.quest.id,
                'text': 'What is acceptance testing?',
                'number': 4,
                'max_score': 5.0,
                'answers': [
                    {'text': 'Testing with real users.', 'is_correct': True, 'reason': 'Correct.'},
                    {'text': 'Testing with test data.', 'is_correct': False, 'reason': 'Not acceptance testing.'},
                ]
            },
            {
                # Missing 'text' field
                'quest_id': self.quest.id,
                'number': 5,
                'max_score': 5.0,
                'answers': [
                    {'text': 'Testing in production.', 'is_correct': True, 'reason': 'Correct.'},
                ]
            }
        ]
        serializer = QuestionSerializer(data=data, many=True)
        self.assertFalse(serializer.is_valid())
        self.assertEqual(len(serializer.errors), 2)
        self.assertIn('text', serializer.errors[1])


class UserQuestAttemptSerializerTest(TestCase):
    def setUp(self):
        # Create organiser
        self.organiser = EduquestUserFactory()
        # Create student
        self.student = EduquestUserFactory()
        # Create course and course group
        self.course = CourseFactory()
        self.course.coordinators.set([self.organiser])
        self.course_group = CourseGroupFactory(course=self.course, instructor=self.organiser)

        # Create a quest
        self.quest = QuestFactory(course_group=self.course_group, organiser=self.organiser, max_attempts=2)

        # Create questions and answers for the quest
        self.question1 = QuestionFactory(quest=self.quest, text='What is unit testing?', number=1, max_score=5.0)
        self.answer1_q1 = AnswerFactory(question=self.question1, text='Testing individual components.', is_correct=True)
        self.answer2_q1 = AnswerFactory(question=self.question1, text='Testing the entire system.', is_correct=False)

        self.question2 = QuestionFactory(quest=self.quest, text='What is integration testing?', number=2, max_score=5.0)
        self.answer1_q2 = AnswerFactory(question=self.question2, text='Testing interactions between components.', is_correct=True)
        self.answer2_q2 = AnswerFactory(question=self.question2, text='Testing individual units.', is_correct=False)

    def test_create_user_quest_attempt_student_not_enrolled(self):
        """
        Test that the serializer raises a validation error when the student is not enrolled in the course group.
        """
        # Attempt to create a quest attempt without enrollment
        data = {
            'quest_id': self.quest.id,
            'student_id': self.student.id
        }
        serializer = UserQuestAttemptSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('non_field_errors', serializer.errors)
        self.assertEqual(
            serializer.errors['non_field_errors'][0],
            "Student must be enrolled in the course group to attempt this quest."
        )

        # Create enrollment
        UserCourseGroupEnrollment.objects.create(
            student=self.student,
            course_group=self.course_group
        )

        # Attempt to create a quest attempt with enrollment
        serializer = UserQuestAttemptSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_create_user_quest_attempt_success(self):
        """
        Test that the serializer successfully creates a UserQuestAttempt and associated UserAnswerAttempts.
        """
        # Create enrollment
        UserCourseGroupEnrollment.objects.create(
            student=self.student,
            course_group=self.course_group
        )
        data = {
            'quest_id': self.quest.id,
            'student_id': self.student.id
        }
        serializer = UserQuestAttemptSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        attempt = serializer.save()

        # Assertions
        self.assertEqual(attempt.quest, self.quest)
        self.assertEqual(attempt.student, self.student)
        self.assertTrue(attempt.submitted is False)
        self.assertEqual(attempt.total_score_achieved, 0)
        self.assertIsNone(attempt.first_attempted_date)
        self.assertIsNone(attempt.last_attempted_date)

        # Check associated UserAnswerAttempts
        self.assertEqual(attempt.answer_attempts.count(), 4)  # 2 questions x 2 answers each
        for uaa in attempt.answer_attempts.all():
            self.assertFalse(uaa.is_selected)
            self.assertEqual(uaa.score_achieved, 0)

    def test_create_user_quest_attempt_max_attempts_exceeded(self):
        """
        Test that the serializer raises a validation error when the maximum number of attempts is exceeded.
        """
        # Create enrollment
        UserCourseGroupEnrollment.objects.create(
            student=self.student,
            course_group=self.course_group
        )
        # Create two existing attempts (max_attempts=2)
        UserQuestAttempt.objects.create(
            quest=self.quest,
            student=self.student,
            submitted=True
        )
        UserQuestAttempt.objects.create(
            quest=self.quest,
            student=self.student,
            submitted=True
        )

        # Attempt to create a third attempt
        data = {
            'quest_id': self.quest.id,
            'student_id': self.student.id
        }
        serializer = UserQuestAttemptSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('non_field_errors', serializer.errors)
        self.assertEqual(
            serializer.errors['non_field_errors'][0],
            f"Maximum number of attempts ({self.quest.max_attempts}) reached for this quest."
        )

    def test_update_user_quest_attempt_success(self):
        """
        Test that the serializer successfully updates a UserQuestAttempt instance.
        """
        # Create enrollment
        UserCourseGroupEnrollment.objects.create(
            student=self.student,
            course_group=self.course_group
        )
        # Create an initial attempt
        attempt = UserQuestAttempt.objects.create(
            quest=self.quest,
            student=self.student,
            submitted=False
        )
        data = {
            'quest_id': self.quest.id,
            'student_id': self.student.id,
            'submitted': True,
            'total_score_achieved': 10.0
        }
        serializer = UserQuestAttemptSerializer(instance=attempt, data=data, partial=True)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        updated_attempt = serializer.save()

        # Assertions
        self.assertTrue(updated_attempt.submitted)
        self.assertEqual(updated_attempt.total_score_achieved, 10.0)


class UserAnswerAttemptSerializerTest(TestCase):
    def setUp(self):
        self.student = EduquestUserFactory()
        self.quest = QuestFactory()
        self.user_course_group_enrollment = UserCourseGroupEnrollmentFactory(student=self.student, course_group=self.quest.course_group)
        self.user_quest_attempt = UserQuestAttemptFactory(student=self.student, quest=self.quest)
        self.question = QuestionFactory(quest=self.quest)
        self.answer_correct = AnswerFactory(question=self.question, is_correct=True)
        self.answer_incorrect = AnswerFactory(question=self.question, is_correct=False)

    def test_serializer_create_valid_data(self):
        """
        Test that the UserAnswerAttemptSerializer creates a UserAnswerAttempt instance with valid data.
        """
        data = {
            'user_quest_attempt_id': self.user_quest_attempt.id,
            'question_id': self.question.id,
            'answer_id': self.answer_correct.id,
            'is_selected': True,
            'score_achieved': 5
        }
        serializer = UserAnswerAttemptSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        user_answer_attempt = serializer.save()
        self.assertEqual(user_answer_attempt.user_quest_attempt, self.user_quest_attempt)
        self.assertEqual(user_answer_attempt.question, self.question)
        self.assertEqual(user_answer_attempt.answer, self.answer_correct)
        self.assertTrue(user_answer_attempt.is_selected)
        self.assertEqual(user_answer_attempt.score_achieved, 5)

    def test_serializer_read(self):
        """
        Test that the UserAnswerAttemptSerializer returns the correct serialized data.
        """
        user_answer_attempt = UserAnswerAttemptFactory(
            user_quest_attempt=self.user_quest_attempt,
            question=self.question,
            answer=self.answer_correct,
            is_selected=True,
            score_achieved=5
        )
        serializer = UserAnswerAttemptSerializer(user_answer_attempt)
        data = serializer.data
        self.assertEqual(data['user_quest_attempt_id'], self.user_quest_attempt.id)
        self.assertEqual(data['question']['id'], self.question.id)
        self.assertEqual(data['question']['answers'][0]['id'], self.answer_correct.id)
        self.assertTrue(data['is_selected'])
        self.assertEqual(data['score_achieved'], 5)

    def test_serializer_update_is_selected(self):
        """
        Test that the UserAnswerAttemptSerializer updates the 'is_selected' field correctly.
        """
        user_answer_attempt = UserAnswerAttemptFactory(
            user_quest_attempt=self.user_quest_attempt,
            question=self.question,
            answer=self.answer_incorrect,
            is_selected=False,
            score_achieved=0
        )
        data = {
            'is_selected': True,
            'score_achieved': 3
        }
        serializer = UserAnswerAttemptSerializer(instance=user_answer_attempt, data=data, partial=True)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        updated_answer_attempt = serializer.save()
        self.assertTrue(updated_answer_attempt.is_selected)
        self.assertEqual(updated_answer_attempt.score_achieved, 3)


class BadgeSerializerTest(TestCase):
    def setUp(self):
        self.image = ImageFactory()

    def test_badge_serializer_create(self):
        """
        Test creating a Badge with the serializer.
        """
        data = {
            'name': 'Test Badge',
            'description': 'A test badge',
            'type': 'Course Type',
            'condition': 'Complete all courses',
            'image_id': self.image.id
        }
        serializer = BadgeSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        badge = serializer.save()
        self.assertEqual(badge.name, 'Test Badge')
        self.assertEqual(badge.image, self.image)

    def test_badge_serializer_read(self):
        """
        Test reading a Badge instance with the serializer.
        """
        badge = BadgeFactory(image=self.image)
        serializer = BadgeSerializer(badge)
        data = serializer.data
        self.assertEqual(data['name'], badge.name)
        self.assertEqual(data['image']['id'], self.image.id)

    def test_badge_serializer_validation(self):
        """
        Test validation when no image is provided.
        """
        data = {
            'name': 'Test Badge',
            'description': 'A test badge',
            'type': 'Course Type',
            'condition': 'Complete all courses',
        }
        serializer = BadgeSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('image_id', serializer.errors)


class UserCourseBadgeSerializerTest(TestCase):
    def setUp(self):
        self.badge = BadgeFactory()
        self.enrollment = UserCourseGroupEnrollmentFactory()

    def test_user_course_badge_serializer_create(self):
        """
        Test creating a UserCourseBadge with the serializer.
        """
        data = {
            'badge_id': self.badge.id,
            'user_course_group_enrollment_id': self.enrollment.id,
        }
        serializer = UserCourseBadgeSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        user_course_badge = serializer.save()
        self.assertEqual(user_course_badge.badge, self.badge)
        self.assertEqual(user_course_badge.user_course_group_enrollment, self.enrollment)

    def test_user_course_badge_serializer_read(self):
        """
        Test reading a UserCourseBadge instance with the serializer.
        """
        user_course_badge = UserCourseBadgeFactory(badge=self.badge, user_course_group_enrollment=self.enrollment)
        serializer = UserCourseBadgeSerializer(user_course_badge)
        data = serializer.data
        self.assertEqual(data['badge']['id'], self.badge.id)
        self.assertEqual(data['user_course_group_enrollment']['id'], self.enrollment.id)

    def test_user_course_badge_serializer_update(self):
        """
        Test updating a UserCourseBadge instance with the serializer.
        """
        user_course_badge = UserCourseBadgeFactory(badge=self.badge, user_course_group_enrollment=self.enrollment)
        new_badge = BadgeFactory()
        data = {
            'badge_id': new_badge.id
        }
        serializer = UserCourseBadgeSerializer(instance=user_course_badge, data=data, partial=True)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        updated_badge = serializer.save()
        self.assertEqual(updated_badge.badge, new_badge)


class UserQuestBadgeSerializerTest(TestCase):
    def setUp(self):
        self.badge = BadgeFactory()
        self.quest_attempt = UserQuestAttemptFactory()

    def test_user_quest_badge_serializer_create(self):
        """
        Test creating a UserQuestBadge with the serializer.
        """
        data = {
            'badge_id': self.badge.id,
            'user_quest_attempt_id': self.quest_attempt.id,
        }
        serializer = UserQuestBadgeSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        user_quest_badge = serializer.save()
        self.assertEqual(user_quest_badge.badge, self.badge)
        self.assertEqual(user_quest_badge.user_quest_attempt, self.quest_attempt)

    def test_user_quest_badge_serializer_read(self):
        """
        Test reading a UserQuestBadge instance with the serializer.
        """
        user_quest_badge = UserQuestBadgeFactory(badge=self.badge, user_quest_attempt=self.quest_attempt)
        serializer = UserQuestBadgeSerializer(user_quest_badge)
        data = serializer.data
        self.assertEqual(data['badge']['id'], self.badge.id)
        self.assertEqual(data['user_quest_attempt']['id'], self.quest_attempt.id)

    def test_user_quest_badge_serializer_update(self):
        """
        Test updating a UserQuestBadge instance with the serializer.
        """
        user_quest_badge = UserQuestBadgeFactory(badge=self.badge, user_quest_attempt=self.quest_attempt)
        new_badge = BadgeFactory()
        data = {
            'badge_id': new_badge.id
        }
        serializer = UserQuestBadgeSerializer(instance=user_quest_badge, data=data, partial=True)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        updated_badge = serializer.save()
        self.assertEqual(updated_badge.badge, new_badge)

