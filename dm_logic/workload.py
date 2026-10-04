import math

def check_workload(required_minutes: int, available_minutes: int) -> tuple[bool, str]:
    """
    Checks if the workload is overloaded using the Pigeonhole Principle.
    Returns (is_overloaded, proof_message).
    Syllabus 5.3: Pigeonhole Principle.
    """
    if required_minutes <= available_minutes:
        return False, ""
    
    # Pigeonhole Principle application
    # Suppose we divide available time into 1-minute slots (holes)
    # and we have 'required_minutes' (pigeons).
    # Since pigeons > holes, at least one slot must contain more than one pigeon (minute of work),
    # which is physically impossible.
    
    proof = (f"Overload detected! You have {required_minutes} minutes of planned study "
             f"but only {available_minutes} minutes available. "
             f"By the Pigeonhole Principle, if we try to place {required_minutes} minutes of work "
             f"into {available_minutes} 1-minute slots, at least one slot must contain "
             f"⌈{required_minutes}/{available_minutes}⌉ = {math.ceil(required_minutes/max(1, available_minutes))} "
             f"minutes of work simultaneously, which is impossible.")
    return True, proof

def is_overloaded(required_minutes: int, available_minutes: int) -> bool:
    """Backward compatibility for existing code."""
    return required_minutes > available_minutes
