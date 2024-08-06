from rest_framework import generics
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from django.http import JsonResponse
from datetime import datetime
import json
from .excel import Excel
from rest_framework.response import Response
from rest_framework import status
from .models import (
    EduquestUser,
    Image,
    AcademicYear,
    Term,
    Course,
    UserCourse,
    Quest,
    Question,
    Answer,
    UserQuestAttempt,
    UserQuestQuestionAttempt,
    AttemptAnswerRecord,
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
    UserCourseSerializer,
    QuestSerializer,
    QuestionSerializer,
    AnswerSerializer,
    UserQuestAttemptSerializer,
    UserQuestQuestionAttemptSerializer,
    AttemptAnswerRecordSerializer,
    BadgeSerializer,
    UserQuestBadgeSerializer,
    UserCourseBadgeSerializer,
    DocumentSerializer
)
# from django.http import HttpResponse

User = get_user_model()


class EduquestUserListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]

    queryset = EduquestUser.objects.all().order_by('-id')
    serializer_class = EduquestUserSerializer


class EduquestUserManageView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]

    queryset = EduquestUser.objects.all().order_by('-id')
    serializer_class = EduquestUserSerializer

    def get_object(self):
        email = self.kwargs.get('email')
        return get_object_or_404(EduquestUser, email=email)


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


class CourseManageView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]

    queryset = Course.objects.all().order_by('-id')
    serializer_class = CourseSerializer


class CourseByTermView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CourseSerializer

    def get_queryset(self):
        term_id = self.kwargs['term_id']
        return Course.objects.filter(term=term_id).order_by('-id')


class UserCourseListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]

    queryset = UserCourse.objects.all().order_by('-id')
    serializer_class = UserCourseSerializer


class UserCourseManageView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]

    queryset = UserCourse.objects.all().order_by('-id')
    serializer_class = UserCourseSerializer


