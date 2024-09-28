from datetime import timedelta
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from django.test import TestCase
from django.contrib.auth import get_user_model
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

User = get_user_model()


class EduquestUserModelTest(TestCase):

    def setUp(self):
        # Get the superuser
        self.superuser = EduquestUser.objects.get(username='admin')
        self.private_course_group = CourseGroup.objects.get(name='Private Course Group')

    @patch('api.models.split_full_name')
    def test_user_creation(self, mock_split_full_name):
        """
        Test that a user is created successfully and enrolled in Private Course Group.
        """
        mock_split_full_name.return_value = ('John', 'Doe')

        user = EduquestUser.objects.create_user(
            username='#John Doe#',
            email='john@example.com',
        )
        # Check if nickname is set correctly
        self.assertEqual(user.nickname, 'John Doe')
        # Check if first_name and last_name are set via split_full_name
        mock_split_full_name.assert_called_with('John Doe')
        self.assertEqual(user.first_name, 'John')
        self.assertEqual(user.last_name, 'Doe')
        # Check if user is enrolled in Private Course Group
        enrollment = UserCourseGroupEnrollment.objects.get(
            student=user,
            course_group=self.private_course_group
        )
        self.assertIsNotNone(enrollment)

    def test_str_method(self):
        """
        Test that the __str__ method of the EduquestUser model returns the expected string
        """
        user = EduquestUser.objects.create_user(
            username='#John Doe#',
            email='john@example.com',
        )
        self.assertEqual(str(user), f"{user.id} - {user.username}")

    def test_save_existing_user_does_not_enroll_again(self):
        """
        Test that saving an existing user does not create additional enrollments
        """
        user = User.objects.create_user(
            username='#Existing User#',
            email='existing@example.com',
        )
        # Count enrollments
        initial_enrollments = UserCourseGroupEnrollment.objects.filter(student=user).count()
        self.assertEqual(initial_enrollments, 1)
        # Save the user again
        user.save()
        # Ensure no additional enrollments are created
        enrollments_after_save = UserCourseGroupEnrollment.objects.filter(student=user).count()
        self.assertEqual(enrollments_after_save, 1)


class ImageModelTest(TestCase):
    def test_str_method(self):
        """
        Test that the __str__ method of the Image model returns the expected string
        """
        image = Image.objects.create(
            name="Test Image",
            filename="test.jpg"
        )
        self.assertEqual(str(image), "Test Image")


class AcademicYearModelTest(TestCase):
    def test_str_method(self):
        """
        Test that the __str__ method of the AcademicYear model returns the expected string
        """
        ay = AcademicYear.objects.create(start_year=2021, end_year=2022)
        self.assertEqual(str(ay), "AY2021-2022")


class TermModelTest(TestCase):
    def setUp(self):
        self.ay = AcademicYearFactory()

    def test_str_method(self):
        """
        Test that the __str__ method of the Term model returns the expected string
        """
        term = Term.objects.create(
            academic_year=self.ay,
            name="Term 1",
            start_date="2021-08-01",
            end_date="2021-12-15"
        )
        expected_str = f"{self.ay} - Term 1 (2021-08-01 to 2021-12-15)"
        self.assertEqual(str(term), expected_str)

    def test_foreign_key_constraint(self):
        """
        Test that a Term cannot be created without an Academic Year
        """
        with self.assertRaises(Exception):
            Term.objects.create(
                academic_year=None,  # Should raise an error since it's not nullable
                name="Term 2"
            )


