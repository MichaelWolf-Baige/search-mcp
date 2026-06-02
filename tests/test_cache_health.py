"""Test cache and health modules."""

import pytest
import time
import asyncio
import hashlib


class TestSearchCache:
    """Test SearchCache class."""

    def test_cache_basic_set_get(self):
        """Test basic set and get operations."""
        from search_tool.utils.cache import SearchCache

        cache = SearchCache()
        cache.clear()

        # Test set and get
        test_data = [{"title": "Test Result", "url": "https://example.com"}]
        cache.set("test_engine", "test_query", 10, test_data)

        # Verify get returns the same data
        result = cache.get("test_engine", "test_query", 10)
        assert result is not None
        assert len(result) == 1
        assert result[0]["title"] == "Test Result"

        cache.clear()

    def test_cache_with_platform(self):
        """Test cache with platform parameter."""
        from search_tool.utils.cache import SearchCache

        cache = SearchCache()
        cache.clear()

        # Set cache with platform
        test_data = [{"title": "Platform Test"}]
        cache.set("social", "python", 10, test_data, platform="zhihu")

        # Get without platform should return None (different key)
        result_no_platform = cache.get("social", "python", 10)
        assert result_no_platform is None

        # Get with platform should return data
        result_with_platform = cache.get("social", "python", 10, platform="zhihu")
        assert result_with_platform is not None
        assert result_with_platform[0]["title"] == "Platform Test"

        cache.clear()

    def test_cache_ttl_expiration(self):
        """Test cache TTL expiration mechanism."""
        from search_tool.utils.cache import SearchCache

        # Create cache with short TTL
        cache = SearchCache(default_ttl=2)  # 2 seconds TTL
        cache.clear()

        # Set cache
        test_data = [{"title": "TTL Test"}]
        cache.set("engine", "query", 5, test_data)

        # Immediately get should return data
        result = cache.get("engine", "query", 5)
        assert result is not None

        # Wait for TTL to expire
        time.sleep(3)

        # After TTL expired, should return None
        result_expired = cache.get("engine", "query", 5)
        assert result_expired is None

        cache.clear()

    def test_cache_custom_ttl(self):
        """Test cache with custom TTL."""
        from search_tool.utils.cache import SearchCache

        cache = SearchCache(default_ttl=300)
        cache.clear()

        # Set cache with custom short TTL
        test_data = [{"title": "Custom TTL"}]
        cache.set("engine", "query", 5, test_data, ttl=1)

        # Immediately should work
        result = cache.get("engine", "query", 5)
        assert result is not None

        # Wait for custom TTL
        time.sleep(2)

        # Should be expired
        result_expired = cache.get("engine", "query", 5)
        assert result_expired is None

        cache.clear()

    def test_cache_stats(self):
        """Test cache statistics functionality."""
        from search_tool.utils.cache import SearchCache

        cache = SearchCache()
        cache.clear()

        # Initial stats
        stats = cache.stats()
        assert stats["total_entries"] == 0
        assert stats["valid_entries"] == 0
        assert stats["hit_count"] == 0
        assert stats["miss_count"] == 0
        assert stats["hit_rate"] == 0

        # Add some entries
        cache.set("e1", "q1", 5, [{"title": "1"}])
        cache.set("e2", "q2", 5, [{"title": "2"}])

        # Get stats after adding
        stats = cache.stats()
        assert stats["total_entries"] == 2
        assert stats["valid_entries"] == 2

        # Hit one entry
        result = cache.get("e1", "q1", 5)
        assert result is not None

        stats = cache.stats()
        assert stats["hit_count"] == 1
        assert stats["miss_count"] == 0
        assert stats["hit_rate"] == 1.0

        # Miss one entry
        result = cache.get("nonexistent", "query", 5)
        assert result is None

        stats = cache.stats()
        assert stats["hit_count"] == 1
        assert stats["miss_count"] == 1
        assert stats["hit_rate"] == 0.5

        cache.clear()

    def test_cache_clear(self):
        """Test cache clear functionality."""
        from search_tool.utils.cache import SearchCache

        cache = SearchCache()
        cache.clear()

        # Add entries
        cache.set("e1", "q1", 5, [{"title": "1"}])
        cache.set("e2", "q2", 5, [{"title": "2"}])

        # Verify entries exist
        assert cache.get("e1", "q1", 5) is not None

        # Clear cache
        cache.clear()

        # Verify all cleared
        stats = cache.stats()
        assert stats["total_entries"] == 0
        assert stats["hit_count"] == 0
        assert stats["miss_count"] == 0

        # All get operations should return None
        assert cache.get("e1", "q1", 5) is None

    def test_cache_key_generation(self):
        """Test cache key generation logic."""
        from search_tool.utils.cache import SearchCache

        cache = SearchCache()

        # Test key generation
        key1 = cache._make_key("engine1", "query1", 10)
        key2 = cache._make_key("engine1", "query1", 10)
        assert key1 == key2  # Same inputs should produce same key

        # Different inputs should produce different keys
        key3 = cache._make_key("engine2", "query1", 10)
        assert key1 != key3

        # Different limit should produce different key
        key4 = cache._make_key("engine1", "query1", 20)
        assert key1 != key4

        # Different platform should produce different key
        key5 = cache._make_key("engine1", "query1", 10, "platform1")
        assert key1 != key5

        # Key should be MD5 hash format (32 hex characters)
        assert len(key1) == 32

        # Verify key is consistent with expected hash
        expected_key_data = "engine1:query1:10:"
        expected_key = hashlib.md5(expected_key_data.encode()).hexdigest()
        assert key1 == expected_key

    def test_cache_invalidate(self):
        """Test cache invalidate functionality."""
        from search_tool.utils.cache import SearchCache

        cache = SearchCache()
        cache.clear()

        # Add entries
        cache.set("engine", "query1", 5, [{"title": "1"}])
        cache.set("engine", "query2", 5, [{"title": "2"}])

        # Verify both exist
        assert cache.get("engine", "query1", 5) is not None
        assert cache.get("engine", "query2", 5) is not None

        # Invalidate one entry
        cache.invalidate("engine", "query1", 5)

        # Verify invalidated entry gone, other remains
        assert cache.get("engine", "query1", 5) is None
        assert cache.get("engine", "query2", 5) is not None

        cache.clear()

    def test_cache_global_instance(self):
        """Test global cache instance functions."""
        from search_tool.utils.cache import get_cache, clear_cache

        # Get global instance
        cache1 = get_cache()
        cache2 = get_cache()
        assert cache1 is cache2  # Should be same instance

        # Clear global cache
        clear_cache()

        stats = cache1.stats()
        assert stats["total_entries"] == 0


