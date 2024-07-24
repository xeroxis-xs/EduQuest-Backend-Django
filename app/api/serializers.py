from rest_framework import serializers
from .utils import split_full_name
from django.utils import timezone
from datetime import datetime
from django.db import transaction
# from django.contrib.auth.models import User
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


class EduquestUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = EduquestUser
        fields = ['id', 'first_name', 'last_name', 'username', 'email', 'nickname', 'last_login',
                  'updated_at', 'is_superuser', 'is_active', 'is_staff']
        read_only_fields = ['first_name', 'last_name', 'is_superuser', 'updated_at', 'username']

    def create(self, validated_data):
        username = validated_data['username']
        validated_data['email'] = validated_data['email'].upper()
        nickname = username.replace("#", "")
        first_name, last_name = split_full_name(nickname)
        # Default handling if nickname is not provided
        user = EduquestUser.objects.create(
            first_name=first_name,
            last_name=last_name,
            nickname=nickname,
            **validated_data
        )
        return user

    def update(self, instance, validated_data):
        first_name, last_name = split_full_name(validated_data.pop('nickname'))
        instance.first_name = first_name
        instance.last_name = last_name
        instance.save()
        return instance


class ImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Image
        fields = '__all__'


class AcademicYearSerializer(serializers.ModelSerializer):
    class Meta:
        model = AcademicYear
        fields = '__all__'


class TermSerializer(serializers.ModelSerializer):
    academic_year = AcademicYearSerializer()
    class Meta:
        model = Term
        fields = '__all__'

    def create(self, validated_data):
        academic_year_data = validated_data.pop('academic_year')
        academic_year = AcademicYear.objects.get_or_create(**academic_year_data)
        term = Term.objects.create(academic_year=academic_year, **validated_data)
        return term

    def update(self, instance, validated_data):
        academic_year_data = validated_data.pop('academic_year')
        academic_year = AcademicYear.objects.get(**academic_year_data)

        instance.academic_year = academic_year

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance


class CourseSerializer(serializers.ModelSerializer):
    term = TermSerializer()
    image = ImageSerializer()

    class Meta:
        model = Course
        fields = '__all__'
        extra_kwargs = {
            'enrolled_users': {'required': False}  # Make the enrolled_users field optional during create
        }

    def create(self, validated_data):
        term_data = validated_data.pop('term')
        image_data = validated_data.pop('image')

        academic_year_data = term_data.pop('academic_year')

        # Retrieve AcademicYear
        academic_year = AcademicYear.objects.get(**academic_year_data)

        # Retrieve Term under the AcademicYear
        term = Term.objects.get(academic_year=academic_year, **term_data)

        # Retrieve Image
        image = Image.objects.get(**image_data)

        # Create Course using the retrieved or newly created Term
        course = Course.objects.create(term=term, image=image, **validated_data)
        return course

    def update(self, instance, validated_data):
        term_data = validated_data.pop('term')
        image_data = validated_data.pop('image')
        # Remove academic_year from term_data
        academic_year_data = term_data.pop('academic_year')
        term = Term.objects.get(**term_data)
        image = Image.objects.get(**image_data)
        instance.term = term
        instance.image = image

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class QuestSerializer(serializers.ModelSerializer):
    from_course = CourseSerializer()
    organiser = EduquestUserSerializer()
    image = ImageSerializer()
    participants = EduquestUserSerializer(many=True, read_only=True, required=False)
    total_max_score = serializers.SerializerMethodField(read_only=True)
    total_questions = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Quest
        fields = '__all__'

    def get_total_max_score(self, obj):
        return obj.total_max_score()

    def get_total_questions(self, obj):
        return obj.total_questions()

    def create(self, validated_data):
        from_course_data = validated_data.pop('from_course')
        term_data = from_course_data.pop('term')
        academic_year_data = term_data.pop('academic_year')
        enrolled_users_data = from_course_data.pop('enrolled_users')
        course_image_data = from_course_data.pop('image')
        organiser_data = validated_data.pop('organiser')
        # organiser_data.pop('username')
        image_data = validated_data.pop('image')

        academic_year = AcademicYear.objects.get(**academic_year_data)
        from_course = Course.objects.get(
            term=Term.objects.get(academic_year=academic_year, **term_data),
            image=Image.objects.get(**course_image_data),
            **from_course_data)
        organiser = EduquestUser.objects.get(**organiser_data)
        image = Image.objects.get(**image_data)

        # Create the Quest instance with the retrieved Course and EduquestUser
        quest = Quest.objects.create(
            from_course=from_course,
            organiser=organiser,
            image=image,
            **validated_data
        )

        return quest

    def update(self, instance, validated_data):
        from_course_data = validated_data.pop('from_course')
        course_image_data = from_course_data.pop('image')
        image_data = validated_data.pop('image')
        # Remove term from from_course_data
        term_data = from_course_data.pop('term')

        from_course = Course.objects.get(**from_course_data)
        image = Image.objects.get(**image_data)
        instance.from_course = from_course
        instance.image = image

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class AnswerSerializer(serializers.ModelSerializer):
    # Explicitly include the id field
    id = serializers.IntegerField(required=False)

    class Meta:
        model = Answer
        fields = '__all__'
        extra_kwargs = {
            'question': {'required': False}  # Make the question field optional during create
        }


