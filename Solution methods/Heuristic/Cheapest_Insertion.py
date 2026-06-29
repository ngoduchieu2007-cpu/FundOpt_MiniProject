'''
FUNCTION Cheapest_Insertion():

    Initialize K empty routes
    Initialize unassigned passengers
    Initialize unassigned parcels

    WHILE unassigned requests remain:

        Find best feasible insertion

        IF no feasible insertion:
            BREAK

        IF best request is passenger:
            Insert pickup-dropoff pair
            Remove passenger from unassigned list

        ELSE:
            Insert parcel pickup-dropoff
            Update parcel load
            Remove parcel from unassigned list

        Update route cost

    RETURN routes
'''

import sys

def read_input():
    line = sys.stdin.readline()
    if not line:
        return None
    N, M, K = map(int, line.split())
    q = list(map(int, sys.stdin.readline().split()))
    Q = list(map(int, sys.stdin.readline().split()))
    size = 2*N + 2*M + 1
    dist = []
    for _ in range(size):
        dist.append(list(map(int, sys.stdin.readline().split())))
    return N, M, K, q, Q, dist

def calc_delta_passenger(route, pos, pickup, dropoff, dist):
    a, b = route[pos], route[pos+1]
    return dist[a][pickup] + dist[pickup][dropoff] + dist[dropoff][b] - dist[a][b]

def check_parcel_capacity(route, pos, pickup, dropoff, weight, capacity, parcel_list):
    test_route = route[:pos+1] + [pickup, dropoff] + route[pos+1:]
    weight_map = {}
    for p, d, w in parcel_list:
        # ??
        weight_map[p] = weight_map.get(p, 0) + w
        weight_map[d] = weight_map.get(d, 0) - w
    weight_map[pickup] = weight_map.get(pickup, 0) + weight
    weight_map[dropoff] = weight_map.get(dropoff, 0) - weight

    current_load = 0
    for point in test_route:
        if point in weight_map:
            current_load += weight_map[point]
        if current_load > capacity:
            return False
    return True

def calc_delta_parcel(route, pos, pickup, dropoff, weight, capacity, dist, parcel_list):
    if not check_parcel_capacity(route, pos, pickup, dropoff, weight, capacity, parcel_list):
        return None
    a, b = route[pos], route[pos+1]
    return dist[a][pickup] + dist[pickup][dropoff] + dist[dropoff][b] - dist[a][b]

def find_best_insertion(unassigned_passengers, unassigned_parcels, routes, routes_parcels,
                        capacities, N, M, q, dis, route_costs):
    best_future_cost = float('inf')
    best_type = None
    best_id = -1
    best_route = -1
    best_pos = -1
    best_delta = 0

    # Duyệt hành khách
    for p_id in unassigned_passengers:
        pickup = p_id + 1
        dropoff = p_id + 1 + N + M
        for r_idx, route in enumerate(routes):
            for pos in range(len(route)-1):
                delta = calc_delta_passenger(route, pos, pickup, dropoff, dis)
                future_cost = route_costs[r_idx] + delta
                if future_cost < best_future_cost:
                    best_future_cost = future_cost
                    best_type = 'passenger'
                    best_id = p_id
                    best_route = r_idx
                    best_pos = pos
                    best_delta = delta

    # Duyệt bưu kiện
    for c_id in unassigned_parcels:
        pickup = c_id + 1 + N
        dropoff = c_id + 1 + 2*N + M
        weight = q[c_id]
        for r_idx, route in enumerate(routes):
            parcel_list = routes_parcels[r_idx]
            for pos in range(len(route)-1):
                delta = calc_delta_parcel(route, pos, pickup, dropoff, weight,
                                          capacities[r_idx], dis, parcel_list)
                if delta is not None:
                    future_cost = route_costs[r_idx] + delta
                    if future_cost < best_future_cost:
                        best_future_cost = future_cost
                        best_type = 'parcel'
                        best_id = c_id
                        best_route = r_idx
                        best_pos = pos
                        best_delta = delta

    if best_future_cost == float('inf'):
        return None
    return (best_future_cost, best_type, best_id, best_route, best_pos, best_delta)

def insert_passenger(route, pickup, dropoff, pos):
    route.insert(pos+1, dropoff)
    route.insert(pos+1, pickup)

def insert_parcel(route, pickup, dropoff, pos):
    route.insert(pos+1, dropoff)
    route.insert(pos+1, pickup)

def build_routes(N, M, K, q, Q, dist):
    routes = [[0,0] for _ in range(K)]
    routes_parcels = [[] for _ in range(K)]
    route_costs = [0] * K  # chi phí hiện tại của từng tuyến

    unassigned_p = list(range(N))
    unassigned_c = list(range(M))

    while unassigned_p or unassigned_c:
        result = find_best_insertion(unassigned_p, unassigned_c, routes, routes_parcels,
                                     Q, N, M, q, dist, route_costs)
        if result is None:
            print("Không tìm được phương án chèn hợp lệ! Dừng.", file=sys.stderr)
            break

        _, best_type, best_id, best_route, best_pos, best_delta = result

        if best_type == 'passenger':
            pickup = best_id + 1
            dropoff = best_id + 1 + N + M
            insert_passenger(routes[best_route], pickup, dropoff, best_pos)
            route_costs[best_route] += best_delta
            unassigned_p.remove(best_id)
        else:  # parcel
            pickup = best_id + 1 + N
            dropoff = best_id + 1 + 2*N + M
            weight = q[best_id]
            insert_parcel(routes[best_route], pickup, dropoff, best_pos)
            routes_parcels[best_route].append((pickup, dropoff, weight))
            route_costs[best_route] += best_delta
            unassigned_c.remove(best_id)

    return routes

def print_solution(routes):
    print(len(routes))
    for route in routes:
        print(len(route))
        print(' '.join(map(str, route)))

def main():
    data = read_input()
    if data is None:
        return
    N, M, K, q, Q, dist = data
    routes = build_routes(N, M, K, q, Q, dist)
    print_solution(routes)

if __name__ == "__main__":
    main()

'''
FUNCTION Cheapest_Insertion():

    Initialize K empty routes
    Initialize unassigned passengers
    Initialize unassigned parcels

    WHILE unassigned requests remain:

        Find best feasible insertion

        IF no feasible insertion:
            BREAK

        IF best request is passenger:
            Insert pickup-dropoff pair
            Remove passenger from unassigned list

        ELSE:
            Insert parcel pickup-dropoff
            Update parcel load
            Remove parcel from unassigned list

        Update route cost

    RETURN routes
'''