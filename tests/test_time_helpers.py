import sys
from datetime import time, timedelta
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from utils.time_helpers import timedelta_to_time

def test_time_passthrough():
    assert timedelta_to_time(time(8, 15, 30)) == time(8, 15, 30)

def test_timedelta_conversion():
    assert timedelta_to_time(timedelta(hours=8, minutes=15, seconds=30)) == time(8, 15, 30)

def test_timedelta_wraps_midnight():
    assert timedelta_to_time(timedelta(days=1, hours=2)) == time(2, 0)
