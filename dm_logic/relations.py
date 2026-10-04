"""
Discrete Mathematics: Relations module.
Provides functions for relation matrices, properties, Warshall's algorithm,
transitive reduction, equivalence partitions, and relation composition.
Used for prerequisite analysis in StudyOS.
"""

from typing import Any, Callable

def relation_matrix(node_ids: list[int], edges: list[tuple[int, int]]) -> list[list[int]]:
    """
    Builds a boolean adjacency/relation matrix from a list of directed edges.
    Syllabus 3.1, 3.3.

    Args:
        node_ids: List of node IDs. The index of the node in this list will be its matrix index.
        edges: List of directed edges as (source, target) tuples.

    Returns:
        A boolean relation matrix represented as a list of lists of integers (0 or 1).
    """
    n = len(node_ids)
    matrix = [[0 for _ in range(n)] for _ in range(n)]
    
    # Map node id to index
    id_to_idx = {node_id: idx for idx, node_id in enumerate(node_ids)}
    
    for u, v in edges:
        if u in id_to_idx and v in id_to_idx:
            matrix[id_to_idx[u]][id_to_idx[v]] = 1
            
    return matrix


def warshall_closure(matrix: list[list[int]]) -> list[list[int]]:
    """
    Warshall's algorithm for computing the transitive closure of a relation (R+).
    Syllabus 3.3.

    Args:
        matrix: The input relation matrix.

    Returns:
        A new relation matrix representing the transitive closure.
    """
    n = len(matrix)
    # Create a deep copy of the matrix
    closure = [[matrix[i][j] for j in range(n)] for i in range(n)]
    
    for k in range(n):
        for i in range(n):
            for j in range(n):
                closure[i][j] = closure[i][j] or (closure[i][k] and closure[k][j])
                
    return closure


def check_relation_properties(matrix: list[list[int]]) -> dict[str, bool]:
    """
    Checks properties of a relation on a set.
    Determines if the relation is reflexive, irreflexive, symmetric, antisymmetric, and transitive.
    Syllabus 3.2.

    Args:
        matrix: The relation matrix.

    Returns:
        A dictionary mapping property names to boolean values.
    """
    n = len(matrix)
    
    reflexive = True
    irreflexive = True
    symmetric = True
    antisymmetric = True
    transitive = True
    
    for i in range(n):
        if matrix[i][i] == 0:
            reflexive = False
        if matrix[i][i] == 1:
            irreflexive = False
            
        for j in range(n):
            if matrix[i][j] == 1:
                if matrix[j][i] == 0:
                    symmetric = False
                if i != j and matrix[j][i] == 1:
                    antisymmetric = False
                    
                # For transitivity check, if i->j and j->k, then i->k must exist
                for k in range(n):
                    if matrix[j][k] == 1 and matrix[i][k] == 0:
                        transitive = False

    return {
        "reflexive": reflexive,
        "irreflexive": irreflexive,
        "symmetric": symmetric,
        "antisymmetric": antisymmetric,
        "transitive": transitive
    }


def transitive_reduction(node_ids: list, edges: list[tuple]) -> list[tuple]:
    """
    Removes redundant edges to compute the transitive reduction (used for Hasse diagrams).
    If A->B and B->C, then the edge A->C is redundant.
    Syllabus 4.1.

    Args:
        node_ids: List of node IDs.
        edges: List of directed edges as (source, target) tuples.

    Returns:
        A list of essential edges forming the transitive reduction.
    """
    matrix = relation_matrix(node_ids, edges)
    closure = warshall_closure(matrix)
    
    n = len(node_ids)
    reduction = [[matrix[i][j] for j in range(n)] for i in range(n)]
    
    for i in range(n):
        for j in range(n):
            if matrix[i][j] == 1:
                # Check if there is a path of length > 1 from i to j
                for k in range(n):
                    if i != k and j != k and matrix[i][k] == 1 and closure[k][j] == 1:
                        reduction[i][j] = 0
                        break
                        
    essential_edges = []
    for i in range(n):
        for j in range(n):
            if reduction[i][j] == 1:
                essential_edges.append((node_ids[i], node_ids[j]))
                
    return essential_edges


def equivalence_partition(items: list, key_fn: Callable[[Any], Any]) -> dict:
    """
    Partitions items into equivalence classes based on a key function.
    Syllabus 3.4.

    Args:
        items: List of items to partition.
        key_fn: Function that maps an item to its equivalence class identifier.

    Returns:
        A dictionary mapping equivalence class identifiers to lists of items.
    """
    partitions = {}
    for item in items:
        key = key_fn(item)
        if key not in partitions:
            partitions[key] = []
        partitions[key].append(item)
    return partitions


def compose_relations(R1: list[list[int]], R2: list[list[int]]) -> list[list[int]]:
    """
    Computes matrix composition R1 ∘ R2 via boolean matrix multiplication.
    Syllabus 3.3.

    Args:
        R1: First relation matrix.
        R2: Second relation matrix.

    Returns:
        Composed relation matrix.
    """
    n1 = len(R1)
    if n1 == 0:
        return []
    m1 = len(R1[0])
    n2 = len(R2)
    if n2 == 0:
        return [[] for _ in range(n1)]
    m2 = len(R2[0])
    
    result = [[0 for _ in range(m2)] for _ in range(n1)]
    for i in range(n1):
        for j in range(m2):
            for k in range(m1):
                if R1[i][k] == 1 and R2[k][j] == 1:
                    result[i][j] = 1
                    break
    return result
