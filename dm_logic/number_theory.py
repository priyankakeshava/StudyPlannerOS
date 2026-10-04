"""
Number theory module for Discrete Mathematics algorithms in StudyOS.
Powers the Revision Rotation feature of the study planner.
"""

def gcd(a: int, b: int) -> int:
    """
    Computes the greatest common divisor of a and b using the iterative Euclidean algorithm.
    Syllabus 2.1
    """
    a = abs(a)
    b = abs(b)
    while b != 0:
        a, b = b, a % b
    return a

def extended_gcd(a: int, b: int) -> tuple[int, int, int]:
    """
    Extended Euclidean algorithm. Returns a tuple (g, x, y) such that a*x + b*y = g = gcd(a, b).
    Syllabus 2.1
    """
    if a == 0:
        return abs(b), 0, 1 if b >= 0 else -1
    
    x0, x1 = 1, 0
    y0, y1 = 0, 1
    
    # Store signs to handle negative inputs
    sign_a = 1 if a >= 0 else -1
    sign_b = 1 if b >= 0 else -1
    a, b = abs(a), abs(b)
    
    while b != 0:
        q = a // b
        a, b = b, a % b
        x0, x1 = x1, x0 - q * x1
        y0, y1 = y1, y0 - q * y1
        
    return a, x0 * sign_a, y0 * sign_b

def lcm(a: int, b: int) -> int:
    """
    Computes the least common multiple of a and b using the GCD.
    For finding when two subject rotation cycles align.
    Syllabus 2.1
    """
    if a == 0 or b == 0:
        return 0
    return abs(a * b) // gcd(a, b)

def sieve_of_eratosthenes(limit: int) -> list[int]:
    """
    Returns all prime numbers less than or equal to limit.
    Used to generate prime-spaced review intervals.
    Syllabus 2.2
    """
    if limit < 2:
        return []
        
    sieve = [True] * (limit + 1)
    sieve[0] = sieve[1] = False
    
    for p in range(2, int(limit**0.5) + 1):
        if sieve[p]:
            for i in range(p * p, limit + 1, p):
                sieve[i] = False
                
    return [i for i, is_prime in enumerate(sieve) if is_prime]

def prime_factorization(n: int) -> list[int]:
    """
    Computes the prime factorization of n using trial division.
    Returns a list of prime factors.
    Syllabus 2.2
    """
    if n <= 1:
        return []
        
    factors = []
    # Divide by 2
    while n % 2 == 0:
        factors.append(2)
        n //= 2
        
    # Divide by odd numbers
    for i in range(3, int(n**0.5) + 1, 2):
        while n % i == 0:
            factors.append(i)
            n //= i
            
    if n > 2:
        factors.append(n)
        
    return factors

def euler_totient(n: int) -> int:
    """
    Computes Euler's totient function φ(n) using prime factorization.
    Counts coprime days in a rotation cycle.
    Syllabus 2.3
    """
    if n < 1:
        return 0
    if n == 1:
        return 1
        
    result = n
    factors = set(prime_factorization(n))
    
    for p in factors:
        result -= result // p
        
    return result

def mod_inverse(a: int, m: int) -> int | None:
    """
    Computes the multiplicative inverse of a modulo m using the Extended Euclidean algorithm.
    Returns None if not coprime. For solving 'which topic falls on day X?'.
    Syllabus 2.3
    """
    g, x, _ = extended_gcd(a, m)
    if g != 1:
        return None
    return x % m

def congruent(a: int, b: int, m: int) -> bool:
    """
    Checks if a is congruent to b modulo m (a ≡ b (mod m)).
    Syllabus 2.3
    """
    if m == 0:
        return a == b
    return (a - b) % m == 0

def lcg_random(seed: int, a: int, c: int, m: int, count: int) -> list[int]:
    """
    Linear Congruential Generator for pseudorandom topic shuffling.
    Returns a list of 'count' pseudorandom integers.
    Syllabus 2 Self-Learning
    """
    if count <= 0:
        return []
        
    result = []
    current = seed
    for _ in range(count):
        current = (a * current + c) % m
        result.append(current)
    return result
