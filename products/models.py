from django.db import models
from typing import Optional

class TimeStampedModel(models.Model):
    """
    모든 모델의 기본이 되는 추상 모델
    생성 시간과 수정 시간을 자동으로 기록하여 운영 편의성을 높임
    """
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class Brand(TimeStampedModel):
    """화장품 브랜드 정보"""
    name = models.CharField(max_length=100, db_index=True)  # 검색 성능을 위해 인덱스 추가
    website_url = models.URLField(blank=True, null=True)

    def __str__(self) -> str:
        return self.name

class Ingredient(TimeStampedModel):
    """
    성분 정보
    화해 서비스의 핵심 데이터. EWG 등급(안전도)을 포함.
    """
    name = models.CharField(max_length=100, unique=True)  # 성분명 중복 방지
    ewg_score = models.IntegerField(default=1, help_text="1~10 사이의 EWG 안전 등급")
    description = models.TextField(blank=True)

    def __str__(self) -> str:
        return f"{self.name} (EWG: {self.ewg_score})"

class Product(TimeStampedModel):
    """
    화장품 상품 정보
    Brand와 1:N 관계, Ingredient와 N:M 관계
    """
    name = models.CharField(max_length=200, db_index=True)
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, related_name='products')
    price = models.IntegerField(default=0)
    image_url = models.URLField(blank=True, null=True)

    # 핵심 관계: 하나의 화장품은 여러 성분을 가짐
    ingredients = models.ManyToManyField(Ingredient, related_name='products')

    class Meta:
        ordering = ['-id']  # 최신순 정렬 기본

    def __str__(self) -> str:
        return self.name