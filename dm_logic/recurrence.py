"""
Discrete Mathematics - Recurrence Relations
Syllabus: Recurrence relations
"""

import datetime
from typing import List, Dict, Any

def fibonacci_intervals(n: int) -> List[int]:
    """
    Generates the first n Fibonacci numbers [1, 1, 2, 3, 5, ...]
    Syllabus: Recurrence relations
    """
    if n <= 0:
        return []
    if n == 1:
        return [1]
    
    seq = [1, 1]
    for _ in range(2, n):
        seq.append(seq[-1] + seq[-2])
    return seq

def exponential_intervals(n: int, base: int = 2) -> List[int]:
    """
    Generates geometric intervals [1, 2, 4, 8, ...]
    Syllabus: Recurrence relations
    """
    if n <= 0:
        return []
    return [base**i for i in range(n)]

def prime_intervals(n: int) -> List[int]:
    """
    Generates the first n prime numbers.
    Syllabus: Recurrence relations
    """
    if n <= 0:
        return []
    primes = []
    num = 2
    while len(primes) < n:
        is_prime = True
        for p in primes:
            if p * p > num:
                break
            if num % p == 0:
                is_prime = False
                break
        if is_prime:
            primes.append(num)
        num += 1
    return primes

def generate_review_schedule(start_date: datetime.date, topics: List[Dict[str, str]], method: str = 'fibonacci') -> List[Dict[str, Any]]:
    """
    Distributes topics across intervals to generate a spaced repetition schedule.
    Returns a list of dicts with keys 'date', 'topic_name', 'topic_subject', 'day_gap'.
    Syllabus: Recurrence relations
    """
    if not topics:
        return []
        
    num_intervals = 5  # default number of reviews per topic
    if method == 'fibonacci':
        intervals = fibonacci_intervals(num_intervals)
    elif method == 'exponential':
        intervals = exponential_intervals(num_intervals)
    elif method == 'prime':
        intervals = prime_intervals(num_intervals)
    else:
        intervals = fibonacci_intervals(num_intervals)
        
    schedule = []
    
    # Each topic gets its own spaced sequence starting on start_date
    for topic in topics:
        current_date = start_date
        for gap in intervals:
            current_date += datetime.timedelta(days=gap)
            schedule.append({
                'date': current_date,
                'topic_name': topic.get('name', ''),
                'topic_subject': topic.get('subject', ''),
                'day_gap': gap
            })
            
    # Sort by date
    schedule.sort(key=lambda x: x['date'])
    return schedule
