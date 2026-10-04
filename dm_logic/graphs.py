from typing import Any

def build_interval_graph(blocks: list[dict]) -> dict[int, list[int]]:
    """
    Builds an interval graph representing scheduling conflicts.
    
    In Discrete Mathematics, an interval graph is the intersection graph of a family of intervals 
    on the real line. Here, vertices represent study blocks and edges represent time overlaps 
    (conflicts) between these blocks.
    
    Syllabus Topic: 6.1 (Graphs and Graph Models)
    
    Args:
        blocks: List of dictionaries, where each dict has 'start' and 'end' keys 
                with comparable time objects (e.g., datetime objects).
                
    Returns:
        An adjacency list represented as a dictionary mapping block indices to lists of 
        conflicting block indices.
    """
    n = len(blocks)
    adj_list = {i: [] for i in range(n)}
    for i in range(n):
        for j in range(i + 1, n):
            # Check for overlap: max(start1, start2) < min(end1, end2)
            start_overlap = max(blocks[i]['start'], blocks[j]['start'])
            end_overlap = min(blocks[i]['end'], blocks[j]['end'])
            if start_overlap < end_overlap:
                adj_list[i].append(j)
                adj_list[j].append(i)
    return adj_list


def greedy_coloring(adj_list: dict[int, list[int]]) -> tuple[dict[int, int], int]:
    """
    Applies the Welsh-Powell greedy graph coloring algorithm to assign colors to vertices 
    such that no two adjacent vertices share the same color.
    
    In the context of the study planner, this algorithm resolves schedule conflicts by assigning 
    conflicting blocks to different parallel tracks (colors). The chromatic number represents 
    the minimum number of parallel tracks needed.
    
    Syllabus Topic: 6.1 (Graph Coloring)
    
    Args:
        adj_list: An adjacency list representing the graph (e.g., the interval graph).
        
    Returns:
        A tuple containing:
            - A dictionary mapping vertex indices to their assigned color (integer starting from 0).
            - The number of colors used (the chromatic number for this coloring).
    """
    # Sort vertices by degree in descending order (Welsh-Powell heuristic)
    vertices = sorted(adj_list.keys(), key=lambda v: len(adj_list[v]), reverse=True)
    coloring: dict[int, int] = {}
    current_color = 0
    
    while len(coloring) < len(vertices):
        colored_this_round: list[int] = []
        for v in vertices:
            if v not in coloring:
                # Check if v is adjacent to any vertex already colored with current_color
                can_color = True
                for neighbor in adj_list[v]:
                    if neighbor in colored_this_round:
                        can_color = False
                        break
                if can_color:
                    coloring[v] = current_color
                    colored_this_round.append(v)
        current_color += 1
        
    return coloring, current_color


def longest_dag_path(nodes: list, edges: list[tuple], weights: dict) -> tuple[list, int]:
    """
    Finds the longest (critical) path in a weighted Directed Acyclic Graph (DAG) using 
    topological sorting and dynamic programming.
    
    This function computes the minimum prep time before an exam by finding the critical path 
    through prerequisite topics.
    
    Syllabus Topic: 6.1 (Directed Graphs, Paths)
    
    Args:
        nodes: A list of node identifiers.
        edges: A list of tuples (u, v) representing directed edges from u to v.
        weights: A dictionary mapping node identifiers to their weights (e.g., estimated_minutes).
        
    Returns:
        A tuple containing:
            - A list of nodes representing the longest path.
            - The total weight of this path.
    """
    # Create adjacency list and in-degree count for topological sort
    adj = {u: [] for u in nodes}
    in_degree = {u: 0 for u in nodes}
    for u, v in edges:
        if u not in adj:
            adj[u] = []
        if v not in in_degree:
            in_degree[v] = 0
        adj[u].append(v)
        in_degree[v] += 1
        
    # Topological sort using Kahn's algorithm
    queue = [u for u in nodes if in_degree.get(u, 0) == 0]
    topo_order = []
    
    while queue:
        u = queue.pop(0)
        topo_order.append(u)
        for v in adj.get(u, []):
            in_degree[v] -= 1
            if in_degree[v] == 0:
                queue.append(v)
                
    # Dynamic programming to find the longest path
    dist = {u: weights.get(u, 0) for u in nodes}
    parent = {u: None for u in nodes}
    
    for u in topo_order:
        for v in adj.get(u, []):
            if dist[u] + weights.get(v, 0) > dist[v]:
                dist[v] = dist[u] + weights.get(v, 0)
                parent[v] = u
                
    # Find the node with the maximum distance
    if not nodes:
        return [], 0
        
    max_node = max(nodes, key=lambda u: dist[u])
    max_dist = dist[max_node]
    
    # Reconstruct the path
    path = []
    curr = max_node
    while curr is not None:
        path.append(curr)
        curr = parent[curr]
    path.reverse()
    
    return path, max_dist


