import os

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from unittest.mock import patch
from django.urls import reverse
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


class BaseViewTest(APITestCase):
    def setUp(self):
        # Create a staff user for authentication
        self.staff_user1 = EduquestUserFactory(is_staff=True)
        self.staff_user2 = EduquestUserFactory(is_staff=True)
        self.client = APIClient()
        self.client.force_authenticate(user=self.staff_user1)
        # Create some students
        self.student1 = EduquestUserFactory(username='#Student One#', email='student_one@example.com')
        self.student2 = EduquestUserFactory(username='#Student Two#', email='student_two@example.com')
        # Create some images
        self.image1 = ImageFactory(name='image 1', filename='image1.jpg')
        self.image2 = ImageFactory(name='image 2', filename='image2.jpg')
        # Create some academic years
        self.ay1 = AcademicYearFactory(start_year=2020, end_year=2021)
        self.ay2 = AcademicYearFactory(start_year=2021, end_year=2022)
        # Create some terms
        self.term1 = TermFactory(name='Term 1', academic_year=self.ay1)
        self.term2 = TermFactory(name='Term 2', academic_year=self.ay2)
        # Create courses
        self.course1 = CourseFactory(name='Course 1', code='CS101', type='System-enroll', image=self.image1, term=self.term1)
        self.course2 = CourseFactory(name='Course 2', code='CS102', type='Private', image=self.image2, term=self.term2)
        self.private_course = Course.objects.get(name='Private Course')
        # Create course groups and enrollments
        self.course_group1 = CourseGroupFactory(course=self.course1, instructor=self.staff_user1, name='Group 1')
        self.course_group2 = CourseGroupFactory(course=self.course1, instructor=self.staff_user2, name='Group 2')
        self.private_course_group = CourseGroup.objects.get(name='Private Course Group')
        self.enrollment1 = UserCourseGroupEnrollmentFactory(course_group=self.course_group1, student=self.student1)
        self.enrollment2 = UserCourseGroupEnrollmentFactory(course_group=self.course_group2, student=self.student2)
        # Create some quests
        self.quest1 = QuestFactory(name='Quest 1', course_group=self.course_group1, organiser=self.staff_user1, image=self.image1)
        self.quest2 = QuestFactory(name='Quest 2', course_group=self.course_group2, organiser=self.staff_user1, image=self.image2)
        self.quest3 = QuestFactory(name='Quest 3', course_group=self.course_group1, organiser=self.staff_user2, image=self.image1)
        self.private_quest = QuestFactory(name='Private Quest', course_group=self.private_course_group, organiser=self.student1, type='Private')
        # Create questions
        self.question1 = QuestionFactory(quest=self.quest1, text='What is the capital of Spain?', number=1, max_score=5)
        self.answer1 = AnswerFactory(question=self.question1, text='Madrid', is_correct=True, reason='Correct answer.')
        self.answer2 = AnswerFactory(question=self.question1, text='Barcelona', is_correct=False, reason='Incorrect answer.')
        # Create user quest attempts
        self.attempt1 = UserQuestAttemptFactory(student=self.student1, quest=self.quest1, submitted=False)
        self.attempt2 = UserQuestAttemptFactory(student=self.student2, quest=self.quest2, submitted=False)
        # Create user answer attempts
        self.answer_attempt1 = UserAnswerAttemptFactory(user_quest_attempt=self.attempt1, question=self.question1, answer=self.answer1, is_selected=True, score_achieved=5)
        self.answer_attempt2 = UserAnswerAttemptFactory(user_quest_attempt=self.attempt1, question=self.question1, answer=self.answer2, is_selected=False, score_achieved=0)
        # Create badges
        self.badge1 = BadgeFactory(name='Badge 1', description='First badge', type='Course Type', condition='Complete Course 1', image=self.image1)
        self.badge2 = BadgeFactory(name='Badge 2', description='Second badge', type='Course Type', condition='Complete Course 2', image=self.image2)
        self.badge3 = BadgeFactory(name='Badge 3', description='Third badge', type='Quest Type', condition='Complete Quest 1', image=self.image1)
        self.badge4 = BadgeFactory(name='Badge 4', description='Fourth badge', type='Quest Type', condition='Complete Quest 2', image=self.image2)
        # Create user quest badges
        self.user_quest_badge1 = UserQuestBadgeFactory(user_quest_attempt=self.attempt1, badge=self.badge1)
        self.user_quest_badge2 = UserQuestBadgeFactory(user_quest_attempt=self.attempt1, badge=self.badge2)
        # Create user course badges
        self.user_course_badge1 = UserCourseBadgeFactory(user_course_group_enrollment=self.enrollment1, badge=self.badge3)
        self.user_course_badge2 = UserCourseBadgeFactory(user_course_group_enrollment=self.enrollment2, badge=self.badge4)


