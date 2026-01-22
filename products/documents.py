from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry
from .models import Product, Brand, Ingredient

@registry.register_document
class ProductDocument(Document):
    # 1. 관계 데이터 처리 (Join 성능 해결)
    # ES는 NoSQL이라 데이터를 '평면화(Flatten)'해서 저장해야 성능이 좋습니다.
    brand = fields.ObjectField(properties={
        'name': fields.TextField(),
    })

    ingredients = fields.NestedField(properties={
        'name': fields.TextField(),
        'ewg_score': fields.IntegerField(),
    })

    class Index:
        # ES에 저장될 인덱스 이름 (RDB의 Table Name과 비슷)
        name = 'products'
        settings = {
            'number_of_shards': 1,
            'number_of_replicas': 0
        }

    class Django:
        model = Product # 연결할 모델

        # ES에 저장할 필드들 (검색에 쓰일 것들 위주로)
        fields = [
            'name',      # 상품명
            'price',     # 가격 (필터링용)
            'image_url', # 결과 보여주기용
            'id',
        ]

        # 2. 데이터 동기화 옵션
        # DB가 변하면 ES도 자동으로 변하게 할 것인가? (False면 수동 업데이트)
        # 개발 편의를 위해 True로 두겠지만, 대용량 실무에선 Celery로 뺍니다.
        ignore_signals = False