def induced_subgraph(adj: dict, vertex_subset: set) -> dict:
    """
    Returns the subgraph induced by a specific subset of vertices.
    
    In Discrete Mathematics, an induced subgraph is a graph formed from a subset of the 
    vertices of a graph and all of the edges connecting pairs of vertices in that subset.
    This is used for filtering prerequisites by subject.
    
    Syllabus Topic: 6.4 (Subgraphs)
    
    Args:
        adj: An adjacency list representing the original graph.
        vertex_subset: A set of vertices to include in the induced subgraph.
        
    Returns:
        A dictionary representing the adjacency list of the induced subgraph.
    """
    subgraph = {}
    for u in vertex_subset:
        if u in adj:
            # Only include neighbors that are also in the vertex subset
            subgraph[u] = [v for v in adj[u] if v in vertex_subset]
        else:
            subgraph[u] = []
    return subgraph


def graph_properties(adj_list: dict[int, list[int]], directed: bool = False) -> dict[str, Any]:
    """
    Calculates various properties of a graph.
    
    Computes the number of vertices, number of edges, degree sequence, and checks if the 
    graph is connected (for undirected graphs).
    
    Syllabus Topic: 6.1 (Graph Terminology and Special Types of Graphs)
    
    Args:
        adj_list: An adjacency list representing the graph.
        directed: A boolean indicating whether the graph is directed.
        
    Returns:
        A dictionary containing:
            - 'num_vertices': Integer count of vertices.
            - 'num_edges': Integer count of edges.
            - 'is_connected': Boolean indicating if the graph is connected (None for directed graphs).
            - 'degree_sequence': List of degrees (out-degrees for directed) in descending order.
    """
    num_vertices = len(adj_list)
    
    degree_seq = []
    total_edges = 0
    for u in adj_list:
        deg = len(adj_list[u])
        degree_seq.append(deg)
        total_edges += deg
        
    if not directed:
        num_edges = total_edges // 2
    else:
        num_edges = total_edges
        
    degree_seq.sort(reverse=True)
    
    is_connected = None
    if not directed and num_vertices > 0:
        # Check connectivity using BFS
        visited = set()
        start_node = next(iter(adj_list.keys()))
        queue = [start_node]
        visited.add(start_node)
        
        while queue:
            u = queue.pop(0)
            for v in adj_list[u]:
                if v not in visited:
                    visited.add(v)
                    queue.append(v)
        is_connected = len(visited) == num_vertices
    elif not directed and num_vertices == 0:
        is_connected = True
        
    return {
        'num_vertices': num_vertices,
        'num_edges': num_edges,
        'is_connected': is_connected,
        'degree_sequence': degree_seq
    }


def hasse_diagram_dot(nodes: list, edges: list[tuple], labels: dict) -> str:
    """
    Generates a Graphviz DOT string for rendering a Hasse diagram.
    
    A Hasse diagram is a type of mathematical diagram used to represent a finite partially 
    ordered set (poset), in the form of a drawing of its transitive reduction. 
    This generates a dark-theme compatible DOT representation for rendering.
    
    Syllabus Topic: 4.1 (Relations and their Properties, Posets, Hasse Diagrams)
    
    Args:
        nodes: A list of node IDs.
        edges: A list of tuples (from, to) representing the edges after transitive reduction.
        labels: A dictionary mapping node IDs to their display names.
        
    Returns:
        A string containing a valid DOT digraph.
    """
    dot_lines = []
    dot_lines.append('digraph Hasse {')
    dot_lines.append('    rankdir=BT;')
    dot_lines.append('    bgcolor="transparent";')
    dot_lines.append('    node [shape=box, style="rounded,filled", fillcolor="#1E3A5F", fontcolor="#E8EDF3", color="#1E3A5F"];')
    dot_lines.append('    edge [color="#4A90D9", dir=none];')
    
    for node in nodes:
        label = labels.get(node, str(node))
        # Escape quotes in label
        label_escaped = str(label).replace('"', '\\"')
        dot_lines.append(f'    "{node}" [label="{label_escaped}"];')
        
    for u, v in edges:
        dot_lines.append(f'    "{u}" -> "{v}";')
        
    dot_lines.append('}')
    return '\\n'.join(dot_lines)
