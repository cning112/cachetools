import unittest

import cachetools
import cachetools.keys


class DecoratorTestMixin(object):

    def cache(self, minsize):
        raise NotImplementedError

    def func(self, *args, **kwargs):
        if hasattr(self, 'count'):
            self.count += 1
        else:
            self.count = 0
        return self.count

    def test_decorator(self):
        cache = self.cache(2)
        wrapper = cachetools.cached(cache)(self.func)

        self.assertEqual(len(cache), 0)
        self.assertEqual(wrapper.__wrapped__, self.func)

        self.assertEqual(wrapper(0), 0)
        self.assertEqual(len(cache), 1)
        self.assertIn(cachetools.keys.hashkey(0), cache)
        self.assertNotIn(cachetools.keys.hashkey(1), cache)
        self.assertNotIn(cachetools.keys.hashkey(1.0), cache)

        self.assertEqual(wrapper(1), 1)
        self.assertEqual(len(cache), 2)
        self.assertIn(cachetools.keys.hashkey(0), cache)
        self.assertIn(cachetools.keys.hashkey(1), cache)
        self.assertIn(cachetools.keys.hashkey(1.0), cache)

        self.assertEqual(wrapper(1), 1)
        self.assertEqual(len(cache), 2)

        self.assertEqual(wrapper(1.0), 1)
        self.assertEqual(len(cache), 2)

        self.assertEqual(wrapper(1.0), 1)
        self.assertEqual(len(cache), 2)

    def test_decorator_typed(self):
        cache = self.cache(3)
        key = cachetools.keys.typedkey
        wrapper = cachetools.cached(cache, key=key)(self.func)

        self.assertEqual(len(cache), 0)
        self.assertEqual(wrapper.__wrapped__, self.func)

        self.assertEqual(wrapper(0), 0)
        self.assertEqual(len(cache), 1)
        self.assertIn(cachetools.keys.typedkey(0), cache)
        self.assertNotIn(cachetools.keys.typedkey(1), cache)
        self.assertNotIn(cachetools.keys.typedkey(1.0), cache)

        self.assertEqual(wrapper(1), 1)
        self.assertEqual(len(cache), 2)
        self.assertIn(cachetools.keys.typedkey(0), cache)
        self.assertIn(cachetools.keys.typedkey(1), cache)
        self.assertNotIn(cachetools.keys.typedkey(1.0), cache)

        self.assertEqual(wrapper(1), 1)
        self.assertEqual(len(cache), 2)

        self.assertEqual(wrapper(1.0), 2)
        self.assertEqual(len(cache), 3)
        self.assertIn(cachetools.keys.typedkey(0), cache)
        self.assertIn(cachetools.keys.typedkey(1), cache)
        self.assertIn(cachetools.keys.typedkey(1.0), cache)

        self.assertEqual(wrapper(1.0), 2)
        self.assertEqual(len(cache), 3)

    def test_decorator_lock(self):
        class Lock(object):

            count = 0

            def __enter__(self):
                Lock.count += 1

            def __exit__(self, *exc):
                pass

        cache = self.cache(2)
        wrapper = cachetools.cached(cache, lock=Lock())(self.func)

        self.assertEqual(len(cache), 0)
        self.assertEqual(wrapper.__wrapped__, self.func)
        self.assertEqual(wrapper(0), 0)
        self.assertEqual(Lock.count, 2)
        self.assertEqual(wrapper(1), 1)
        self.assertEqual(Lock.count, 4)
        self.assertEqual(wrapper(1), 1)
        self.assertEqual(Lock.count, 5)