class QuestImportView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):

        excel_file = request.FILES.get('file')
        if not excel_file:
            return JsonResponse({"No file provided, please try again"}, status=400)
        try:
            excel = Excel()
            excel.read_excel_sheets(excel_file)
            questions_data = excel.get_questions()
            users_data = excel.get_users()
        except Exception as e:
            return JsonResponse({"Error processing excel file: ": str(e)}, status=400)

        # Extract other form data
        quest_data = {
            'type': request.data.get('type'),
            'name': request.data.get('name'),
            'description': request.data.get('description'),
            'status': request.data.get('status'),
            'max_attempts': request.data.get('max_attempts'),
            'from_course': json.loads(request.data.get('from_course')),
            'image': json.loads(request.data.get('image')),
            'organiser': json.loads(request.data.get('organiser'))
        }
        last_attempted_on = datetime.now()
        course = Course.objects.get(id=quest_data['from_course']['id'])
        print(course.id)
        # Create a Quest object
        quest_serializer = QuestSerializer(data=quest_data)

        if quest_serializer.is_valid():
            # Save the Quest object
            quest_serializer.save()
            # Get the ID of the newly created Quest object
            new_quest_id = quest_serializer.data.get('id')
            from_course = quest_serializer.data.get('from_course')
            print(from_course)
            course = Course.objects.get(id=from_course['id'])
            print(course.id)

            questions_serializer = []
            # Process each question in the questions_data list
            for question_data in questions_data:
                # Extract question data
                question_data['from_quest'] = new_quest_id
                # Create a Question object for each question
                question_serializer = QuestionSerializer(data=question_data)
                if question_serializer.is_valid():
                    question_serializer.save()
                    # Return the question data
                    questions_serializer.append(question_serializer.data)
                else:
                    return Response(question_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            # Create UserQuestAttempt object (auto-generate UserQuestQuestionAttempt objects)
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
                # Enroll the users in the course if they are not already enrolled
                UserCourse.objects.get_or_create(
                    user=user,
                    course=course
                )

                # Create a UserQuestAttempt object for each User
                user_quest_attempt_data = {
                    'user': user.id,
                    'quest': new_quest_id,
                    'last_attempted_on': last_attempted_on,
                }
                user_quest_attempt_serializer = UserQuestAttemptSerializer(data=user_quest_attempt_data)
                if user_quest_attempt_serializer.is_valid():
                    user_quest_attempt_serializer.save()
                    # Get the ID of the newly created UserQuestAttempt object
                    new_user_quest_attempt_id = user_quest_attempt_serializer.data.get('id')
                    print(f"New UserQuestAttempt ID: {new_user_quest_attempt_id}")
                    # user_question_attempts = UserQuestQuestionAttempt.objects.filter(user_quest_attempt=new_user_quest_attempt_id)
                    # print(f"User question attempts: {user_question_attempts}")
                else:
                    return Response(user_quest_attempt_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

                # Update the selected_answers for the auto-generated UserQuestQuestionAttempt
                user_question_attempts = UserQuestQuestionAttempt.objects.filter(user_quest_attempt=new_user_quest_attempt_id)
                # Iterate through each user_question_attempt question
                for user_question_attempt in user_question_attempts:
                    print(f"User question attempt: {user_question_attempt.question.text}")
                    # Get the wooclap_questions_selected_answers for the user
                    print(f"User: {user.email}")
                    wooclap_questions_selected_answers = excel.get_user_question_attempts(user.email)
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
                        if wooclap_question_selected_answers['question'] == user_question_attempt.question.text:
                            # Get the AttemptAnswerRecord objects for the user_question_attempt
                            answer_records = AttemptAnswerRecord.objects.filter(user_quest_question_attempt=user_question_attempt.id)

                            # Iterate through each answer record in selected_answers
                            for wooclap_selected_answer in wooclap_question_selected_answers['selected_answers']:
                                # Iterate through each selected answer
                                for selected_answer in answer_records:

                                    if selected_answer.answer.text == wooclap_selected_answer:
                                        # print(f"Selected answer: {selected_answer.answer.text}")
                                        selected_answer.is_selected = True
                                        selected_answer.save()

            return Response(questions_serializer, status=status.HTTP_201_CREATED)
        else:
            return Response(quest_serializer.errors, status=status.HTTP_400_BAD_REQUEST)


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


class UserQuestQuestionAttemptByQuestView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserQuestQuestionAttemptSerializer

    def get_queryset(self):
        quest_id = self.kwargs['quest_id']
        user_quest_attempts = UserQuestAttempt.objects.filter(quest=quest_id)
        return UserQuestQuestionAttempt.objects.filter(user_quest_attempt__in=user_quest_attempts).order_by('-id')


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

            serializer.update(instances, serializer.validated_data)
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserQuestQuestionAttemptListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]

    queryset = UserQuestQuestionAttempt.objects.all().order_by('-id')
    serializer_class = UserQuestQuestionAttemptSerializer


class UserQuestQuestionAttemptManageView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]

    queryset = UserQuestQuestionAttempt.objects.all().order_by('-id')
    serializer_class = UserQuestQuestionAttemptSerializer


class BulkUpdateUserQuestQuestionAttemptView(APIView):
    def patch(self, request, *args, **kwargs):
        serializer = UserQuestQuestionAttemptSerializer(data=request.data, many=True)
        if serializer.is_valid():
            ids = [item.get('id') for item in request.data if 'id' in item]
            instances = UserQuestQuestionAttempt.objects.filter(id__in=ids)

            # Add logging to debug
            print(f" UserQuestQuestionAttempt Instances found: {[instance.id for instance in instances]}")

            if len(instances) != len(ids):
                return Response({"detail": "One or more instances not found."}, status=status.HTTP_404_NOT_FOUND)

            serializer.update(instances, serializer.validated_data)
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserQuestQuestionAttemptByUserQuestAttemptView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserQuestQuestionAttemptSerializer

    def get_queryset(self):
        user_quest_attempt_id = self.kwargs['user_quest_attempt_id']
        return UserQuestQuestionAttempt.objects.filter(user_quest_attempt=user_quest_attempt_id).order_by('question__number')


class AttemptAnswerRecordListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]

    queryset = AttemptAnswerRecord.objects.all().order_by('-id')
    serializer_class = AttemptAnswerRecordSerializer


class AttemptAnswerRecordManageView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]

    queryset = AttemptAnswerRecord.objects.all().order_by('-id')
    serializer_class = AttemptAnswerRecordSerializer



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