class CourseModelTest(TestCase):

    def setUp(self):
        # Create necessary related objects
        self.image = ImageFactory()
        self.ay = AcademicYearFactory()
        self.term = TermFactory(academic_year=self.ay)
        self.coordinator1 = EduquestUserFactory()
        self.coordinator2 = EduquestUserFactory()
        self.course = CourseFactory(
            term=self.term,
            image=self.image
        )
        self.course.coordinators.set([self.coordinator1, self.coordinator2])

    def test_str_method(self):
        """
        Test that the __str__ method of the Course model returns the expected string
        """
        expected_str = f"Term {self.term.name} - {self.course.code}"
        self.assertEqual(str(self.course), expected_str)

    @patch('api.tasks.check_course_completion_and_award_completionist_badge.delay')
    def test_save_trigger_tasks_on_status_change_to_expired(self, mock_task):
        """
        Test that the task is triggered when the course status is changed to Expired
        """
        # Change status from Active to Expired
        self.course.status = "Expired"
        self.course.save()
        # Assert that the task was called with the course ID
        mock_task.assert_called_with(self.course.id)

    @patch('api.tasks.check_course_completion_and_award_completionist_badge.delay')
    def test_save_does_not_trigger_tasks_on_new_instance_with_expired_status(self, mock_task):
        """
        Test that the task is not triggered when a new course is created with status Expired
        """
        # Create a new course with status Expired
        course_new = Course.objects.create(
            term=self.term,
            name="Advanced Testing",
            code="CS2000",
            type="Private",
            description="An advanced course on testing methodologies.",
            status="Expired",
            image=self.image
        )
        course_new.coordinators.set([self.coordinator1])
        # Assert that the task was not called with the new course ID
        mock_task.assert_not_called()

    def test_total_students_enrolled(self):
        """
        Test that the total_students_enrolled method returns the correct number of students enrolled
        """
        # Create course groups
        group1 = CourseGroup.objects.create(
            course=self.course,
            name="Group A",
            instructor=self.coordinator1
        )
        group2 = CourseGroup.objects.create(
            course=self.course,
            name="Group B",
            instructor=self.coordinator2
        )
        # Enroll students
        student1 = User.objects.create_user(
            username='#Student One#',
            email='student1@example.com',
        )
        student2 = User.objects.create_user(
            username='#Student Two#',
            email='student2@example.com',
        )
        UserCourseGroupEnrollment.objects.create(
            student=student1,
            course_group=group1
        )
        UserCourseGroupEnrollment.objects.create(
            student=student2,
            course_group=group2
        )
        self.assertEqual(self.course.total_students_enrolled(), 2)


class CourseGroupModelTest(TestCase):

    def setUp(self):
        # Create necessary related objects
        self.course = CourseFactory()
        self.coordinator = EduquestUserFactory()
        self.group = CourseGroupFactory(
            course=self.course,
            instructor=self.coordinator
        )

    def test_str_method(self):
        """
        Test that the __str__ method of the CourseGroup model returns the expected string
        """
        expected_str = f"Group {self.group.name} from {self.course.code}"
        self.assertEqual(str(self.group), expected_str)

    def test_total_students_enrolled(self):
        """
        Test that the total_students_enrolled method returns the correct number of students enrolled
        """
        # Enroll students
        student1 = User.objects.create_user(
            username='#Student One#',
            email='student1@example.com',
        )
        student2 = User.objects.create_user(
            username='#Student Two#',
            email='student2@example.com',
        )
        UserCourseGroupEnrollment.objects.create(
            student=student1,
            course_group=self.group
        )
        UserCourseGroupEnrollment.objects.create(
            student=student2,
            course_group=self.group
        )
        self.assertEqual(self.group.total_students_enrolled(), 2)


