from django.db import models
from django.contrib.auth import get_user_model
User = get_user_model()


# Create your models here.
class Subscription(models.Model):
    class Meta:
        verbose_name_plural = "Subscriptions"
        db_table = "subscription"
 
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    plan_name = models.CharField(max_length=100,default='Premium Plan')
    currency_symbol = models.CharField(max_length=100,default='USD')
    plan_price = models.DecimalField(max_digits=8, decimal_places=2, default=4.90)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
 
    def __str__(self):
        return str(self.user)