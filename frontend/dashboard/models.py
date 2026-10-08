from django.db import models


class Policy(models.Model):
    CATEGORY_CHOICES = [
        ("Security", "Security"),
        ("Finance", "Finance"),
        ("HR", "HR"),
        ("Operations", "Operations"),
        ("Legal", "Legal"),
        ("Other", "Other"),
    ]

    STATUS_CHOICES = [
        ("Processing", "Processing"),
        ("Ready", "Ready"),
        ("Failed", "Failed"),
    ]

    name = models.CharField(max_length=255)

    original_filename = models.CharField(
        max_length=255
    )

    file_path = models.CharField(
        max_length=500
    )

    category = models.CharField(
        max_length=50,
        choices=CATEGORY_CHOICES,
        default="Other",
    )

    pages = models.PositiveIntegerField(
        default=0
    )

    chunks = models.PositiveIntegerField(
        default=0
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="Processing",
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return self.name