class UserCourseGroupEnrollmentModelTest(TestCase):

    def setUp(self):
        # Create necessary related objects
        self.student = EduquestUserFactory()
        self.coordinator = EduquestUserFactory()
        self.course = CourseFactory()
        self.course.coordinators.set([self.coordinator])
        self.group = CourseGroupFactory(
            course=self.course,
            instructor=self.coordinator
        )

    def test_str_method(self):
        """
        Test that the __str__ method of the UserCourseGroupEnrollment model returns the expected string
        """
        enrollment = UserCourseGroupEnrollment.objects.create(
            student=self.student,
            course_group=self.group
        )
        expected_str = f"{self.student.username} enrolled in {self.group.course.code} - {self.group.name}"
        self.assertEqual(str(enrollment), expected_str)

    def test_enrolled_on_auto_set(self):
        """
        Test that the 'enrolled_on' field is automatically set to the current date and time
        """
        enrollment = UserCourseGroupEnrollment.objects.create(
            student=self.student,
            course_group=self.group
        )
        self.assertIsNotNone(enrollment.enrolled_on)
        # Ensure 'completed_on' is None by default
        self.assertIsNone(enrollment.completed_on)

    def test_completed_on_optional(self):
        """
        Test that the 'completed_on' field can be set to None or a valid datetime
        """
        enrollment = UserCourseGroupEnrollment.objects.create(
            student=self.student,
            course_group=self.group
        )
        # Initially, completed_on is None
        self.assertIsNone(enrollment.completed_on)
        # Update completed_on
        completion_time = timezone.now()
        enrollment.completed_on = completion_time
        enrollment.save()
        enrollment_refreshed = UserCourseGroupEnrollment.objects.get(pk=enrollment.pk)
        self.assertEqual(enrollment_refreshed.completed_on, completion_time)


class QuestModelTest(TestCase):

    def setUp(self):
        # Create necessary related objects
        self.course = CourseFactory()
        self.group = CourseGroupFactory(course=self.course)
        self.image = ImageFactory()
        self.organiser = EduquestUserFactory()
        self.quest = QuestFactory(course_group=self.group, image=self.image)

    def test_str_method(self):
        """
        Test that the __str__ method of the Quest model returns the expected string
        """
        expected_str = f"{self.quest.name} from Group {self.group.course.name} {self.group.course.code}"
        self.assertEqual(str(self.quest), expected_str)

    def test_total_max_score_no_questions(self):
        """
        Test that the total_max_score method returns 0 when there are no questions
        """
        self.assertEqual(self.quest.total_max_score(), 0)

    def test_total_max_score_with_questions(self):
        """
        Test that the total_max_score method returns the correct total score when questions are present
        """
        # Create questions
        Question.objects.create(
            quest=self.quest,
            text="What is Python?",
            number=1,
            max_score=2
        )
        Question.objects.create(
            quest=self.quest,
            text="Explain unit testing.",
            number=2,
            max_score=3
        )
        self.assertEqual(self.quest.total_max_score(), 5)

    def test_total_questions(self):
        """
        Test that the total_questions method returns the correct number of questions
        """
        self.assertEqual(self.quest.total_questions(), 0)
        Question.objects.create(
            quest=self.quest,
            text="What is Python?",
            number=1,
            max_score=2
        )
        self.assertEqual(self.quest.total_questions(), 1)

    @patch('api.tasks.award_speedster_badge.delay')
    @patch('api.tasks.award_expert_badge.delay')
    def test_save_trigger_tasks_on_status_change_to_expired(self, mock_expert_badge, mock_speedster_badge):
        """
        Test that the tasks are triggered when the quest status is changed to Expired
        """
        # Change status from Active to Expired
        self.quest.status = "Expired"
        self.quest.save()
        # Assert that both tasks were called with the quest ID
        mock_expert_badge.assert_called_with(self.quest.id)
        mock_speedster_badge.assert_called_with(self.quest.id)
        # Check if expiration_date is set to now
        self.quest.refresh_from_db()
        self.assertIsNotNone(self.quest.expiration_date)

    @patch('api.tasks.award_speedster_badge.delay')
    @patch('api.tasks.award_expert_badge.delay')
    def test_save_trigger_tasks_on_new_instance_with_expired_status(self, mock_expert_badge, mock_speedster_badge):
        """
        Test that the tasks are not triggered when a new quest is created with status Expired
        """
        # Create a new quest with status Expired
        quest_new = Quest.objects.create(
            course_group=self.group,
            name="Quest 2",
            description="Second quest description.",
            type="EduQuest MCQ",
            status="Expired",
            tutorial_date=timezone.now(),
            expiration_date=timezone.now() + timedelta(days=7),
            max_attempts=2,
            organiser=self.organiser,
            image=self.image
        )
        # Assert that tasks were not called for a new quest with status Expired
        mock_expert_badge.assert_not_called()
        mock_speedster_badge.assert_not_called()
        # Check if expiration_date is set to now
        quest_new.refresh_from_db()
        self.assertIsNotNone(quest_new.expiration_date)


