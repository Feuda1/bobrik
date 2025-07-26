"""
Утилиты кеширования для оптимизации производительности
"""
import time
from typing import Any, Dict, Optional, Callable
from functools import wraps


class SimpleCache:
    """Простой кеш с TTL (время жизни)"""
    
    def __init__(self, default_ttl: int = 300):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._default_ttl = default_ttl
    
    def get(self, key: str) -> Optional[Any]:
        """Получить значение из кеша"""
        if key not in self._cache:
            return None
            
        entry = self._cache[key]
        if time.time() > entry['expires']:
            del self._cache[key]
            return None
            
        return entry['value']
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Сохранить значение в кеш"""
        if ttl is None:
            ttl = self._default_ttl
            
        self._cache[key] = {
            'value': value,
            'expires': time.time() + ttl
        }
    
    def clear(self) -> None:
        """Очистить весь кеш"""
        self._cache.clear()
    
    def clear_expired(self) -> None:
        """Очистить просроченные записи"""
        current_time = time.time()
        expired_keys = [
            key for key, entry in self._cache.items()
            if current_time > entry['expires']
        ]
        for key in expired_keys:
            del self._cache[key]


# Глобальный экземпляр кеша
global_cache = SimpleCache()


def cached(ttl: int = 300, key_func: Optional[Callable] = None):
    """
    Декоратор для кеширования результатов функций
    
    Args:
        ttl: Время жизни кеша в секундах
        key_func: Функция для генерации ключа кеша
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Генерируем ключ кеша
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = f"{func.__name__}_{hash(str(args) + str(sorted(kwargs.items())))}"
            
            # Пытаемся получить из кеша
            cached_result = global_cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Выполняем функцию и кешируем результат
            result = func(*args, **kwargs)
            global_cache.set(cache_key, result, ttl)
            return result
            
        return wrapper
    return decorator


def memoize_method(ttl: int = 300):
    """
    Декоратор для кеширования методов класса
    """
    def decorator(method):
        cache_attr = f"_cache_{method.__name__}"
        
        @wraps(method)
        def wrapper(self, *args, **kwargs):
            # Инициализируем кеш для экземпляра если нужно
            if not hasattr(self, cache_attr):
                setattr(self, cache_attr, SimpleCache(ttl))
            
            cache = getattr(self, cache_attr)
            cache_key = f"{hash(str(args) + str(sorted(kwargs.items())))}"
            
            # Пытаемся получить из кеша
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Выполняем метод и кешируем результат
            result = method(self, *args, **kwargs)
            cache.set(cache_key, result)
            return result
            
        return wrapper
    return decorator