class CacheWrapperTest(unittest.TestCase, DecoratorTestMixin):

    def cache(self, minsize):
        return cachetools.Cache(maxsize=minsize)

    def test_zero_size_cache_decorator(self):
        cache = self.cache(0)
        wrapper = cachetools.cached(cache)(self.func)

        self.assertEqual(len(cache), 0)
        self.assertEqual(wrapper.__wrapped__, self.func)

        self.assertEqual(wrapper(0), 0)
        self.assertEqual(len(cache), 0)

    def test_zero_size_cache_decorator_lock(self):
        class Lock(object):

            count = 0

            def __enter__(self):
                Lock.count += 1

            def __exit__(self, *exc):
                pass

        cache = self.cache(0)
        wrapper = cachetools.cached(cache, lock=Lock())(self.func)

        self.assertEqual(len(cache), 0)
        self.assertEqual(wrapper.__wrapped__, self.func)

        self.assertEqual(wrapper(0), 0)
        self.assertEqual(len(cache), 0)
        self.assertEqual(Lock.count, 2)

    def test_conditional_cache_decorator(self):
        def func(k):
            return k

        def ignore_negative(v, *args, **kwargs):
            return v < 0

        cache = self.cache(5)
        wrapper = cachetools.cached(cache, ignore=ignore_negative)(func)

        self.assertEqual(len(cache), 0)
        self.assertEqual(wrapper.__wrapped__, func)

        self.assertEqual(wrapper(-1), -1)
        self.assertEqual(len(cache), 0)

        self.assertEqual(wrapper(0), 0)
        self.assertEqual(len(cache), 1)

        self.assertEqual(wrapper(1), 1)
        self.assertEqual(len(cache), 2)

        self.assertEqual(wrapper(-1), -1)
        self.assertEqual(len(cache), 2)

    def test_conditional_cache_decorator_lock(self):
        class Lock(object):

            count = 0

            def __enter__(self):
                Lock.count += 1

            def __exit__(self, *exc):
                pass

        def func(k):
            return k

        def ignore_negative(v, *args, **kwargs):
            return v < 0

        cache = self.cache(5)
        wrapper = cachetools.cached(cache, lock=Lock(), ignore=ignore_negative)(func)

        self.assertEqual(len(cache), 0)
        self.assertEqual(wrapper.__wrapped__, func)

        self.assertEqual(wrapper(-1), -1)
        self.assertEqual(len(cache), 0)
        self.assertEqual(Lock.count, 1)

        self.assertEqual(wrapper(0), 0)
        self.assertEqual(len(cache), 1)
        self.assertEqual(Lock.count, 3)

        self.assertEqual(wrapper(1), 1)
        self.assertEqual(len(cache), 2)
        self.assertEqual(Lock.count, 5)

        self.assertEqual(wrapper(-1), -1)
        self.assertEqual(len(cache), 2)
        self.assertEqual(Lock.count, 6)

    def test_conditional_cache_decorators(self):
        cache_positive = self.cache(5)
        cache_negative = self.cache(5)

        def func(k):
            return k

        def ignore_non_positive(v, *args, **kwargs):
            return v <= 0

        def ignore_non_negative(v, *args, **kwargs):
            return v >= 0

        wrapper = cachetools.cached(cache_positive, ignore=ignore_non_positive)(func)
        wrapper = cachetools.cached(cache_negative, ignore=ignore_non_negative)(wrapper)

        self.assertEqual(len(cache_positive), 0)
        self.assertEqual(len(cache_negative), 0)
        self.assertEqual(wrapper.__wrapped__.__wrapped__, func)

        self.assertEqual(wrapper(0), 0)
        self.assertEqual(len(cache_positive), 0)
        self.assertEqual(len(cache_negative), 0)

        self.assertEqual(wrapper(1), 1)
        self.assertEqual(len(cache_positive), 1)
        self.assertEqual(len(cache_negative), 0)

        self.assertEqual(wrapper(-1), -1)
        self.assertEqual(len(cache_positive), 1)
        self.assertEqual(len(cache_negative), 1)

        self.assertEqual(wrapper(1), 1)
        self.assertEqual(len(cache_positive), 1)
        self.assertEqual(len(cache_negative), 1)

        self.assertEqual(wrapper(-1), -1)
        self.assertEqual(len(cache_positive), 1)
        self.assertEqual(len(cache_negative), 1)

    def test_conditional_cache_decorators_lock(self):
        class Lock(object):

            count = 0

            def __enter__(self):
                Lock.count += 1

            def __exit__(self, *exc):
                pass

        def func(k):
            return k

        def ignore_non_positive(v, *args, **kwargs):
            return v <= 0

        def ignore_non_negative(v, *args, **kwargs):
            return v >= 0

        lock = Lock()

        cache_positive = self.cache(5)
        cache_negative = self.cache(5)
        wrapper = cachetools.cached(cache_positive, lock=lock, ignore=ignore_non_positive)(func)
        wrapper = cachetools.cached(cache_negative, lock=lock, ignore=ignore_non_negative)(wrapper)

        self.assertEqual(len(cache_positive), 0)
        self.assertEqual(len(cache_negative), 0)
        self.assertEqual(wrapper.__wrapped__.__wrapped__, func)

        self.assertEqual(wrapper(0), 0)
        self.assertEqual(len(cache_positive), 0)
        self.assertEqual(len(cache_negative), 0)
        self.assertEqual(lock.count, 2)

        self.assertEqual(wrapper(1), 1)
        self.assertEqual(len(cache_positive), 1)
        self.assertEqual(len(cache_negative), 0)
        self.assertEqual(lock.count, 5)

        self.assertEqual(wrapper(-1), -1)
        self.assertEqual(len(cache_positive), 1)
        self.assertEqual(len(cache_negative), 1)
        self.assertEqual(lock.count, 8)

        self.assertEqual(wrapper(1), 1)
        self.assertEqual(len(cache_positive), 1)
        self.assertEqual(len(cache_negative), 1)
        self.assertEqual(lock.count, 10)

        self.assertEqual(wrapper(-1), -1)
        self.assertEqual(len(cache_positive), 1)
        self.assertEqual(len(cache_negative), 1)
        self.assertEqual(lock.count, 11)


class DictWrapperTest(unittest.TestCase, DecoratorTestMixin):

    def cache(self, minsize):
        return dict()


class NoneWrapperTest(unittest.TestCase):

    def func(self, *args, **kwargs):
        return args + tuple(kwargs.items())

    def test_decorator(self):
        wrapper = cachetools.cached(None)(self.func)
        self.assertEqual(wrapper.__wrapped__, self.func)

        self.assertEqual(wrapper(0), (0,))
        self.assertEqual(wrapper(1), (1,))
        self.assertEqual(wrapper(1, foo='bar'), (1, ('foo', 'bar')))
