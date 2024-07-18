from rest_framework import generics
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import (
    EduquestUser,
    Image,
    AcademicYear,
    Term,
    Course,
    Quest,
    Question,
    Answer,
    UserQuestAttempt,
    UserQuestQuestionAttempt,
    AttemptAnswerRecord,
    UserCourseCompletion,
    Badge
)
from .serializers import (
    EduquestUserSerializer,
    ImageSerializer,
    AcademicYearSerializer,
    TermSerializer,
    CourseSerializer,
    QuestSerializer,
    QuestionSerializer,
    AnswerSerializer,
    UserQuestAttemptSerializer,
    UserQuestQuestionAttemptSerializer,
    AttemptAnswerRecordSerializer,
    UserCourseCompletionSerializer,
    BadgeSerializer
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


class CourseEnrollmentAPIView(APIView):
    def post(self, request, course_id):
        course = get_object_or_404(Course, id=course_id)
        user_ids = request.data.get('user_ids', [])

        # Fetch users and enroll them
        users_to_enroll = EduquestUser.objects.filter(id__in=user_ids)
        for user in users_to_enroll:
            course.enrolled_users.add(user)

        return Response({"message": "Users enrolled successfully."}, status=status.HTTP_200_OK)


class CourseByTermView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CourseSerializer

    def get_queryset(self):
        term_id = self.kwargs['term_id']
        return Course.objects.filter(term=term_id).order_by('-id')


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
            print(f"IDs to be updated: {ids}")
            print(f"Instances found: {[instance.id for instance in instances]}")

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


class UserCourseCompletionListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]

    queryset = UserCourseCompletion.objects.all().order_by('-id')
    serializer_class = UserCourseCompletionSerializer


class UserCourseCompletionManageView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]

    queryset = UserCourseCompletion.objects.all().order_by('-id')
    serializer_class = UserCourseCompletionSerializer


class BadgeListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]

    queryset = Badge.objects.all().order_by('-id')
    serializer_class = BadgeSerializer


class BadgeManageView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]

    queryset = Badge.objects.all().order_by('-id')
    serializer_class = BadgeSerializer
