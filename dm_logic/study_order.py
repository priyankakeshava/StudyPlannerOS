from collections import deque

def topological_order(nodes, edges):
    """
    Kahn's algorithm for topological sorting; edges are prerequisite -> dependent.
    Syllabus Topic: 4. Self-Learning (Topological Order).
    """
    nodes = list(nodes)
    outgoing = {n: [] for n in nodes}
    indegree = {n: 0 for n in nodes}
    for source, target in edges:
        if source not in outgoing or target not in outgoing:
            raise ValueError("Edge endpoint is missing from nodes.")
        outgoing[source].append(target)
        indegree[target] += 1
        
    ready = deque([n for n in nodes if indegree[n] == 0])
    order = []
    
    while ready:
        current = ready.popleft()
        order.append(current)
        for nxt in outgoing[current]:
            indegree[nxt] -= 1
            if indegree[nxt] == 0:
                ready.append(nxt)
                
    if len(order) != len(nodes):
        cycle = find_cycle(nodes, edges)
        cycle_str = " -> ".join(map(str, cycle)) if cycle else "Unknown"
        raise ValueError(f"Prerequisite cycle detected: {cycle_str}")
        
    return order

def find_cycle(nodes, edges):
    """
    Finds a directed cycle using DFS back-edge detection.
    Returns a list of nodes forming the cycle, or None if no cycle exists.
    """
    adj = {n: [] for n in nodes}
    for u, v in edges:
        adj[u].append(v)
        
    visited = set()
    rec_stack = set()
    path = []
    
    def dfs(u):
        visited.add(u)
        rec_stack.add(u)
        path.append(u)
        
        for v in adj[u]:
            if v not in visited:
                cycle = dfs(v)
                if cycle:
                    return cycle
            elif v in rec_stack:
                # Cycle found
                cycle_start_idx = path.index(v)
                return path[cycle_start_idx:] + [v]
                
        rec_stack.remove(u)
        path.pop()
        return None
        
    for node in nodes:
        if node not in visited:
            cycle = dfs(node)
            if cycle:
                return cycle
    return None

def eligible_topics(topic_ids, completed_ids, prerequisites):
    completed = set(completed_ids)
    return [topic for topic in topic_ids
            if topic not in completed
            and set(prerequisites.get(topic, ())).issubset(completed)]
