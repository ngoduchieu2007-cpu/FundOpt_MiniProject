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

    Node indexing:
    - Depot: 0
    - Passenger pickup: 1..N
    - Parcel pickup: N+1 .. N+M
    - Passenger dropoff: N+M+1 .. 2N+M
    - Parcel dropoff: 2N+M+1 .. 2N+2M
    """

    if seed is not None:
        random.seed(seed)

    total_nodes = 2 * N + 2 * M + 1

    # -----------------------------
    # Generate parcel quantities
    # -----------------------------
    q = [random.randint(1, max_parcel_quantity) for _ in range(M)]

    # -----------------------------
    # Generate taxi capacities
    # Ensure capacities can handle parcels
    # -----------------------------
    Q = [
        random.randint(1, max_taxi_capacity)
        for _ in range(K)
    ]

    # -----------------------------
    # Generate coordinates
    # -----------------------------
    coords = []

    for _ in range(total_nodes):
        x = random.randint(0, max_coord)
        y = random.randint(0, max_coord)
        coords.append((x, y))

    # -----------------------------
    # Build symmetric distance matrix
    # -----------------------------
    d = [[0] * total_nodes for _ in range(total_nodes)]

    for i in range(total_nodes):
        xi, yi = coords[i]

        for j in range(total_nodes):
            xj, yj = coords[j]

            if i == j:
                d[i][j] = 0
            else:
                # Manhattan distance
                dist = abs(xi - xj) + abs(yi - yj)
                d[i][j] = dist
    return d, q, Q