class QuestionModelTest(TestCase):

    def setUp(self):
        # Create necessary related objects
        self.quest = QuestFactory()
        self.question = QuestionFactory(quest=self.quest)

    def test_str_method(self):
        """
        Test that the __str__ method of the Question model returns the expected
        """
        expected_str = f"{self.question.number} from Quest ID {self.quest.id}"
        self.assertEqual(str(self.question), expected_str)


class AnswerModelTest(TestCase):

    def setUp(self):
        # Create necessary related objects
        self.question = QuestionFactory()
        self.answer = AnswerFactory(question=self.question)

    def test_str_method(self):
        """
        Test that the __str__ method of the Answer model returns the expected string
        """
        expected_str = f"{self.answer.text} for Question ID {self.question.id}"
        self.assertEqual(str(self.answer), expected_str)


class UserQuestAttemptModelTest(TestCase):

    def setUp(self):
        # Create necessary related objects
        self.student = EduquestUserFactory()
        self.group = CourseGroupFactory()
        self.quest = QuestFactory(course_group=self.group)
        self.attempt = UserQuestAttemptFactory(quest=self.quest, student=self.student)

    def test_str_method(self):
        """
        Test that the __str__ method of the UserQuestAttempt model returns the expected string
        """
        expected_str = f"{self.attempt.student.username} attempted {self.attempt.quest.name}"
        self.assertEqual(str(self.attempt), expected_str)

    def test_calculate_total_score_achieved_no_answers(self):
        """
        Test that the calculate_total_score_achieved method returns 0 when there are no answers
        """
        self.assertEqual(self.attempt.calculate_total_score_achieved(), 0)

    def test_calculate_total_score_achieved_with_answers(self):
        """
        Test that the calculate_total_score_achieved method returns the correct total score achieved
        """
        # Create questions and answers
        question1 = Question.objects.create(
            quest=self.quest,
            text="What is Python?",
            number=1,
            max_score=2
        )
        answer1_q1 = Answer.objects.create(
            question=question1,
            text="A programming language.",
            is_correct=True
        )
        answer2_q1 = Answer.objects.create(
            question=question1,
            text="A snake.",
            is_correct=False
        )
        # User selects correct answer
        UserAnswerAttempt.objects.create(
            user_quest_attempt=self.attempt,
            question=question1,
            answer=answer1_q1,
            is_selected=True
        )
        # User selects incorrect answer
        UserAnswerAttempt.objects.create(
            user_quest_attempt=self.attempt,
            question=question1,
            answer=answer2_q1,
            is_selected=True
        )
        total_score = self.attempt.calculate_total_score_achieved()
        # max_score = 2, 2 answers, weight_per_option = 1
        # Correct selection: 1, Incorrect: 0
        self.assertEqual(total_score, 1)
        # Check if score_achieved fields are set correctly
        answer_attempts = self.attempt.answer_attempts.all()
        for ua in answer_attempts:
            if ua.answer.is_correct:
                self.assertEqual(ua.score_achieved, 1)
            else:
                self.assertEqual(ua.score_achieved, 0)

    def test_time_taken_property(self):
        """
        Test that the time_taken property returns the correct time taken in milliseconds
        """
        self.attempt.first_attempted_date = timezone.now() - timedelta(minutes=10)
        self.attempt.last_attempted_date = timezone.now()
        self.attempt.save()
        # Time taken should be approximately 600000 milliseconds (10 minutes)
        self.assertAlmostEqual(self.attempt.time_taken, 600000, delta=1000)

    @patch('api.tasks.award_first_attempt_badge.delay')
    @patch('api.tasks.calculate_score_and_issue_points.delay')
    def test_save_trigger_tasks_on_submission(self, mock_score_task, mock_badge_task):
        """
        Test that the tasks are triggered when the attempt is submitted
        """
        # Submit the attempt
        self.attempt.submitted = True
        self.attempt.save()
        # Assert that both tasks were called with the attempt ID
        mock_score_task.assert_called_with(self.attempt.id)
        mock_badge_task.assert_called_with(self.attempt.id)

    @patch('api.tasks.award_first_attempt_badge.delay')
    @patch('api.tasks.calculate_score_and_issue_points.delay')
    def test_save_trigger_tasks_on_new_submission(self, mock_score_task, mock_badge_task):
        """
        Test that the tasks are not triggered when a new attempt is created with submitted=True
        """
        # Create a new attempt with submitted=True
        attempt_new = UserQuestAttempt.objects.create(
            student=self.student,
            quest=self.quest,
            submitted=True
        )
        # Assert that tasks were not called for a new attempt with submitted=True
        mock_score_task.assert_not_called()
        mock_badge_task.assert_not_called()


