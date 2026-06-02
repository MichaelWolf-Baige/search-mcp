"""Additional edge case tests for cache and health modules."""

import sys
import time
import asyncio

sys.path.insert(0, "D:/search-mcp")

print("=" * 60)
print("Edge Case Tests")
print("=" * 60)

# Edge Case 1: Non-200 status code with DEGRADED response time
print("\n1. Testing non-200 status code (should be UNHEALTHY, not DEGRADED)...")
try:
    from search_tool.utils.health import HealthChecker, HealthStatus
    import unittest.mock as mock

    checker = HealthChecker(timeout=5, degraded_threshold=100)

    # Slow response with 404 status
    with mock.patch('requests.get') as mock_get:
        mock_response = mock.Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        # Patch time to simulate slow response
        call_times = [100.0, 100.5, 100.5, 100.5]
        with mock.patch('time.time', side_effect=call_times):
            health = checker._check_url_sync("test_source", "https://test.url")

            # Bug check: should be UNHEALTHY (because status code != 200)
            # NOT DEGRADED (even if response time > threshold)
            assert health.status == HealthStatus.UNHEALTHY, \
                f"Expected UNHEALTHY for 404 status, got {health.status}"
            assert "404" in health.error_message, \
                f"Expected error message with 404, got {health.error_message}"

    print("   PASSED: Non-200 status correctly marked as UNHEALTHY")
except AssertionError as e:
    print(f"   BUG FOUND: {e}")
except Exception as e:
    print(f"   ERROR: {e}")

# Edge Case 2: Empty cache data
print("\n2. Testing cache with empty data...")
try:
    from search_tool.utils.cache import SearchCache

    cache = SearchCache()
    cache.clear()

    # Set empty list
    cache.set("engine", "query", 10, [])

    result = cache.get("engine", "query", 10)
    assert result is not None, "Empty list should still be cached"
    assert result == [], "Should return empty list"

    cache.clear()
    print("   PASSED: Empty data cached correctly")
except Exception as e:
    print(f"   FAILED: {e}")

# Edge Case 3: Same key with different data (overwrite)
print("\n3. Testing cache overwrite...")
try:
    from search_tool.utils.cache import SearchCache

    cache = SearchCache()
    cache.clear()

    cache.set("engine", "query", 10, [{"title": "Old"}])
    result = cache.get("engine", "query", 10)
    assert result[0]["title"] == "Old"

    # Overwrite with new data
    cache.set("engine", "query", 10, [{"title": "New"}])
    result = cache.get("engine", "query", 10)
    assert result[0]["title"] == "New", "Should have new data after overwrite"

    # Stats should still have 1 entry
    stats = cache.stats()
    assert stats["total_entries"] == 1, "Should have 1 entry after overwrite"

    cache.clear()
    print("   PASSED: Cache overwrite works correctly")
except Exception as e:
    print(f"   FAILED: {e}")

# Edge Case 4: TTL = 0 (immediate expiration) - BUG FIXED
print("\n4. Testing TTL=0 (immediate expiration) - testing bug fix...")
try:
    from search_tool.utils.cache import SearchCache

    cache = SearchCache()
    cache.clear()

    # Set with TTL=0
    cache.set("engine", "query", 10, [{"title": "Test"}], ttl=0)

    # Check entry TTL is 0
    entry = cache._memory_cache.get(cache._make_key("engine", "query", 10))
    assert entry.ttl == 0, f"Expected TTL=0, got {entry.ttl}"

    # Should expire immediately (time.time() - timestamp >= 0 always)
    result = cache.get("engine", "query", 10)
    assert result is None, "TTL=0 should expire immediately"

    cache.clear()
    print("   PASSED: TTL=0 expires immediately (bug fixed)")
except Exception as e:
    print(f"   FAILED: {e}")

# Edge Case 5: Special characters in query
print("\n5. Testing special characters in query...")
try:
    from search_tool.utils.cache import SearchCache

    cache = SearchCache()
    cache.clear()

    # Special characters: unicode, spaces, symbols
    special_queries = [
        "中文查询",
        "query with spaces",
        "query:special:chars",
        "query?param=value",
        "query&another",
    ]

    for q in special_queries:
        cache.set("engine", q, 10, [{"query": q}])
        result = cache.get("engine", q, 10)
        assert result is not None, f"Failed for query: {q}"
        assert result[0]["query"] == q, f"Data mismatch for: {q}"

    cache.clear()
    print("   PASSED: Special characters handled correctly")
except Exception as e:
    print(f"   FAILED: {e}")

# Edge Case 6: Large data in cache
print("\n6. Testing large data in cache...")
try:
    from search_tool.utils.cache import SearchCache

    cache = SearchCache()
    cache.clear()

    # Large data
    large_data = [{"title": f"Result {i}", "url": f"https://example.com/{i}"} for i in range(1000)]
    cache.set("engine", "query", 10, large_data)

    result = cache.get("engine", "query", 10)
    assert result is not None
    assert len(result) == 1000

    cache.clear()
    print("   PASSED: Large data cached correctly")
except Exception as e:
    print(f"   FAILED: {e}")

# Edge Case 7: get_healthy_sources with empty dict
print("\n7. Testing get_healthy_sources with empty dict...")
try:
    from search_tool.utils.health import HealthChecker, HealthStatus, SourceHealth

    checker = HealthChecker()

    # Set some statuses
    checker._health_status["source"] = SourceHealth(
        name="source", status=HealthStatus.HEALTHY,
        last_check=time.time(), response_time=100.0
    )

    # Empty source dict
    healthy = checker.get_healthy_sources({})
    assert healthy == {}, "Empty input should return empty output"

    print("   PASSED: Empty dict handled correctly")
