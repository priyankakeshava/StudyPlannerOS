from dm_logic.graphs import build_interval_graph, greedy_coloring

def overlaps(start_a, end_a, start_b, end_b):
    """Half-open interval overlap check; adjacent blocks do not conflict."""
    return start_a < end_b and start_b < end_a

def find_conflicts(blocks):
    """Finds pairwise conflicts in a list of blocks."""
    conflicts = []
    ordered = sorted(blocks, key=lambda block: block["start"])
    for index, first in enumerate(ordered):
        for second in ordered[index + 1:]:
            if second["start"] >= first["end"]:
                break
            if overlaps(first["start"], first["end"], second["start"], second["end"]):
                conflicts.append((first, second))
    return conflicts

def suggest_resolution(blocks):
    """
    Uses graph coloring to suggest a resolution for scheduling conflicts.
    Returns (coloring, chromatic_number), where coloring maps block index to a 'track' or 'color'.
    Syllabus Topic: 6.1 (Graph Coloring).
    """
    adj_list = build_interval_graph(blocks)
    coloring, chromatic_number = greedy_coloring(adj_list)
    return coloring, chromatic_number
