from django.db import models
import uuid


class User(models.Model):
    unique_user_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    aadhar_id = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    email_id = models.EmailField(unique=True)
    annual_income = models.DecimalField(max_digits=15, decimal_places=2)
    credit_score = models.IntegerField(default=0)

    def __str__(self):
        return self.name