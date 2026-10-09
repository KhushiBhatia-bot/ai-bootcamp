from django.db import models


class PolicyEvaluation(models.Model):
    scenario = models.TextField()
    status = models.CharField(max_length=30)
    reason = models.TextField()
    claimed_policy = models.CharField(max_length=255, blank=True)
    claimed_page = models.CharField(max_length=50, blank=True)
    evidence = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.status} - {self.created_at}"


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