from collections import defaultdict

from django.db import transaction
from rest_framework import viewsets
from rest_framework import generics
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from django.http import JsonResponse
from datetime import timedelta
from django.db.models import Count, Q, Max, Avg, Prefetch
from .excel import Excel
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from django.db.models import Sum, F, ExpressionWrapper, DurationField
from .models import (
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
from .serializers import (
    EduquestUserSerializer,
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

User = get_user_model()


class EduquestUserViewSet(viewsets.ModelViewSet):
    queryset = EduquestUser.objects.all().order_by('-id')
    serializer_class = EduquestUserSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def by_email(self, request):
        email = request.query_params.get('email')
        queryset = EduquestUser.objects.get(email=email)
        serializer = EduquestUserSerializer(queryset)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def by_admin(self, request):
        queryset = EduquestUser.objects.filter(is_staff=True).order_by('-id')
        serializer = EduquestUserSerializer(queryset, many=True)
        return Response(serializer.data)


class AcademicYearViewSet(viewsets.ModelViewSet):
    queryset = AcademicYear.objects.all().order_by('-id')
    serializer_class = AcademicYearSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def non_private(self, request):
        queryset = AcademicYear.objects.exclude(start_year=0).order_by('-id')
        serializer = AcademicYearSerializer(queryset, many=True)
        return Response(serializer.data)


class TermViewSet(viewsets.ModelViewSet):
    queryset = Term.objects.all().order_by('-id')
    serializer_class = TermSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def non_private(self, request):
        queryset = Term.objects.exclude(name='Private Term').order_by('-id')
        serializer = TermSerializer(queryset, many=True)
        return Response(serializer.data)


class ImageViewSet(viewsets.ModelViewSet):
    queryset = Image.objects.all().order_by('-id')
    serializer_class = ImageSerializer
    permission_classes = [IsAuthenticated]


class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all().order_by('-id')
    serializer_class = CourseSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def non_private(self, request):
        queryset = Course.objects.exclude(type='Private').order_by('-id')
        serializer = CourseSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def by_enrolled_user(self, request):
        user_id = request.query_params.get('user_id')
        # Get the course group enrollments for the given user
        course_group_enrollments = UserCourseGroupEnrollment.objects.filter(student_id=user_id)
        # Extract the course IDs from the related course groups
        course_ids = CourseGroup.objects.filter(
            id__in=course_group_enrollments.values_list('course_group', flat=True)
        ).values_list('course_id', flat=True)
        # Query the courses excluding Private courses
        queryset = Course.objects.exclude(type='Private').filter(id__in=course_ids).order_by('-id')

        # Serialize the results
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class CourseGroupViewSet(viewsets.ModelViewSet):
    queryset = CourseGroup.objects.all().order_by('-id')
    serializer_class = CourseGroupSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def by_course(self, request):
        course_id = request.query_params.get('course_id')
        queryset = CourseGroup.objects.filter(course=course_id).order_by('-id')
        serializer = CourseGroupSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def by_private_course(self, request):
        queryset = CourseGroup.objects.filter(course__type='Private').order_by('-id')
        serializer = CourseGroupSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def non_private(self, request):
        queryset = CourseGroup.objects.exclude(course__type='Private').order_by('-id')
        serializer = CourseGroupSerializer(queryset, many=True)
        return Response(serializer.data)


class UserCourseGroupEnrollmentViewSet(viewsets.ModelViewSet):
    queryset = UserCourseGroupEnrollment.objects.all().order_by('-id')
    serializer_class = UserCourseGroupEnrollmentSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def by_course_group_and_user(self, request):
        course_group_id = request.query_params.get('course_group_id')
        user_id = request.query_params.get('user_id')
        queryset = UserCourseGroupEnrollment.objects.filter(course_group=course_group_id, student=user_id).order_by(
            '-id')
        serializer = UserCourseGroupEnrollmentSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def by_course_and_user(self, request):
        course_id = request.query_params.get('course_id')
        user_id = request.query_params.get('user_id')
        queryset = UserCourseGroupEnrollment.objects.filter(course_group__course=course_id, student=user_id).order_by(
            '-id')
        serializer = UserCourseGroupEnrollmentSerializer(queryset, many=True)
        return Response(serializer.data)


class QuestViewSet(viewsets.ModelViewSet):
    queryset = Quest.objects.all().order_by('-id')
    serializer_class = QuestSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def non_private(self, request):
        queryset = Quest.objects.exclude(type='Private').order_by('-id')
        serializer = QuestSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def private_by_user(self, request):
        user = request.user
        queryset = Quest.objects.filter(organiser=user, type='Private').order_by('-id')
        serializer = QuestSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def by_enrolled_user(self, request):
        user_id = request.query_params.get('user_id')
        # Get all course group enrollments for the user
        course_group_enrollments = UserCourseGroupEnrollment.objects.filter(student=user_id)
        # Get all quests for the course groups
        queryset = Quest.objects.filter(
            course_group__in=course_group_enrollments.values('course_group')
        ).order_by('-id')
        serializer = QuestSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def by_course_group(self, request):
        course_group_id = request.query_params.get('course_group_id')
        queryset = Quest.objects.filter(course_group=course_group_id).order_by('-id')
        serializer = QuestSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def import_quest(self, request):
        try:
            excel_file = request.FILES.get('file')
        except Exception as e:
            return Response(
                {"Error processing excel file": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not excel_file:
            return Response(
                {"No file provided, please try again"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            excel = Excel()
            excel.read_excel_sheets(excel_file)
            questions_data = excel.get_questions()
            users_data = excel.get_users()
        except Exception as e:
            return Response(
                {"Error processing excel file": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Extract other form data
            quest_data = {
                'type': request.data.get('type'),
                'name': request.data.get('name'),
                'description': request.data.get('description'),
                'status': request.data.get('status'),
                'max_attempts': request.data.get('max_attempts'),
                'course_group_id': request.data.get('course_group_id'),
                'tutorial_date': request.data.get('tutorial_date'),
                'image_id': request.data.get('image_id'),
                'organiser_id': request.data.get('organiser_id')
            }
        except Exception as e:
            return Response(
                {"Error extracting form data": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Use atomic transaction to ensure data integrity
        with transaction.atomic():
            try:
                # Create a Quest object
                quest_serializer = QuestSerializer(data=quest_data)
                quest_serializer.is_valid(raise_exception=True)
                quest = quest_serializer.save()
                new_quest_id = quest.id
                course_group = quest_serializer.data.get('course_group')

                questions_serializer = []
                # Process each question in the questions_data list
                for question_data in questions_data:
                    question_data['quest_id'] = new_quest_id
                    question_serializer = QuestionSerializer(data=question_data)
                    question_serializer.is_valid(raise_exception=True)
                    question = question_serializer.save()
                    questions_serializer.append(question_serializer.data)

                # Enroll users and create UserQuestAttempt and UserAnswerAttempt objects
                for user_data in users_data:
                    user, created = EduquestUser.objects.get_or_create(
                        email=user_data['email'],
                        defaults={
                            'email': user_data['email'],
                            'username': user_data['username'],
                            'nickname': user_data['username']
                        }
                    )

                    # Enroll the user in the course group
                    enrollment, enrolled = UserCourseGroupEnrollment.objects.get_or_create(
                        student=user,
                        course_group_id=course_group['id']
                    )

                    # Create a UserQuestAttempt object
                    user_quest_attempt_data = {
                        'student_id': user.id,
                        'quest_id': new_quest_id
                    }
                    user_quest_attempt_serializer = UserQuestAttemptSerializer(data=user_quest_attempt_data)
                    user_quest_attempt_serializer.is_valid(raise_exception=True)
                    user_quest_attempt = user_quest_attempt_serializer.save()
                    new_user_quest_attempt_id = user_quest_attempt.id

                    # Get the generated empty-prefilled UserAnswerAttempt objects for the UserQuestAttempt
                    user_answer_attempts = UserAnswerAttempt.objects.filter(user_quest_attempt=new_user_quest_attempt_id)
                    # Update selected answers based on Excel data
                    try:
                        for user_answer_attempt in user_answer_attempts:
                            selected_answers = excel.get_user_answer_attempts(user.email)
                            for selected_answer in selected_answers:
                                if selected_answer['question'] == user_answer_attempt.question.text:
                                    if user_answer_attempt.answer.text in selected_answer['selected_answers']:
                                        user_answer_attempt.is_selected = True
                                        user_answer_attempt.save()
                    except Exception as e:
                        raise ValidationError({"Error updating selected answers": str(e)})

            except ValidationError as ve:
                return Response(
                    {"Validation Error": ve.detail},
                    status=status.HTTP_400_BAD_REQUEST
                )
            except Exception as e:
                return Response(
                    {"Error creating quest": str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )

        return Response(questions_serializer, status=status.HTTP_201_CREATED)


class QuestionViewSet(viewsets.ModelViewSet):
    queryset = Question.objects.all().order_by('-id')
    serializer_class = QuestionSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        # Check if the request contains a list (bulk create)
        if isinstance(request.data, list):
            # Many=True indicates we're expecting a list of data
            serializer = self.get_serializer(data=request.data, many=True)
            serializer.is_valid(raise_exception=True)

            # Save all the questions (bulk creation)
            self.perform_create(serializer)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        # Fallback to single object creation
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save()


class AnswerViewSet(viewsets.ModelViewSet):
    queryset = Answer.objects.all().order_by('-id')
    serializer_class = AnswerSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['put'], url_path='bulk-update')
    def bulk_update(self, request):
        # Ensure the request data is a list
        if not isinstance(request.data, list):
            return Response({"error": "Expected a list of items."}, status=status.HTTP_400_BAD_REQUEST)

        # Initialize the serializer with 'many=True'
        serializer = self.get_serializer(data=request.data, many=True)
        serializer.is_valid(raise_exception=True)

        # Extract the validated data
        validated_data = serializer.validated_data

        # Collect the IDs of the answers to update
        answer_ids = [item['id'] for item in validated_data]

        # Retrieve the existing answers from the database
        answers = Answer.objects.filter(id__in=answer_ids)

        # Map existing answers by ID for easy lookup
        answer_dict = {answer.id: answer for answer in answers}

        updated_answers = []
        for item in validated_data:
            answer_id = item.get('id')
            if answer_id in answer_dict:
                answer_instance = answer_dict[answer_id]
                # Update the fields
                for attr, value in item.items():
                    setattr(answer_instance, attr, value)
                answer_instance.save()
                updated_answers.append(answer_instance)
            else:
                return Response({"error": f"Answer with id {answer_id} does not exist."},
                                status=status.HTTP_404_NOT_FOUND)

        # Serialize the updated answers to return in the response
        output_serializer = self.get_serializer(updated_answers, many=True)
        return Response(output_serializer.data, status=status.HTTP_200_OK)


class UserQuestAttemptViewSet(viewsets.ModelViewSet):
    queryset = UserQuestAttempt.objects.all().order_by('-id')
    serializer_class = UserQuestAttemptSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def by_user_quest(self, request):
        quest_id = request.query_params.get('quest_id')
        user_id = request.query_params.get('user_id')
        queryset = UserQuestAttempt.objects.filter(student=user_id, quest=quest_id).order_by('-id')
        serializer = UserQuestAttemptSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def by_quest(self, request):
        quest_id = request.query_params.get('quest_id')
        queryset = UserQuestAttempt.objects.filter(quest=quest_id).order_by('-id')
        serializer = UserQuestAttemptSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def set_all_attempts_submitted_by_quest(self, request):
        quest_id = request.query_params.get('quest_id')
        queryset = UserQuestAttempt.objects.filter(quest=quest_id)
        for instance in queryset:
            instance.submitted = True
            instance.save()
        return Response({"message": f"All attempts for quest {quest_id} have been marked as submitted."})


    @action(detail=False, methods=['patch'], url_path='bulk-update')
    def bulk_update(self, request, *args, **kwargs):
        """
        Bulk update UserQuestAttempt
        """
        if isinstance(request.data, list):
            updated_attempts = []
            for attempt_data in request.data:
                attempt_id = attempt_data.get('id')
                if not attempt_id:
                    return Response({"error": "ID is required for each attempt."}, status=status.HTTP_400_BAD_REQUEST)

                try:
                    # Retrieve the instance to update
                    attempt_instance = UserQuestAttempt.objects.get(id=attempt_id)
                except UserQuestAttempt.DoesNotExist:
                    return Response({"error": f"UserQuestAttempt with id {attempt_id} not found."},
                                    status=status.HTTP_404_NOT_FOUND)

                # Use the existing serializer for each update
                serializer = self.get_serializer(instance=attempt_instance, data=attempt_data, partial=True)
                if serializer.is_valid():
                    serializer.save()
                    updated_attempts.append(serializer.data)
                else:
                    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            return Response({"updated_attempts": updated_attempts}, status=status.HTTP_200_OK)

        return Response({"error": "Expected a list of data."}, status=status.HTTP_400_BAD_REQUEST)


class UserAnswerAttemptViewSet(viewsets.ModelViewSet):
    queryset = UserAnswerAttempt.objects.all().order_by('-id')
    serializer_class = UserAnswerAttemptSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def by_user_quest_attempt(self, request):
        user_quest_attempt_id = request.query_params.get('user_quest_attempt_id')
        queryset = UserAnswerAttempt.objects.filter(user_quest_attempt=user_quest_attempt_id).order_by('-id')
        serializer = UserAnswerAttemptSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def by_quest(self, request):
        quest_id = request.query_params.get('quest_id')
        queryset = UserAnswerAttempt.objects.filter(user_quest_attempt__quest=quest_id).order_by('-id')
        serializer = UserAnswerAttemptSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['patch'], url_path='bulk-update')
    def bulk_update(self, request, *args, **kwargs):
        """
        Bulk update UserAnswerAttempt
        """
        if isinstance(request.data, list):
            updated_attempts = []
            for attempt_data in request.data:
                attempt_id = attempt_data.get('id')
                if not attempt_id:
                    return Response({"error": "ID is required for each attempt."}, status=status.HTTP_400_BAD_REQUEST)

                try:
                    # Retrieve the instance to update
                    attempt_instance = UserAnswerAttempt.objects.get(id=attempt_id)
                except UserAnswerAttempt.DoesNotExist:
                    return Response({"error": f"UserAnswerAttempt with id {attempt_id} not found."},
                                    status=status.HTTP_404_NOT_FOUND)

                # Use the existing serializer for each update
                serializer = self.get_serializer(instance=attempt_instance, data=attempt_data, partial=True)
                if serializer.is_valid():
                    serializer.save()
                    updated_attempts.append(serializer.data)
                else:
                    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            return Response({"updated_attempts": updated_attempts}, status=status.HTTP_200_OK)

        return Response({"error": "Expected a list of data."}, status=status.HTTP_400_BAD_REQUEST)


class BadgeViewSet(viewsets.ModelViewSet):
    queryset = Badge.objects.all().order_by('-id')
    serializer_class = BadgeSerializer
    permission_classes = [IsAuthenticated]


class UserQuestBadgeViewSet(viewsets.ModelViewSet):
    queryset = UserQuestBadge.objects.all().order_by('-id')
    serializer_class = UserQuestBadgeSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def by_user(self, request):
        user_id = request.query_params.get('user_id')
        queryset = UserQuestBadge.objects.filter(user_quest_attempt__student=user_id).order_by('-id')
        serializer = UserQuestBadgeSerializer(queryset, many=True)
        return Response(serializer.data)


class UserCourseBadgeViewSet(viewsets.ModelViewSet):
    queryset = UserCourseBadge.objects.all().order_by('-id')
    serializer_class = UserCourseBadgeSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def by_user(self, request):
        user_id = request.query_params.get('user_id')
        queryset = UserCourseBadge.objects.filter(user_course_group_enrollment__student=user_id).order_by('-id')
        serializer = UserCourseBadgeSerializer(queryset, many=True)
        return Response(serializer.data)


class DocumentViewSet(viewsets.ModelViewSet):
    queryset = Document.objects.all().order_by('-id')
    serializer_class = DocumentSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def by_user(self, request):
        user_id = request.query_params.get('user_id')
        queryset = Document.objects.filter(uploaded_by=user_id).order_by('-id')
        serializer = DocumentSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def upload(self, request):
        try:
            file = request.FILES.get('file')
            if not file:
                return Response({"No file provided, please try again"}, status=status.HTTP_400_BAD_REQUEST)
            data = {
                'uploaded_by': request.user.id,
                'file': file,
                'name': request.data.get('name'),
                'size': request.data.get('size'),
            }
            serializer = DocumentSerializer(data=data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"Error uploading document": str(e)}, status=status.HTTP_400_BAD_REQUEST)


#
# # class EduquestUserListCreateView(generics.ListCreateAPIView):
# #     permission_classes = [IsAuthenticated]
# #
# #     queryset = EduquestUser.objects.all().order_by('-id')
# #     serializer_class = EduquestUserSerializer
#
#
# # class EduquestUserManageView(generics.RetrieveUpdateDestroyAPIView):
# #     permission_classes = [IsAuthenticated]
# #
# #     queryset = EduquestUser.objects.all().order_by('-id')
# #     serializer_class = EduquestUserSerializer
# #
# #     def get_object(self):
# #         email = self.kwargs.get('email')
# #         return get_object_or_404(EduquestUser, email=email)
#
#
# class ImageListCreateView(generics.ListCreateAPIView):
#     permission_classes = [IsAuthenticated]
#
#     queryset = Image.objects.all().order_by('-id')
#     serializer_class = ImageSerializer
#
#
# class ImageManageView(generics.RetrieveUpdateDestroyAPIView):
#     permission_classes = [IsAuthenticated]
#
#     queryset = Image.objects.all().order_by('-id')
#     serializer_class = ImageSerializer
#
#
# class AcademicYearListCreateView(generics.ListCreateAPIView):
#     permission_classes = [IsAuthenticated]
#
#     queryset = AcademicYear.objects.all().order_by('-id')
#     serializer_class = AcademicYearSerializer
#
#
# class AcademicYearManageView(generics.RetrieveUpdateDestroyAPIView):
#     permission_classes = [IsAuthenticated]
#
#     queryset = AcademicYear.objects.all().order_by('-id')
#     serializer_class = AcademicYearSerializer
#
#
# class TermListCreateView(generics.ListCreateAPIView):
#     permission_classes = [IsAuthenticated]
#
#     queryset = Term.objects.all().order_by('-id')
#     serializer_class = TermSerializer
#
#
# class TermManageView(generics.RetrieveUpdateDestroyAPIView):
#     permission_classes = [IsAuthenticated]
#
#     queryset = Term.objects.all().order_by('-id')
#     serializer_class = TermSerializer
#
#
# class CourseListCreateView(generics.ListCreateAPIView):
#     permission_classes = [IsAuthenticated]
#
#     queryset = Course.objects.all().order_by('-id')
#     serializer_class = CourseSerializer
#
#
# class NonPrivateCourseListCreateView(generics.ListCreateAPIView):
#     permission_classes = [IsAuthenticated]
#
#     queryset = Course.objects.exclude(type='Private').order_by('-id')
#     serializer_class = CourseSerializer
#
#
# class CourseManageView(generics.RetrieveUpdateDestroyAPIView):
#     permission_classes = [IsAuthenticated]
#
#     queryset = Course.objects.all().order_by('-id')
#     serializer_class = CourseSerializer
#
#
# # class CourseByTermView(generics.ListAPIView):
# #     permission_classes = [IsAuthenticated]
# #     serializer_class = CourseSerializer
# #
# #     def get_queryset(self):
# #         term_id = self.kwargs['term_id']
# #         return Course.objects.filter(term=term_id).order_by('-id')
#
#
# # class CourseByUserView(generics.ListAPIView):
# #     permission_classes = [IsAuthenticated]
# #     serializer_class = CourseSerializer
# #
# #     def get_queryset(self):
# #         user_id = self.kwargs['user_id']
# #         return Course.objects.filter(enrolled_users__user=user_id).order_by('-id')
#
#
# # class CourseGroupListCreateView(generics.ListCreateAPIView):
# #     permission_classes = [IsAuthenticated]
# #
# #     queryset = CourseGroup.objects.all().order_by('-id')
# #     serializer_class = CourseGroupSerializer
# #
# #
# # class CourseGroupManageView(generics.RetrieveUpdateDestroyAPIView):
# #     permission_classes = [IsAuthenticated]
# #
# #     queryset = CourseGroup.objects.all().order_by('-id')
# #     serializer_class = CourseGroupSerializer
# #
# #
# # class UserCourseGroupEnrollmentListCreateView(generics.ListCreateAPIView):
# #     permission_classes = [IsAuthenticated]
# #
# #     queryset = UserCourseGroupEnrollment.objects.all().order_by('-id')
# #     serializer_class = UserCourseGroupEnrollmentSerializer
#
#     # def perform_create(self, serializer):
#     #     user = self.request.data.get('user')
#     #     if user and isinstance(user, dict):
#     #         user_id = user['id']
#     #         user = EduquestUser.objects.get(id=user_id)
#     #     course = self.request.data.get('course')
#     #     if course and isinstance(course, dict):
#     #         course_id = course['id']
#     #         course = Course.objects.get(id=course_id)
#     #     if UserCourseGroupEnrollmentSerializer.objects.filter(user=user, course=course).exists():
#     #         return  # Do nothing if the user is already enrolled in the course
#     #     serializer.save()
#
#
# # class UserCourseGroupEnrollmentManageView(generics.RetrieveUpdateDestroyAPIView):
# #     permission_classes = [IsAuthenticated]
# #
# #     queryset = UserCourseGroupEnrollment.objects.all().order_by('-id')
# #     serializer_class = UserCourseGroupEnrollmentSerializer
#
#
# class QuestImportView(APIView):
#     parser_classes = (MultiPartParser, FormParser)
#
#     def post(self, request, *args, **kwargs):
#
#         excel_file = request.FILES.get('file')
#         if not excel_file:
#             return JsonResponse(data={"No file provided, please try again"}, status=400)
#         try:
#             excel = Excel()
#             excel.read_excel_sheets(excel_file)
#             questions_data = excel.get_questions()
#             users_data = excel.get_users()
#         except Exception as e:
#             return JsonResponse(data={"Error processing excel file": str(e)}, status=400)
#
#         # Extract other form data
#         quest_data = {
#             'type': request.data.get('type'),
#             'name': request.data.get('name'),
#             'description': request.data.get('description'),
#             'status': request.data.get('status'),
#             'max_attempts': request.data.get('max_attempts'),
#             'course_group_id': request.data.get('course_group_id'),
#             'image_id': request.data.get('image_id'),
#             'organiser_id': request.data.get('organiser_id')
#         }
#         # Create a Quest object
#         quest_serializer = QuestSerializer(data=quest_data)
#
#         if quest_serializer.is_valid():
#             # Save the Quest object
#             quest_serializer.save()
#             # Get the ID of the newly created Quest object
#             new_quest_id = quest_serializer.data.get('id')
#             print(f"New Quest ID: {new_quest_id}")
#             course_group = quest_serializer.data.get('course_group')
#             course = Course.objects.get(id=course_group['id'])
#
#             questions_serializer = []
#             # Process each question in the questions_data list
#             for question_data in questions_data:
#                 # Extract question data
#                 question_data['quest'] = new_quest_id
#                 # Create a Question object for each question
#                 question_serializer = QuestionSerializer(data=question_data)
#                 if question_serializer.is_valid():
#                     question_serializer.save()
#                     # Return the question data
#                     questions_serializer.append(question_serializer.data)
#                 else:
#                     return Response(data={"Error creating questions": question_serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
# #
#             # Create UserQuestAttempt object (auto-generate UserAnswerAttempt objects)
#             for user_data in users_data:
#                 # Create a User object
#                 user, created = EduquestUser.objects.get_or_create(
#                     email=user_data['email'],
#                     defaults={
#                         'email': user_data['email'],
#                         'username': user_data['username'],
#                         'nickname': user_data['username']
#                     }
#                 )
#                 # Enroll the users in the course_group if they are not already enrolled
#                 UserCourseGroupEnrollment.objects.get_or_create(
#                     user=user,
#                     course_group=course_group
#                 )
# #
#                 # Create a UserQuestAttempt object for each User
#                 user_quest_attempt_data = {
#                     'student_id': user.id,
#                     'quest_id': new_quest_id
#                 }
#                 user_quest_attempt_serializer = UserQuestAttemptSerializer(data=user_quest_attempt_data)
#                 if user_quest_attempt_serializer.is_valid():
#                     user_quest_attempt_serializer.save()
#                     # Get the ID of the newly created UserQuestAttempt object
#                     new_user_quest_attempt_id = user_quest_attempt_serializer.data.get('id')
#                     print(f"New UserQuestAttempt ID: {new_user_quest_attempt_id}")
#                     # print(f"User question attempts: {user_question_attempts}")
#                 else:
#                     return Response(data={"Error user quest attempt template": user_quest_attempt_serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
#
#                 # Create UserAnswerAttempt objects for each UserQuestAttempt
#                 for question_serializer in questions_serializer:
#                     # Iterate through each answer record in selected_answers
#                     for answer_serializer in question_serializer['answers']:
#                         user_answer_attempt_data = {
#                             'user_quest_attempt_id': new_user_quest_attempt_id,
#                             'question_id': question_serializer['id'],
#                             'answer_id': answer_serializer['id'],
#                             'is_selected': False
#                         }
#                         user_answer_attempt_serializer = UserAnswerAttemptSerializer(data=user_answer_attempt_data)
#                         if user_answer_attempt_serializer.is_valid():
#                             user_answer_attempt_serializer.save()
#                         else:
#                             return Response(data={"Error creating user answer attempts": user_answer_attempt_serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
#
#                 user_answer_attempts = UserAnswerAttempt.objects.filter(user_quest_attempt=new_user_quest_attempt_id)
#                 try:
#                     # Iterate through each user_answer_attempts question
#                     for user_answer_attempt in user_answer_attempts:
#                         print(f"User question attempt: {user_answer_attempt.question.text}")
#                         # Get the wooclap_questions_selected_answers for the user
#                         print(f"User: {user.email}")
#                         wooclap_questions_selected_answers = excel.get_user_answer_attempts(user.email)
#                         print(f"Wooclap questions selected answers: {wooclap_questions_selected_answers}")
#                         # Iterate through each wooclap_question_selected_answers
#                         for wooclap_question_selected_answers in wooclap_questions_selected_answers:
#                             # print(f"Wooclap question selected answers: {wooclap_question_selected_answers}")
#                             # If the question in the wooclap_question_selected_answers matches
#                             # the user_question_attempt question
#                             """
#                             wooclap_question_selected_answers
#                             {
#                                 'question': 'What is the primary key in a database?',
#                                 'selected_answers': ['A field in a table that uniquely identifies each row']
#                             }
#                             """
#                             if wooclap_question_selected_answers['question'] == user_answer_attempt.question.text:
#
# #                                 # Get the AttemptAnswerRecord objects for the user_question_attempt
# #                                 answer_records = AttemptAnswerRecord.objects.filter(user_quest_question_attempt=user_question_attempt.id)
# #
#                                 # Iterate through each answer record in selected_answers
#                                 for wooclap_selected_answer in wooclap_question_selected_answers['selected_answers']:
#                                     # Iterate through each 'empty' attempted answer records in the system
# #                                     for answer_record in answer_records:
#                                         # If the answer in the user_answer_attempt  matches the selected answer in wooclap
#                                         if user_answer_attempt.answer.text == wooclap_selected_answer:
#                                             # print(f"Selected answer: {selected_answer.answer.text}")
#                                             user_answer_attempt.is_selected = True
#                                             user_answer_attempt.save()
#                 except Exception as e:
#                     return Response(data={"Error updating selected answers": str(e)}, status=status.HTTP_400_BAD_REQUEST)
# #
#             return Response(questions_serializer, status=status.HTTP_201_CREATED)
#         else:
#             return Response(data={"Error creating quest": quest_serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
#
#
# class QuestListCreateView(generics.ListCreateAPIView):
#     permission_classes = [IsAuthenticated]
#
#     queryset = Quest.objects.all().order_by('-id')
#     serializer_class = QuestSerializer
#
#
# class QuestManageView(generics.RetrieveUpdateDestroyAPIView):
#     permission_classes = [IsAuthenticated]
#
#     queryset = Quest.objects.all().order_by('-id')
#     serializer_class = QuestSerializer
#
#
# class QuestByCourseView(generics.ListAPIView):
#     permission_classes = [IsAuthenticated]
#     serializer_class = QuestSerializer
#
#     def get_queryset(self):
#         course_id = self.kwargs['course_id']
#         return Quest.objects.filter(from_course=course_id).order_by('-id')
#
#
# class PrivateQuestByUserView(generics.ListAPIView):
#     permission_classes = [IsAuthenticated]
#     serializer_class = QuestSerializer
#
#     def get_queryset(self):
#         user = self.request.user
#         return Quest.objects.filter(organiser=user, type='Private').order_by('-id')
#
#
# class QuestByEnrolledUser(generics.ListAPIView):
#     permission_classes = [IsAuthenticated]
#     serializer_class = QuestSerializer
#
#     def get_queryset(self):
#         user_id = self.kwargs['user_id']
#         return Quest.objects.filter(from_course__enrolled_users__user=user_id).distinct().order_by('-id')
#
# class QuestionListCreateView(generics.ListCreateAPIView):
#     permission_classes = [IsAuthenticated]
#
#     queryset = Question.objects.all().order_by('-id')
#     serializer_class = QuestionSerializer
#
#
# class QuestionManageView(generics.RetrieveUpdateDestroyAPIView):
#     permission_classes = [IsAuthenticated]
#
#     queryset = Question.objects.all().order_by('-id')
#     serializer_class = QuestionSerializer
#
#
# class QuestionByQuestView(generics.ListAPIView):
#     permission_classes = [IsAuthenticated]
#     serializer_class = QuestionSerializer
#
#     def get_queryset(self):
#         quest_id = self.kwargs['quest_id']
#         return Question.objects.filter(from_quest=quest_id).order_by('number')
#
#
# class BulkCreateQuestionView(APIView):
#     def post(self, request, *args, **kwargs):
#         serializer = QuestionSerializer(data=request.data, many=True)
#         if serializer.is_valid():
#             serializer.save()
#             return Response(serializer.data, status=status.HTTP_201_CREATED)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
#
#
# class BulkUpdateQuestionView(APIView):
#     def patch(self, request, *args, **kwargs):
#         serializer = QuestionSerializer(data=request.data, many=True)
#
#         if serializer.is_valid():
#             ids = [item.get('id') for item in request.data if 'id' in item]
#             instances = Question.objects.filter(id__in=ids)
#
#             # Add logging to debug
#             print(f"Question Instances found: {[instance.id for instance in instances]}")
#
#             if len(instances) != len(ids):
#                 return Response({"detail": "One or more instances not found."}, status=status.HTTP_404_NOT_FOUND)
#
#             serializer.update(instances, serializer.validated_data)
#             return Response(serializer.data, status=status.HTTP_200_OK)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
#
#
# class AnswerListCreateView(generics.ListCreateAPIView):
#     permission_classes = [IsAuthenticated]
#
#     queryset = Answer.objects.all().order_by('-id')
#     serializer_class = AnswerSerializer
#
#
# class AnswerManageView(generics.RetrieveUpdateDestroyAPIView):
#     permission_classes = [IsAuthenticated]
#
#     queryset = Answer.objects.all().order_by('-id')
#     serializer_class = AnswerSerializer
#
#
# class AnswerByQuestView(generics.ListAPIView):
#     permission_classes = [IsAuthenticated]
#     serializer_class = AnswerSerializer
#
#     def get_queryset(self):
#         quest_id = self.kwargs['quest_id']
#         questions = Question.objects.filter(from_quest=quest_id).order_by('number')
#         return Answer.objects.filter(question__in=questions).order_by('-id')
#
#
# class UserQuestAttemptListCreateView(generics.ListCreateAPIView):
#     permission_classes = [IsAuthenticated]
#
#     queryset = UserQuestAttempt.objects.all().order_by('-id')
#     serializer_class = UserQuestAttemptSerializer
#
#
# class UserQuestAttemptManageView(generics.RetrieveUpdateDestroyAPIView):
#     permission_classes = [IsAuthenticated]
#
#     queryset = UserQuestAttempt.objects.all().order_by('-id')
#     serializer_class = UserQuestAttemptSerializer
#
#
# class UserQuestAttemptByUserQuestView(generics.ListAPIView):
#     permission_classes = [IsAuthenticated]
#     serializer_class = UserQuestAttemptSerializer
#
#     def get_queryset(self):
#         quest_id = self.kwargs['quest_id']
#         user_id = self.kwargs['user_id']
#         return UserQuestAttempt.objects.filter(user=user_id, quest=quest_id).order_by('-id')
#
#
# class UserQuestAttemptByQuestView(generics.ListAPIView):
#     permission_classes = [IsAuthenticated]
#     serializer_class = UserQuestAttemptSerializer
#
#     def get_queryset(self):
#         quest_id = self.kwargs['quest_id']
#         return UserQuestAttempt.objects.filter(quest=quest_id).order_by('-id')
#
#
# # class UserQuestQuestionAttemptByQuestView(generics.ListAPIView):
# #     permission_classes = [IsAuthenticated]
# #     serializer_class = UserQuestQuestionAttemptSerializer
# #
# #     def get_queryset(self):
# #         quest_id = self.kwargs['quest_id']
# #         user_quest_attempts = UserQuestAttempt.objects.filter(quest=quest_id)
# #         return UserQuestQuestionAttempt.objects.filter(user_quest_attempt__in=user_quest_attempts)
#
#
# class BulkUpdateUserQuestAttemptView(APIView):
#     def patch(self, request, *args, **kwargs):
#         serializer = UserQuestAttemptSerializer(data=request.data, many=True)
#         if serializer.is_valid():
#             ids = [item.get('id') for item in request.data if 'id' in item]
#             instances = UserQuestAttempt.objects.filter(id__in=ids)
#
#             # Add logging to debug
#             print(f"UserQuestAttempt Instances found: {[instance.id for instance in instances]}")
#
#             if len(instances) != len(ids):
#                 return Response({"detail": "One or more instances not found."}, status=status.HTTP_404_NOT_FOUND)
#
#
#             # Convert quest field to Quest instance
#             for item in serializer.validated_data:
#                 quest_data = item.pop('quest')
#                 item['quest'] = Quest.objects.get(id=quest_data['id'])
#
#             serializer.update(instances, serializer.validated_data)
#             return Response(serializer.data, status=status.HTTP_200_OK)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
#
#
# # class UserQuestQuestionAttemptListCreateView(generics.ListCreateAPIView):
# #     permission_classes = [IsAuthenticated]
# #
# #     queryset = UserQuestQuestionAttempt.objects.all().order_by('-id')
# #     serializer_class = UserQuestQuestionAttemptSerializer
# #
# #
# # class UserQuestQuestionAttemptManageView(generics.RetrieveUpdateDestroyAPIView):
# #     permission_classes = [IsAuthenticated]
# #
# #     queryset = UserQuestQuestionAttempt.objects.all().order_by('-id')
# #     serializer_class = UserQuestQuestionAttemptSerializer
#
#
# # class BulkUpdateUserQuestQuestionAttemptView(APIView):
# #     def patch(self, request, *args, **kwargs):
# #         serializer = UserQuestQuestionAttemptSerializer(data=request.data, many=True)
# #         if serializer.is_valid():
# #             ids = [item.get('id') for item in request.data if 'id' in item]
# #             instances = UserQuestQuestionAttempt.objects.filter(id__in=ids)
# #
# #             # Check if Quest has expired
# #             for instance in instances:
# #                 quest = Quest.objects.get(id=instance.user_quest_attempt.quest.id)
# #                 if quest.status == 'Expired':
# #                     return Response({"detail": "Quest has expired."}, status=status.HTTP_400_BAD_REQUEST)
# #                 else:
# #                     break
# #
# #             # Add logging to debug
# #             print(f"UserQuestQuestionAttempt Instances found: {[instance.id for instance in instances]}")
# #
# #             if len(instances) != len(ids):
# #                 return Response({"detail": "One or more instances not found."}, status=status.HTTP_404_NOT_FOUND)
# #
# #             serializer.update(instances, serializer.validated_data)
# #             return Response(serializer.data, status=status.HTTP_200_OK)
# #         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
# #
# #
# # class UserQuestQuestionAttemptByUserQuestAttemptView(generics.ListAPIView):
# #     permission_classes = [IsAuthenticated]
# #     serializer_class = UserQuestQuestionAttemptSerializer
# #
# #     def get_queryset(self):
# #         user_quest_attempt_id = self.kwargs['user_quest_attempt_id']
# #         return UserQuestQuestionAttempt.objects.filter(user_quest_attempt=user_quest_attempt_id).order_by('question__number')
# #
# #
# # class AttemptAnswerRecordListCreateView(generics.ListCreateAPIView):
# #     permission_classes = [IsAuthenticated]
# #
# #     queryset = AttemptAnswerRecord.objects.all().order_by('-id')
# #     serializer_class = AttemptAnswerRecordSerializer
# #
# #
# # class AttemptAnswerRecordManageView(generics.RetrieveUpdateDestroyAPIView):
# #     permission_classes = [IsAuthenticated]
# #
# #     queryset = AttemptAnswerRecord.objects.all().order_by('-id')
# #     serializer_class = AttemptAnswerRecordSerializer
#
#
#
# class BadgeListCreateView(generics.ListCreateAPIView):
#     permission_classes = [IsAuthenticated]
#
#     queryset = Badge.objects.all().order_by('-id')
#     serializer_class = BadgeSerializer
#
#
# class BadgeManageView(generics.RetrieveUpdateDestroyAPIView):
#     permission_classes = [IsAuthenticated]
#
#     queryset = Badge.objects.all().order_by('-id')
#     serializer_class = BadgeSerializer
#
#
# class UserQuestBadgeListCreateView(generics.ListCreateAPIView):
#     permission_classes = [IsAuthenticated]
#
#     queryset = UserQuestBadge.objects.all().order_by('-id')
#     serializer_class = UserQuestBadgeSerializer
#
#
# class UserQuestBadgeManageView(generics.RetrieveUpdateDestroyAPIView):
#     permission_classes = [IsAuthenticated]
#
#     queryset = UserQuestBadge.objects.all().order_by('-id')
#     serializer_class = UserQuestBadgeSerializer
#
#
# class UserQuestBadgeByUserView(generics.ListAPIView):
#     permission_classes = [IsAuthenticated]
#     serializer_class = UserQuestBadgeSerializer
#
#     def get_queryset(self):
#         user_id = self.kwargs['user_id']
#         return UserQuestBadge.objects.filter(quest_attempted__user=user_id).order_by('-id')
#
#
# class UserCourseBadgeListCreateView(generics.ListCreateAPIView):
#     permission_classes = [IsAuthenticated]
#
#     queryset = UserCourseBadge.objects.all().order_by('-id')
#     serializer_class = UserCourseBadgeSerializer
#
#
# class UserCourseBadgeManageView(generics.RetrieveUpdateDestroyAPIView):
#     permission_classes = [IsAuthenticated]
#
#     queryset = UserCourseBadge.objects.all().order_by('-id')
#     serializer_class = UserCourseBadgeSerializer
#
#
# class UserCourseBadgeByUserView(generics.ListAPIView):
#     permission_classes = [IsAuthenticated]
#     serializer_class = UserCourseBadgeSerializer
#
#     def get_queryset(self):
#         user_id = self.kwargs['user_id']
#         return UserCourseBadge.objects.filter(course_completed__user=user_id).order_by('-id')
#
#
# class DocumentUploadView(generics.CreateAPIView):
#     permission_classes = [IsAuthenticated]
# 
#     queryset = Document.objects.all()
#     serializer_class = DocumentSerializer
#     parser_classes = (MultiPartParser, FormParser)
#
#
# class DocumentManageView(generics.RetrieveUpdateDestroyAPIView):
#     permission_classes = [IsAuthenticated]
#
#     queryset = Document.objects.all()
#     serializer_class = DocumentSerializer
#
#
# class DocumentByUserView(generics.ListAPIView):
#     permission_classes = [IsAuthenticated]
#     serializer_class = DocumentSerializer
#
#     def get_queryset(self):
#         user_id = self.kwargs['user_id']
#         return Document.objects.filter(uploaded_by=user_id).order_by('-id')


class AnalyticsPartOneView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        # Current time and time one week ago
        now = timezone.now()
        last_week = now - timedelta(weeks=1)

        # 1. Total number of users excluding admin and new users since last week
        total_users = EduquestUser.objects.exclude(is_staff=True).count()
        new_users_last_week = EduquestUser.objects.exclude(is_staff=True).filter(date_joined__gte=last_week).count()
        new_users_percentage = (new_users_last_week / total_users) * 100 if total_users > 0 else 0

        # 2. Total number of course enrollments and new enrollments since last week
        total_enrollments = UserCourseGroupEnrollment.objects.exclude(course_group__course__type="Private").count()
        new_enrollments_last_week = UserCourseGroupEnrollment.objects.exclude(course_group__course__type="Private").filter(
            enrolled_on__gte=last_week).count()
        new_enrollments_percentage = (new_enrollments_last_week / total_enrollments) * 100 if total_enrollments > 0 else 0

        # 3. Total number of quest attempts and new attempts since last week
        total_quest_attempts = UserQuestAttempt.objects.exclude(quest__type="Private").count()
        new_quest_attempts_last_week = UserQuestAttempt.objects.exclude(quest__type="Private").filter(
            first_attempted_date__gte=last_week).count()
        new_quest_attempts_percentage = (new_quest_attempts_last_week / total_quest_attempts) * 100 if total_quest_attempts > 0 else 0

        # 4. User with the shortest non-zero time_taken and perfect score
        # Filter UserQuestBadge for users with the "Perfectionist" badge
        perfectionist_badge_attempts = UserQuestBadge.objects.filter(
            badge__name="Perfectionist"
        ).annotate(
            time_taken=ExpressionWrapper(
                F('user_quest_attempt__last_attempted_date') - F('user_quest_attempt__first_attempted_date'),
                output_field=DurationField()
            )
        ).filter(
            time_taken__gt=timedelta(seconds=0)
        ).order_by('time_taken').first()

        if perfectionist_badge_attempts:
            shortest_time_user = {
                'nickname': perfectionist_badge_attempts.quest_attempted.user.nickname,
                'time_taken': int(perfectionist_badge_attempts.time_taken.total_seconds() * 1000),
                # Convert to milliseconds and round to whole number
                'quest_id': perfectionist_badge_attempts.quest_attempted.quest.id,
                'quest_name': perfectionist_badge_attempts.quest_attempted.quest.name,
                'course': f"{perfectionist_badge_attempts.quest_attempted.quest.course_group.course.code} {perfectionist_badge_attempts.quest_attempted.quest.course_group.course.name}"
            }
        else:
            shortest_time_user = None

        data = {
            'user_stats': {
                'total_users': total_users,
                'new_users_percentage': new_users_percentage,
            },
            'course_enrollment_stats': {
                'total_enrollments': total_enrollments,
                'new_enrollments_percentage': new_enrollments_percentage,
            },
            'quest_attempt_stats': {
                'total_quest_attempts': total_quest_attempts,
                'new_quest_attempts_percentage': new_quest_attempts_percentage,
            },
            'shortest_time_user': shortest_time_user
        }

        return Response(data)


class AnalyticsPartTwoView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user_id = self.request.query_params.get('user_id')
        option = self.request.query_params.get('option')  # course_progression, badge_progression, or both

        # Validation
        if not user_id:
            return Response({"error": "user_id is required in the URL parameters."}, status=400)
        if not option:
            return Response({"error": "option is required in the URL parameters."}, status=400)
        if option not in ['course_progression', 'badge_progression', 'both']:
            return Response({"error": "option must be either course_progression, badge_progression, or both."}, status=400)

        if option == 'course_progression':
            return self.get_course_progression(user_id)
        if option == 'badge_progression':
            return self.get_badge_progression(user_id)
        if option == 'both':
            return self.get_course_and_badge_progression(user_id)

    def get_course_progression(self, user_id):
        # Fetch enrollments with related course and quests in a single query
        enrollments = UserCourseGroupEnrollment.objects.filter(
            student_id=user_id
        ).exclude(
            course_group__course__name="Private Course"
        ).select_related('course_group__course').prefetch_related('course_group__quests')

        course_quest_completion = []

        for enrollment in enrollments:
            course_group = enrollment.course_group
            course = course_group.course

            quest_attempts = UserQuestAttempt.objects.filter(
                student_id=user_id,
                quest__course_group__course_id=course.id,
                submitted=True
            ).distinct('quest')

            completed_quests = quest_attempts.count()
            total_quests = course_group.quests.count()
            completion_ratio = completed_quests / total_quests if total_quests > 0 else 0

            # Get the highest score for each quest attempted in the course
            quest_scores = []
            for quest in course_group.quests.all():
                # Fetch all attempts for this quest by the user
                attempts = UserQuestAttempt.objects.filter(
                    student_id=user_id,
                    quest=quest
                )
                if attempts.exists():
                    # Aggregate the highest score achieved across all attempts for this quest
                    highest_score = attempts.aggregate(
                        highest_score=Sum('total_score_achieved')
                    )['highest_score'] or 0
                else:
                    highest_score = 0

                quest_scores.append({
                    'quest_id': quest.id,
                    'quest_name': quest.name,
                    'max_score': quest.total_max_score(),
                    'highest_score': highest_score
                })

            course_quest_completion.append({
                'course_id': course.id,
                'course_term': f"AY {course.term.academic_year.start_year} - {course.term.academic_year.end_year} {course.term.name}",
                'course_code': course.code,
                'course_name': course.name,
                'completed_quests': completed_quests,
                'total_quests': total_quests,
                'completion_ratio': round(completion_ratio, 2),  # Rounded to 2 decimal places
                'quest_scores': quest_scores
            })
        # Sort the results by completion ratio in descending order
        course_quest_completion.sort(key=lambda x: x['completion_ratio'], reverse=True)

        return Response({'user_course_progression': course_quest_completion})

    def get_badge_progression(self, user_id):
        all_badges = Badge.objects.all()
        user_quest_badges = UserQuestBadge.objects.filter(
            user_quest_attempt__student_id=user_id
        ).select_related('badge')
        user_course_badges = UserCourseBadge.objects.filter(
            user_course_group_enrollment__student_id=user_id
        ).select_related('badge')

        badge_aggregation = {badge.id: {'badge_id': badge.id, 'badge_name': badge.name, 'badge_filename': badge.image.filename if badge.image else None, 'count': 0} for badge in all_badges}

        for badge in user_quest_badges:
            badge_aggregation[badge.badge.id]['count'] += 1

        for badge in user_course_badges:
            badge_aggregation[badge.badge.id]['count'] += 1

        badge_aggregation = [v for v in badge_aggregation.values() if v['count'] > 0]
        sorted_badge_aggregation = sorted(badge_aggregation, key=lambda x: x['count'], reverse=True)

        return Response({'user_badge_progression': sorted_badge_aggregation})

    def get_course_and_badge_progression(self, user_id):
        course_progression = self.get_course_progression(user_id).data
        badge_progression = self.get_badge_progression(user_id).data
        return Response({**course_progression, **badge_progression})


class AnalyticsPartThreeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        # Fetch top 5 users with the most badges with quest badge and course badge combined
        top_users = EduquestUser.objects.annotate(
            quest_badge_count=Count('attempted_quests__earned_quest_badges', distinct=True),
            course_badge_count=Count('enrolled_course_groups__earned_course_badges', distinct=True),
        ).annotate(
            total_badge_count=F('quest_badge_count') + F('course_badge_count')
        ).order_by('-total_badge_count')[:5]

        # Prefetch related badges to reduce database hits
        quest_badges = UserQuestBadge.objects.select_related('badge', 'user_quest_attempt__student').all()
        course_badges = UserCourseBadge.objects.select_related('badge', 'user_course_group_enrollment__student').all()

        user_badge_details = []
        for user in top_users:
            # Aggregate quest badges
            quest_badges_dict = {}
            for badge in quest_badges:
                if badge.user_quest_attempt.student == user:
                    badge_id = badge.badge.id
                    if badge_id not in quest_badges_dict:
                        quest_badges_dict[badge_id] = {
                            "badge_id": badge_id,
                            "badge_name": badge.badge.name,
                            "badge_filename": badge.badge.image.filename,
                            "count": 1
                        }
                    else:
                        quest_badges_dict[badge_id]["count"] += 1

            # Convert the dictionary to a list
            quest_badges_data = list(quest_badges_dict.values())

            # Aggregate course badges similarly
            course_badges_dict = {}
            for badge in course_badges:
                if badge.user_course_group_enrollment.student == user:
                    badge_id = badge.badge.id
                    if badge_id not in course_badges_dict:
                        course_badges_dict[badge_id] = {
                            "badge_id": badge_id,
                            "badge_name": badge.badge.name,
                            "badge_filename": badge.badge.image.filename,
                            "count": 1
                        }
                    else:
                        course_badges_dict[badge_id]["count"] += 1

            # Convert the dictionary to a list
            course_badges_data = list(course_badges_dict.values())

            # Add the aggregated data to the user_badge_details
            user_badge = {
                "user_id": user.id,
                "nickname": user.nickname,
                "badge_count": user.total_badge_count,  # Use the annotated total_badge_count
                "quest_badges": quest_badges_data,
                "course_badges": course_badges_data
            }
            user_badge_details.append(user_badge)

        # Get top 5 most recent badge awards from both UserQuestBadge and UserCourseBadge
        recent_quest_badges = quest_badges.order_by('-awarded_date')[:5]
        recent_course_badges = course_badges.order_by('-awarded_date')[:5]

        # Combine and sort the badges by the most recent award date
        recent_badges = sorted(
            list(recent_quest_badges) + list(recent_course_badges),
            key=lambda badge: badge.awarded_date,
            reverse=True
        )[:5]

        recent_badges_data = []
        record_id = 0
        for badge in recent_badges:
            badge_name = badge.badge.name
            awarded_date = badge.awarded_date
            quest_id = None
            quest_name = None
            if isinstance(badge, UserCourseBadge):
                user_id = badge.user_course_group_enrollment.student.id
                nickname = badge.user_course_group_enrollment.student.nickname
                course_id = badge.user_course_group_enrollment.course_group.course.id
                course_code = badge.user_course_group_enrollment.course_group.course.code
                course_name = badge.user_course_group_enrollment.course_group.course.name
            else:
                user_id = badge.user_quest_attempt.student.id
                nickname = badge.user_quest_attempt.student.nickname
                quest_id = badge.user_quest_attempt.quest.id
                quest_name = badge.user_quest_attempt.quest.name
                course_id = badge.user_quest_attempt.quest.course_group.course.id
                course_code = badge.user_quest_attempt.quest.course_group.course.code
                course_name = badge.user_quest_attempt.quest.course_group.course.name

            badge_data = {
                'record_id': record_id,
                'user_id': user_id,
                'nickname': nickname,
                'badge_name': badge_name,
                'awarded_date': awarded_date,
                'course_id': course_id,
                'course_code': course_code,
                'course_name': course_name,
                'quest_id': quest_id,
                'quest_name': quest_name,
            }
            record_id += 1
            recent_badges_data.append(badge_data)

        data = {
            'top_users_with_most_badges': user_badge_details,
            'recent_badge_awards': recent_badges_data
        }

        return Response(data)


class AnalyticsPartFourView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        """
        Retrieves comprehensive statistics and aggregations for all courses (excluding private),
        including course groups, enrollments, quests, quest progression,
        and detailed student progress for each quest.
        """
        # Step 1: Fetch all courses except those with type="private"
        courses = Course.objects.exclude(type="Private").select_related(
            'term__academic_year',  # Fetch related Term and AcademicYear
            'image'                  # Fetch related Image
        ).prefetch_related(
            Prefetch(
                'groups',
                queryset=CourseGroup.objects.annotate(
                    enrolled_students_count=Count('enrolled_students')  # Annotate enrolled students count
                ).prefetch_related(
                    Prefetch(
                        'quests',
                        queryset=Quest.objects.annotate(
                            quest_completion=Count(
                                'attempted_by__student',
                                filter=Q(attempted_by__submitted=True),
                                distinct=True
                            )
                        )
                    )
                )
            )
        )

        if not courses.exists():
            return Response(
                {"message": "No courses available."},
                status=200
            )

        # Step 2: Fetch all enrollments for the fetched courses
        enrollments = UserCourseGroupEnrollment.objects.filter(
            course_group__course__in=courses
        ).select_related(
            'student',
            'course_group'
        )

        # Mapping: course_group_id -> set of student IDs
        group_to_students = defaultdict(set)
        student_id_to_username = {}

        for enrollment in enrollments:
            group_id = enrollment.course_group.id
            student = enrollment.student
            group_to_students[group_id].add(student.id)
            student_id_to_username[student.id] = student.username

        # Step 3: Fetch all UserQuestAttempt data for the fetched courses' quests and enrolled students
        user_quest_attempts = UserQuestAttempt.objects.filter(
            quest__course_group__course__in=courses,
            student__in=EduquestUser.objects.filter(
                enrolled_course_groups__course_group__course__in=courses
            ).distinct()
        ).values(
            'quest_id',
            'student_id'
        ).annotate(
            highest_score=Max('total_score_achieved')
        )

        # Build a mapping: (quest_id, student_id) -> highest_score
        quest_student_to_score = {}
        for attempt in user_quest_attempts:
            key = (attempt['quest_id'], attempt['student_id'])
            quest_student_to_score[key] = attempt['highest_score']

        # Step 4: Construct response data for all courses
        all_courses_data = []
        for course in courses:
            course_groups_data = []
            for group in course.groups.all():
                group_id = group.id
                enrolled_students_count = group.enrolled_students_count
                enrolled_student_ids = group_to_students.get(group_id, set())

                # Build a list of enrolled students with their usernames
                enrolled_students = [
                    {'student_id': student_id, 'username': student_id_to_username.get(student_id, 'Unknown')}
                    for student_id in enrolled_student_ids
                ]

                # Build quests data for each course group
                quests_data = []
                for quest in group.quests.all():
                    # For each quest, build a list of student progress
                    student_progress = []
                    for student in enrolled_students:
                        key = (quest.id, student['student_id'])
                        highest_score = quest_student_to_score.get(key, None)  # None if no attempts

                        student_progress.append({
                            'username': student['username'],
                            'highest_score': highest_score
                        })

                    quest_data = {
                        'quest_id': quest.id,
                        'quest_name': quest.name,
                        'quest_completion': quest.quest_completion,
                        'quest_max_score': quest.total_max_score(),
                        'students_progress': student_progress
                    }
                    quests_data.append(quest_data)

                # Assemble group data
                group_data = {
                    'group_id': group.id,
                    'group_name': group.name,
                    'enrolled_students': enrolled_students_count,
                    'quests': quests_data
                }
                course_groups_data.append(group_data)

            # Assemble course data
            course_data = {
                'course_id': course.id,
                'course_code': course.code,
                'course_name': course.name,
                'course_term': f"AY {course.term.academic_year.start_year} - {course.term.academic_year.end_year} {course.term.name}",
                'course_image': course.image.filename if course.image else None,
                'course_groups': course_groups_data
            }
            all_courses_data.append(course_data)

        # Step 5: Return the response data
        return Response(all_courses_data)
