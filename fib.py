import sys

def n_fibonnaci(n: int, cache: dict) -> int:
    print(n)
    if n <= 0:
        return 0
    if n == 1:
        return 1
    if n in cache:
        return cache[n]

    cache[n] = n_fibonnaci(n - 1, cache) + n_fibonnaci(n - 2, cache)
    return cache[n]

def call_fib(n: int):
    cache = {}
    sys.setrecursionlimit(1000000)
    return n_fibonnaci(n, cache)

print(call_fib(4096))