class UserAnswerAttemptModelTest(TestCase):

    def setUp(self):
        # Create necessary related objects
        self.quest = QuestFactory()
        self.student = EduquestUserFactory()
        self.question = QuestionFactory(quest=self.quest, max_score=2)
        self.answer1 = AnswerFactory(question=self.question, is_correct=True)
        self.answer2 = AnswerFactory(question=self.question, is_correct=False)
        self.attempt = UserQuestAttemptFactory(quest=self.quest, student=self.student)
        self.user_answer_attempt = UserAnswerAttemptFactory(
            user_quest_attempt=self.attempt,
            question=self.question,
            answer=self.answer1,
            is_selected=True
        )

    def test_str_method(self):
        """
        Test that the __str__ method of the UserAnswerAttempt model returns the expected string
        """
        expected_str = f"{self.attempt.student.username} selected {self.answer1.text} for question {self.question.number}"
        self.assertEqual(str(self.user_answer_attempt), expected_str)

    def test_score_achieved_default(self):
        """
        Test that the score_achieved field is set to 0 by default
        """
        self.assertEqual(self.user_answer_attempt.score_achieved, 0)

    def test_score_achieved_after_calculation(self):
        """
        Test that the score_achieved field is set correctly after calculation
        """
        # Simulate score calculation
        self.attempt.calculate_total_score_achieved()
        self.user_answer_attempt.refresh_from_db()
        # Since the answer is correct and weight_per_option is 1 (2/2)
        self.assertEqual(self.user_answer_attempt.score_achieved, 1)

    def test_is_selected_default(self):
        """
        Test that the is_selected field is set to False by default
        """
        self.assertTrue(self.user_answer_attempt.is_selected)


class BadgeModelTest(TestCase):
    def setUp(self):
        self.image = ImageFactory()
        self.badge = BadgeFactory(name="Completionist Badge", image=self.image)

    def test_str_method(self):
        """
        Test that the __str__ method of the Badge model returns the expected string
        """
        self.assertEqual(str(self.badge), "Completionist Badge")

    def test_badge_creation(self):
        """
        Test that the badge is created successfully with the correct attributes
        """
        badge = Badge.objects.create(
            name="Completionist Badge",
            description="Awarded for completing all courses.",
            type="Course Type",
            condition="Complete all courses",
            image=self.image
        )
        self.assertEqual(badge.name, "Completionist Badge")
        self.assertEqual(badge.description, "Awarded for completing all courses.")
        self.assertEqual(badge.type, "Course Type")
        self.assertEqual(badge.condition, "Complete all courses")
        self.assertEqual(badge.image, self.image)


