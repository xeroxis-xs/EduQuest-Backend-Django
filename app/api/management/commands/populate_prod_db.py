import os
from dotenv import load_dotenv
from azure.storage.blob import BlobServiceClient
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from ...models import (
    EduquestUser,
    Course,
    CourseGroup,
    Image,
    AcademicYear,
    Term,
    Badge,
    Document, Quest, UserCourseGroupEnrollment,
)
from .template import *
from faker import Faker
import random



User = get_user_model()
fake = Faker()
load_dotenv()

class Command(BaseCommand):
    help = 'Populate the database with random data'
    instructor = None

    def handle(self, *args, **kwargs):
        self.clear_db()
        self.instructor = self.create_staff()
        self.create_images()
        self.create_badges()
        self.create_academic_years_terms()
        self.create_courses()
        self.create_course_groups()
        self.create_fake_data()


    def clear_db(self):
        eduquestUsers = EduquestUser.objects.exclude(email__in=[
            'CHINANN.ONG@STAFF.MAIN.NTU.EDU.SG',
            'C210101@E.NTU.EDU.SG'
        ])
        eduquestUsers.delete()
        Image.objects.all().delete()
        AcademicYear.objects.all().delete()
        Badge.objects.all().delete()

        confirm = input("Do you want to delete all the uploaded documents in Azure Storage? (y/n): ")
        if confirm.lower() == 'y':
            self.delete_all_documents()
            # Document.objects.all().delete()
            print("Deleted all Document objects")
        else:
            print("Skipped deleting Document objects")

        print("Cleared all tables")

    def create_staff(self):
        instructor = EduquestUser.objects.get_or_create(
            email='CHINANN.ONG@STAFF.MAIN.NTU.EDU.SG',
            username='Ong Chin Ann',
            first_name='Chin Ann',
            last_name='Ong',
            nickname='Ong Chin Ann',
            is_active=True,
            is_staff=True,
            is_superuser=True
        )
        return instructor

    def delete_all_documents(self):
        # Delete all Document objects
        Document.objects.all().delete()

        # Initialize the BlobServiceClient
        blob_service_client = BlobServiceClient.from_connection_string(os.environ.get('AZURE_STORAGE_ACCOUNT_CONNECTION_STRING'))
        container_name = os.environ.get('AZURE_CONTAINER')

        # List all blobs in the container
        container_client = blob_service_client.get_container_client(container_name)
        blobs = container_client.list_blobs()

        # Delete each blob
        for blob in blobs:
            blob_client = container_client.get_blob_client(blob)
            blob_client.delete_blob()
            print(f"Deleted blob: {blob.name}")

    def create_images(self):
        for image_item in image_list:
            Image.objects.create(
                name=image_item["name"],
                filename=image_item["filename"]
            )
            print(f"Created image: {image_item['name']}")

    def create_badges(self):
        for badge in badge_list:
            Badge.objects.create(
                name=badge["name"],
                description=badge["description"],
                type=badge["type"],
                condition=badge["condition"],
                image=Image.objects.get(filename=badge["image"])
            )

    def create_academic_years_terms(self):
        # Create a private year and term for the private course
        private_academic_year = AcademicYear.objects.create(
            start_year=0,
            end_year=0
        )
        Term.objects.create(
            academic_year=private_academic_year,
            name="Private Term",
            start_date=None,
            end_date=None
        )

        # Create normal academic years and their terms
        for year in year_list:
            academic_year = AcademicYear.objects.create(
                start_year=year["start_year"],
                end_year=year["end_year"]
            )
            for term_item in term_list:
                Term.objects.create(
                    academic_year=academic_year,
                    name=term_item["name"],
                    start_date=term_item["start_date"],
                    end_date=term_item["end_date"]
                )
                print(f"Created academic year: {academic_year.start_year}-{academic_year.end_year}")

    def create_courses(self):
        # Get semester 1
        term = Term.objects.get(name="Semester 1")
        coordinator = EduquestUser.objects.get(username="admin")
        for course_item in course_list:
            course = Course.objects.create(
                name=course_item["name"],
                description=course_item["description"],
                code=course_item["code"],
                term=term,
                type='System-enroll',
                status='Active',
                image=Image.objects.get(name=course_item["name"])
            )
            course.coordinators.set([coordinator])
            print(f"Created course: {course.name}")

    def create_course_groups(self):
        # Get all courses
        course_list = Course.objects.all()
        for course in course_list:
            for course_group_group in course_group_list:
                if course.code == course_group_group["course_code"]:
                    CourseGroup.objects.create(
                        name=course_group_group["name"],
                        session_day=course_group_group["session_day"],
                        session_time=course_group_group["session_time"],
                        instructor=self.instructor,
                        course=course  # Ensure the course is set
                    )
                    print(f"Created course group: {course_group_group['name']}")


    def create_fake_data(self):
        confirm = input("Do you want to use faker to populate the rest of the database with fake data? (y/n): ")
        if confirm.lower() == 'y':
            print("Creating fake data...")
            self.create_fake_students()
            self.create_fake_quests()
            print("Finished creating all fake data")

    def create_fake_students(self):
        for _ in range(6):
            name = fake.name().upper()
            user = EduquestUser.objects.create(
                username=f"#{name}#",
                email=f"{fake.user_name().upper()}@e.ntu.edu.sg",
                password='password',
                nickname=name,
                is_active=True,
                is_staff=False
            )
        print(f"Finished creating all fake students")

    def create_fake_quests(self):
        # Get all course groups
        course_group_list = CourseGroup.objects.all()
        image = Image.objects.get(name="Eduquest MCQ Quest")
        for course_group in course_group_list:
            for i in range(random.randint(0, 2)):
                Quest.objects.create(
                    course_group=course_group,
                    name=f"Quest {i+1}",
                    description=fake.text(),
                    type='Eduquest MCQ',
                    status='Active',
                    organiser=self.instructor,
                    image=image,
                )
            print(f"Finished creating all fake quests for course group: {course_group.name}")

    # def create_fake_user_course_group_enrollments(self):
    #     # Get all students
    #     student_list = EduquestUser.objects.filter(is_superuser=False)
    #     # Get all course groups
    #     course_group_list = CourseGroup.objects.all()
    #     for student in student_list:
    #         for course_group in course_group_list:
    #             if random.choice([True, False]):
    #                 enrollment, created = UserCourseGroupEnrollment.objects.get_or_create(
    #                     course_group=course_group
    #                 )
    #                 enrollment.students.add(student)
    #                 print(f"Enrolled student: {student.username} into course group: {course_group.name}")