class BulkQuestionSerializer(serializers.ListSerializer):
    def update(self, instances, validated_data):
        for instance in instances:
            print("Instance:", instance.id)  # Debugging
        # Create a mapping of instance IDs to instances themselves
        instance_mapping = {instance.id: instance for instance in instances}

        print("Instance Mapping:", instance_mapping)  # Debugging

        # Process the validated data
        for item in validated_data:
            print("Validated Item:", item)  # Debugging
            instance_id = item.get('id', None)
            if instance_id is not None and instance_id in instance_mapping:
                print("Instance ID found:", instance_id)  # Debugging
                print("Instance:", instance_mapping[instance_id])  # Debugging
                self.child.update(instance_mapping[instance_id], item)
            else:
                print("Instance ID not found:", instance_id)  # Debugging
                # Handle insertions or raise an exception
                pass

        # Optionally, handle deletions
        return instances


class QuestionSerializer(serializers.ModelSerializer):
    answers = AnswerSerializer(many=True)
    id = serializers.IntegerField(required=False)  # Explicitly include the id field
    class Meta:
        model = Question
        fields = '__all__'
        list_serializer_class = BulkQuestionSerializer

    # Create question with new answers (without specifying answer IDs)
    def create(self, validated_data):
        answers_data = validated_data.pop('answers', [])
        question = Question.objects.create(**validated_data)

        # Note: Do not specify 'question' in each answer_data
        for answer_data in answers_data:
            Answer.objects.create(question=question, **answer_data)

        return question

    def update(self, instance, validated_data):
        answers_data = validated_data.pop('answers', [])

        # Handle nested answers
        for answer_data in answers_data:
            answer_id = answer_data.get('id')
            if answer_id:
                answer_instance = Answer.objects.get(id=answer_id)
                answer_instance.text = answer_data.get('text', answer_instance.text)
                answer_instance.is_correct = answer_data.get('is_correct', answer_instance.is_correct)
                answer_instance.save()
            else:
                Answer.objects.create(question=instance, **answer_data)

        # Update other fields as usual
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class UserQuestAttemptSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    total_score_achieved = serializers.SerializerMethodField(required=False)

    class Meta:
        model = UserQuestAttempt
        fields = '__all__'

    def get_total_score_achieved(self, obj):
        return obj.total_score_achieved()

    def create(self, validated_data):
        user_quest_attempt = UserQuestAttempt.objects.create(**validated_data)

        # Create a UserQuestQuestionAttempt instance with empty selected_answers for newly created UserQuestAttempt
        questions = Question.objects.filter(from_quest=user_quest_attempt.quest)

        # Create UserQuestQuestionAttempt for each question in the quest
        for question in questions:
            user_quest_question_attempt = UserQuestQuestionAttempt.objects.create(
                user_quest_attempt=user_quest_attempt,
                question=question,
                score_achieved=0,
            )
            # Create AttemptAnswerRecord for each answer in the question
            # Set is_selected to False for each answer
            answers = Answer.objects.filter(question=question)
            for answer in answers:
                AttemptAnswerRecord.objects.create(
                    user_quest_question_attempt=user_quest_question_attempt,
                    answer=answer,
                    is_selected=False  # Marking is_selected as False
                )

        return user_quest_attempt

    def update(self, instance, validated_data):
        validated_data.pop('time_taken', None)  # Remove 'time_taken' from validated_data
        # Use the latest 'last_attempted_on' from validated_data or the existing one if not provided
        last_attempted_on = validated_data.get('last_attempted_on', instance.last_attempted_on)

        # Calculate 'time_taken' using the chosen 'last_attempted_on' and 'first_attempted_on'
        instance.time_taken = (last_attempted_on - instance.first_attempted_on).total_seconds() * 1000

        # Update other fields as usual
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance


