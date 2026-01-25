# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**PurePick** is a cosmetic product search backend service using Elasticsearch and Redis for high-performance search and real-time trend analytics. The stack combines MySQL for data storage, Elasticsearch for full-text search, and Redis for caching and ranking.

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

1. Check Redis cache (key: `search:{query}`)
2. If miss, execute Elasticsearch multi_match query with fuzzy matching (oops correction)
3. Fetch product details from MySQL using returned IDs
4. Cache serialized response for 1 hour
5. Increment Sorted Set score for keyword ranking

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
GET  /api/products/items/                    # List all products
POST /api/products/items/                    # Create product
GET  /api/products/items/{id}/              # Retrieve product
PATCH /api/products/items/{id}/             # Update product
DELETE /api/products/items/{id}/            # Delete product
GET  /api/products/items/search/?q=keyword  # Full-text search with caching
GET  /api/products/items/ranking/           # Top 10 trending keywords
```

## Important Implementation Details

### Cache Management
- Cache key format: `search:{query}` with 1-hour TTL
- Ranking increments on **every** search (both cache hits and misses)
- Use `django.core.cache` for generic caching, `django_redis.get_redis_connection()` for direct Redis control

### Elasticsearch Configuration
- Index name: `products`
- Single shard, no replicas (suitable for development)
- Fuzzy matching enabled on multi_match queries for typo correction
- Connection via `elasticsearch_dsl` library at version <8.0 (critical constraint)

### MySQL & Connection
- Database: `purepick`
- Character set: utf8mb4 (emoji support)
- Host: `db` (Docker Compose service name)
- Queries use `.select_related()` and `.prefetch_related()` for optimization

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

- Run health checks: `docker-compose ps` (verify all services "healthy" or "running")
- Test search API: `curl "http://localhost:8000/api/products/items/search/?q=토너"`
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

## Future Enhancement Considerations

- Implement Celery for async Elasticsearch index updates at scale
- Add pagination to search results
- Implement API rate limiting
- Add authentication/authorization layer
- Separate test database configuration
- Consider read replicas for MySQL in production