class UserCourseBadgeModelTest(TestCase):
    def setUp(self):

        self.student = EduquestUserFactory()
        self.course = CourseFactory()
        self.group = CourseGroupFactory(course=self.course)
        self.enrollment = UserCourseGroupEnrollmentFactory(student=self.student, course_group=self.group)
        self.badge = BadgeFactory()
        self.user_course_badge = UserCourseBadgeFactory(
            badge=self.badge,
            user_course_group_enrollment=self.enrollment
        )

    def test_str_method(self):
        """
        Test that the __str__ method of the UserCourseBadge model returns the expected string
        """
        expected_str = f"{self.student.username} earned {self.badge.name} from Course {self.course.code} - {self.group.name}"
        self.assertEqual(str(self.user_course_badge), expected_str)

    def test_user_course_badge_creation(self):
        """
        Test that the UserCourseBadge is created successfully with the correct attributes
        """
        self.assertEqual(self.user_course_badge.badge, self.badge)
        self.assertEqual(self.user_course_badge.user_course_group_enrollment, self.enrollment)
        self.assertIsNotNone(self.user_course_badge.awarded_date)


class UserQuestBadgeModelTest(TestCase):
    def setUp(self):
        self.quest = QuestFactory()
        self.student = EduquestUserFactory()
        self.attempt = UserQuestAttemptFactory(student=self.student, quest=self.quest)
        self.badge = BadgeFactory()
        self.user_quest_badge = UserQuestBadgeFactory(
            badge=self.badge,
            user_quest_attempt=self.attempt,
        )

    def test_str_method(self):
        """
        Test that the __str__ method of the UserQuestBadge model returns the expected string
        """
        expected_str = f"{self.student.username} earned {self.badge.name} from Quest {self.quest.name}"
        self.assertEqual(str(self.user_quest_badge), expected_str)

    def test_user_quest_badge_creation(self):
        """
        Test that the UserQuestBadge is created successfully with the correct attributes
        """
        self.assertEqual(self.user_quest_badge.badge, self.badge)
        self.assertEqual(self.user_quest_badge.user_quest_attempt, self.attempt)
        self.assertIsNotNone(self.user_quest_badge.awarded_date)


