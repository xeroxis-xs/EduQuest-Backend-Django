from rest_framework import viewsets
from rest_framework import generics
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from django.http import JsonResponse
from datetime import datetime, timedelta
from django.db.models import Count
import json
import pytz
from .excel import Excel
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from django.db.models import Sum, F, ExpressionWrapper, fields, DurationField
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
    # UserQuestQuestionAttempt,
    # AttemptAnswerRecord,
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
    # UserQuestQuestionAttemptSerializer,
    # AttemptAnswerRecordSerializer,
    BadgeSerializer,
    UserQuestBadgeSerializer,
    UserCourseBadgeSerializer,
    DocumentSerializer, BulkUpdateUserQuestAttemptSerializer, BulkUpdateUserAnswerAttemptSerializer
)
# from django.http import HttpResponse

User = get_user_model()


class EduquestUserViewSet(viewsets.ModelViewSet):
    queryset = EduquestUser.objects.all().order_by('-id')
    serializer_class = EduquestUserSerializer
    permission_classes = [IsAuthenticated]


class AcademicYearViewSet(viewsets.ModelViewSet):
    queryset = AcademicYear.objects.all().order_by('-id')
    serializer_class = AcademicYearSerializer
    permission_classes = [IsAuthenticated]


class TermViewSet(viewsets.ModelViewSet):
    queryset = Term.objects.all().order_by('-id')
    serializer_class = TermSerializer
    permission_classes = [IsAuthenticated]


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


class UserCourseGroupEnrollmentViewSet(viewsets.ModelViewSet):
    queryset = UserCourseGroupEnrollment.objects.all().order_by('-id')
    serializer_class = UserCourseGroupEnrollmentSerializer
    permission_classes = [IsAuthenticated]


