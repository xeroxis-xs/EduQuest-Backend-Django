from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from .models import (
    EduquestUser,
    AcademicYear,
    Term,
    Course,
    Quest,
    Question,
    Answer,
    UserQuestAttempt,
    UserQuestQuestionAttempt,
    UserCourseCompletion,
    Badge
)
from .serializers import (
    EduquestUserSerializer,
    AcademicYearSerializer,
    TermSerializer,
    CourseSerializer,
    QuestSerializer,
    QuestionSerializer,
    AnswerSerializer,
    UserQuestAttemptSerializer,
    UserQuestQuestionAttemptSerializer,
    UserCourseCompletionSerializer,
    BadgeSerializer
)
# from django.http import HttpResponse

User = get_user_model()


class EduquestUserListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]

    queryset = EduquestUser.objects.all()
    serializer_class = EduquestUserSerializer


class EduquestUserManageView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]

    queryset = EduquestUser.objects.all()
    serializer_class = EduquestUserSerializer


class AcademicYearListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]

    queryset = AcademicYear.objects.all()
    serializer_class = AcademicYearSerializer


class AcademicYearManageView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]

    queryset = AcademicYear.objects.all()
    serializer_class = AcademicYearSerializer


class TermListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]

    queryset = Term.objects.all()
    serializer_class = TermSerializer


class TermManageView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]

    queryset = Term.objects.all()
    serializer_class = TermSerializer


class CourseListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]

    queryset = Course.objects.all()
    serializer_class = CourseSerializer


class CourseManageView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]

    queryset = Course.objects.all()
    serializer_class = CourseSerializer


class QuestListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]

    queryset = Quest.objects.all()
    serializer_class = QuestSerializer


class QuestManageView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]

    queryset = Quest.objects.all()
    serializer_class = QuestSerializer


class QuestionListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]

    queryset = Question.objects.all()
    serializer_class = QuestionSerializer


class QuestionManageView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]

    queryset = Question.objects.all()
    serializer_class = QuestionSerializer


class AnswerListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]

    queryset = Answer.objects.all()
    serializer_class = AnswerSerializer


class AnswerManageView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]

    queryset = Answer.objects.all()
    serializer_class = AnswerSerializer


class UserQuestAttemptListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]

    queryset = UserQuestAttempt.objects.all()
    serializer_class = UserQuestAttemptSerializer


class UserQuestAttemptManageView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]

    queryset = UserQuestAttempt.objects.all()
    serializer_class = UserQuestAttemptSerializer


class UserQuestQuestionAttemptListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]

    queryset = UserQuestQuestionAttempt.objects.all()
    serializer_class = UserQuestQuestionAttemptSerializer


class UserQuestQuestionAttemptManageView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]

    queryset = UserQuestQuestionAttempt.objects.all()
    serializer_class = UserQuestQuestionAttemptSerializer


class UserCourseCompletionListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]

    queryset = UserCourseCompletion.objects.all()
    serializer_class = UserCourseCompletionSerializer


class UserCourseCompletionManageView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]

    queryset = UserCourseCompletion.objects.all()
    serializer_class = UserCourseCompletionSerializer


class BadgeListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]

    queryset = Badge.objects.all()
    serializer_class = BadgeSerializer


class BadgeManageView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]

    queryset = Badge.objects.all()
    serializer_class = BadgeSerializer