except Exception as e:
    print(f"   FAILED: {e}")

# Edge Case 8: _check_engine_sync mock test
print("\n8. Testing _check_engine_sync with mock...")
try:
    from search_tool.utils.health import HealthChecker, HealthStatus
    import unittest.mock as mock

    checker = HealthChecker(timeout=5, degraded_threshold=1000)

    # Mock engine available
    with mock.patch('search_tool.engines.social.get_social_engine') as mock_get_engine:
        mock_engine = mock.Mock()
        mock_engine.is_available.return_value = True
        mock_get_engine.return_value = mock_engine

        health = checker._check_engine_sync("hackernews")

        assert health.name == "hackernews"
        assert health.status == HealthStatus.HEALTHY
        assert health.error_message is None

    print("   PASSED: _check_engine_sync with available engine")
except Exception as e:
    print(f"   FAILED: {e}")

# Edge Case 9: _check_engine_sync with unavailable engine
print("\n9. Testing _check_engine_sync with unavailable engine...")
try:
    from search_tool.utils.health import HealthChecker, HealthStatus
    import unittest.mock as mock

    checker = HealthChecker(timeout=5)

    # Mock engine unavailable
    with mock.patch('search_tool.engines.social.get_social_engine') as mock_get_engine:
        mock_engine = mock.Mock()
        mock_engine.is_available.return_value = False
        mock_get_engine.return_value = mock_engine

        health = checker._check_engine_sync("hackernews")

        assert health.status == HealthStatus.UNHEALTHY
        assert health.error_message == "Engine not available"

    print("   PASSED: Unavailable engine marked correctly")
except Exception as e:
    print(f"   FAILED: {e}")

# Edge Case 10: Check response_time calculation accuracy
print("\n10. Testing response_time calculation in _check_url_sync...")
try:
    from search_tool.utils.health import HealthChecker, HealthStatus
    import unittest.mock as mock

    checker = HealthChecker(timeout=5)

    # Test with controlled time
    call_times = [100.0, 100.25, 100.25, 100.25]  # 250ms elapsed

    with mock.patch('requests.get') as mock_get:
        mock_response = mock.Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        with mock.patch('time.time', side_effect=call_times):
            health = checker._check_url_sync("test", "https://test.url")

            # Response time should be 250ms
            assert health.response_time == 250.0, \
                f"Expected 250.0, got {health.response_time}"

    print("   PASSED: Response time calculation correct")
except AssertionError as e:
    print(f"   BUG FOUND: {e}")
except Exception as e:
    print(f"   ERROR: {e}")

# Edge Case 11: Async URL check mock test
print("\n11. Testing _check_url_async with mock...")
try:
    from search_tool.utils.health import HealthChecker, HealthStatus
    import unittest.mock as mock

    checker = HealthChecker(timeout=5, degraded_threshold=1000)

    async def test_async():
        # Mock aiohttp session
        mock_session = mock.MagicMock()
        mock_response = mock.MagicMock()
        mock_response.status = 200

        # Setup async context managers
        mock_session.__aenter__ = mock.AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = mock.AsyncMock(return_value=None)
        mock_session.get = mock.MagicMock()
        mock_session.get.return_value = mock_response
        mock_response.__aenter__ = mock.AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = mock.AsyncMock(return_value=None)

        with mock.patch('aiohttp.ClientSession', return_value=mock_session):
            with mock.patch('aiohttp.ClientTimeout'):
                with mock.patch('aiohttp.TCPConnector'):
                    health = await checker._check_url_async("test_source", "https://test.url")

                    return health

    health = asyncio.run(test_async())

    assert health.name == "test_source"
    assert health.status == HealthStatus.HEALTHY

    print("   PASSED: Async URL check works")
except Exception as e:
    print(f"   FAILED: {e}")

# Edge Case 12: Cache key collision test
print("\n12. Testing cache key collision (different inputs)...")
try:
    from search_tool.utils.cache import SearchCache

    cache = SearchCache()

    # Check different inputs produce different keys
    inputs = [
        ("engine1", "query", 10, None),
        ("engine1", "query", 10, "platform"),
        ("engine2", "query", 10, None),
        ("engine1", "different", 10, None),
        ("engine1", "query", 20, None),
    ]

    keys = [cache._make_key(e, q, l, p) for e, q, l, p in inputs]

    # All keys should be unique
    assert len(keys) == len(set(keys)), "Keys should be unique for different inputs"

    print("   PASSED: No key collisions")
except Exception as e:
    print(f"   FAILED: {e}")

# Edge Case 13: Health status summary counts
print("\n13. Testing summary with UNKNOWN status...")
try:
    from search_tool.utils.health import HealthChecker, HealthStatus, SourceHealth

    checker = HealthChecker()

    # Only UNKNOWN sources (not in _health_status)
    # get_summary should return 0 for unknown since UNKNOWN is not in _health_status values
    checker._health_status.clear()

    summary = checker.get_summary()
    assert summary["unknown"] == 0, "Unknown count should be 0 for empty status"

    print("   PASSED: Unknown status handling correct")
except Exception as e:
    print(f"   FAILED: {e}")

print("\n" + "=" * 60)
print("Edge Case Tests Completed")
print("=" * 60)