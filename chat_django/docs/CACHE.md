# Cache Configuration

The chat application supports two caching modes:
1. In-memory cache (default)
2. Redis cache (recommended for production)

## Configuration

The caching behavior is controlled by environment variables:

```bash
# Enable/disable Redis (default: false)
USE_REDIS=false

# Redis connection URL (default: redis://localhost:6379/0)
REDIS_URL=redis://localhost:6379/0
```

## Development Mode

By default, the application uses an in-memory cache which:
- Stores data in Python dictionaries
- Persists only during server runtime
- Doesn't require any external services
- Is suitable for development and testing
- Doesn't support data sharing between multiple server instances

To use in-memory cache, either:
- Don't set any cache-related environment variables, or
- Explicitly set `USE_REDIS=false`

## Production Mode

For production deployments, Redis cache is recommended as it:
- Persists data across server restarts
- Supports data sharing between multiple server instances
- Provides better memory management
- Allows for cache size monitoring and control

To use Redis cache:
1. Set `USE_REDIS=true`
2. Configure `REDIS_URL` to point to your Redis instance
3. Ensure Redis is running and accessible

Example production configuration:
```bash
USE_REDIS=true
REDIS_URL=redis://your-redis-host:6379/0
```

## Fallback Behavior

If Redis is enabled but cannot be connected to:
1. A warning will be logged
2. The system will automatically fall back to in-memory cache
3. The application will continue to function, but without persistence

## Implementation Details

The caching system is implemented in `chat/cache.py` and provides:

- `BaseCache`: Abstract base class defining the cache interface
- `RedisCache`: Redis implementation
- `InMemoryCache`: Simple dictionary-based implementation
- `get_cache()`: Factory function that returns the appropriate cache implementation

Cache operations available:
- `get(key)`: Retrieve a value
- `set(key, value, expiry=None)`: Store a value with optional expiry
- `delete(key)`: Remove a value

## Best Practices

1. Development:
   - Use in-memory cache for simplicity
   - No need to run Redis locally

2. Testing:
   - Use in-memory cache for isolation
   - Easier to reset between tests

3. Production:
   - Always use Redis
   - Configure appropriate memory limits
   - Monitor Redis health
   - Set up proper authentication if Redis is exposed