class EduquestUserViewSetTest(BaseViewTest):

    def test_list_users(self):
        """
        Test that the serializer returns all users.
        """
        url = reverse('eduquest-users-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Check that both users are listed
        self.assertEqual(len(response.data), 5)  # Including staff_user and superuser

    def test_retrieve_user(self):
        """
        Test that the serializer returns the correct user.
        """
        url = reverse('eduquest-users-detail', args=[self.student1.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], self.student1.username)

    def test_update_user_nickname(self):
        """
        Test that the serializer updates the user correctly.
        """
        url = reverse('eduquest-users-detail', args=[self.student1.id])
        data = {
            'nickname': 'updatednickname'
        }
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        updated_user = EduquestUser.objects.get(id=self.student1.id)
        self.assertEqual(updated_user.nickname, 'updatednickname')

    def test_delete_user(self):
        """
        Test that the serializer deletes the user correctly.
        """
        url = reverse('eduquest-users-detail', args=[self.student1.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        with self.assertRaises(EduquestUser.DoesNotExist):
            EduquestUser.objects.get(id=self.student1.id)

    def test_by_email_action(self):
        """
        Test that the serializer returns the correct user by email.
        """
        url = reverse('eduquest-users-by-email')
        response = self.client.get(url, {'email': 'student_one@example.com'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], '#Student One#')

    def test_by_admin_action(self):
        """
        Test that the serializer returns only staff users.
        """
        url = reverse('eduquest-users-by-admin')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Only staff users should be returned
        self.assertEqual(len(response.data), 3)  # 2 staff_user and 1 admin

    def test_authentication_required(self):
        """
        Test that user requires authentication to access the API.
        """
        # Logout the current user
        self.client.logout()
        url = reverse('eduquest-users-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class ImageViewSetTest(BaseViewTest):

    def test_list_images(self):
        """
        Test that the serializer returns all images.
        """
        url = reverse('images-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Check that both images are listed
        self.assertEqual(len(response.data), 3 + 1)  # 3 existing + 1 'private'

    def test_retrieve_image(self):
        """
        Test that the serializer returns the correct image.
        """
        url = reverse('images-detail', args=[self.image1.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], self.image1.name)

    def test_create_image(self):
        """
        Test that the serializer creates an image instance.
        """
        url = reverse('images-list')
        data = {
            'name': 'image 3',
            'filename': 'image3.jpg'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Image.objects.count(), 4 + 1)  # 4 existing + 1 new
        self.assertEqual(Image.objects.get(id=response.data['id']).name, 'image 3')

    def test_update_image(self):
        """
        Test that the serializer updates an existing image instance.
        """
        url = reverse('images-detail', args=[self.image1.id])
        data = {
            'filename': 'updatedimage1.jpg'
        }
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.image1.refresh_from_db()
        self.assertEqual(self.image1.filename, 'updatedimage1.jpg')

    def test_delete_image(self):
        """
        Test that the serializer deletes an image instance.
        """
        url = reverse('images-detail', args=[self.image1.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Image.objects.filter(id=self.image1.id).exists())


class AcademicYearViewSetTest(BaseViewTest):

    def test_list_academic_years(self):
        """
        Test that the serializer returns all academic years.
        """
        url = reverse('academic-years-list')
        response = self.client.get(url)
        academic_years = AcademicYear.objects.all().order_by('-id')
        serializer = AcademicYearSerializer(academic_years, many=True)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_retrieve_academic_year(self):
        """
        Test that the serializer returns the correct academic year.
        """
        url = reverse('academic-years-detail', args=[self.ay1.id])
        response = self.client.get(url)
        serializer = AcademicYearSerializer(self.ay1)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_create_academic_year(self):
        """
        Test that the serializer creates an academic year instance.
        """
        url = reverse('academic-years-list')
        data = {
            'start_year': 2022,
            'end_year': 2023
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(AcademicYear.objects.count(), 3+1)  # 3 existing + 1 private
        self.assertEqual(AcademicYear.objects.get(id=response.data['id']).start_year, 2022)

    def test_update_academic_year(self):
        """
        Test that the serializer updates an existing academic year instance.
        """
        url = reverse('academic-years-detail', args=[self.ay1.id])
        data = {
            'end_year': 2025
        }
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.ay1.refresh_from_db()
        self.assertEqual(self.ay1.end_year, 2025)

    def test_delete_academic_year(self):
        """
        Test that the serializer deletes an academic year instance.
        """
        url = reverse('academic-years-detail', args=[self.ay1.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(AcademicYear.objects.filter(id=self.ay1.id).exists())

    def test_non_private_action(self):
        """
        Test that the serializer returns only non-private academic
        """
        url = reverse('academic-years-non-private')
        response = self.client.get(url)
        # Assuming 'start_year=0' is private, but our setup doesn't have any
        # So all should be returned
        academic_years = AcademicYear.objects.exclude(start_year=0).order_by('-id')
        serializer = AcademicYearSerializer(academic_years, many=True)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)


class TermViewSetTest(BaseViewTest):

    def test_list_terms(self):
        """
        Test that the serializer returns all terms.
        """
        url = reverse('terms-list')
        response = self.client.get(url)
        terms = Term.objects.all().order_by('-id')
        serializer = TermSerializer(terms, many=True)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_retrieve_term(self):
        """
        Test that the serializer returns the correct term.
        """
        url = reverse('terms-detail', args=[self.term1.id])
        response = self.client.get(url)
        serializer = TermSerializer(self.term1)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_create_term(self):
        """
        Test that the serializer creates a term instance.
        """
        url = reverse('terms-list')
        data = {
            'name': 'Term 3',
            'start_date': '2022-01-15',
            'end_date': '2022-05-30',
            'academic_year_id': self.ay1.id
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Term.objects.count(), 3 + 1)  # 3 existing + 1 private
        self.assertEqual(Term.objects.get(id=response.data['id']).name, 'Term 3')

    def test_update_term(self):
        """
        Test that the serializer updates an existing term instance.
        """
        url = reverse('terms-detail', args=[self.term1.id])
        new_ay = AcademicYear.objects.create(start_year=2023, end_year=2024)
        data = {
            'name': 'Updated Term 1',
            'academic_year_id': new_ay.id
        }
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.term1.refresh_from_db()
        self.assertEqual(self.term1.name, 'Updated Term 1')
        self.assertEqual(self.term1.academic_year, new_ay)

    def test_delete_term(self):
        """
        Test that the serializer deletes a term instance.
        """
        url = reverse('terms-detail', args=[self.term1.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Term.objects.filter(id=self.term1.id).exists())

    def test_non_private_action(self):
        """
        Test that the serializer returns only non-private terms.
        """
        url = reverse('terms-non-private')
        response = self.client.get(url)
        terms = Term.objects.exclude(name='Private Term').order_by('-id')
        serializer = TermSerializer(terms, many=True)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_permission_required(self):
        """
        Test that user requires permission to access the API.
        """
        # Logout the current user
        self.client.logout()
        url = reverse('terms-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class CourseViewSetTest(BaseViewTest):

    def test_list_courses(self):
        """
        Test that the list endpoint returns all courses.
        """
        url = reverse('courses-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should include both courses
        self.assertEqual(len(response.data), 2 + 1)  # 2 existing + 1 private
        course_names = [course['name'] for course in response.data]
        self.assertIn('Course 1', course_names)
        self.assertIn('Course 2', course_names)

    def test_create_course(self):
        """
        Test creating a new course.
        """
        url = reverse('courses-list')
        data = {
            'name': 'Course 3',
            'code': 'CS103',
            'type': 'System-enroll',
            'description': 'A new course.',
            'status': 'Active',
            'term_id': self.term1.id,
            'image_id': self.image1.id,
            'coordinators': [self.staff_user1.id, self.staff_user2.id],
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Course.objects.count(), 3 + 1)  # 3 existing + 1 private
        new_course = Course.objects.get(name='Course 3')
        self.assertEqual(new_course.code, 'CS103')
        self.assertEqual(new_course.type, 'System-enroll')
        self.assertEqual(new_course.term, self.term1)
        self.assertEqual(new_course.image, self.image1)
        self.assertEqual(list(new_course.coordinators.all()), [self.staff_user1, self.staff_user2])

    def test_retrieve_course(self):
        """
        Test retrieving a specific course.
        """
        url = reverse('courses-detail', args=[self.course1.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Course 1')
        self.assertEqual(response.data['code'], 'CS101')

    def test_update_course(self):
        """
        Test updating an existing course.
        """
        url = reverse('courses-detail', args=[self.course1.id])
        data = {
            'name': 'Updated Course 1',
            'coordinators': [self.staff_user2.id],  # Update coordinators
        }
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        updated_course = Course.objects.get(id=self.course1.id)
        self.assertEqual(updated_course.name, 'Updated Course 1')
        self.assertEqual(list(updated_course.coordinators.all()), [self.staff_user2])

    def test_delete_course(self):
        """
        Test deleting a course.
        """
        url = reverse('courses-detail', args=[self.course1.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Course.objects.filter(id=self.course1.id).exists())

    def test_non_private_courses_action(self):
        """
        Test the custom 'non_private' action to list courses excluding type 'Private'.
        """
        url = reverse('courses-non-private')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should include only course1
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'Course 1')

    def test_courses_by_enrolled_user_action(self):
        """
        Test the custom 'by_enrolled_user' action to list courses a user is enrolled in, excluding 'Private'.
        """
        url = reverse('courses-by-enrolled-user')
        response = self.client.get(url, {'user_id': self.student1.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # User1 is enrolled in course1, which is non-private
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'Course 1')

        # Test with a user enrolled in a private course
        response = self.client.get(url, {'user_id': self.student2.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # User2 is enrolled in course1 (non-private), and course2 (private). Only course1 should be listed
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'Course 1')

    def test_courses_by_enrolled_user_no_enrollments(self):
        """
        Test the 'by_enrolled_user' action when the user has no enrollments.
        """
        new_user = EduquestUserFactory(username='user3', email='user3@example.com')
        url = reverse('courses-by-enrolled-user')
        response = self.client.get(url, {'user_id': new_user.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_courses_by_enrolled_user_invalid_user(self):
        """
        Test the 'by_enrolled_user' action with an invalid user_id.
        """
        url = reverse('courses-by-enrolled-user')
        response = self.client.get(url, {'user_id': 9999})  # Assuming this ID doesn't exist
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_permission_required_for_course_endpoints(self):
        """
        Test that unauthenticated users cannot access course endpoints.
        """
        self.client.logout()
        url = reverse('courses-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        url = reverse('courses-non-private')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class UserCourseGroupEnrollmentViewSetTest(BaseViewTest):

    def test_list_enrollments(self):
        """
        Test that the list endpoint returns all enrollments.
        """
        url = reverse('user-course-group-enrollments-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should include both enrollments
        self.assertEqual(len(response.data), 2 + 2 + 2)  # 2 existing + 2 private + 2 private (staff_user)
        enrollment_ids = [enrollment['id'] for enrollment in response.data]
        self.assertIn(self.enrollment1.id, enrollment_ids)
        self.assertIn(self.enrollment2.id, enrollment_ids)

    def test_create_enrollment(self):
        """
        Test creating a new enrollment for a new course.
        """
        new_course = Course.objects.create(
            name='Course 3',
            code='CS103',
            type='System-enroll',
            description='A new course.',
            status='Active',
            image=self.image1,
            term=self.term1
        )
        new_course_group = CourseGroup.objects.create(course=new_course, instructor=self.staff_user1, name='Group 3')
        url = reverse('user-course-group-enrollments-list')
        data = {
            'course_group_id': new_course_group.id,
            'student_id': self.student2.id,
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(UserCourseGroupEnrollment.objects.count(), 3 + 2 + 2)  # 3 existing + 2 private + 2 private (staff_user)
        new_enrollment = UserCourseGroupEnrollment.objects.get(id=response.data['id'])
        self.assertEqual(new_enrollment.course_group, new_course_group)
        self.assertEqual(new_enrollment.student, self.student2)

    def test_retrieve_enrollment(self):
        """
        Test retrieving a specific enrollment.
        """
        url = reverse('user-course-group-enrollments-detail', args=[self.enrollment1.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.enrollment1.id)
        self.assertEqual(response.data['course_group']['id'], self.course_group1.id)
        self.assertEqual(response.data['student_id'], self.student1.id)

    def test_update_enrollment(self):
        """
        Test updating an existing enrollment.
        """
        student3 = EduquestUserFactory(username='student3', email='student3@example.com')
        url = reverse('user-course-group-enrollments-detail', args=[self.enrollment1.id])
        data = {
            'course_group_id': self.course_group2.id,  # Change course group
            'student_id': student3.id,  # Change student
        }
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        updated_enrollment = UserCourseGroupEnrollment.objects.get(id=self.enrollment1.id)
        self.assertEqual(updated_enrollment.student, student3)

    def test_delete_enrollment(self):
        """
        Test deleting an enrollment.
        """
        url = reverse('user-course-group-enrollments-detail', args=[self.enrollment1.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(UserCourseGroupEnrollment.objects.filter(id=self.enrollment1.id).exists())

    def test_by_course_group_and_user_action(self):
        """
        Test the custom 'by_course_group_and_user' action to filter enrollments by course group and user.
        """
        url = reverse('user-course-group-enrollments-by-course-group-and-user')
        response = self.client.get(url, {'course_group_id': self.course_group1.id, 'user_id': self.student1.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], self.enrollment1.id)

    def test_by_course_and_user_action(self):
        """
        Test the custom 'by_course_and_user' action to filter enrollments by course and user.
        """
        url = reverse('user-course-group-enrollments-by-course-and-user')
        response = self.client.get(url, {'course_id': self.course1.id, 'user_id': self.student2.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], self.enrollment2.id)

    def test_by_course_group_and_user_no_match(self):
        """
        Test the 'by_course_group_and_user' action with no matching enrollments.
        """
        url = reverse('user-course-group-enrollments-by-course-group-and-user')
        response = self.client.get(url, {'course_group_id': self.course_group1.id, 'user_id': self.student2.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_by_course_and_user_no_match(self):
        """
        Test the 'by_course_and_user' action with no matching enrollments.
        """
        url = reverse('user-course-group-enrollments-by-course-and-user')
        response = self.client.get(url, {'course_id': self.course2.id, 'user_id': self.student2.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_permission_required_for_enrollment_endpoints(self):
        """
        Test that unauthenticated users cannot access enrollment endpoints.
        """
        self.client.logout()

        # List endpoint
        url = reverse('user-course-group-enrollments-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Custom actions
        url = reverse('user-course-group-enrollments-by-course-group-and-user')
        response = self.client.get(url, {'course_group_id': self.course_group1.id, 'user_id': self.student1.id})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        url = reverse('user-course-group-enrollments-by-course-and-user')
        response = self.client.get(url, {'course_id': self.course1.id, 'user_id': self.student1.id})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class QuestViewSetTest(BaseViewTest):

    def test_list_quests(self):
        """
        Test that the list endpoint returns all quests.
        """
        url = reverse('quests-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should include all quests
        self.assertEqual(len(response.data), 3 + 1)  # 3 normal existing + 1 private existing

    def test_create_quest(self):
        """
        Test creating a new quest.
        """
        url = reverse('quests-list')
        data = {
            'name': 'Quest 1',
            'description': 'A new quest.',
            'type': 'EduQuest MCQ',
            'status': 'Active',
            'tutorial_date': '2022-01-15T10:00:00Z',
            'expiration_date': '2022-01-15T12:00:00Z',
            'max_attempts': 3,
            'course_group_id': self.course_group1.id,
            'organiser_id': self.staff_user1.id,
            'image_id': self.image1.id,
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Quest.objects.count(), 4 + 1)  # 3 existing + 1 private + 1 new
        new_quest = Quest.objects.get(id=response.data['id'])
        self.assertEqual(new_quest.name, 'Quest 1')
        self.assertEqual(new_quest.description, 'A new quest.')
        self.assertEqual(new_quest.type, 'EduQuest MCQ')
        self.assertEqual(new_quest.status, 'Active')
        self.assertEqual(new_quest.tutorial_date, timezone.datetime(2022, 1, 15, 10, 0, 0, tzinfo=timezone.timezone.utc))
        self.assertEqual(new_quest.expiration_date, timezone.datetime(2022, 1, 15, 12, 0, 0, tzinfo=timezone.timezone.utc))
        self.assertEqual(new_quest.max_attempts, 3)
        self.assertEqual(new_quest.course_group, self.course_group1)
        self.assertEqual(new_quest.organiser, self.staff_user1)
        self.assertEqual(new_quest.image, self.image1)

    def test_retrieve_quest(self):
        """
        Test retrieving a specific quest.
        """
        url = reverse('quests-detail', args=[self.quest1.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Quest 1')
        self.assertEqual(response.data['type'], 'EduQuest MCQ')

    def test_update_quest(self):
        """
        Test updating an existing quest.
        """
        url = reverse('quests-detail', args=[self.quest1.id])
        data = {
            'name': 'Updated Quest 1',
            'type': 'Private',  # Change type
            'organiser_id': self.staff_user2.id,  # Change organiser
        }
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        updated_quest = Quest.objects.get(id=self.quest1.id)
        self.assertEqual(updated_quest.name, 'Updated Quest 1')
        self.assertEqual(updated_quest.type, 'Private')
        self.assertEqual(updated_quest.organiser, self.staff_user2)

    def test_delete_quest(self):
        """
        Test deleting a quest.
        """
        url = reverse('quests-detail', args=[self.quest1.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Quest.objects.filter(id=self.quest1.id).exists())

    def test_non_private_quests_action(self):
        """
        Test the custom 'non_private' action to list quests excluding type 'Private'.
        """
        url = reverse('quests-non-private')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should include quest1 and quest3
        self.assertEqual(len(response.data), 3)
        quest_names = [quest['name'] for quest in response.data]
        self.assertIn('Quest 1', quest_names)
        self.assertIn('Quest 3', quest_names)
        self.assertIn('Quest 2', quest_names)
        self.assertNotIn('Private Quest', quest_names)

    def test_private_by_user_action(self):
        """
        Test the custom 'private_by_user' action to list private quests organized by the authenticated user.
        """
        self.client.force_authenticate(user=self.student1)
        url = reverse('quests-private-by-user')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # private_quest is private and organized by student 1
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'Private Quest')

    def test_by_enrolled_user_action(self):
        """
        Test the custom 'by_enrolled_user' action to list quests a user is enrolled in, excluding 'Private'.
        """
        url = reverse('quests-by-enrolled-user')
        response = self.client.get(url, {'user_id': self.student1.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # student 1 is enrolled in public course_group1, which has quest1 and quest3
        self.assertEqual(len(response.data), 2)  # 2 existing
        quest_names = [quest['name'] for quest in response.data]
        self.assertIn('Quest 1', quest_names)
        self.assertIn('Quest 3', quest_names)

        response = self.client.get(url, {'user_id': self.student2.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # student 2 is enrolled in public course_group2, which has quest2
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'Quest 2')

    def test_by_course_group_action(self):
        """
        Test the custom 'by_course_group' action to list quests for a specific course group.
        """
        url = reverse('quests-by-course-group')
        response = self.client.get(url, {'course_group_id': self.course_group1.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # course_group1 has quest1 and quest3
        self.assertEqual(len(response.data), 2)
        quest_names = [quest['name'] for quest in response.data]
        self.assertIn('Quest 1', quest_names)
        self.assertIn('Quest 3', quest_names)

        response = self.client.get(url, {'course_group_id': self.course_group2.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # course_group2 has quest2
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'Quest 2')

    def test_import_quest_action(self):
        """
        Test the custom 'import_quest' action to import quests from an Excel file.
        """
        url = reverse('quests-import-quest')
        # get current dir
        current_dir = os.path.dirname(os.path.realpath(__file__))
        excel_file_path = os.path.join(current_dir, 'test_files', 'test_excel.xlsx')

        with open(excel_file_path, 'rb') as excel_file:

            # Prepare data
            data = {
                'file':  SimpleUploadedFile(excel_file_path, excel_file.read(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
                'type': 'Wooclap!',
                'name': 'Imported Quest',
                'description': 'Imported quest description.',
                'status': 'Active',
                'max_attempts': 3,
                'course_group_id': self.course_group1.id,
                'tutorial_date': '2023-11-15T10:00:00Z',
                'image_id': self.image1.id,
                'organiser_id': self.staff_user1.id,
            }

            response = self.client.post(url, data, format='multipart')
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            # Verify that the quest was created
            imported_quest = Quest.objects.get(name='Imported Quest')
            self.assertEqual(imported_quest.type, 'Wooclap!')
            self.assertEqual(imported_quest.course_group, self.course_group1)
            self.assertEqual(imported_quest.organiser, self.staff_user1)
            self.assertEqual(imported_quest.image, self.image1)

            # Verify that questions were created
            self.assertEqual(imported_quest.questions.count(), 2)
            question1 = imported_quest.questions.get(text='Question 1')
            question2 = imported_quest.questions.get(text='Question 2')
            self.assertEqual(question1.number, 1)
            self.assertEqual(question1.max_score, 5)
            self.assertEqual(question2.number, 2)
            self.assertEqual(question2.max_score, 10)

            # Verify that users were created and enrolled
            self.assertTrue(EduquestUser.objects.filter(email='STUDENT3@EXAMPLE.COM').exists())
            self.assertTrue(EduquestUser.objects.filter(email='STUDENT4@EXAMPLE.COM').exists())
            student3 = EduquestUser.objects.get(email='STUDENT3@EXAMPLE.COM')
            student4 = EduquestUser.objects.get(email='STUDENT4@EXAMPLE.COM')

            # Verify enrollments
            enrollment3 = UserCourseGroupEnrollment.objects.get(student=student3, course_group=self.course_group1)
            enrollment4 = UserCourseGroupEnrollment.objects.get(student=student4, course_group=self.course_group1)
            self.assertIsNotNone(enrollment3)
            self.assertIsNotNone(enrollment4)

            # Verify attempts
            student3_attempt1 = UserQuestAttempt.objects.get(student=student3, quest=imported_quest)
            student4_attempt1 = UserQuestAttempt.objects.get(student=student4, quest=imported_quest)
            self.assertIsNotNone(student3_attempt1)
            self.assertIsNotNone(student4_attempt1)

            # Verify selected answers in attempts
            student3_answer_attempts = UserAnswerAttempt.objects.filter(user_quest_attempt=student3_attempt1)
            student4_answer_attempts = UserAnswerAttempt.objects.filter(user_quest_attempt=student4_attempt1)

            self.assertEqual(student3_answer_attempts.count(), 4)  # 4 total answers including selected=False
            self.assertEqual(student4_answer_attempts.count(), 4)  # 4 total answers including selected=False
            for answer_attempt in student3_answer_attempts:
                if answer_attempt.answer.text == 'Choice 1A':
                    self.assertTrue(answer_attempt.is_selected)
                    continue
                if answer_attempt.answer.text == 'Choice 1B':
                    self.assertFalse(answer_attempt.is_selected)
                    continue
                if answer_attempt.answer.text == 'Choice 2A':
                    self.assertFalse(answer_attempt.is_selected)
                    continue
                if answer_attempt.answer.text == 'Choice 2B':
                    self.assertTrue(answer_attempt.is_selected)
                    continue

            for answer_attempt in student4_answer_attempts:
                if answer_attempt.answer.text == 'Choice 1A':
                    self.assertFalse(answer_attempt.is_selected)
                    continue
                if answer_attempt.answer.text == 'Choice 1B':
                    self.assertTrue(answer_attempt.is_selected)
                    continue
                if answer_attempt.answer.text == 'Choice 2A':
                    self.assertFalse(answer_attempt.is_selected)
                    continue
                if answer_attempt.answer.text == 'Choice 2B':
                    self.assertFalse(answer_attempt.is_selected)
                    continue


class QuestionViewSetTest(BaseViewTest):

    def test_list_questions(self):
        """
        Test that the list endpoint returns all questions.
        """
        url = reverse('questions-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should include the created question
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['text'], 'What is the capital of Spain?')

    def test_create_question(self):
        """
        Test creating a new question.
        """
        url = reverse('questions-list')
        data = {
            'quest_id': self.quest1.id,
            'text': 'What is 2 + 2?',
            'number': 2,
            'max_score': 3,
            'answers': [
                {'text': '3', 'is_correct': False, 'reason': 'Incorrect.'},
                {'text': '4', 'is_correct': True, 'reason': 'Correct.'},
            ]
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Question.objects.count(), 2)
        new_question = Question.objects.get(text='What is 2 + 2?')
        self.assertEqual(new_question.number, 2)
        self.assertEqual(new_question.max_score, 3)
        self.assertEqual(new_question.quest, self.quest1)
        self.assertEqual(new_question.answers.count(), 2)
        self.assertTrue(new_question.answers.filter(text='4', is_correct=True).exists())

    def test_create_question_bulk(self):
        """
        Test bulk creation of questions.
        """
        url = reverse('questions-list')
        bulk_data = [
            {
                'quest_id': self.quest1.id,
                'text': 'What is the boiling point of water?',
                'number': 3,
                'max_score': 4,
                'answers': [
                    {'text': '100°C', 'is_correct': True, 'reason': 'Correct.'},
                    {'text': '90°C', 'is_correct': False, 'reason': 'Incorrect.'},
                ]
            },
            {
                'quest_id': self.quest1.id,
                'text': 'What is the largest planet?',
                'number': 4,
                'max_score': 5,
                'answers': [
                    {'text': 'Jupiter', 'is_correct': True, 'reason': 'Correct.'},
                    {'text': 'Mars', 'is_correct': False, 'reason': 'Incorrect.'},
                ]
            }
        ]
        response = self.client.post(url, bulk_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Question.objects.count(), 3)
        self.assertTrue(Question.objects.filter(text='What is the boiling point of water?').exists())
        self.assertTrue(Question.objects.filter(text='What is the largest planet?').exists())

    def test_create_question_invalid_missing_answers(self):
        """
        Test creating a question without providing answers should fail.
        """
        url = reverse('questions-list')
        data = {
            'quest_id': self.quest1.id,
            'text': 'Incomplete Question',
            'number': 5,
            'max_score': 2,
            'answers': []  # No answers provided
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_question(self):
        """
        Test retrieving a specific question.
        """
        url = reverse('questions-detail', args=[self.question1.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['text'], 'What is the capital of Spain?')
        self.assertEqual(len(response.data['answers']), 2)


    def test_delete_question(self):
        """
        Test deleting a question.
        """
        url = reverse('questions-detail', args=[self.question1.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Question.objects.filter(id=self.question1.id).exists())
        # Ensure answers are also deleted if cascade is set
        self.assertFalse(Answer.objects.filter(id=self.answer1.id).exists())
        self.assertFalse(Answer.objects.filter(id=self.answer2.id).exists())

    def test_bulk_create_questions_with_invalid_data(self):
        """
        Test bulk creation with one invalid question should fail the entire operation.
        """
        url = reverse('questions-list')
        bulk_data = [
            {
                'quest_id': self.quest1.id,
                'text': 'Valid Question',
                'number': 6,
                'max_score': 4,
                'answers': [
                    {'text': 'Option A', 'is_correct': True, 'reason': 'Correct.'},
                    {'text': 'Option B', 'is_correct': False, 'reason': 'Incorrect.'},
                ]
            },
            {
                'quest_id': self.quest1.id,
                'text': 'Invalid Question',
                'number': 7,
                'max_score': 3,
                'answers': []  # Missing answers
            }
        ]
        response = self.client.post(url, bulk_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # Ensure no new questions were created
        self.assertEqual(Question.objects.count(), 1)

    def test_permission_required_for_question_endpoints(self):
        """
        Test that unauthenticated users cannot access question endpoints.
        """
        self.client.logout()

        # List endpoint
        url = reverse('questions-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Detail endpoint
        url = reverse('questions-detail', args=[self.question1.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Bulk create endpoint
        url = reverse('questions-list')
        data = [
            {
                'quest_id': self.quest1.id,
                'text': 'Another Question',
                'number': 8,
                'max_score': 2,
                'answers': [
                    {'text': 'Yes', 'is_correct': False, 'reason': 'No.'},
                    {'text': 'No', 'is_correct': True, 'reason': 'Yes.'},
                ]
            }
        ]
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class AnswerViewSetTest(BaseViewTest):

    def test_list_answers(self):
        """
        Test that the list endpoint returns all answers.
        """
        url = reverse('answers-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should include both answers
        self.assertEqual(len(response.data), 2)
        answer_texts = [answer['text'] for answer in response.data]
        self.assertIn('Madrid', answer_texts)
        self.assertIn('Barcelona', answer_texts)

    def test_retrieve_answer(self):
        """
        Test retrieving a specific answer.
        """
        url = reverse('answers-detail', args=[self.answer1.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['text'], 'Madrid')
        self.assertTrue(response.data['is_correct'])

    def test_update_answer(self):
        """
        Test updating an existing answer.
        """
        url = reverse('answers-detail', args=[self.answer2.id])
        data = {
            'text': 'Seville',
            'is_correct': False,
            'reason': 'Still incorrect.',
        }
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        updated_answer = Answer.objects.get(id=self.answer2.id)
        self.assertEqual(updated_answer.text, 'Seville')
        self.assertFalse(updated_answer.is_correct)
        self.assertEqual(updated_answer.reason, 'Still incorrect.')

    def test_delete_answer(self):
        """
        Test deleting an answer.
        """
        url = reverse('answers-detail', args=[self.answer1.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Answer.objects.filter(id=self.answer1.id).exists())

    def test_bulk_update_answers(self):
        """
        Test the custom 'bulk_update' action to update multiple answers simultaneously.
        """
        url = reverse('answers-bulk-update')
        bulk_data = [
            {
                'id': self.answer1.id,
                'text': 'Madrid Updated',
                'is_correct': True,
                'reason': 'Updated reason.'
            },
            {
                'id': self.answer2.id,
                'text': 'Barcelona Updated',
                'is_correct': False,
                'reason': 'Updated reason.'
            },
        ]
        response = self.client.put(url, bulk_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Verify updates
        updated_answer1 = Answer.objects.get(id=self.answer1.id)
        updated_answer2 = Answer.objects.get(id=self.answer2.id)
        self.assertEqual(updated_answer1.text, 'Madrid Updated')
        self.assertEqual(updated_answer1.reason, 'Updated reason.')
        self.assertEqual(updated_answer2.text, 'Barcelona Updated')
        self.assertEqual(updated_answer2.reason, 'Updated reason.')

    def test_bulk_update_answers_with_invalid_id(self):
        """
        Test bulk updating answers with an invalid answer ID.
        """
        url = reverse('answers-bulk-update')
        bulk_data = [
            {
                'id': self.answer1.id,
                'text': 'Madrid Updated',
                'is_correct': True,
                'reason': 'Updated reason.'
            },
            {
                'id': 9999,  # Assuming this ID doesn't exist
                'text': 'Invalid Answer',
                'is_correct': False,
                'reason': 'Invalid reason.'
            },
        ]
        response = self.client.put(url, bulk_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error'], 'Answer with id 9999 does not exist.')

    def test_bulk_update_answers_with_non_list_data(self):
        """
        Test that bulk updating with non-list data fails.
        """
        url = reverse('answers-bulk-update')
        data = {
            'id': self.answer1.id,
            'text': 'Madrid Updated',
            'is_correct': True,
            'reason': 'Updated reason.'
        }
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error'], 'Expected a list of items.')

    def test_permission_required_for_answer_endpoints(self):
        """
        Test that unauthenticated users cannot access answer endpoints.
        """
        self.client.logout()

        # List endpoint
        url = reverse('answers-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Detail endpoint
        url = reverse('answers-detail', args=[self.answer1.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Bulk update endpoint
        url = reverse('answers-bulk-update')
        bulk_data = [
            {
                'id': self.answer1.id,
                'text': 'Madrid Unauthorized',
                'is_correct': True,
                'reason': 'Unauthorized update.'
            }
        ]
        response = self.client.put(url, bulk_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class UserQuestAttemptViewSetTest(BaseViewTest):

    def test_list_user_quest_attempts(self):
        """
        Test that the list endpoint returns all user quest attempts.
        """
        url = reverse('user-quest-attempts-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should include both attempts
        self.assertEqual(len(response.data), 2)
        attempt_ids = [attempt['id'] for attempt in response.data]
        self.assertIn(self.attempt1.id, attempt_ids)
        self.assertIn(self.attempt2.id, attempt_ids)

    def test_create_user_quest_attempt(self):
        """
        Test creating a new user quest attempt.
        """
        url = reverse('user-quest-attempts-list')
        data = {
            'student_id': self.student1.id,
            'quest_id': self.quest1.id,
            'last_attempted_date': None
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(UserQuestAttempt.objects.count(), 3)
        new_attempt = UserQuestAttempt.objects.get(id=response.data['id'])
        self.assertEqual(new_attempt.student, self.student1)
        self.assertEqual(new_attempt.quest, self.quest1)
        self.assertFalse(new_attempt.submitted)

    def test_retrieve_user_quest_attempt(self):
        """
        Test retrieving a specific user quest attempt.
        """
        url = reverse('user-quest-attempts-detail', args=[self.attempt1.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['student_id'], self.student1.id)
        self.assertEqual(response.data['quest_id'], self.quest1.id)
        self.assertFalse(response.data['submitted'])

    def test_update_user_quest_attempt(self):
        """
        Test updating an existing user quest attempt.
        """
        url = reverse('user-quest-attempts-detail', args=[self.attempt1.id])
        data = {
            'submitted': True,
            'last_attempted_date': '2023-10-02T15:30:00Z',
            'student_id': self.student1.id,
            'quest_id': self.quest1.id,
        }
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        updated_attempt = UserQuestAttempt.objects.get(id=self.attempt1.id)
        self.assertTrue(updated_attempt.submitted)
        self.assertEqual(updated_attempt.total_score_achieved, 0)
        self.assertEqual(updated_attempt.last_attempted_date, timezone.datetime(2023, 10, 2, 15, 30, 0, tzinfo=timezone.timezone.utc))

    def test_delete_user_quest_attempt(self):
        """
        Test deleting a user quest attempt.
        """
        url = reverse('user-quest-attempts-detail', args=[self.attempt1.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(UserQuestAttempt.objects.filter(id=self.attempt1.id).exists())

    def test_by_user_quest_action(self):
        """
        Test the custom 'by_user_quest' action to filter attempts by user and quest.
        """
        url = reverse('user-quest-attempts-by-user-quest')
        response = self.client.get(url, {'user_id': self.student1.id, 'quest_id': self.quest1.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should return attempt1
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], self.attempt1.id)

    def test_by_quest_action(self):
        """
        Test the custom 'by_quest' action to filter attempts by quest.
        """
        url = reverse('user-quest-attempts-by-quest')
        response = self.client.get(url, {'quest_id': self.quest1.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should return attempt1
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], self.attempt1.id)

    def test_set_all_attempts_submitted_by_quest_action(self):
        """
        Test the custom 'set_all_attempts_submitted_by_quest' action to mark all attempts as submitted.
        """
        url = reverse('user-quest-attempts-set-all-attempts-submitted-by-quest')
        response = self.client.post(f"{url}?quest_id={self.quest1.id}", format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Check if attempt 1 is from quest 1
        self.assertEqual(self.attempt1.quest, self.quest1)
        # Verify that attempt1 is now submitted
        updated_attempt1 = UserQuestAttempt.objects.get(id=self.attempt1.id)
        self.assertTrue(updated_attempt1.submitted)

        # Check if attempt 2 not from quest 1
        self.assertNotEqual(self.attempt2.quest, self.quest1)
        # attempt2 should remain unchanged
        updated_attempt2 = UserQuestAttempt.objects.get(id=self.attempt2.id)
        self.assertFalse(updated_attempt2.submitted)
        self.assertEqual(response.data['message'], f"All attempts for quest {self.quest1.id} have been marked as submitted.")

    def test_permission_required_for_user_quest_attempt_endpoints(self):
        """
        Test that unauthenticated users cannot access user quest attempt endpoints.
        """
        self.client.logout()

        # List endpoint
        url = reverse('user-quest-attempts-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Detail endpoint
        url = reverse('user-quest-attempts-detail', args=[self.attempt1.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Custom actions
        url = reverse('user-quest-attempts-by-user-quest')
        response = self.client.get(url, {'user_id': self.student1.id, 'quest_id': self.quest1.id})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        url = reverse('user-quest-attempts-set-all-attempts-submitted-by-quest')
        response = self.client.post(url, {'quest_id': self.quest1.id}, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class UserAnswerAttemptViewSetTest(BaseViewTest):

    def test_list_user_answer_attempts(self):
        """
        Test that the list endpoint returns all user answer attempts.
        """
        url = reverse('user-answer-attempts-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should include both answer attempts
        self.assertEqual(len(response.data), 2)
        attempt_ids = [attempt['id'] for attempt in response.data]
        self.assertIn(self.answer_attempt1.id, attempt_ids)
        self.assertIn(self.answer_attempt2.id, attempt_ids)

    def test_create_user_answer_attempt(self):
        """
        Test creating a new user answer attempt.
        """
        url = reverse('user-answer-attempts-list')
        data = {
            'user_quest_attempt_id': self.attempt1.id,
            'question_id': self.question1.id,
            'answer_id': self.answer2.id,
            'is_selected': True,
            'score_achieved': 0
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(UserAnswerAttempt.objects.count(), 3)
        new_attempt = UserAnswerAttempt.objects.get(id=response.data['id'])
        self.assertEqual(new_attempt.user_quest_attempt, self.attempt1)
        self.assertEqual(new_attempt.question, self.question1)
        self.assertEqual(new_attempt.answer, self.answer2)
        self.assertTrue(new_attempt.is_selected)
        self.assertEqual(new_attempt.score_achieved, 0)

    def test_retrieve_user_answer_attempt(self):
        """
        Test retrieving a specific user answer attempt.
        """
        url = reverse('user-answer-attempts-detail', args=[self.answer_attempt1.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['user_quest_attempt_id'], self.attempt1.id)
        self.assertEqual(response.data['question']['id'], self.question1.id)
        self.assertEqual(response.data['answer']['id'], self.answer1.id)
        self.assertTrue(response.data['is_selected'])
        self.assertEqual(response.data['score_achieved'], 5)

    def test_update_user_answer_attempt(self):
        """
        Test updating an existing user answer attempt.
        """
        url = reverse('user-answer-attempts-detail', args=[self.answer_attempt2.id])
        data = {
            'is_selected': True,
            'score_achieved': 3
        }
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        updated_attempt = UserAnswerAttempt.objects.get(id=self.answer_attempt2.id)
        self.assertTrue(updated_attempt.is_selected)
        self.assertEqual(updated_attempt.score_achieved, 3)

    def test_delete_user_answer_attempt(self):
        """
        Test deleting a user answer attempt.
        """
        url = reverse('user-answer-attempts-detail', args=[self.answer_attempt1.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(UserAnswerAttempt.objects.filter(id=self.answer_attempt1.id).exists())

    def test_by_user_quest_attempt_action(self):
        """
        Test the custom 'by_user_quest_attempt' action to filter answer attempts by user quest attempt.
        """
        url = reverse('user-answer-attempts-by-user-quest-attempt')
        response = self.client.get(url, {'user_quest_attempt_id': self.attempt1.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should return both answer attempts
        self.assertEqual(len(response.data), 2)
        attempt_ids = [attempt['id'] for attempt in response.data]
        self.assertIn(self.answer_attempt1.id, attempt_ids)
        self.assertIn(self.answer_attempt2.id, attempt_ids)

    def test_by_quest_action(self):
        """
        Test the custom 'by_quest' action to filter answer attempts by quest.
        """
        url = reverse('user-answer-attempts-by-quest')
        response = self.client.get(url, {'quest_id': self.quest1.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should return both answer attempts
        self.assertEqual(len(response.data), 2)
        attempt_ids = [attempt['id'] for attempt in response.data]
        self.assertIn(self.answer_attempt1.id, attempt_ids)
        self.assertIn(self.answer_attempt2.id, attempt_ids)

    def test_bulk_update_user_answer_attempts(self):
        """
        Test the custom 'bulk_update' action to update multiple user answer attempts.
        """
        url = reverse('user-answer-attempts-bulk-update')
        bulk_data = [
            {
                'id': self.answer_attempt1.id,
                'is_selected': False,
                'score_achieved': 0
            },
            {
                'id': self.answer_attempt2.id,
                'is_selected': True,
                'score_achieved': 3
            }
        ]
        response = self.client.patch(url, bulk_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        updated_attempts = response.data['updated_attempts']
        self.assertEqual(len(updated_attempts), 2)
        # Verify updates
        updated_attempt1 = UserAnswerAttempt.objects.get(id=self.answer_attempt1.id)
        updated_attempt2 = UserAnswerAttempt.objects.get(id=self.answer_attempt2.id)
        self.assertFalse(updated_attempt1.is_selected)
        self.assertEqual(updated_attempt1.score_achieved, 0)
        self.assertTrue(updated_attempt2.is_selected)
        self.assertEqual(updated_attempt2.score_achieved, 3)

    def test_bulk_update_user_answer_attempts_with_non_list_data(self):
        """
        Test bulk updating user answer attempts with non-list data.
        """
        url = reverse('user-answer-attempts-bulk-update')
        data = {
            'id': self.answer_attempt1.id,
            'is_selected': False,
            'score_achieved': 0
        }
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error'], 'Expected a list of data.')

    def test_permission_required_for_user_answer_attempt_endpoints(self):
        """
        Test that unauthenticated users cannot access user answer attempt endpoints.
        """
        self.client.logout()

        # List endpoint
        url = reverse('user-answer-attempts-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Detail endpoint
        url = reverse('user-answer-attempts-detail', args=[self.answer_attempt1.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Custom actions
        url = reverse('user-answer-attempts-by-user-quest-attempt')
        response = self.client.get(url, {'user_quest_attempt_id': self.answer_attempt1.id})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        url = reverse('user-answer-attempts-bulk-update')
        bulk_data = [
            {
                'id': self.answer_attempt1.id,
                'is_selected': False,
                'score_achieved': 0
            }
        ]
        response = self.client.patch(url, bulk_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class BadgeViewSetTest(BaseViewTest):

    def test_list_badges(self):
        """
        Test that the list endpoint returns all badges.
        """
        url = reverse('badges-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should include both badges
        self.assertEqual(len(response.data), 4)
        badge_names = [badge['name'] for badge in response.data]
        self.assertIn('Badge 1', badge_names)
        self.assertIn('Badge 2', badge_names)

    def test_create_badge(self):
        """
        Test creating a new badge.
        """
        url = reverse('badges-list')
        data = {
            'name': 'Badge 10',
            'description': 'Tenth badge',
            'type': 'Course Type',
            'condition': 'Complete Course 3',
            'image_id': self.image1.id
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Badge.objects.count(), 4 + 1)
        new_badge = Badge.objects.get(name='Badge 10')
        self.assertEqual(new_badge.description, 'Tenth badge')
        self.assertEqual(new_badge.type, 'Course Type')
        self.assertEqual(new_badge.condition, 'Complete Course 3')
        self.assertEqual(new_badge.image, self.image1)

    def test_retrieve_badge(self):
        """
        Test retrieving a specific badge.
        """
        url = reverse('badges-detail', args=[self.badge1.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Badge 1')
        self.assertEqual(response.data['description'], 'First badge')
        self.assertEqual(response.data['image']['id'], self.image1.id)

    def test_update_badge(self):
        """
        Test updating an existing badge.
        """
        url = reverse('badges-detail', args=[self.badge1.id])
        data = {
            'description': 'Updated first badge',
            'image_id': self.image2.id
        }
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        updated_badge = Badge.objects.get(id=self.badge1.id)
        self.assertEqual(updated_badge.description, 'Updated first badge')
        self.assertEqual(updated_badge.image, self.image2)

    def test_delete_badge(self):
        """
        Test deleting a badge.
        """
        url = reverse('badges-detail', args=[self.badge1.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Badge.objects.filter(id=self.badge1.id).exists())

    def test_create_badge_invalid_missing_image(self):
        """
        Test creating a badge without providing an image should fail.
        """
        url = reverse('badges-list')
        data = {
            'name': 'Badge 4',
            'description': 'Fourth badge',
            'type': 'Course Type',
            'condition': 'Complete Course 4',
            # 'image_id' is missing
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('image_id', response.data)

    def test_permission_required_for_badge_endpoints(self):
        """
        Test that unauthenticated users cannot access badge endpoints.
        """
        self.client.logout()

        # List endpoint
        url = reverse('badges-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Detail endpoint
        url = reverse('badges-detail', args=[self.badge1.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Create endpoint
        url = reverse('badges-list')
        data = {
            'name': 'Badge 5',
            'description': 'Fifth badge',
            'type': 'Course Type',
            'condition': 'Complete Course 5',
            'image_id': self.image1.id
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class UserQuestBadgeViewSetTest(BaseViewTest):

    def test_list_user_quest_badges(self):
        """
        Test that the list endpoint returns all user quest badges.
        """
        url = reverse('user-quest-badges-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should include both badges
        self.assertEqual(len(response.data), 2)
        badge_names = [badge['badge']['name'] for badge in response.data]
        self.assertIn('Badge 1', badge_names)
        self.assertIn('Badge 2', badge_names)

    def test_create_user_quest_badge(self):
        """
        Test creating a new user quest badge.
        """
        url = reverse('user-quest-badges-list')
        data = {
            'badge_id': self.badge1.id,
            'user_quest_attempt_id': self.attempt1.id,
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(UserQuestBadge.objects.count(), 3)
        new_badge = UserQuestBadge.objects.get(id=response.data['id'])
        self.assertEqual(new_badge.badge, self.badge1)
        self.assertEqual(new_badge.user_quest_attempt, self.attempt1)

    def test_retrieve_user_quest_badge(self):
        """
        Test retrieving a specific user quest badge.
        """
        url = reverse('user-quest-badges-detail', args=[self.user_quest_badge1.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['badge']['name'], 'Badge 1')
        self.assertEqual(response.data['user_quest_attempt']['id'], self.attempt1.id)

    def test_update_user_quest_badge(self):
        """
        Test updating an existing user quest badge.
        """
        url = reverse('user-quest-badges-detail', args=[self.user_quest_badge1.id])
        data = {
            'badge_id': self.badge2.id,  # Change badge
        }
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        updated_badge = UserQuestBadge.objects.get(id=self.user_quest_badge1.id)
        self.assertEqual(updated_badge.badge, self.badge2)

    def test_delete_user_quest_badge(self):
        """
        Test deleting a user quest badge.
        """
        url = reverse('user-quest-badges-detail', args=[self.user_quest_badge1.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(UserQuestBadge.objects.filter(id=self.user_quest_badge1.id).exists())

    def test_by_user_action(self):
        """
        Test the custom 'by_user' action to filter user quest badges by user.
        """
        url = reverse('user-quest-badges-by-user')
        response = self.client.get(url, {'user_id': self.student1.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should include both badges
        self.assertEqual(len(response.data), 2)
        badge_names = [badge['badge']['name'] for badge in response.data]
        self.assertIn('Badge 1', badge_names)
        self.assertIn('Badge 2', badge_names)

    def test_by_user_action_no_badges(self):
        """
        Test the 'by_user' action when the user has no badges.
        """
        new_user = EduquestUserFactory(username='student3', email='student3@example.com')
        url = reverse('user-quest-badges-by-user')
        response = self.client.get(url, {'user_id': new_user.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_permission_required_for_user_quest_badge_endpoints(self):
        """
        Test that unauthenticated users cannot access user quest badge endpoints.
        """
        self.client.logout()

        # List endpoint
        url = reverse('user-quest-badges-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Detail endpoint
        url = reverse('user-quest-badges-detail', args=[self.user_quest_badge1.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Custom action
        url = reverse('user-quest-badges-by-user')
        response = self.client.get(url, {'user_id': self.student1.id})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class UserCourseBadgeViewSetTest(BaseViewTest):

    def test_list_user_course_badges(self):
        """
        Test that the list endpoint returns all user course badges.
        """
        url = reverse('user-course-badges-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should include both course badges
        self.assertEqual(len(response.data), 2)
        badge_names = [badge['badge']['name'] for badge in response.data]
        self.assertIn('Badge 3', badge_names)
        self.assertIn('Badge 4', badge_names)

    def test_create_user_course_badge(self):
        """
        Test creating a new user course badge.
        """
        url = reverse('user-course-badges-list')
        data = {
            'badge_id': self.badge1.id,
            'user_course_group_enrollment_id': self.enrollment2.id,
            'awarded_date': '2023-10-03T10:00:00Z'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(UserCourseBadge.objects.count(), 3)
        new_badge = UserCourseBadge.objects.get(id=response.data['id'])
        self.assertEqual(new_badge.badge, self.badge1)
        self.assertEqual(new_badge.user_course_group_enrollment, self.enrollment2)

    def test_retrieve_user_course_badge(self):
        """
        Test retrieving a specific user course badge.
        """
        url = reverse('user-course-badges-detail', args=[self.user_course_badge1.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['badge']['name'], 'Badge 3')
        self.assertEqual(response.data['user_course_group_enrollment']['id'], self.enrollment1.id)

    def test_update_user_course_badge(self):
        """
        Test updating an existing user course badge.
        """
        url = reverse('user-course-badges-detail', args=[self.user_course_badge1.id])
        data = {
            'badge_id': self.badge2.id,  # Change badge
            'awarded_date': '2023-10-04T14:00:00Z'
        }
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        updated_badge = UserCourseBadge.objects.get(id=self.user_course_badge1.id)
        self.assertEqual(updated_badge.badge, self.badge2)

    def test_delete_user_course_badge(self):
        """
        Test deleting a user course badge.
        """
        url = reverse('user-course-badges-detail', args=[self.user_course_badge1.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(UserCourseBadge.objects.filter(id=self.user_course_badge1.id).exists())

    def test_by_user_action(self):
        """
        Test the custom 'by_user' action to filter user course badges by user.
        """
        url = reverse('user-course-badges-by-user')
        response = self.client.get(url, {'user_id': self.student1.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should include badge1
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['badge']['name'], 'Badge 3')

        response = self.client.get(url, {'user_id': self.student2.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should include badge2
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['badge']['name'], 'Badge 4')

    def test_by_user_action_no_badges(self):
        """
        Test the 'by_user' action when the user has no badges.
        """
        new_user = EduquestUserFactory(username='student3', email='student3@example.com')
        url = reverse('user-course-badges-by-user')
        response = self.client.get(url, {'user_id': new_user.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_permission_required_for_user_course_badge_endpoints(self):
        """
        Test that unauthenticated users cannot access user course badge endpoints.
        """
        self.client.logout()

        # List endpoint
        url = reverse('user-course-badges-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Detail endpoint
        url = reverse('user-course-badges-detail', args=[self.user_course_badge1.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Custom action
        url = reverse('user-course-badges-by-user')
        response = self.client.get(url, {'user_id': self.student1.id})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
