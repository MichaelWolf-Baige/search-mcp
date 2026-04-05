"""源健康检测"""

import asyncio
import time
import requests
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum


class HealthStatus(Enum):
    """健康状态枚举"""
    HEALTHY = "healthy"       # 正常工作
    DEGRADED = "degraded"     # 响应慢但有结果
    UNHEALTHY = "unhealthy"   # 不可用
    UNKNOWN = "unknown"       # 未检测


@dataclass
class SourceHealth:
    """源健康状态"""
    name: str
    status: HealthStatus
    last_check: float          # 检测时间戳
    response_time: float       # 响应时间（毫秒）
    error_message: Optional[str] = None


class HealthChecker:
    """源健康检测器"""

    def __init__(self, timeout: int = 10, degraded_threshold: float = 2000):
        """
        初始化健康检测器

        Args:
            timeout: 检测超时时间（秒）
            degraded_threshold: 降级阈值（毫秒），响应时间超过此值视为降级
        """
        self.timeout = timeout
        self.degraded_threshold = degraded_threshold
        self._health_status: Dict[str, SourceHealth] = {}
        self._last_check_time: float = 0
        self._check_interval = 300  # 5分钟检测一次

    def check_all_sync(self) -> Dict[str, SourceHealth]:
        """
        同步检测所有源

        Returns:
            各源的健康状态字典
        """
        results = {}

        # 检测 RSS 源
        from search_tool.engines.news import NewsEngine
        news_engine = NewsEngine()

        for name, url in news_engine.RSS_SOURCES.items():
            health = self._check_url_sync(name, url)
            results[name] = health

        # 检测社交引擎（通过尝试获取引擎实例）
        from search_tool.engines.social import SOCIAL_ENGINES
        for name in SOCIAL_ENGINES.keys():
            health = self._check_engine_sync(name)
            results[name] = health

        self._health_status = results
        self._last_check_time = time.time()
        return results

    async def check_all(self) -> Dict[str, SourceHealth]:
        """
        异步检测所有源

        Returns:
            各源的健康状态字典
        """
        results = {}

        # 检测 RSS 源
        from search_tool.engines.news import NewsEngine
        news_engine = NewsEngine()

        tasks = []
        for name, url in news_engine.RSS_SOURCES.items():
            tasks.append(self._check_url_async(name, url))

        rss_results = await asyncio.gather(*tasks, return_exceptions=True)

        for i, (name, url) in enumerate(news_engine.RSS_SOURCES.items()):
            if isinstance(rss_results[i], SourceHealth):
                results[name] = rss_results[i]
            else:
                results[name] = SourceHealth(
                    name=name,
                    status=HealthStatus.UNHEALTHY,
                    last_check=time.time(),
                    response_time=0,
                    error_message=str(rss_results[i])
                )

        # 检测社交引擎
        from search_tool.engines.social import SOCIAL_ENGINES
        engine_tasks = []
        for name in SOCIAL_ENGINES.keys():
            engine_tasks.append(self._check_engine_async(name))

        engine_results = await asyncio.gather(*engine_tasks, return_exceptions=True)

        for i, name in enumerate(SOCIAL_ENGINES.keys()):
            if isinstance(engine_results[i], SourceHealth):
                results[name] = engine_results[i]
            else:
                results[name] = SourceHealth(
                    name=name,
                    status=HealthStatus.UNHEALTHY,
                    last_check=time.time(),
                    response_time=0,
                    error_message=str(engine_results[i])
                )

        self._health_status = results
        self._last_check_time = time.time()
        return results

    def _check_url_sync(self, name: str, url: str) -> SourceHealth:
        """同步检测 URL 可用性"""
        start = time.time()
        try:
            from search_tool.config import get_config
            config = get_config()
            proxies = {"http": config.proxy, "https": config.proxy} if config.proxy else None

            response = requests.get(
                url,
                timeout=self.timeout,
                proxies=proxies,
                headers={"User-Agent": "Mozilla/5.0 SearchTool/1.0"}
            )
            elapsed = (time.time() - start) * 1000

            if response.status_code == 200:
                status = HealthStatus.HEALTHY if elapsed < self.degraded_threshold else HealthStatus.DEGRADED
            else:
                status = HealthStatus.UNHEALTHY

            return SourceHealth(
                name=name,
                status=status,
                last_check=time.time(),
                response_time=elapsed,
                error_message=None if status == HealthStatus.HEALTHY else f"Status code: {response.status_code}"
            )

        except requests.exceptions.Timeout:
            return SourceHealth(
                name=name,
                status=HealthStatus.UNHEALTHY,
                last_check=time.time(),
                response_time=self.timeout * 1000,
                error_message="Timeout"
            )
        except requests.exceptions.ConnectionError as e:
            return SourceHealth(
                name=name,
                status=HealthStatus.UNHEALTHY,
                last_check=time.time(),
                response_time=0,
                error_message=f"Connection error: {str(e)[:100]}"
            )
        except Exception as e:
            return SourceHealth(
                name=name,
                status=HealthStatus.UNHEALTHY,
                last_check=time.time(),
                response_time=0,
                error_message=str(e)[:100]
            )

    async def _check_url_async(self, name: str, url: str) -> SourceHealth:
        """异步检测 URL 可用性"""
        start = time.time()
        try:
            import aiohttp
            from search_tool.config import get_config
            config = get_config()

            connector = aiohttp.TCPConnector()
            timeout = aiohttp.ClientTimeout(total=self.timeout)

            async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
                proxy = config.proxy if config.proxy else None
                async with session.get(url, proxy=proxy) as resp:
                    elapsed = (time.time() - start) * 1000

                    if resp.status == 200:
                        status = HealthStatus.HEALTHY if elapsed < self.degraded_threshold else HealthStatus.DEGRADED
                    else:
                        status = HealthStatus.UNHEALTHY

                    return SourceHealth(
                        name=name,
                        status=status,
                        last_check=time.time(),
                        response_time=elapsed,
                        error_message=None if status == HealthStatus.HEALTHY else f"Status code: {resp.status}"
                    )

        except asyncio.TimeoutError:
            return SourceHealth(
                name=name,
                status=HealthStatus.UNHEALTHY,
                last_check=time.time(),
                response_time=self.timeout * 1000,
                error_message="Timeout"
            )
        except Exception as e:
            return SourceHealth(
                name=name,
                status=HealthStatus.UNHEALTHY,
                last_check=time.time(),
                response_time=0,
                error_message=str(e)[:100]
            )

    def _check_engine_sync(self, name: str) -> SourceHealth:
        """同步检测引擎可用性"""
        start = time.time()
        try:
            from search_tool.engines.social import get_social_engine
            engine = get_social_engine(name)

            if engine and engine.is_available():
                elapsed = (time.time() - start) * 1000
                status = HealthStatus.HEALTHY if elapsed < self.degraded_threshold else HealthStatus.DEGRADED
                return SourceHealth(
                    name=name,
                    status=status,
                    last_check=time.time(),
                    response_time=elapsed
                )
            else:
                return SourceHealth(
                    name=name,
                    status=HealthStatus.UNHEALTHY,
                    last_check=time.time(),
                    response_time=0,
                    error_message="Engine not available"
                )

        except Exception as e:
            return SourceHealth(
                name=name,
                status=HealthStatus.UNHEALTHY,
                last_check=time.time(),
                response_time=0,
                error_message=str(e)[:100]
            )

    async def _check_engine_async(self, name: str) -> SourceHealth:
        """异步检测引擎可用性"""
        # 由于引擎检测本身是同步的，使用 run_in_executor
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._check_engine_sync, name)

    def get_status(self, source_name: str) -> HealthStatus:
        """
        获取单个源状态

        Args:
            source_name: 源名称

        Returns:
            健康状态
        """
        health = self._health_status.get(source_name)
        return health.status if health else HealthStatus.UNKNOWN

    def should_skip(self, source_name: str) -> bool:
        """
        判断是否应该跳过该源

        Args:
            source_name: 源名称

        Returns:
            True 表示应该跳过
        """
        return self.get_status(source_name) == HealthStatus.UNHEALTHY

    def get_healthy_sources(self, source_dict: Dict[str, str]) -> Dict[str, str]:
        """
        过滤出不健康的源

        Args:
            source_dict: 源名称到 URL 的映射

        Returns:
            仅包含健康源的映射
        """
        return {
            name: url for name, url in source_dict.items()
            if not self.should_skip(name)
        }

    def needs_refresh(self) -> bool:
        """
        判断是否需要刷新健康状态

        Returns:
            True 表示需要重新检测
        """
        if not self._health_status:
            return True
        return time.time() - self._last_check_time > self._check_interval

    def get_summary(self) -> Dict[str, Any]:
        """
        获取健康状态摘要

        Returns:
            包含 healthy_count, unhealthy_count 等的字典
        """
        healthy = 0
        degraded = 0
        unhealthy = 0
        unknown = 0

        for health in self._health_status.values():
            if health.status == HealthStatus.HEALTHY:
                healthy += 1
            elif health.status == HealthStatus.DEGRADED:
                degraded += 1
            elif health.status == HealthStatus.UNHEALTHY:
                unhealthy += 1
            else:
                unknown += 1

        return {
            "healthy": healthy,
            "degraded": degraded,
            "unhealthy": unhealthy,
            "unknown": unknown,
            "total": len(self._health_status),
            "last_check": self._last_check_time
        }


# 全局实例
_checker: Optional[HealthChecker] = None


def get_health_checker() -> HealthChecker:
    """获取全局健康检测器实例"""
    global _checker
    if _checker is None:
        _checker = HealthChecker()
    return _checker


def check_health_sync() -> Dict[str, SourceHealth]:
    """同步检测所有源健康状态"""
    return get_health_checker().check_all_sync()