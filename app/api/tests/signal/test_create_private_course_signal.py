from django.test import TestCase
from django.contrib.auth import get_user_model
from ...models import Course, UserCourse, Image

EduquestUser = get_user_model()

class CreatePrivateCourseSignalTest(TestCase):

    @classmethod
    def setUp(cls):
        # Set up a default image for the private course, required by the signal
        cls.private_image = Image.objects.get(name="Private Course")

    def test_create_private_course_signal(self):
        """Test that a private course is created when a new user is created."""

        # Create a new user, which should trigger the signal
        user = EduquestUser.objects.create_user(
            username="newuser#456",
            password="password456",
            email="newuser@example.com"
        )

        # Check that the private course was created
        private_course = Course.objects.get(code=f"PRIVATE {user.id}")
        self.assertEqual(private_course.name, "Private Course")
        self.assertEqual(private_course.group, "Private")
        self.assertEqual(private_course.type, "Private")
        self.assertEqual(private_course.description, "This is a private Course created for you to generate Quests for your own usage. Only you can see this course.")
        self.assertEqual(private_course.status, "Active")
        self.assertEqual(private_course.image, self.private_image)

        # Check that the user is enrolled in the private course
        user_course = UserCourse.objects.get(user=user, course=private_course)
        self.assertEqual(user_course.user, user)
        self.assertEqual(user_course.course, private_course)

        # Verify that the academic year and term are correctly set
        private_year = private_course.term.academic_year
        self.assertEqual(private_year.start_year, 0)
        self.assertEqual(private_year.end_year, 0)

        private_term = private_course.term
        self.assertEqual(private_term.name, "Private Term")
        self.assertIsNone(private_term.start_date)
        self.assertIsNone(private_term.end_date)

