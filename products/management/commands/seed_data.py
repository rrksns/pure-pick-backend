import random
from django.core.management.base import BaseCommand
from django.db import transaction
from faker import Faker
from products.models import Brand, Product, Ingredient

class Command(BaseCommand):
    help = '초기 더미 데이터를 생성합니다.'

    def handle(self, *args, **kwargs):
        fake = Faker('ko_KR')

        self.stdout.write('데이터 생성을 시작합니다... (약 10~20초 소요)')

        # 1. 브랜드 생성 (10개)
        brands = []
        for _ in range(10):
            # get_or_create: 중복되면 가져오고, 없으면 생성함 (에러 방지)
            brand, created = Brand.objects.get_or_create(
                name=fake.company(),
                defaults={'website_url': fake.url()}
            )
            brands.append(brand)
        self.stdout.write(self.style.SUCCESS(f'Brand 데이터 준비 완료 (총 {len(brands)}개)'))

        # 2. 성분 생성 (50개)
        ingredients = []
        for _ in range(50):
            # 화학명 생성 시도, 실패시 단어 조합
            try:
                raw_name = fake.unique.chemical_name()
            except:
                raw_name = fake.word() + " 추출물"

            ing, created = Ingredient.objects.get_or_create(
                name=raw_name,
                defaults={
                    'ewg_score': random.randint(1, 10),
                    'description': fake.sentence()
                }
            )
            ingredients.append(ing)
        self.stdout.write(self.style.SUCCESS(f'Ingredient 데이터 준비 완료 (총 {len(ingredients)}개)'))

        # 3. 상품 생성 및 성분 연결 (100개)
        created_count = 0

        # 상품은 이름이 같아도 생성이 가능하도록 두되, 너무 많은 중복 방지를 위해 약간의 랜덤성 추가
        with transaction.atomic():
            for _ in range(100):
                # Product는 중복 허용 정책이라면 create, 아니라면 get_or_create.
                # 여기서는 더미데이터 양을 늘리기 위해 create를 유지하되 랜덤성을 강화
                product = Product.objects.create(
                    name=fake.catch_phrase() + " " + random.choice(['토너', '로션', '크림', '앰플', '세럼']) + f" {random.randint(1, 999)}",
                    brand=random.choice(brands),
                    price=random.randint(100, 2000) * 100,
                    image_url=fake.image_url()
                )

                # 제품 하나당 성분 3~10개 랜덤 매칭
                selected_ingredients = random.sample(ingredients, k=random.randint(3, 10))
                product.ingredients.add(*selected_ingredients)
                created_count += 1

        self.stdout.write(self.style.SUCCESS(f'Product {created_count}개 생성 완료!'))