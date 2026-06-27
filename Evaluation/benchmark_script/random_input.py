import random

def generate_input(
    N=10,
    M=10,
    K=3,
    max_coord=100,
    max_parcel_quantity=20,
    max_taxi_capacity=50,
    seed=None
):
    """
    Generate random input for the balanced taxi routing problem.
    """
    if seed is not None:
        random.seed(seed)

    total_nodes = 2 * N + 2 * M + 1

    # 1. Generate parcel quantities
    q = [random.randint(1, max_parcel_quantity) for _ in range(M)]

    # 2. Generate taxi capacities
    # FIX: Ensure capacities can handle AT LEAST the largest single parcel
    # Otherwise, the instance might be inherently infeasible.
    min_required_capacity = max(q) if q else 1
    safe_max_capacity = max(max_taxi_capacity, min_required_capacity)
    
    Q = [
        random.randint(min_required_capacity, safe_max_capacity)
        for _ in range(K)
    ]

    # 3. Generate coordinates
    coords = []
    for _ in range(total_nodes):
        x = random.randint(0, max_coord)
        y = random.randint(0, max_coord)
        coords.append((x, y))

    # 4. Build symmetric distance matrix
    d = [[0] * total_nodes for _ in range(total_nodes)]
    for i in range(total_nodes):
        xi, yi = coords[i]
        for j in range(total_nodes):
            if i == j:
                d[i][j] = 0
            else:
                # Manhattan distance
                d[i][j] = abs(xi - coords[j][0]) + abs(yi - coords[j][1])
                
    return d,q,Q
