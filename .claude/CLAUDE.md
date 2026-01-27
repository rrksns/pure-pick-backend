# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**PurePick** is a production-ready cosmetic product search backend service featuring comprehensive testing (33 tests), type hints, pagination, and performance optimizations. The stack combines MySQL for relational data, Elasticsearch for full-text search, and Redis for caching and ranking.

**Status**: All 5 improvement phases completed (Type hints, Error handling, Testing, Pagination, Performance optimization).

All microservices run via Docker Compose with automatic health checks to ensure proper initialization order.

## Architecture

### Core Components
- **Django REST Framework API** (Port 8000): Main application serving product search and ranking endpoints
- **MySQL 8.0** (Port 3306): Primary relational database storing products, brands, and ingredients
- **Elasticsearch 7.17** (Port 9200): Full-text search engine with denormalized document structure
- **Redis** (Port 6379): Cache layer (Look-aside pattern, TTL 1h) and ranking aggregation (Sorted Sets)
- **Kibana** (Port 5601): Optional visualization tool for Elasticsearch data inspection

### Data Model
```
Brand (1) ──→ (N) Product
           ↓
        Ingredients (M:N through ProductIngredient)
```

Key models in `products/models.py`:
- **TimeStampedModel**: Abstract base with `created_at`/`updated_at` auto-tracking
- **Brand**: Cosmetic brand information with website URL
- **Ingredient**: Chemical ingredients with EWG safety scores (1-10 scale)
- **Product**: Core entity linking brands and ingredients via foreign/many-to-many relationships

### Search Architecture Pattern
**Look-aside Caching** → **Elasticsearch Multi-match Query** → **MySQL Detail Fetch** → **Redis Ranking**

1. **Input Validation**: Trim whitespace, check query length (1-100 chars)
2. **Cache Check**: Redis key `search:{query}` with dynamic TTL
   - High popularity (score > 10): 2 hours
   - Medium (2-10): 1 hour
   - Low (< 2): 30 minutes
3. **ES Search**: Multi-match query with fuzzy matching on `name`, `brand.name`, `ingredients.name`
4. **MySQL Fetch**: Preserve Elasticsearch order using `Case/When` annotation
5. **Pagination**: PageNumberPagination with configurable page size (default: 20)
6. **Cache Store**: Save paginated response with dynamic TTL
7. **Ranking Update**: Increment Redis Sorted Set score atomically

### Elasticsearch Document Structure
`ProductDocument` in `products/documents.py` denormalizes relational data using:
- **ObjectField** for brand (single object)
- **NestedField** for ingredients (array of objects) — enables proper array querying

Auto-sync enabled (`ignore_signals=False`) for development; consider Celery for production at scale.

## Development Commands

### Docker Startup & Initialization
```bash
# Build and start all services (MySQL, Redis, ES, Django)
docker-compose up -d --build

# View container logs (follow)
docker-compose logs -f web

# Stop all services
docker-compose down
```

### Data Setup
```bash
# Generate 100 dummy products with 10 brands and 50 ingredients
docker-compose exec web python manage.py seed_data

# Rebuild Elasticsearch indices (required after schema changes)
docker-compose exec web python manage.py search_index --rebuild
```

### Django Management
```bash
# Run Django shell (useful for testing queries)
docker-compose exec web python manage.py shell

# Create database migrations
docker-compose exec web python manage.py makemigrations

# Apply migrations
docker-compose exec web python manage.py migrate

# Create superuser
docker-compose exec web python manage.py createsuperuser
```

### API Exploration
- **Swagger UI**: http://localhost:8000/swagger/
- **ReDoc**: http://localhost:8000/redoc/
- **Kibana**: http://localhost:5601/ (inspect ES indices and data)

### Key API Endpoints
```
GET  /api/products/items/                           # List all products (paginated)
POST /api/products/items/                           # Create product
GET  /api/products/items/{id}/                      # Retrieve product
PATCH /api/products/items/{id}/                     # Update product
DELETE /api/products/items/{id}/                    # Delete product
GET  /api/products/items/search/?q=keyword          # Full-text search (paginated, cached)
     &page=1&page_size=20
GET  /api/products/items/ranking/                   # Top 10 trending keywords
```

All endpoints return proper HTTP status codes (200, 400, 500, 503) with structured error messages.

## Important Implementation Details

### Type Hints
All functions and methods include complete type annotations:
- Views: `Request → Response`, helper methods with `str → int`, `str → None`, etc.
- Models: Return type annotations on `__str__() → str`
- Use `typing` module: `Dict`, `List`, `Any`, `Optional`

### Cache Management
- Cache key format: `search:{query}` with **dynamic TTL** based on popularity
- Ranking increments on **every** search (both cache hits and misses) using `zincrby`
- Helper method `_get_cache_ttl(keyword: str) → int` determines TTL automatically
- Use `django.core.cache` for generic caching, `django_redis.get_redis_connection()` for direct Redis control

### Pagination
- REST Framework `PageNumberPagination` configured in `settings.py`
- Default page size: 20 items
- Query params: `?page=2&page_size=50`
- Response format includes `count`, `next`, `previous`, `results`

