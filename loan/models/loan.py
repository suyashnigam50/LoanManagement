from django.db import models
from loan.models.user import User
import uuid


class Loan(models.Model):
    LOAN_TYPE_CHOICES = (
        ('Car', 'Car'),
        ('Home', 'Home'),
        ('Education', 'Education'),
        ('Personal', 'Personal')
    )
    loan_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    user = models.ForeignKey('User', on_delete=models.CASCADE)  # String reference 'User'
    loan_type = models.CharField(max_length=20, choices=LOAN_TYPE_CHOICES)
    loan_amount = models.DecimalField(max_digits=15, decimal_places=2)
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2)
    term_period = models.IntegerField()  # in months
    disbursement_date = models.DateField()

    def __str__(self):
        return f"{self.loan_type} Loan for {self.user.name}"
