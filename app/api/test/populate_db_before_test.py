from django.test.runner import DiscoverRunner
from ..models import EduquestUser, Image, AcademicYear, Term, Course, CourseGroup


class PopulateDBBeforeTest(DiscoverRunner):

    def setup_databases(self, **kwargs):
        # Call the super method to create the test databases first
        result = super().setup_databases(**kwargs)

        # Check if the superuser already exists
        if not EduquestUser.objects.filter(username='admin').exists():
            self.superuser = EduquestUser.objects.create_superuser(
                username='admin',
                email='admin@example.com',
                password='password123'
            )
        else:
            self.superuser = EduquestUser.objects.get(username='admin')

        # Create other necessary objects for testing
        self.image = Image.objects.create(
            name="Test Image",
            filename="test_image.svg"
        )

        self.private_year = AcademicYear.objects.create(
            start_year=0,
            end_year=0
        )

        self.private_term = Term.objects.create(
            name="Private Term",
            academic_year=self.private_year,
        )

        self.private_course = Course.objects.create(
            name="Private Course",
            term=self.private_term,
            image=self.image,
            type="Private",
            status="Active",
            description="Private Course Description",
        )

        # Set the course coordinators
        self.private_course.coordinators.set([self.superuser])

        # Create a course group
        self.private_course_group = CourseGroup.objects.create(
            name="Private Course Group",
            instructor=self.superuser,
            course=self.private_course,
        )

        return result

    def teardown_databases(self, old_config, **kwargs):
        # Optionally, clean up any additional resources if necessary
        return super().teardown_databases(old_config, **kwargs)
