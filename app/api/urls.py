from django.urls import path, include
from .views import (
    EduquestUserViewSet,
    AcademicYearViewSet,
    TermViewSet,
    ImageViewSet,
    CourseViewSet,
    CourseGroupViewSet,
    UserCourseGroupEnrollmentViewSet,
    QuestViewSet,
    QuestionViewSet,
    AnswerViewSet,
    UserQuestAttemptViewSet,
    UserAnswerAttemptViewSet,
    BadgeViewSet,
    UserQuestBadgeViewSet,
    UserCourseBadgeViewSet,
    DocumentViewSet,
    AnalyticsPartOneView,
    AnalyticsPartTwoView,
    AnalyticsPartThreeView,
    AnalyticsPartFourView,
    test_view,
    status_view
)
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'eduquest-users', EduquestUserViewSet, basename='eduquest-users')
router.register(r'images', ImageViewSet, basename='images')
router.register(r'academic-years', AcademicYearViewSet, basename='academic-years')
router.register(r'terms', TermViewSet, basename='terms')
router.register(r'courses', CourseViewSet, basename='courses')
router.register(r'course-groups', CourseGroupViewSet, basename='course-groups')
router.register(r'user-course-group-enrollments', UserCourseGroupEnrollmentViewSet, basename='user-course-group-enrollments')
router.register(r'quests', QuestViewSet, basename='quests')
router.register(r'questions', QuestionViewSet, basename='questions')
router.register(r'answers', AnswerViewSet, basename='answers')
router.register(r'user-quest-attempts', UserQuestAttemptViewSet, basename='user-quest-attempts')
router.register(r'user-answer-attempts', UserAnswerAttemptViewSet, basename='user-answer-attempts')
router.register(r'badges', BadgeViewSet, basename='badges')
router.register(r'user-quest-badges', UserQuestBadgeViewSet, basename='user-quest-badges')
router.register(r'user-course-badges', UserCourseBadgeViewSet, basename='user-course-badges')
router.register(r'documents', DocumentViewSet, basename='documents')


urlpatterns = [
    path('test/', test_view),
    path('status/', status_view),
    path('', include(router.urls)),
    path("analytics/part-one/", AnalyticsPartOneView.as_view(), name='analytics-part-one'),
    path("analytics/part-two/", AnalyticsPartTwoView.as_view(), name='analytics-part-two'),
    path("analytics/part-three/", AnalyticsPartThreeView.as_view(), name='analytics-part-three'),
    path("analytics/part-four/", AnalyticsPartFourView.as_view(), name='analytics-part-four'),
]