class DocumentModelTest(TestCase):

    def setUp(self):
        # Create test users
        self.uploader_one = EduquestUserFactory()
        self.uploader_two = EduquestUserFactory()

    def test_document_save(self):
        # Create a test file
        test_file = SimpleUploadedFile("testfile.txt", b"file_content", content_type="text/plain")
        document = Document(name="Test Document", file=test_file, size=10.0, uploaded_by=self.uploader_one)
        document.save()

        # Check if the document was saved correctly
        self.assertEqual(Document.objects.count(), 1)
        self.assertEqual(Document.objects.first().name, "Test Document")

    # @patch('api.models.AzureStorage')  # Ensure this path matches where AzureStorage is used in your models
    # def test_document_save_with_existing_file(self, mock_azure_storage):
    #     """
    #     Test that the save method renames the file if it already exists.
    #     """
    #     # Create a mock storage instance
    #     mock_storage = MagicMock()
    #     # Simulate that the original file exists, and the renamed file does not
    #     mock_storage.exists.side_effect = [True, False]
    #     mock_azure_storage.return_value = mock_storage
    #
    #     # Create a Document instance with a file
    #     document = Document(
    #         name="Test Document",
    #         file=SimpleUploadedFile('test_document.pdf', b'file_content'),  # Properly assign a file
    #         size=1.5,
    #         uploaded_by=self.uploader_one
    #     )
    #
    #     # Mock os.path.splitext to control the splitting of the filename
    #     with patch('os.path.splitext', return_value=('test_document', '.pdf')):
    #         # Save the document; should attempt to rename
    #         document.save()
    #
    #         # Assert that 'exists' was called with the original filename
    #         mock_storage.exists.assert_any_call('test_document.pdf')
    #         # Assert that 'exists' was called with the new filename after renaming
    #         mock_storage.exists.assert_any_call('test_document_1.pdf')
    #
    #         # The final file name should have '_1' appended
    #         expected_new_name = 'test_document_1.pdf'
    #         self.assertEqual(document.file.name, expected_new_name)
    #
    # @patch('api.models.AzureStorage')
    # def test_save_unique_filename_no_conflict(self, mock_azure_storage):
    #     """
    #     Test that the save method does not rename the file if it does not exist.
    #     """
    #     # Create a mock storage instance
    #     mock_storage = MagicMock()
    #     # Simulate that the file does not exist
    #     mock_storage.exists.return_value = False
    #     mock_azure_storage.return_value = mock_storage
    #
    #     # Create a Document instance with a file
    #     document = Document(
    #         name="Another Test Document",
    #         file=SimpleUploadedFile('another_test_document.pdf', b'file_content'),
    #         size=2.0,
    #         uploaded_by=self.uploader_two
    #     )
    #
    #     # Mock os.path.splitext just in case
    #     with patch('os.path.splitext', return_value=('another_test_document', '.pdf')):
    #         # Save the document; should not attempt to rename
    #         document.save()
    #
    #         # Assert that 'exists' was called once with the original filename
    #         mock_storage.exists.assert_called_once_with('another_test_document.pdf')
    #
    #         # The final file name should remain unchanged
    #         self.assertEqual(document.file.name, 'another_test_document.pdf')
    #
    #         # Verify that no renaming was attempted by ensuring 'exists' wasn't called with a new filename
    #         # Since 'exists' is already mocked to return False, no further calls should be made
    #
    # @patch('api.models.AzureStorage')
    # def test_document_delete_when_file_exists(self, mock_azure_storage):
    #     """
    #     Test that the delete method removes the file from storage if it exists
    #     and deletes the document instance from the database.
    #     """
    #     # Create a mock storage instance
    #     mock_storage = MagicMock()
    #     mock_storage.exists.side_effect = [False, True]  # Simulate that the file exists
    #     mock_azure_storage.return_value = mock_storage
    #
    #     # Create a Document instance with a file
    #     document = Document.objects.create(
    #         name="Test Document",
    #         file=SimpleUploadedFile('test_document.pdf', b'file_content'),
    #         size=10.0,
    #         uploaded_by=self.uploader_one
    #     )
    #
    #     # Delete the document
    #     document.delete()
    #
    #     # Assert that the document was deleted from the database
    #     self.assertEqual(Document.objects.count(), 0)
    #
    #     # Assert that storage.exists was called with the correct file name
    #     mock_storage.exists.assert_called_once_with(document.file.name)
    #
    #     # Assert that storage.delete was called with the correct file name
    #     mock_storage.delete.assert_called_once_with(document.file.name)
    #
    # @patch('api.models.AzureStorage')
    # def test_document_delete_when_file_does_not_exist(self, mock_azure_storage):
    #     """
    #     Test that the delete method does not attempt to remove the file from storage
    #     if it does not exist and deletes the document instance from the database.
    #     """
    #     # Create a mock storage instance
    #     mock_storage = MagicMock()
    #     # Simulate that the file does not exist
    #     mock_storage.exists.return_value = False
    #     mock_azure_storage.return_value = mock_storage
    #
    #     # Create a Document instance with a file
    #     test_file = SimpleUploadedFile("nonexistentfile.txt", b"file_content", content_type="text/plain")
    #     document = Document.objects.create(
    #         name="Nonexistent File Document",
    #         file=test_file,
    #         size=5.0,
    #         uploaded_by=self.uploader_one
    #     )
    #
    #     # Delete the document
    #     document.delete()
    #
    #     # Assert that the document was deleted from the database
    #     self.assertEqual(Document.objects.count(), 0)
    #
    #     # Assert that storage.exists was called with the correct file name
    #     mock_storage.exists.assert_called_once_with(document.file.name)
    #
    #     # Assert that storage.delete was NOT called since the file does not exist
    #     mock_storage.delete.assert_not_called()
    #
    # @patch('api.models.AzureStorage')
    # def test_document_delete_without_file(self, mock_azure_storage):
    #     """
    #     Test that the delete method handles documents without a file gracefully.
    #     """
    #     # Create a mock storage instance (though it shouldn't be used)
    #     mock_storage = MagicMock()
    #     mock_azure_storage.return_value = mock_storage
    #
    #     # Create a Document instance without a file
    #     document = Document.objects.create(
    #         name="No File Document",
    #         size=0.0,
    #         uploaded_by=self.uploader_one
    #     )
    #
    #     # Delete the document
    #     document.delete()
    #
    #     # Assert that the document was deleted from the database
    #     self.assertEqual(Document.objects.count(), 0)
    #
    #     # Assert that storage.exists was NOT called since there is no file
    #     mock_storage.exists.assert_not_called()
    #
    #     # Assert that storage.delete was NOT called since there is no file
    #     mock_storage.delete.assert_not_called()