### Elasticsearch Configuration
- Index name: `products`
- Single shard, no replicas (suitable for development)
- Fuzzy matching enabled on multi_match queries for typo correction
- Connection via `elasticsearch_dsl` library at version <8.0 (critical constraint)

### MySQL & Connection
- Database: `purepick` (production), `purepick_test` (test environment, auto-detected)
- Character set: utf8mb4 (emoji support)
- Host: `db` (Docker Compose service name)
- Performance optimizations:
  - `.select_related('brand')` on all Product queries
  - `.prefetch_related('ingredients')` for M2M relationships
  - Preserve Elasticsearch order using `Case/When` with `annotate(_order=...)`

### Redis & Ranking
- Database 1 used for caching (DB 0 reserved for system use)
- Sorted Set key: `search_ranking`
- Ranking scores are integer increments (use `zincrby` for atomic operations)

## Configuration Files

- **settings.py**: Django configuration, Elasticsearch/Redis/MySQL connections, Swagger setup
- **docker-compose.yml**: Service orchestration with critical MySQL healthcheck
- **requirements.txt**: Fixed versions (especially Elasticsearch <8.0) to prevent TypeErrors
- **Dockerfile**: Python 3.11 with MySQL client libraries

## Testing & Validation

### Running Tests
```bash
# All tests (33 total)
docker-compose exec web python manage.py test products.tests --verbosity=2

# Specific test class
docker-compose exec web python manage.py test products.tests.ProductSearchAPITests

# Single test method
docker-compose exec web python manage.py test products.tests.ProductSearchAPITests.test_search_caching_hit
```

### Test Coverage
- **ProductModelTests** (6 tests): Model creation, relationships, validation
- **ProductSearchAPITests** (6 tests): Search functionality, caching, ranking
- **ProductRankingAPITests** (4 tests): Ranking retrieval, format validation
- **ProductSearchErrorHandlingTests** (7 tests): Input validation, ES/Redis failures
- **ProductRankingErrorHandlingTests** (2 tests): Redis connection errors
- **ProductListAPITests** (5 tests): CRUD operations
- **ProductPaginationTests** (3 tests): Pagination functionality

### Health Checks
- Container status: `docker-compose ps`
- Test search API: `curl "http://localhost:8000/api/products/items/search/?q=토너&page=1"`
- Monitor ES indices: Kibana at localhost:5601
- Monitor Redis state: `docker-compose exec redis redis-cli ZRANGE search_ranking 0 -1 WITHSCORES`

## Common Issues & Solutions

| Issue | Solution |
|-------|----------|
| Django fails to connect to MySQL | Ensure MySQL healthcheck passes; check `docker-compose logs db` for startup errors |
| Elasticsearch connection refused | Wait 30s for ES startup; verify `elasticsearch:9200` returns cluster info |
| TypeErrors with Elasticsearch library | Verify `requirements.txt` has `elasticsearch<8.0`; reinstall if needed |
| Cache not working / Redis connection issues | Check Redis running: `docker-compose logs redis` |
| Search returns empty results | Rebuild indices: `docker-compose exec web python manage.py search_index --rebuild` |
| Tests fail with connection errors | Use mocked tests; check if services are running for integration tests |
| Type hints show errors in IDE | Install type stubs: `pip install types-redis django-stubs` |
| Pagination not working | Verify `REST_FRAMEWORK.DEFAULT_PAGINATION_CLASS` is set in settings.py |

## Code Quality Standards

### Type Hints (Required)
All new code must include type annotations:
```python
def _get_cache_ttl(self, keyword: str) -> int:
    """Calculate cache TTL based on keyword popularity."""
    ...

def search(self, request: Request) -> Response:
    """Handle product search with caching and ranking."""
    ...
```

### Error Handling (Required)
Use structured error handling with appropriate HTTP codes:
- `400 Bad Request`: Invalid input (empty query, too long, invalid format)
- `500 Internal Server Error`: Unexpected errors, database failures
- `503 Service Unavailable`: External service failures (ES, Redis connection)

Always include:
- `logger` calls at appropriate levels (DEBUG, INFO, WARNING, ERROR)
- User-friendly error messages in response
- Try-except blocks around external service calls

### Logging Standards
```python
logger.info(f"Cache hit: {query}")           # Success operations
logger.warning(f"Cache failure: {str(e)}")   # Recoverable issues
logger.error(f"ES connection failed")        # Service failures
logger.exception(f"Unexpected error")        # Unhandled exceptions
```

### Testing Requirements
When adding new features:
1. Write tests BEFORE implementation (TDD)
2. Cover happy path, edge cases, and error conditions
3. Use `@patch` for external dependencies (ES, Redis)
4. Ensure test database isolation with `cache.clear()` and Redis cleanup

## Future Enhancement Considerations

- ✅ ~~Add pagination to search results~~ (Completed)
- ✅ ~~Implement type hints~~ (Completed)
- ✅ ~~Add comprehensive error handling~~ (Completed)
- Implement Celery for async Elasticsearch index updates at scale
- Implement API rate limiting with Django Ratelimit
- Add authentication/authorization layer (JWT or OAuth2)
- Consider read replicas for MySQL in production
- Add monitoring with Prometheus/Grafana
