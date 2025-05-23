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
    # 만기 이자율(%)
    mtrt_int = models.FloatField('만기 이자율', default=0.0)
    # 저축 기간(개월)
    save_trm = models.PositiveIntegerField('저축 기간(개월)', null=True, blank=True)

class DepositOption(models.Model):
    product = models.ForeignKey(DepositProduct, on_delete=models.CASCADE, related_name='options')
    save_trm = models.IntegerField()  # 예: 6개월, 12개월
    intr_rate = models.FloatField()
    intr_rate2 = models.FloatField()
    
class FinancialCompany(models.Model):
    fin_co_no     = models.CharField(max_length=10, unique=True)  # 회사 코드
    kor_co_nm     = models.CharField(max_length=100)              # 회사 이름
    homp_url      = models.URLField(blank=True, null=True)
    cal_tel       = models.CharField(max_length=20, blank=True, null=True)
    dcls_chrg_man = models.CharField(max_length=200, blank=True, null=True)

class CompanyBranch(models.Model):
    company   = models.ForeignKey(FinancialCompany, on_delete=models.CASCADE, related_name='branches')
    area_cd   = models.CharField(max_length=2)
    area_nm   = models.CharField(max_length=20)
    exis_yn   = models.BooleanField()

class AnnuityProduct(models.Model):
    fin_prdt_cd     = models.CharField(max_length=50, unique=True)   # 상품 코드
    fin_co          = models.ForeignKey(FinancialCompany, on_delete=models.SET_NULL, null=True)
    fin_prdt_nm     = models.CharField(max_length=200)
    avg_prft_rate   = models.FloatField()
    prdt_type_nm    = models.CharField(max_length=50)
    sale_strt_day   = models.DateField()