class AttemptAnswerRecordSerializer(serializers.ModelSerializer):
    answer = AnswerSerializer()
    id = serializers.IntegerField(required=False)  # Explicitly include the id field
    class Meta:
        model = AttemptAnswerRecord
        fields = '__all__'

    def create(self, validated_data):
        answer_data = validated_data.pop('answer')
        answer = Answer.objects.get(id=answer_data['id'])
        attempt_answer_record = AttemptAnswerRecord.objects.create(
            user_quest_question_attempt=validated_data['user_quest_question_attempt'],
            answer=answer,
            is_selected=validated_data['is_selected']
        )
        return attempt_answer_record

    def update(self, instance, validated_data):
        answer_data = validated_data.pop('answer')
        answer = Answer.objects.get(id=answer_data['id'])
        instance.answer = answer

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class BulkUserQuestQuestionAttemptSerializer(serializers.ListSerializer):
    def update(self, instances, validated_data):
        # Create a mapping of instance IDs to instances themselves
        instance_mapping = {instance.id: instance for instance in instances}

        print("Instance Mapping:", instance_mapping)  # Debugging

        # Process the validated data
        for item in validated_data:
            print("Validated Item:", item)  # Debugging
            instance_id = item.get('id', None)
            if instance_id is not None and instance_id in instance_mapping:
                self.child.update(instance_mapping[instance_id], item)
            else:
                print("Instance ID not found:", instance_id)  # Debugging
                # Handle insertions or raise an exception
                pass

        # Optionally, handle deletions
        return instances


class UserQuestQuestionAttemptSerializer(serializers.ModelSerializer):
    selected_answers = AttemptAnswerRecordSerializer(many=True, required=False)
    question = QuestionSerializer(required=False)
    id = serializers.IntegerField(required=False)

    class Meta:
        model = UserQuestQuestionAttempt
        fields = '__all__'
        list_serializer_class = BulkUserQuestQuestionAttemptSerializer

    def create(self, validated_data):
        question_data = validated_data.pop('question')
        question = Question.objects.get(id=question_data['id'])

        user_quest_question_attempt = UserQuestQuestionAttempt.objects.create(
            user_quest_attempt=validated_data['user_quest_attempt'],
            question=question,
            score_achieved=validated_data['score_achieved'],
            # submitted=validated_data['submitted']
        )
        return user_quest_question_attempt


    def update(self, instance, validated_data):
        selected_answers_data = validated_data.pop('selected_answers', [])

        # Handle nested selected_answers
        for selected_answer_data in selected_answers_data:
            attempt_answer_record_id = selected_answer_data.get('id')
            attempt_answer_record = AttemptAnswerRecord.objects.get(id=attempt_answer_record_id)

            # Ensure 'answer' is treated as a dictionary
            answer_data = selected_answer_data.get('answer')
            if isinstance(answer_data, dict):  # Ensure it's a dictionary
                answer_id = answer_data['id']
                answer_instance = Answer.objects.get(id=answer_id)
                attempt_answer_record.answer = answer_instance

            attempt_answer_record.is_selected = selected_answer_data['is_selected']
            attempt_answer_record.save()

        # Handle question data
        question_data = validated_data.pop('question')
        question = Question.objects.get(id=question_data['id'])
        instance.question = question

        # Update other fields as usual
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class UserCourseCompletionSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserCourseCompletion
        fields = '__all__'


class BadgeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Badge
        fields = '__all__'
