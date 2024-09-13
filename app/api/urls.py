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
    # EduquestUserListCreateView,
    # EduquestUserManageView,
    ImageListCreateView,
    ImageManageView,
    AcademicYearListCreateView,
    AcademicYearManageView,
    TermListCreateView,
    TermManageView,
    CourseListCreateView,
    NonPrivateCourseListCreateView,
    CourseManageView,
    # CourseByTermView,
    # CourseByUserView,
    CourseGroupListCreateView,
    CourseGroupManageView,
    UserCourseGroupEnrollmentListCreateView,
    UserCourseGroupEnrollmentManageView,
    QuestImportView,
    QuestListCreateView,
    QuestManageView,
    QuestByCourseView,
    PrivateQuestByUserView,
    QuestByEnrolledUser,
    QuestionListCreateView,
    QuestionManageView,
    QuestionByQuestView,
    BulkCreateQuestionView,
    BulkUpdateQuestionView,
    AnswerListCreateView,
    AnswerManageView,
    AnswerByQuestView,
    UserQuestAttemptListCreateView,
    UserQuestAttemptManageView,
    UserQuestAttemptByUserQuestView,
    UserQuestAttemptByQuestView,
    BulkUpdateUserQuestAttemptView,
    UserQuestQuestionAttemptListCreateView,
    UserQuestQuestionAttemptManageView,
    UserQuestQuestionAttemptByQuestView,
    BulkUpdateUserQuestQuestionAttemptView,
    AttemptAnswerRecordListCreateView,
    AttemptAnswerRecordManageView,
    UserQuestQuestionAttemptByUserQuestAttemptView,
    BadgeListCreateView,
    BadgeManageView,
    UserQuestBadgeListCreateView,
    UserQuestBadgeManageView,
    UserQuestBadgeByUserView,
    UserCourseBadgeListCreateView,
    UserCourseBadgeManageView,
    UserCourseBadgeByUserView,
    DocumentUploadView,
    DocumentManageView,
    DocumentByUserView,
    AnalyticsPartOneView,
    AnalyticsPartTwoView,
    AnalyticsPartThreeView,
    # AnalyticsPartFourView
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

