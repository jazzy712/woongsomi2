from django.db import models

# Create your models here.
class DepositProduct(models.Model):
    fin_prdt_cd = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    bank = models.CharField(max_length=50)
    join_way = models.TextField()
    join_member = models.TextField()
    spcl_cnd = models.TextField(blank=True, null=True)
    max_limit = models.BigIntegerField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

class DepositOption(models.Model):
    product = models.ForeignKey(DepositProduct, on_delete=models.CASCADE, related_name='options')
    save_trm = models.IntegerField()  # 예: 6개월, 12개월
    intr_rate = models.FloatField()
    intr_rate2 = models.FloatField()
