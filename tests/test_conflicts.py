import sys
from datetime import datetime, timedelta
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from dm_logic.conflicts import find_conflicts

def test_long_block_overlaps_two_short_blocks():
    t = datetime(2026, 1, 1, 9)
    blocks = [
        {"start": t, "end": t + timedelta(hours=3), "title": "Long"},
        {"start": t + timedelta(minutes=30), "end": t + timedelta(hours=1), "title": "Short A"},
        {"start": t + timedelta(hours=2), "end": t + timedelta(hours=2, minutes=30), "title": "Short B"},
    ]
    assert len(find_conflicts(blocks)) == 2

def test_adjacent_blocks_do_not_conflict():
    t = datetime(2026, 1, 1, 9)
    assert find_conflicts([{"start": t, "end": t+timedelta(hours=1)}, {"start": t+timedelta(hours=1), "end": t+timedelta(hours=2)}]) == []
