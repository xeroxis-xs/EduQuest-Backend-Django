from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from ...models import (
    EduquestUser,
    Image,
    AcademicYear,
    Term,
    Badge,
)
from .template import *

User = get_user_model()


class Command(BaseCommand):
    help = 'Populate the database with random data'

    def handle(self, *args, **kwargs):
        self.clear_db()
        self.create_images()
        self.create_badges()
        self.create_academic_years_terms()


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

            print(f"Created academic year: {academic_year.start_year}-{academic_year.end_year}")