class BadgeAssociationTest(TestCase):
    def setUp(self):
        self.badge_course = Badge.objects.create(
            name="Completionist",
            description="Awarded for completing all courses.",
            type="Course Type",
            condition="Complete all courses"
        )
        self.badge_quest = Badge.objects.create(
            name="Speedster",
            description="Awarded for completing quests quickly.",
            type="Quest Type",
            condition="Complete quests within 10 minutes"
        )
        self.student = User.objects.create_user(
            username='#Student Three#',
            email='student3@example.com',
        )
        self.image = Image.objects.create(
            name="Badge Image",
            filename="badge_image.svg"
        )
        self.ay = AcademicYear.objects.create(start_year=2022, end_year=2023)
        self.term = Term.objects.create(
            academic_year=self.ay,
            name="Term 2",
            start_date="2022-01-10",
            end_date="2022-05-20"
        )
        self.course = Course.objects.create(
            term=self.term,
            name="Advanced Testing",
            code="CS2000",
            type="Private",
            description="An advanced course on testing methodologies.",
            status="Active",
            image=self.image
        )
        self.coordinator = User.objects.create_user(
            username='#Instructor Three#',
            email='instructor3@example.com',
            is_staff=True
        )
        self.course.coordinators.set([self.coordinator])
        self.group = CourseGroup.objects.create(
            course=self.course,
            name="Group C",
            instructor=self.coordinator
        )
        self.enrollment = UserCourseGroupEnrollment.objects.create(
            student=self.student,
            course_group=self.group
        )
        self.user_course_badge = UserCourseBadge.objects.create(
            badge=self.badge_course,
            user_course_group_enrollment=self.enrollment
        )
        self.quest = Quest.objects.create(
            course_group=self.group,
            name="Quest B",
            description="Second quest description.",
            type="EduQuest MCQ",
            status="Active",
            tutorial_date=timezone.now(),
            expiration_date=timezone.now() + timedelta(days=7),
            max_attempts=2,
            organiser=self.coordinator,
            image=self.image
        )
        self.attempt = UserQuestAttempt.objects.create(
            student=self.student,
            quest=self.quest,
            submitted=True
        )
        self.user_quest_badge = UserQuestBadge.objects.create(
            badge=self.badge_quest,
            user_quest_attempt=self.attempt
        )

    def test_user_course_badge_association(self):
        """
        Test that the UserCourseBadge is associated with the correct Badge and UserCourseGroupEnrollment
        """
        self.assertIn(self.user_course_badge, self.badge_course.awarded_to_course_completion.all())
        self.assertIn(self.user_course_badge, self.enrollment.earned_course_badges.all())

    def test_user_quest_badge_association(self):
        """
        Test that the UserQuestBadge is associated with the correct Badge and UserQuestAttempt
        """
        self.assertIn(self.user_quest_badge, self.badge_quest.awarded_to_quest_attempt.all())
        self.assertIn(self.user_quest_badge, self.attempt.earned_quest_badges.all())
