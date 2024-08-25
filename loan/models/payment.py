from django.db import models
from .loan import Loan

class Payment(models.Model):
    loan = models.ForeignKey(Loan, on_delete=models.CASCADE)
    date = models.DateField()
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2)
    
    def __str__(self):
        return f"Payment of {self.amount_paid} for {self.loan.loan_type}"