class QuestViewSet(viewsets.ModelViewSet):
    queryset = Quest.objects.all().order_by('-id')
    serializer_class = QuestSerializer
    permission_classes = [IsAuthenticated]

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
        excel_file = request.FILES.get('file')
        if not excel_file:
            return JsonResponse(data={"No file provided, please try again"}, status=400)
        try:
            excel = Excel()
            excel.read_excel_sheets(excel_file)
            questions_data = excel.get_questions()
            users_data = excel.get_users()
        except Exception as e:
            return JsonResponse(data={"Error processing excel file": str(e)}, status=400)

        # Extract other form data
        quest_data = {
            'type': request.data.get('type'),
            'name': request.data.get('name'),
            'description': request.data.get('description'),
            'status': request.data.get('status'),
            'max_attempts': request.data.get('max_attempts'),
            'course_group_id': request.data.get('course_group_id'),
            'image_id': request.data.get('image_id'),
            'organiser_id': request.data.get('organiser_id')
        }
        # Create a Quest object
        quest_serializer = QuestSerializer(data=quest_data)

        if quest_serializer.is_valid():
            # Save the Quest object
            quest_serializer.save()
            # Get the ID of the newly created Quest object
            new_quest_id = quest_serializer.data.get('id')
            print(f"New Quest ID: {new_quest_id}")
            course_group = quest_serializer.data.get('course_group')

            questions_serializer = []
            # Process each question in the questions_data list
            for question_data in questions_data:
                print(f"Question data: {question_data}")
                # Extract question data
                question_data['quest_id'] = new_quest_id
                # Create a Question object for each question
                question_serializer = QuestionSerializer(data=question_data)
                if question_serializer.is_valid():
                    question_serializer.save()
                    # Return the question data
                    questions_serializer.append(question_serializer.data)
                else:
                    return Response(data={"Error creating questions": question_serializer.errors},
                                    status=status.HTTP_400_BAD_REQUEST)
            #
            # Create UserQuestAttempt object (auto-generate UserAnswerAttempt objects)
            for user_data in users_data:
                # Create a User object
                user, created = EduquestUser.objects.get_or_create(
                    email=user_data['email'],
                    defaults={
                        'email': user_data['email'],
                        'username': user_data['username'],
                        'nickname': user_data['username']
                    }
                )
                # Enroll the users in the course_group if they are not already enrolled
                UserCourseGroupEnrollment.objects.get_or_create(
                    student_id=user.id,
                    course_group_id=course_group['id']
                )
                #
                # Create a UserQuestAttempt object for each User
                user_quest_attempt_data = {
                    'student_id': user.id,
                    'quest_id': new_quest_id
                }
                user_quest_attempt_serializer = UserQuestAttemptSerializer(data=user_quest_attempt_data)
                if user_quest_attempt_serializer.is_valid():
                    user_quest_attempt_serializer.save()
                    # Get the ID of the newly created UserQuestAttempt object
                    new_user_quest_attempt_id = user_quest_attempt_serializer.data.get('id')
                    print(f"New UserQuestAttempt ID: {new_user_quest_attempt_id}")
                    # print(f"User question attempts: {user_question_attempts}")
                else:
                    return Response(
                        data={"Error user quest attempt template": user_quest_attempt_serializer.errors},
                        status=status.HTTP_400_BAD_REQUEST)

                # Create UserAnswerAttempt objects for each UserQuestAttempt
                for question_serializer in questions_serializer:
                    # Iterate through each answer record in selected_answers
                    for answer_serializer in question_serializer['answers']:
                        user_answer_attempt_data = {
                            'user_quest_attempt_id': new_user_quest_attempt_id,
                            'question_id': question_serializer['id'],
                            'answer_id': answer_serializer['id'],
                            'is_selected': False
                        }
                        user_answer_attempt_serializer = UserAnswerAttemptSerializer(
                            data=user_answer_attempt_data)
                        if user_answer_attempt_serializer.is_valid():
                            user_answer_attempt_serializer.save()
                        else:
                            return Response(data={
                                "Error creating user answer attempts": user_answer_attempt_serializer.errors},
                                            status=status.HTTP_400_BAD_REQUEST)

                user_answer_attempts = UserAnswerAttempt.objects.filter(
                    user_quest_attempt=new_user_quest_attempt_id)
                try:
                    # Iterate through each user_answer_attempts question
                    for user_answer_attempt in user_answer_attempts:
                        print(f"User question attempt: {user_answer_attempt.question.text}")
                        # Get the wooclap_questions_selected_answers for the user
                        print(f"User: {user.email}")
                        wooclap_questions_selected_answers = excel.get_user_answer_attempts(user.email)
                        print(f"Wooclap questions selected answers: {wooclap_questions_selected_answers}")
                        # Iterate through each wooclap_question_selected_answers
                        for wooclap_question_selected_answers in wooclap_questions_selected_answers:
                            # print(f"Wooclap question selected answers: {wooclap_question_selected_answers}")
                            # If the question in the wooclap_question_selected_answers matches
                            # the user_question_attempt question
                            """
                            wooclap_question_selected_answers
                            {
                                'question': 'What is the primary key in a database?',
                                'selected_answers': ['A field in a table that uniquely identifies each row']
                            }
                            """
                            if wooclap_question_selected_answers[
                                'question'] == user_answer_attempt.question.text:

                                #                                 # Get the AttemptAnswerRecord objects for the user_question_attempt
                                #                                 answer_records = AttemptAnswerRecord.objects.filter(user_quest_question_attempt=user_question_attempt.id)
                                #
                                # Iterate through each answer record in selected_answers
                                for wooclap_selected_answer in wooclap_question_selected_answers[
                                    'selected_answers']:
                                    # Iterate through each 'empty' attempted answer records in the system
                                    #                                     for answer_record in answer_records:
                                    # If the answer in the user_answer_attempt  matches the selected answer in wooclap
                                    if user_answer_attempt.answer.text == wooclap_selected_answer:
                                        # print(f"Selected answer: {selected_answer.answer.text}")
                                        user_answer_attempt.is_selected = True
                                        user_answer_attempt.save()
                except Exception as e:
                    return Response(data={"Error updating selected answers": str(e)},
                                    status=status.HTTP_400_BAD_REQUEST)

            return Response(questions_serializer, status=status.HTTP_201_CREATED)
        else:
            return Response(data={"Error creating quest": quest_serializer.errors},
                            status=status.HTTP_400_BAD_REQUEST)


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
        if not isinstance(request.data, list):
            return Response({"error": "Expected a list of items."}, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(data=request.data, many=True)
        serializer.is_valid(raise_exception=True)

        # Collect the IDs of the answers to update
        answer_ids = [item['id'] for item in serializer.validated_data]

        # Retrieve the existing answers from the database
        answers = Answer.objects.filter(id__in=answer_ids)

        # Map existing answers by ID for easy lookup
        answer_dict = {answer.id: answer for answer in answers}

        updated_answers = []
        for item in serializer.validated_data:
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
                    return Response({"error": f"UserQuestAttempt with id {attempt_id} not found."}, status=status.HTTP_404_NOT_FOUND)

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
                    return Response({"error": f"UserAnswerAttempt with id {attempt_id} not found."}, status=status.HTTP_404_NOT_FOUND)

                # Use the existing serializer for each update
                serializer = self.get_serializer(instance=attempt_instance, data=attempt_data, partial=True)
                if serializer.is_valid():
                    serializer.save()
                    updated_attempts.append(serializer.data)
                else:
                    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            return Response({"updated_attempts": updated_attempts}, status=status.HTTP_200_OK)

        return Response({"error": "Expected a list of data."}, status=status.HTTP_400_BAD_REQUEST)


# class UserQuestQuestionAttemptViewSet(viewsets.ModelViewSet):
#     queryset = UserQuestQuestionAttempt.objects.all().order_by('-id')
#     serializer_class = UserQuestQuestionAttemptSerializer
#     permission_classes = [IsAuthenticated]
#
#     @action(detail=False, methods=['get'])
#     def by_user_quest_attempt(self, request):
#         user_quest_attempt_id = request.query_params.get('user_quest_attempt_id')
#         queryset = UserQuestQuestionAttempt.objects.filter(user_quest_attempt=user_quest_attempt_id).order_by('-id')
#         serializer = UserQuestQuestionAttemptSerializer(queryset, many=True)
#         return Response(serializer.data)
#
#
# class AttemptAnswerRecordViewSet(viewsets.ModelViewSet):
#     queryset = AttemptAnswerRecord.objects.all().order_by('-id')
#     serializer_class = AttemptAnswerRecordSerializer
#     permission_classes = [IsAuthenticated]


class BadgeViewSet(viewsets.ModelViewSet):
    queryset = Badge.objects.all().order_by('-id')
    serializer_class = BadgeSerializer
    permission_classes = [IsAuthenticated]


class UserQuestBadgeViewSet(viewsets.ModelViewSet):
    queryset = UserQuestBadge.objects.all().order_by('-id')
    serializer_class = UserQuestBadgeSerializer
    permission_classes = [IsAuthenticated]


class UserCourseBadgeViewSet(viewsets.ModelViewSet):
    queryset = UserCourseBadge.objects.all().order_by('-id')
    serializer_class = UserCourseBadgeSerializer
    permission_classes = [IsAuthenticated]


class DocumentViewSet(viewsets.ModelViewSet):
    queryset = Document.objects.all().order_by('-id')
    serializer_class = DocumentSerializer
    permission_classes = [IsAuthenticated]




# class EduquestUserListCreateView(generics.ListCreateAPIView):
#     permission_classes = [IsAuthenticated]
#
#     queryset = EduquestUser.objects.all().order_by('-id')
#     serializer_class = EduquestUserSerializer


# class EduquestUserManageView(generics.RetrieveUpdateDestroyAPIView):
#     permission_classes = [IsAuthenticated]
#
#     queryset = EduquestUser.objects.all().order_by('-id')
#     serializer_class = EduquestUserSerializer
#
#     def get_object(self):
#         email = self.kwargs.get('email')
#         return get_object_or_404(EduquestUser, email=email)


class ImageListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]

    queryset = Image.objects.all().order_by('-id')
    serializer_class = ImageSerializer


