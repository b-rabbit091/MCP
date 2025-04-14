from django.contrib.auth.models import User
from django.db import models


class ICD10(models.Model):
    code = models.CharField(max_length=20, unique=True)  # Added unique=True for code
    description = models.TextField()

    def __str__(self):
        return f"{self.code}: {self.description}"


class Case(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    icd10_id = models.ManyToManyField(ICD10)

    def __str__(self):
        return self.title


class Submission(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='submissions',blank=True, null=True)
    case_number = models.CharField(max_length=50)
    submitted_icd = models.CharField(max_length=10,null=True, blank=True)
    is_correct = models.BooleanField(default=None)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username}'s submission for case {self.case_number}"
