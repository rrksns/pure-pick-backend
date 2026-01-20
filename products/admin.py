from django.contrib import admin
from .models import Brand, Product, Ingredient

@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'created_at']

@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'ewg_score']
    search_fields = ['name'] # 관리자 페이지에서 검색 가능하도록 설정

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'brand', 'price']
    list_filter = ['brand'] # 브랜드별 필터링 기능
    search_fields = ['name']
    filter_horizontal = ['ingredients'] # N:M 관계를 예쁘게 선택하는 UI 제공