class ImageManageView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]

    queryset = Image.objects.all().order_by('-id')
    serializer_class = ImageSerializer


class AcademicYearListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]

    queryset = AcademicYear.objects.all().order_by('-id')
    serializer_class = AcademicYearSerializer


class AcademicYearManageView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]

    queryset = AcademicYear.objects.all().order_by('-id')
    serializer_class = AcademicYearSerializer


class TermListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]

    queryset = Term.objects.all().order_by('-id')
    serializer_class = TermSerializer


class TermManageView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]

    queryset = Term.objects.all().order_by('-id')
    serializer_class = TermSerializer


class CourseListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]

    queryset = Course.objects.all().order_by('-id')
    serializer_class = CourseSerializer


class NonPrivateCourseListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]

    queryset = Course.objects.exclude(type='Private').order_by('-id')
    serializer_class = CourseSerializer


class CourseManageView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]

    queryset = Course.objects.all().order_by('-id')
    serializer_class = CourseSerializer


# class CourseByTermView(generics.ListAPIView):
#     permission_classes = [IsAuthenticated]
#     serializer_class = CourseSerializer
#
#     def get_queryset(self):
#         term_id = self.kwargs['term_id']
#         return Course.objects.filter(term=term_id).order_by('-id')


# class CourseByUserView(generics.ListAPIView):
#     permission_classes = [IsAuthenticated]
#     serializer_class = CourseSerializer
#
#     def get_queryset(self):
#         user_id = self.kwargs['user_id']
#         return Course.objects.filter(enrolled_users__user=user_id).order_by('-id')


# class CourseGroupListCreateView(generics.ListCreateAPIView):
#     permission_classes = [IsAuthenticated]
#
#     queryset = CourseGroup.objects.all().order_by('-id')
#     serializer_class = CourseGroupSerializer
#
#
# class CourseGroupManageView(generics.RetrieveUpdateDestroyAPIView):
#     permission_classes = [IsAuthenticated]
#
#     queryset = CourseGroup.objects.all().order_by('-id')
#     serializer_class = CourseGroupSerializer
#
#
# class UserCourseGroupEnrollmentListCreateView(generics.ListCreateAPIView):
#     permission_classes = [IsAuthenticated]
#
#     queryset = UserCourseGroupEnrollment.objects.all().order_by('-id')
#     serializer_class = UserCourseGroupEnrollmentSerializer

    # def perform_create(self, serializer):
    #     user = self.request.data.get('user')
    #     if user and isinstance(user, dict):
    #         user_id = user['id']
    #         user = EduquestUser.objects.get(id=user_id)
    #     course = self.request.data.get('course')
    #     if course and isinstance(course, dict):
    #         course_id = course['id']
    #         course = Course.objects.get(id=course_id)
    #     if UserCourseGroupEnrollmentSerializer.objects.filter(user=user, course=course).exists():
    #         return  # Do nothing if the user is already enrolled in the course
    #     serializer.save()


