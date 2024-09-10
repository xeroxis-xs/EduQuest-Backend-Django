import os
from dotenv import load_dotenv
from azure.storage.blob import BlobServiceClient
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from ...models import (
    EduquestUser,
    Course,
    Image,
    AcademicYear,
    Term,
    Badge,
    Document,
)
from .template import *


User = get_user_model()
load_dotenv()

class Command(BaseCommand):
    help = 'Populate the database with random data'

    def handle(self, *args, **kwargs):
        self.clear_db()
        self.create_images()
        self.create_badges()
        self.create_academic_years_terms()
        self.create_courses()


    def clear_db(self):
        eduquestUsers = EduquestUser.objects.filter(id__gt=1)
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

    def delete_all_documents(self):
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
        for course_item in course_list:
            course = Course.objects.create(
                name=course_item["name"],
                description=course_item["description"],
                code=course_item["code"],
                term=term,
                type='System-enroll',
                status='Active',
                group=course_item["group"],
                image=Image.objects.get(name=course_item["name"])
            )
            print(f"Created course: {course.name}")

