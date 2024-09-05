from django.test import TestCase
from ...models import Image

class ImageModelTest(TestCase):
    def setUp(self):
        self.image = Image.objects.create(name="Test Image", filename="test_image.jpg")

    def test_image_creation(self):
        self.assertEqual(self.image.name, "Test Image")
        self.assertEqual(self.image.filename, "test_image.jpg")

    def test_image_str(self):
        self.assertEqual(str(self.image), "Test Image")
