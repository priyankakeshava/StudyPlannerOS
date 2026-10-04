from datetime import datetime, timedelta, date, time
from utils.time_helpers import timedelta_to_time

def _time_value(value):
    if isinstance(value, datetime):
        return value.time()
    if isinstance(value, timedelta):
        return timedelta_to_time(value)
    return value

def get_free_time_slots(target_date: date, routine_blocks: list, events: list, existing_sessions: list) -> list[tuple[datetime, datetime]]:
    """
    Calculates free time slots for a given day using Set Difference.
    Total Day [00:00 - 23:59] - (Routine U Events U Sessions)
    """
    day_start = datetime.combine(target_date, time(7, 0))
    day_end = datetime.combine(target_date, time(23, 0))
    
    occupied_intervals = []
    
    for begin, finish in routine_blocks + events + existing_sessions:
        if isinstance(begin, datetime):
            begin_dt = begin
        else:
            begin_dt = datetime.combine(target_date, _time_value(begin))
            
        if isinstance(finish, datetime):
            finish_dt = finish
        else:
            finish_dt = datetime.combine(target_date, _time_value(finish))
            # Handle overnight blocks (like sleep)
            if finish_dt <= begin_dt:
                finish_dt += timedelta(days=1)
            
        # Only care about overlaps with the current target_date
        overlap_start = max(day_start, begin_dt)
        overlap_end = min(day_end, finish_dt)
        
        if overlap_start < overlap_end:
            occupied_intervals.append((overlap_start, overlap_end))
            
    # Sort and merge occupied intervals
    occupied_intervals.sort(key=lambda x: x[0])
    merged = []
    for current in occupied_intervals:
        if not merged:
            merged.append(current)
        else:
            prev = merged[-1]
            if current[0] <= prev[1]:
                # Merge overlapping or touching intervals
                merged[-1] = (prev[0], max(prev[1], current[1]))
            else:
                merged.append(current)
                
    # Calculate set difference
    free_slots = []
    current_time = day_start
    
    for occ_start, occ_end in merged:
        if current_time < occ_start:
            free_slots.append((current_time, occ_start))
        current_time = max(current_time, occ_end)
        
    if current_time < day_end:
        free_slots.append((current_time, day_end))
        
    return free_slots

def auto_schedule_topics(topics_to_schedule: list[dict], free_slots: list[tuple[datetime, datetime]]) -> tuple[list[dict], list[dict]]:
    """
    Greedy Interval Scheduling.
    Takes a topologically ordered list of topics and available free slots.
    Attempts to pack topics into the slots.
    Returns (scheduled_sessions, remaining_topics).
    """
    scheduled = []
    remaining = []
    
    # Copy free slots so we can mutate them
    available_slots = list(free_slots)
    
    for topic in topics_to_schedule:
        req_minutes = topic['estimated_minutes']
        req_duration = timedelta(minutes=req_minutes)
        
        scheduled_flag = False
        
        for i, (slot_start, slot_end) in enumerate(available_slots):
            slot_duration = slot_end - slot_start
            
            if slot_duration >= req_duration:
                # We found a gap! Schedule it at the beginning of the gap.
                session_start = slot_start
                session_end = slot_start + req_duration
                
                scheduled.append({
                    'topic_id': topic['topic_id'],
                    'title': f"Auto-Study: {topic['name']}",
                    'starts_at': session_start,
                    'ends_at': session_end
                })
                
                # Update the remaining gap
                available_slots[i] = (session_end, slot_end)
                scheduled_flag = True
                break
                
        if not scheduled_flag:
            remaining.append(topic)
            
    return scheduled, remaining