class TestHealthChecker:
    """Test HealthChecker class."""

    def test_health_status_enum(self):
        """Test HealthStatus enum values."""
        from search_tool.utils.health import HealthStatus

        assert HealthStatus.HEALTHY.value == "healthy"
        assert HealthStatus.DEGRADED.value == "degraded"
        assert HealthStatus.UNHEALTHY.value == "unhealthy"
        assert HealthStatus.UNKNOWN.value == "unknown"

    def test_source_health_dataclass(self):
        """Test SourceHealth dataclass."""
        from search_tool.utils.health import SourceHealth, HealthStatus

        # Create SourceHealth instance
        health = SourceHealth(
            name="test_source",
            status=HealthStatus.HEALTHY,
            last_check=time.time(),
            response_time=100.0,
            error_message=None
        )

        assert health.name == "test_source"
        assert health.status == HealthStatus.HEALTHY
        assert health.response_time == 100.0
        assert health.error_message is None

        # With error message
        health_error = SourceHealth(
            name="error_source",
            status=HealthStatus.UNHEALTHY,
            last_check=time.time(),
            response_time=0,
            error_message="Connection failed"
        )
        assert health_error.error_message == "Connection failed"

    def test_health_checker_init(self):
        """Test HealthChecker initialization."""
        from search_tool.utils.health import HealthChecker

        checker = HealthChecker(timeout=5, degraded_threshold=1000)

        assert checker.timeout == 5
        assert checker.degraded_threshold == 1000
        assert checker._check_interval == 300
        assert len(checker._health_status) == 0

    def test_get_status_unknown(self):
        """Test get_status for unknown source."""
        from search_tool.utils.health import HealthChecker, HealthStatus

        checker = HealthChecker()

        # No health status recorded, should return UNKNOWN
        status = checker.get_status("nonexistent_source")
        assert status == HealthStatus.UNKNOWN

    def test_should_skip_logic(self):
        """Test should_skip method logic."""
        from search_tool.utils.health import HealthChecker, HealthStatus, SourceHealth

        checker = HealthChecker()

        # Unknown source - should not skip (need to check)
        assert checker.should_skip("unknown_source") == False

        # Manually set health status
        checker._health_status["healthy_source"] = SourceHealth(
            name="healthy_source",
            status=HealthStatus.HEALTHY,
            last_check=time.time(),
            response_time=100.0
        )
        checker._health_status["unhealthy_source"] = SourceHealth(
            name="unhealthy_source",
            status=HealthStatus.UNHEALTHY,
            last_check=time.time(),
            response_time=0,
            error_message="Failed"
        )
        checker._health_status["degraded_source"] = SourceHealth(
            name="degraded_source",
            status=HealthStatus.DEGRADED,
            last_check=time.time(),
            response_time=3000.0
        )

        # HEALTHY - should not skip
        assert checker.should_skip("healthy_source") == False

        # UNHEALTHY - should skip
        assert checker.should_skip("unhealthy_source") == True

        # DEGRADED - should not skip (still works)
        assert checker.should_skip("degraded_source") == False

    def test_get_healthy_sources(self):
        """Test get_healthy_sources filtering."""
        from search_tool.utils.health import HealthChecker, HealthStatus, SourceHealth

        checker = HealthChecker()

        # Set up health statuses
        checker._health_status["source1"] = SourceHealth(
            name="source1",
            status=HealthStatus.HEALTHY,
            last_check=time.time(),
            response_time=100.0
        )
        checker._health_status["source2"] = SourceHealth(
            name="source2",
            status=HealthStatus.UNHEALTHY,
            last_check=time.time(),
            response_time=0,
            error_message="Failed"
        )
        checker._health_status["source3"] = SourceHealth(
            name="source3",
            status=HealthStatus.DEGRADED,
            last_check=time.time(),
            response_time=3000.0
        )

        # Test filtering
        source_dict = {
            "source1": "https://url1.com",
            "source2": "https://url2.com",
            "source3": "https://url3.com",
            "source4": "https://url4.com"  # Unknown status
        }

        healthy_sources = checker.get_healthy_sources(source_dict)

        # Should include HEALTHY, DEGRADED, and UNKNOWN
        # Should exclude UNHEALTHY
        assert "source1" in healthy_sources  # HEALTHY
        assert "source2" not in healthy_sources  # UNHEALTHY
        assert "source3" in healthy_sources  # DEGRADED (still works)
        assert "source4" in healthy_sources  # UNKNOWN (not yet checked)

    def test_needs_refresh(self):
        """Test needs_refresh logic."""
        from search_tool.utils.health import HealthChecker, HealthStatus, SourceHealth

        checker = HealthChecker()

        # No health status - needs refresh
        assert checker.needs_refresh() == True

        # Set health status and check time
        checker._health_status["source"] = SourceHealth(
            name="source",
            status=HealthStatus.HEALTHY,
            last_check=time.time(),
            response_time=100.0
        )
        checker._last_check_time = time.time()

        # Just checked - does not need refresh
        assert checker.needs_refresh() == False

        # Simulate old check time
        checker._last_check_time = time.time() - 400  # More than check_interval (300)

        # Should need refresh now
        assert checker.needs_refresh() == True

    def test_get_summary(self):
        """Test get_summary method."""
        from search_tool.utils.health import HealthChecker, HealthStatus, SourceHealth

        checker = HealthChecker()

        # Empty summary
        summary = checker.get_summary()
        assert summary["healthy"] == 0
        assert summary["degraded"] == 0
        assert summary["unhealthy"] == 0
        assert summary["unknown"] == 0
        assert summary["total"] == 0

        # Add various health statuses
        checker._health_status["h1"] = SourceHealth(
            name="h1", status=HealthStatus.HEALTHY,
            last_check=time.time(), response_time=100.0
        )
        checker._health_status["h2"] = SourceHealth(
            name="h2", status=HealthStatus.HEALTHY,
            last_check=time.time(), response_time=100.0
        )
        checker._health_status["d1"] = SourceHealth(
            name="d1", status=HealthStatus.DEGRADED,
            last_check=time.time(), response_time=3000.0
        )
        checker._health_status["u1"] = SourceHealth(
            name="u1", status=HealthStatus.UNHEALTHY,
            last_check=time.time(), response_time=0
        )

        summary = checker.get_summary()
        assert summary["healthy"] == 2
        assert summary["degraded"] == 1
        assert summary["unhealthy"] == 1
        assert summary["unknown"] == 0
        assert summary["total"] == 4

    def test_check_url_sync_healthy(self):
        """Test _check_url_sync with mocked healthy response."""
        from search_tool.utils.health import HealthChecker, HealthStatus
        import unittest.mock as mock

        checker = HealthChecker(timeout=5, degraded_threshold=1000)

        # Mock successful response
        with mock.patch('requests.get') as mock_get:
            mock_response = mock.Mock()
            mock_response.status_code = 200
            mock_get.return_value = mock_response

            health = checker._check_url_sync("test_source", "https://test.url")

            assert health.name == "test_source"
            assert health.status == HealthStatus.HEALTHY
            assert health.error_message is None

    def test_check_url_sync_unhealthy_status_code(self):
        """Test _check_url_sync with non-200 status code."""
        from search_tool.utils.health import HealthChecker, HealthStatus
        import unittest.mock as mock

        checker = HealthChecker(timeout=5)

        # Mock failed response (non-200 status)
        with mock.patch('requests.get') as mock_get:
            mock_response = mock.Mock()
            mock_response.status_code = 404
            mock_get.return_value = mock_response

            health = checker._check_url_sync("test_source", "https://test.url")

            assert health.name == "test_source"
            assert health.status == HealthStatus.UNHEALTHY
            assert "404" in health.error_message

    def test_check_url_sync_timeout(self):
        """Test _check_url_sync with timeout."""
        from search_tool.utils.health import HealthChecker, HealthStatus
        import unittest.mock as mock
        import requests

        checker = HealthChecker(timeout=5)

        # Mock timeout
        with mock.patch('requests.get') as mock_get:
            mock_get.side_effect = requests.exceptions.Timeout()

            health = checker._check_url_sync("test_source", "https://test.url")

            assert health.name == "test_source"
            assert health.status == HealthStatus.UNHEALTHY
            assert health.error_message == "Timeout"

    def test_check_url_sync_connection_error(self):
        """Test _check_url_sync with connection error."""
        from search_tool.utils.health import HealthChecker, HealthStatus
        import unittest.mock as mock
        import requests

        checker = HealthChecker(timeout=5)

        # Mock connection error
        with mock.patch('requests.get') as mock_get:
            mock_get.side_effect = requests.exceptions.ConnectionError("Connection failed")

            health = checker._check_url_sync("test_source", "https://test.url")

            assert health.name == "test_source"
            assert health.status == HealthStatus.UNHEALTHY
            assert "Connection error" in health.error_message

    def test_check_url_sync_degraded(self):
        """Test _check_url_sync with slow response (degraded status)."""
        from search_tool.utils.health import HealthChecker, HealthStatus
        import unittest.mock as mock

        checker = HealthChecker(timeout=5, degraded_threshold=100)  # 100ms threshold

        # Mock slow response
        with mock.patch('requests.get') as mock_get:
            mock_response = mock.Mock()
            mock_response.status_code = 200
            mock_get.return_value = mock_response

            # Simulate slow response by patching time
            original_time = time.time
            call_times = [100.0, 100.5, 100.5, 100.5]  # 500ms elapsed
            with mock.patch('time.time', side_effect=call_times):
                health = checker._check_url_sync("test_source", "https://test.url")

                assert health.name == "test_source"
                assert health.status == HealthStatus.DEGRADED  # Response time > threshold

    @pytest.mark.asyncio
    async def test_check_url_async_healthy(self):
        """Test _check_url_async with mocked healthy response."""
        from search_tool.utils.health import HealthChecker, HealthStatus
        import unittest.mock as mock

        checker = HealthChecker(timeout=5, degraded_threshold=1000)

        # Mock aiohttp session
        mock_session = mock.AsyncMock()
        mock_response = mock.AsyncMock()
        mock_response.status = 200
        mock_session.get.return_value = mock_response

        # Mock ClientSession constructor
        with mock.patch('aiohttp.ClientSession') as mock_client_session:
            mock_client_session.return_value = mock_session

            health = await checker._check_url_async("test_source", "https://test.url")

            assert health.name == "test_source"
            assert health.status == HealthStatus.HEALTHY

    def test_global_health_checker_instance(self):
        """Test global health checker instance."""
        from search_tool.utils.health import get_health_checker

        checker1 = get_health_checker()
        checker2 = get_health_checker()
        assert checker1 is checker2  # Should be same instance


if __name__ == "__main__":
    pytest.main([__file__, "-v"])