# class UserCourseGroupEnrollmentManageView(generics.RetrieveUpdateDestroyAPIView):
#     permission_classes = [IsAuthenticated]
#
#     queryset = UserCourseGroupEnrollment.objects.all().order_by('-id')
#     serializer_class = UserCourseGroupEnrollmentSerializer


class QuestImportView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):

        excel_file = request.FILES.get('file')
        if not excel_file:
            return JsonResponse(data={"No file provided, please try again"}, status=400)
        try:
            excel = Excel()
            excel.read_excel_sheets(excel_file)
            questions_data = excel.get_questions()
            users_data = excel.get_users()
        except Exception as e:
            return JsonResponse(data={"Error processing excel file": str(e)}, status=400)

        # Extract other form data
        quest_data = {
            'type': request.data.get('type'),
            'name': request.data.get('name'),
            'description': request.data.get('description'),
            'status': request.data.get('status'),
            'max_attempts': request.data.get('max_attempts'),
            'course_group_id': request.data.get('course_group_id'),
            'image_id': request.data.get('image_id'),
            'organiser_id': request.data.get('organiser_id')
        }
        # Create a Quest object
        quest_serializer = QuestSerializer(data=quest_data)

        if quest_serializer.is_valid():
            # Save the Quest object
            quest_serializer.save()
            # Get the ID of the newly created Quest object
            new_quest_id = quest_serializer.data.get('id')
            print(f"New Quest ID: {new_quest_id}")
            course_group = quest_serializer.data.get('course_group')
            course = Course.objects.get(id=course_group['id'])

            questions_serializer = []
            # Process each question in the questions_data list
            for question_data in questions_data:
                # Extract question data
                question_data['quest'] = new_quest_id
                # Create a Question object for each question
                question_serializer = QuestionSerializer(data=question_data)
                if question_serializer.is_valid():
                    question_serializer.save()
                    # Return the question data
                    questions_serializer.append(question_serializer.data)
                else:
                    return Response(data={"Error creating questions": question_serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
#
            # Create UserQuestAttempt object (auto-generate UserAnswerAttempt objects)
            for user_data in users_data:
                # Create a User object
                user, created = EduquestUser.objects.get_or_create(
                    email=user_data['email'],
                    defaults={
                        'email': user_data['email'],
                        'username': user_data['username'],
                        'nickname': user_data['username']
                    }
                )
                # Enroll the users in the course_group if they are not already enrolled
                UserCourseGroupEnrollment.objects.get_or_create(
                    user=user,
                    course_group=course_group
                )
#
                # Create a UserQuestAttempt object for each User
                user_quest_attempt_data = {
                    'student_id': user.id,
                    'quest_id': new_quest_id
                }
                user_quest_attempt_serializer = UserQuestAttemptSerializer(data=user_quest_attempt_data)
                if user_quest_attempt_serializer.is_valid():
                    user_quest_attempt_serializer.save()
                    # Get the ID of the newly created UserQuestAttempt object
                    new_user_quest_attempt_id = user_quest_attempt_serializer.data.get('id')
                    print(f"New UserQuestAttempt ID: {new_user_quest_attempt_id}")
                    # print(f"User question attempts: {user_question_attempts}")
                else:
                    return Response(data={"Error user quest attempt template": user_quest_attempt_serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

                # Create UserAnswerAttempt objects for each UserQuestAttempt
                for question_serializer in questions_serializer:
                    # Iterate through each answer record in selected_answers
                    for answer_serializer in question_serializer['answers']:
                        user_answer_attempt_data = {
                            'user_quest_attempt_id': new_user_quest_attempt_id,
                            'question_id': question_serializer['id'],
                            'answer_id': answer_serializer['id'],
                            'is_selected': False
                        }
                        user_answer_attempt_serializer = UserAnswerAttemptSerializer(data=user_answer_attempt_data)
                        if user_answer_attempt_serializer.is_valid():
                            user_answer_attempt_serializer.save()
                        else:
                            return Response(data={"Error creating user answer attempts": user_answer_attempt_serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

                user_answer_attempts = UserAnswerAttempt.objects.filter(user_quest_attempt=new_user_quest_attempt_id)
                try:
                    # Iterate through each user_answer_attempts question
                    for user_answer_attempt in user_answer_attempts:
                        print(f"User question attempt: {user_answer_attempt.question.text}")
                        # Get the wooclap_questions_selected_answers for the user
                        print(f"User: {user.email}")
                        wooclap_questions_selected_answers = excel.get_user_answer_attempts(user.email)
                        print(f"Wooclap questions selected answers: {wooclap_questions_selected_answers}")
                        # Iterate through each wooclap_question_selected_answers
                        for wooclap_question_selected_answers in wooclap_questions_selected_answers:
                            # print(f"Wooclap question selected answers: {wooclap_question_selected_answers}")
                            # If the question in the wooclap_question_selected_answers matches
                            # the user_question_attempt question
                            """
                            wooclap_question_selected_answers
                            {
                                'question': 'What is the primary key in a database?',
                                'selected_answers': ['A field in a table that uniquely identifies each row']
                            }
                            """
                            if wooclap_question_selected_answers['question'] == user_answer_attempt.question.text:

#                                 # Get the AttemptAnswerRecord objects for the user_question_attempt
#                                 answer_records = AttemptAnswerRecord.objects.filter(user_quest_question_attempt=user_question_attempt.id)
#
                                # Iterate through each answer record in selected_answers
                                for wooclap_selected_answer in wooclap_question_selected_answers['selected_answers']:
                                    # Iterate through each 'empty' attempted answer records in the system
#                                     for answer_record in answer_records:
                                        # If the answer in the user_answer_attempt  matches the selected answer in wooclap
                                        if user_answer_attempt.answer.text == wooclap_selected_answer:
                                            # print(f"Selected answer: {selected_answer.answer.text}")
                                            user_answer_attempt.is_selected = True
                                            user_answer_attempt.save()
                except Exception as e:
                    return Response(data={"Error updating selected answers": str(e)}, status=status.HTTP_400_BAD_REQUEST)
#
            return Response(questions_serializer, status=status.HTTP_201_CREATED)
        else:
            return Response(data={"Error creating quest": quest_serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class QuestListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]

    queryset = Quest.objects.all().order_by('-id')
    serializer_class = QuestSerializer


class QuestManageView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]

    queryset = Quest.objects.all().order_by('-id')
    serializer_class = QuestSerializer


class QuestByCourseView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = QuestSerializer

    def get_queryset(self):
        course_id = self.kwargs['course_id']
        return Quest.objects.filter(from_course=course_id).order_by('-id')


class PrivateQuestByUserView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = QuestSerializer

    def get_queryset(self):
        user = self.request.user
        return Quest.objects.filter(organiser=user, type='Private').order_by('-id')


class QuestByEnrolledUser(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = QuestSerializer

    def get_queryset(self):
        user_id = self.kwargs['user_id']
        return Quest.objects.filter(from_course__enrolled_users__user=user_id).distinct().order_by('-id')

class QuestionListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]

    queryset = Question.objects.all().order_by('-id')
    serializer_class = QuestionSerializer


class QuestionManageView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]

    queryset = Question.objects.all().order_by('-id')
    serializer_class = QuestionSerializer


class QuestionByQuestView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = QuestionSerializer

    def get_queryset(self):
        quest_id = self.kwargs['quest_id']
        return Question.objects.filter(from_quest=quest_id).order_by('number')


class BulkCreateQuestionView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = QuestionSerializer(data=request.data, many=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class BulkUpdateQuestionView(APIView):
    def patch(self, request, *args, **kwargs):
        serializer = QuestionSerializer(data=request.data, many=True)

        if serializer.is_valid():
            ids = [item.get('id') for item in request.data if 'id' in item]
            instances = Question.objects.filter(id__in=ids)

            # Add logging to debug
            print(f"Question Instances found: {[instance.id for instance in instances]}")

            if len(instances) != len(ids):
                return Response({"detail": "One or more instances not found."}, status=status.HTTP_404_NOT_FOUND)

            serializer.update(instances, serializer.validated_data)
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AnswerListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]

    queryset = Answer.objects.all().order_by('-id')
    serializer_class = AnswerSerializer


class AnswerManageView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]

    queryset = Answer.objects.all().order_by('-id')
    serializer_class = AnswerSerializer


class AnswerByQuestView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = AnswerSerializer

    def get_queryset(self):
        quest_id = self.kwargs['quest_id']
        questions = Question.objects.filter(from_quest=quest_id).order_by('number')
        return Answer.objects.filter(question__in=questions).order_by('-id')


class UserQuestAttemptListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]

    queryset = UserQuestAttempt.objects.all().order_by('-id')
    serializer_class = UserQuestAttemptSerializer


class UserQuestAttemptManageView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]

    queryset = UserQuestAttempt.objects.all().order_by('-id')
    serializer_class = UserQuestAttemptSerializer


class UserQuestAttemptByUserQuestView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserQuestAttemptSerializer

    def get_queryset(self):
        quest_id = self.kwargs['quest_id']
        user_id = self.kwargs['user_id']
        return UserQuestAttempt.objects.filter(user=user_id, quest=quest_id).order_by('-id')


class UserQuestAttemptByQuestView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserQuestAttemptSerializer

    def get_queryset(self):
        quest_id = self.kwargs['quest_id']
        return UserQuestAttempt.objects.filter(quest=quest_id).order_by('-id')


# class UserQuestQuestionAttemptByQuestView(generics.ListAPIView):
#     permission_classes = [IsAuthenticated]
#     serializer_class = UserQuestQuestionAttemptSerializer
#
#     def get_queryset(self):
#         quest_id = self.kwargs['quest_id']
#         user_quest_attempts = UserQuestAttempt.objects.filter(quest=quest_id)
#         return UserQuestQuestionAttempt.objects.filter(user_quest_attempt__in=user_quest_attempts)


class BulkUpdateUserQuestAttemptView(APIView):
    def patch(self, request, *args, **kwargs):
        serializer = UserQuestAttemptSerializer(data=request.data, many=True)
        if serializer.is_valid():
            ids = [item.get('id') for item in request.data if 'id' in item]
            instances = UserQuestAttempt.objects.filter(id__in=ids)

            # Add logging to debug
            print(f"UserQuestAttempt Instances found: {[instance.id for instance in instances]}")

            if len(instances) != len(ids):
                return Response({"detail": "One or more instances not found."}, status=status.HTTP_404_NOT_FOUND)


            # Convert quest field to Quest instance
            for item in serializer.validated_data:
                quest_data = item.pop('quest')
                item['quest'] = Quest.objects.get(id=quest_data['id'])

            serializer.update(instances, serializer.validated_data)
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# class UserQuestQuestionAttemptListCreateView(generics.ListCreateAPIView):
#     permission_classes = [IsAuthenticated]
#
#     queryset = UserQuestQuestionAttempt.objects.all().order_by('-id')
#     serializer_class = UserQuestQuestionAttemptSerializer
#
#
# class UserQuestQuestionAttemptManageView(generics.RetrieveUpdateDestroyAPIView):
#     permission_classes = [IsAuthenticated]
#
#     queryset = UserQuestQuestionAttempt.objects.all().order_by('-id')
#     serializer_class = UserQuestQuestionAttemptSerializer


# class BulkUpdateUserQuestQuestionAttemptView(APIView):
#     def patch(self, request, *args, **kwargs):
#         serializer = UserQuestQuestionAttemptSerializer(data=request.data, many=True)
#         if serializer.is_valid():
#             ids = [item.get('id') for item in request.data if 'id' in item]
#             instances = UserQuestQuestionAttempt.objects.filter(id__in=ids)
#
#             # Check if Quest has expired
#             for instance in instances:
#                 quest = Quest.objects.get(id=instance.user_quest_attempt.quest.id)
#                 if quest.status == 'Expired':
#                     return Response({"detail": "Quest has expired."}, status=status.HTTP_400_BAD_REQUEST)
#                 else:
#                     break
#
#             # Add logging to debug
#             print(f"UserQuestQuestionAttempt Instances found: {[instance.id for instance in instances]}")
#
#             if len(instances) != len(ids):
#                 return Response({"detail": "One or more instances not found."}, status=status.HTTP_404_NOT_FOUND)
#
#             serializer.update(instances, serializer.validated_data)
#             return Response(serializer.data, status=status.HTTP_200_OK)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
#
#
# class UserQuestQuestionAttemptByUserQuestAttemptView(generics.ListAPIView):
#     permission_classes = [IsAuthenticated]
#     serializer_class = UserQuestQuestionAttemptSerializer
#
#     def get_queryset(self):
#         user_quest_attempt_id = self.kwargs['user_quest_attempt_id']
#         return UserQuestQuestionAttempt.objects.filter(user_quest_attempt=user_quest_attempt_id).order_by('question__number')
#
#
# class AttemptAnswerRecordListCreateView(generics.ListCreateAPIView):
#     permission_classes = [IsAuthenticated]
#
#     queryset = AttemptAnswerRecord.objects.all().order_by('-id')
#     serializer_class = AttemptAnswerRecordSerializer
#
#
# class AttemptAnswerRecordManageView(generics.RetrieveUpdateDestroyAPIView):
#     permission_classes = [IsAuthenticated]
#
#     queryset = AttemptAnswerRecord.objects.all().order_by('-id')
#     serializer_class = AttemptAnswerRecordSerializer



class BadgeListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]

    queryset = Badge.objects.all().order_by('-id')
    serializer_class = BadgeSerializer


class BadgeManageView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]

    queryset = Badge.objects.all().order_by('-id')
    serializer_class = BadgeSerializer


class UserQuestBadgeListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]

    queryset = UserQuestBadge.objects.all().order_by('-id')
    serializer_class = UserQuestBadgeSerializer


class UserQuestBadgeManageView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]

    queryset = UserQuestBadge.objects.all().order_by('-id')
    serializer_class = UserQuestBadgeSerializer


class UserQuestBadgeByUserView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserQuestBadgeSerializer

    def get_queryset(self):
        user_id = self.kwargs['user_id']
        return UserQuestBadge.objects.filter(quest_attempted__user=user_id).order_by('-id')


class UserCourseBadgeListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]

    queryset = UserCourseBadge.objects.all().order_by('-id')
    serializer_class = UserCourseBadgeSerializer


class UserCourseBadgeManageView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]

    queryset = UserCourseBadge.objects.all().order_by('-id')
    serializer_class = UserCourseBadgeSerializer


class UserCourseBadgeByUserView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserCourseBadgeSerializer

    def get_queryset(self):
        user_id = self.kwargs['user_id']
        return UserCourseBadge.objects.filter(course_completed__user=user_id).order_by('-id')


class DocumentUploadView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]

    queryset = Document.objects.all()
    serializer_class = DocumentSerializer
    parser_classes = (MultiPartParser, FormParser)


class DocumentManageView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]

    queryset = Document.objects.all()
    serializer_class = DocumentSerializer