urlpatterns = [
    path('', include(router.urls)),
    # path("EduquestUser/", EduquestUserListCreateView.as_view(), name='EduquestUser-list-create'),
    # path("EduquestUser/<str:email>/", EduquestUserManageView.as_view(), name='EduquestUser-retrieve-update-destroy'),

    # path("Image/", ImageListCreateView.as_view(), name='Image-list-create'),
    # path("Image/<int:pk>/", ImageManageView.as_view(), name='Image-retrieve-update-destroy'),
    #
    # path("AcademicYear/", AcademicYearListCreateView.as_view(), name='AcademicYear-list-create'),
    # path("AcademicYear/<int:pk>/", AcademicYearManageView.as_view(), name='AcademicYear-retrieve-update-destroy'),
    # path("Term/", TermListCreateView.as_view(), name='Term-list-create'),
    # path("Term/<int:pk>/", TermManageView.as_view(), name='Term-retrieve-update-destroy'),
    #
    # path("Course/", CourseListCreateView.as_view(), name='Course-list-create'),
    # path("Course/non-private/", NonPrivateCourseListCreateView.as_view(), name='Course-non-private-list-create'),
    # path("Course/<int:pk>/", CourseManageView.as_view(), name='Course-retrieve-update-destroy'),
    # # path("Course/by-term/<int:term_id>/", CourseByTermView.as_view(), name='Course-by-term'),
    # # path("Course/by-user/<int:user_id>/", CourseByUserView.as_view(), name='Course-by-user'),
    #
    # path("CourseGroup/", CourseGroupListCreateView.as_view(), name='CourseGroup-list-create'),
    # path("CourseGroup/<int:pk>/", CourseGroupManageView.as_view(), name='CourseGroup-retrieve-update-destroy'),
    #
    # path("UserCourseGroupEnrollment/", UserCourseGroupEnrollmentListCreateView.as_view(), name='UserCourseGroupEnrollment-list-create'),
    # path("UserCourseGroupEnrollment/<int:pk>/", UserCourseGroupEnrollmentManageView.as_view(), name='UserCourseGroupEnrollment-retrieve-update-destroy'),
    #
    # path("Quest/", QuestListCreateView.as_view(), name='Quest-list-create'),
    # path("Quest/import/", QuestImportView.as_view(), name='Quest-import'),
    # path("Quest/<int:pk>/", QuestManageView.as_view(), name='Quest-retrieve-update-destroy'),
    # path("Quest/by-course/<int:course_id>/", QuestByCourseView.as_view(), name='Quest-by-course'),
    # path("Quest/private/by-user/<int:user_id>/", PrivateQuestByUserView.as_view(), name='Private-Quest-by-user'),
    # path("Quest/by-enrolled-user/<int:user_id>/", QuestByEnrolledUser.as_view(), name='Quest-by-enrolled-user'),

    path("Question/", QuestionListCreateView.as_view(), name='Question-list-create'),
    path("Question/<int:pk>/", QuestionManageView.as_view(), name='Question-retrieve-update-destroy'),
    path("Question/by-quest/<int:quest_id>/", QuestionByQuestView.as_view(), name='Question-by-quest'),
    path('Question/bulk-create/', BulkCreateQuestionView.as_view(), name='bulk_create_questions'),
    path("Question/bulk-update/", BulkUpdateQuestionView.as_view(), name='bulk-update-question'),

    path("Answer/", AnswerListCreateView.as_view(), name='Answer-list-create'),
    path("Answer/<int:pk>/", AnswerManageView.as_view(), name='Answer-retrieve-update-destroy'),
    path("Answer/by-quest/<int:quest_id>/", AnswerByQuestView.as_view(), name='Answer-by-quest'),

    path("UserQuestAttempt/", UserQuestAttemptListCreateView.as_view(), name='UserQuestAttempt-list-create'),
    path("UserQuestAttempt/<int:pk>/", UserQuestAttemptManageView.as_view(), name='UserQuestAttempt-retrieve-update-destroy'),
    path("UserQuestAttempt/by-user/<int:user_id>/by-quest/<int:quest_id>/", UserQuestAttemptByUserQuestView.as_view(), name='UserQuestAttempt-by-user-quest'),
    path("UserQuestAttempt/by-quest/<int:quest_id>/", UserQuestAttemptByQuestView.as_view(), name='UserQuestAttempt-by-quest'),
    path('UserQuestAttempt/bulk-update/', BulkUpdateUserQuestAttemptView.as_view(), name='bulk-update-user-quest-attempt'),

    path("AttemptAnswerRecord/", AttemptAnswerRecordListCreateView.as_view(), name='AttemptAnswerRecord-list-create'),
    path("AttemptAnswerRecord/<int:pk>/", AttemptAnswerRecordManageView.as_view(), name='AttemptAnswerRecord-retrieve-update-destroy'),

    path("UserQuestQuestionAttempt/", UserQuestQuestionAttemptListCreateView.as_view(), name='UserQuestQuestionAttempt-list-create'),
    path("UserQuestQuestionAttempt/<int:pk>/", UserQuestQuestionAttemptManageView.as_view(), name='UserQuestQuestionAttempt-retrieve-update-destroy'),
    path("UserQuestQuestionAttempt/by-user-quest-attempt/<int:user_quest_attempt_id>", UserQuestQuestionAttemptByUserQuestAttemptView.as_view(), name='UserQuestQuestionAttemptByUserQuestAttempt-by-user-quest-attempt'),
    path('UserQuestQuestionAttempt/bulk-update/', BulkUpdateUserQuestQuestionAttemptView.as_view(), name='bulk-update-user-quest-question-attempt'),
    path('UserQuestQuestionAttempt/by-quest/<int:quest_id>', UserQuestQuestionAttemptByQuestView.as_view(), name='UserQuestQuestionAttempt-by-quest'),

    path("Badge/", BadgeListCreateView.as_view(), name='Badge-list-create'),
    path("Badge/<int:pk>/", BadgeManageView.as_view(), name='Badge-retrieve-update-destroy'),

    path("UserQuestBadge/", UserQuestBadgeListCreateView.as_view(), name='UserQuestBadge-list-create'),
    path("UserQuestBadge/<int:pk>/", UserQuestBadgeManageView.as_view(), name='UserQuestBadge-retrieve-update-destroy'),
    path("UserQuestBadge/by-user/<int:user_id>/", UserQuestBadgeByUserView.as_view(), name='UserQuestBadge-by-user'),

    path("UserCourseBadge/", UserCourseBadgeListCreateView.as_view(), name='UserCourseBadge-list-create'),
    path("UserCourseBadge/<int:pk>/", UserCourseBadgeManageView.as_view(), name='UserCourseBadge-retrieve-update-destroy'),
    path("UserCourseBadge/by-user/<int:user_id>/", UserCourseBadgeByUserView.as_view(), name='UserCourseBadge-by-user'),

    path("DocumentUpload/", DocumentUploadView.as_view(), name='Document-upload'),
    path("Document/<int:pk>/", DocumentManageView.as_view(), name='Document-retrieve-update-destroy'),
    path("Document/by-user/<int:user_id>/", DocumentByUserView.as_view(), name='Document-by-user'),

    path("Analytics/part-one/", AnalyticsPartOneView.as_view(), name='Analytics-part-one'),
    path("Analytics/part-two/<int:user_id>/", AnalyticsPartTwoView.as_view(), name='Analytics-part-two'),
    path("Analytics/part-three/", AnalyticsPartThreeView.as_view(), name='Analytics-part-three'),
    # path("Analytics/part-four/<int:user_id>/", AnalyticsPartFourView.as_view(), name='Analytics-part-four'),
]
