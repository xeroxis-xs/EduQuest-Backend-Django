from django.test import TestCase
from ...models import EduquestUser

class EduquestUserModelTest(TestCase):

    @classmethod
    def setUp(self):
        self.user = EduquestUser.objects.create_user(
            username="testuser#123",
            password="password123",
            first_name="",
            last_name="",
            email="testuser@example.com"
        )

    def test_save_method_nickname_autopopulation(self):
        """Test that the nickname is auto-populated based on the username."""
        self.assertEqual(self.user.nickname, "testuser123")

    def test_save_method_first_name_last_name(self):
        """Test that the first_name and last_name are populated correctly on creation."""
        self.assertEqual(self.user.first_name, "testuser123")
        self.assertEqual(self.user.last_name, "")

    def test_save_method_no_override(self):
        """Test that the save method does not override first_name or last_name if they are set."""
        self.user.first_name = "John"
        self.user.last_name = "Doe"
        self.user.save()
        self.assertEqual(self.user.first_name, "John")
        self.assertEqual(self.user.last_name, "Doe")

    def test_save_method_update(self):
        """Test that updating a user does not change the nickname if the username is unchanged."""
        self.user.total_points = 50
        self.user.save()
        self.assertEqual(self.user.nickname, "testuser123")
        self.assertEqual(self.user.total_points, 50)

    def test_nickname_editable(self):
        """Test that nickname remains editable after user creation."""
        self.user.nickname = "newnickname"
        self.user.save()
        self.assertEqual(self.user.nickname, "newnickname")

    def test_update_is_staff(self):
        """Test that is_staff can be updated."""
        self.user.is_staff = True
        self.user.save()
        self.assertTrue(self.user.is_staff)

    def test_is_active_default(self):
        """Test that is_active defaults to True."""
        self.assertTrue(self.user.is_active)

    def test_is_staff_default(self):
        """Test that is_staff defaults to False."""
        self.assertFalse(self.user.is_staff)

    def test_total_points_default(self):
        """Test that total_points defaults to 0."""
        self.assertEqual(self.user.total_points, 0)
