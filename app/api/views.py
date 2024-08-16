from rest_framework import generics
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from django.http import JsonResponse
from datetime import datetime, timedelta
from django.db.models import Count
import json
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
                    'quest': {
                        'id': new_quest_id
                    },
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


            # Convert quest field to Quest instance
            for item in serializer.validated_data:
                quest_data = item.pop('quest')
                item['quest'] = Quest.objects.get(id=quest_data['id'])

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
        total_enrollments = UserCourse.objects.count()
        new_enrollments_last_week = UserCourse.objects.filter(enrolled_on__gte=last_week).count()
        new_enrollments_percentage = (new_enrollments_last_week / total_enrollments) * 100 if total_enrollments > 0 else 0

        # 3. Total number of quest attempts and new attempts since last week
        total_quest_attempts = UserQuestAttempt.objects.count()
        new_quest_attempts_last_week = UserQuestAttempt.objects.filter(first_attempted_on__gte=last_week).count()
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
                'time_taken': int(perfectionist_badge_attempts.time_taken.total_seconds() * 1000),  # Convert to milliseconds and round to whole number                'quest_id': perfectionist_badge_attempts.quest_attempted.quest.id,
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
        user_courses = UserCourse.objects.filter(user=user_id).exclude(course__name="Private Course").distinct('course').order_by('course__id')

        # Aggregate the number of unique completed quests per course
        course_quest_completion = []
        for user_course in user_courses:
            course_id = user_course.course.id
            quest_attempts = UserQuestAttempt.objects.filter(user=user_id, quest__from_course=course_id, all_questions_submitted=True).distinct('quest')
            completed_quests = quest_attempts.count()
            total_quests = user_course.course.quests.count()
            completion_ratio = completed_quests / total_quests if total_quests > 0 else 0
            course_quest_completion.append({
                'course_id': course_id,
                'course_term': f"AY {user_course.course.term.academic_year.start_year} - {user_course.course.term.academic_year.end_year} {user_course.course.term.name}",
                'course_name': f"{user_course.course.code} {user_course.course.name}",
                'completed_quests': completed_quests,
                'total_quests': total_quests,
                'completion_ratio': completion_ratio
            })

        # Sort the results by completion ratio in descending order
        course_quest_completion.sort(key=lambda x: x['completion_ratio'], reverse=True)

        # Fetch a user's course badges and quest badges
        user_quest_badges = UserQuestBadge.objects.filter(quest_attempted__user=user_id)
        user_course_badges = UserCourseBadge.objects.filter(course_completed__user=user_id)

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
        # Fetch top 5 users with the most badges
        top_users = UserQuestBadge.objects.values('quest_attempted__user__id', 'quest_attempted__user__nickname') \
                        .annotate(badge_count=Count('badge')) \
                        .order_by('-badge_count')[:5]

        # Fetch badge details for each user
        user_badge_details = []
        for user in top_users:
            user_id = user['quest_attempted__user__id']
            quest_badges = UserQuestBadge.objects.filter(quest_attempted__user__id=user_id)
            course_badges = UserCourseBadge.objects.filter(course_completed__user__id=user_id)
            quest_badges_serializer = UserQuestBadgeSerializer(quest_badges, many=True)
            course_badges_serializer = UserCourseBadgeSerializer(course_badges, many=True)
            total_badge_count = quest_badges.count() + course_badges.count()
            user_badge_details.append({
                'user_id': user_id,
                'nickname': user['quest_attempted__user__nickname'],
                'badge_count': total_badge_count,
                'quest_badges': quest_badges_serializer.data,
                'course_badges': course_badges_serializer.data
            })

        # Fetch top 5 most recent badge awards from both UserQuestBadge and UserCourseBadge
        recent_quest_badges = UserQuestBadge.objects.all().order_by('-id')[:5]
        recent_course_badges = UserCourseBadge.objects.all().order_by('-id')[:5]

        # Combine and sort the badges by the most recent award date
        recent_badges = sorted(
            list(recent_quest_badges) + list(recent_course_badges),
            key=lambda badge: badge.awarded_date,
            reverse=True
        )[:5]

        # Serialize the combined badge data
        recent_badges_data = []
        for badge in recent_badges:
            if isinstance(badge, UserCourseBadge):
                user_id = badge.course_completed.user.id
                nickname = badge.course_completed.user.nickname
                badge_data = UserCourseBadgeSerializer(badge).data

            else:
                user_id = badge.quest_attempted.user.id
                nickname = badge.quest_attempted.user.nickname
                badge_data = UserQuestBadgeSerializer(badge).data

            badge_data.update({
                'user_id': user_id,
                'nickname': nickname
            })
            recent_badges_data.append(badge_data)

        # Combine the data
        data = {
            'top_users_with_most_badges': user_badge_details,
            'recent_badge_awards': recent_badges_data
        }

        return Response(data)