class DocumentByUserView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = DocumentSerializer

    def get_queryset(self):
        user_id = self.kwargs['user_id']
        return Document.objects.filter(uploaded_by=user_id).order_by('-id')


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
        total_enrollments = UserCourseGroupEnrollment.objects.exclude(course__type="Private").count()
        new_enrollments_last_week = UserCourseGroupEnrollment.objects.exclude(course__type="Private").filter(
            enrolled_on__gte=last_week).count()
        new_enrollments_percentage = (new_enrollments_last_week / total_enrollments) * 100 if total_enrollments > 0 else 0

        # 3. Total number of quest attempts and new attempts since last week
        total_quest_attempts = UserQuestAttempt.objects.exclude(quest__type="Private").count()
        new_quest_attempts_last_week = UserQuestAttempt.objects.exclude(quest__type="Private").filter(first_attempted_on__gte=last_week).count()
        new_quest_attempts_percentage = (new_quest_attempts_last_week / total_quest_attempts) * 100 if total_quest_attempts > 0 else 0

        # 4. User with the shortest non-zero time_taken and perfect score
        # Filter UserQuestBadge for users with the "Perfectionist" badge
        perfectionist_badge_attempts = UserQuestBadge.objects.filter(
            badge__name="Perfectionist"
        ).annotate(
            time_taken=ExpressionWrapper(
                F('quest_attempted__last_attempted_on') - F('quest_attempted__first_attempted_on'),
                output_field=DurationField()
            )
        ).filter(
            time_taken__gt=timedelta(seconds=0)
        ).order_by('time_taken').first()

        if perfectionist_badge_attempts:
            shortest_time_user = {
                'nickname': perfectionist_badge_attempts.quest_attempted.user.nickname,
                'time_taken': int(perfectionist_badge_attempts.time_taken.total_seconds() * 1000),  # Convert to milliseconds and round to whole number
                'quest_id': perfectionist_badge_attempts.quest_attempted.quest.id,
                'quest_name': perfectionist_badge_attempts.quest_attempted.quest.name,
                'course': f"{perfectionist_badge_attempts.quest_attempted.quest.from_course.code} {perfectionist_badge_attempts.quest_attempted.quest.from_course.name}"
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
        user_id = self.kwargs['user_id']

        # Fetch a user's enrolled course progression, excluding courses with code "PRIVATE"
        user_courses = UserCourseGroupEnrollment.objects.filter(user=user_id).exclude(course__name="Private Course")

        # Aggregate the number of unique completed quests per course
        course_quest_completion = []
        for user_course in user_courses:
            course_id = user_course.course.id
            quest_attempts = UserQuestAttempt.objects.filter(user=user_id, quest__from_course=course_id, submitted=True).distinct('quest')
            completed_quests = quest_attempts.count()
            total_quests = user_course.course.quests.count()
            completion_ratio = completed_quests / total_quests if total_quests > 0 else 0

            # Get the highest score for each quest attempted in the course
            quest_scores = []
            for quest in user_course.course.quests.all():
                quest_attempts = UserQuestAttempt.objects.filter(user=user_id, quest=quest)
                if quest_attempts.exists():
                    highest_score = quest_attempts.aggregate(highest_score=Sum('total_score_achieved'))['highest_score']
                else:
                    highest_score = 0
                quest_scores.append({
                    'quest_id': quest.id,
                    'quest_name': quest.name,
                    'max_score': quest.total_max_score(),
                    'highest_score': highest_score
                })

            course_quest_completion.append({
                'course_id': course_id,
                'course_term': f"AY {user_course.course.term.academic_year.start_year} - {user_course.course.term.academic_year.end_year} {user_course.course.term.name}",
                'course_code': user_course.course.code,
                'course_name': user_course.course.name,
                'completed_quests': completed_quests,
                'total_quests': total_quests,
                'completion_ratio': completion_ratio,
                'quest_scores': quest_scores
            })

        # Sort the results by completion ratio in descending order
        course_quest_completion.sort(key=lambda x: x['completion_ratio'], reverse=True)

        # Fetch all badges
        all_badges = Badge.objects.all()

        # Fetch a user's course badges and quest badges
        user_quest_badges = UserQuestBadge.objects.filter(quest_attempted__user=user_id)
        user_course_badges = UserCourseBadge.objects.filter(course_completed__user=user_id)

        # Aggregate the badge data
        badge_aggregation = {badge.id: {
            'badge_id': badge.id,
            'badge_name': badge.name,
            'badge_filename': badge.image.filename if badge.image else None,
            'count': 0
        } for badge in all_badges}

        for badge in user_quest_badges:
            badge_id = badge.badge.id
            badge_aggregation[badge_id]['count'] += 1

        for badge in user_course_badges:
            badge_id = badge.badge.id
            badge_aggregation[badge_id]['count'] += 1

        # Exclude badges with a count of 0
        badge_aggregation = {k: v for k, v in badge_aggregation.items() if v['count'] > 0}

        # Sort the badges by count in descending order
        sorted_badge_aggregation = sorted(badge_aggregation.values(), key=lambda x: x['count'], reverse=True)

        data = {
            'user_course_progression': course_quest_completion,
            'user_badge_progression': sorted_badge_aggregation
        }
        return Response(data)


class AnalyticsPartThreeView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, *args, **kwargs):
        # Fetch top 5 users with the most badges with quest badge and course badge combined
        # Get all badges awarded to users and count the number of badges

        top_users = EduquestUser.objects.annotate(
            quest_badge_count=Count('attempted_quests__earned_quest_badges', distinct=True),
            course_badge_count=Count('enrolled_courses__earned_course_badges', distinct=True),
        ).annotate(
            total_badge_count=F('quest_badge_count') + F('course_badge_count')
        ).order_by('-total_badge_count')[:5]

        quest_badges = UserQuestBadge.objects.all().order_by('-id')
        course_badges = UserCourseBadge.objects.all().order_by('-id')

        # Perform operations on top_users
        user_badge_details = []
        for user in top_users:
            # Fetch badges for the user
            filtered_quest_badges = quest_badges.filter(quest_attempted__user=user)
            filtered_course_badges = course_badges.filter(course_completed__user=user)

            # Serialize badge data
            quest_badges_data = [
                {
                    'badge_id': badge.badge.id,
                    'badge_name': badge.badge.name,
                    'badge_filename': badge.badge.image.filename,
                    'count': filtered_quest_badges.filter(badge=badge.badge).count()
                }
                for badge in filtered_quest_badges
            ]
            course_badges_data = [
                {
                    'badge_id': badge.badge.id,
                    'badge_name': badge.badge.name,
                    'badge_filename': badge.badge.image.filename,
                    'count': filtered_course_badges.filter(badge=badge.badge).count()
                }
                for badge in filtered_course_badges
            ]

            user_badge = {
                'user_id': user.id,
                'nickname': user.nickname,
                'badge_count': user.total_badge_count,
                'quest_badges': quest_badges_data,
                'course_badges': course_badges_data,
            }

            user_badge_details.append(user_badge)

        # Get top 5 most recent badge awards from both UserQuestBadge and UserCourseBadge
        recent_quest_badges = quest_badges[:5]
        recent_course_badges = course_badges[:5]

        # Combine and sort the badges by the most recent award date
        recent_badges = sorted(
            list(recent_quest_badges) + list(recent_course_badges),
            key=lambda badge: badge.awarded_date,
            reverse=True
        )[:5]

        # Serialize the combined badge data
        recent_badges_data = []
        record_id = 0
        for badge in recent_badges:
            badge_name = badge.badge.name
            awarded_date = badge.awarded_date
            quest_id = None
            quest_name = None
            if isinstance(badge, UserCourseBadge):
                user_id = badge.course_completed.user.id
                nickname = badge.course_completed.user.nickname
                course_id = badge.course_completed.course.id
                course_code = badge.course_completed.course.code
                course_name = badge.course_completed.course.name
            else:
                user_id = badge.quest_attempted.user.id
                nickname = badge.quest_attempted.user.nickname
                quest_id = badge.quest_attempted.quest.id
                quest_name = badge.quest_attempted.quest.name
                course_id = badge.quest_attempted.quest.from_course.id
                course_code = badge.quest_attempted.quest.from_course.code
                course_name = badge.quest_attempted.quest.from_course.name

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

        # Combine the data
        data = {
            'top_users_with_most_badges': user_badge_details,
            'recent_badge_awards': recent_badges_data
        }

        return Response(data)




