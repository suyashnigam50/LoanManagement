from django.db import models

class EMI(models.Model):
    loan = models.ForeignKey('Loan', on_delete=models.CASCADE)  # Use string reference 'Loan'
    due_date = models.DateField()
    amount_due = models.DecimalField(max_digits=10, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return f"EMI due on {self.due_date} for Loan {self.loan.loan_id}"
