from rest_framework import serializers
from .models import Brand, Ingredient, Product

class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = ['id', 'name', 'website_url']

class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ['id', 'name', 'ewg_score']

class ProductSerializer(serializers.ModelSerializer):
    brand = BrandSerializer(read_only=True) # 브랜드 정보 포함
    ingredients = IngredientSerializer(many=True, read_only=True) # 성분 리스트 포함

    class Meta:
        model = Product
        fields = ['id', 'name', 'brand', 'price', 'ingredients', 'image_url', 'created_at']