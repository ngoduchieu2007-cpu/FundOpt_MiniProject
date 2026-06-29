import random
import time
from random_input import *
from typing import List, Tuple, Optional
from bnb import bnb
from scip import *
def check_solution(N: int, M: int, K: int, 
                   q: List[int], Q: List[int], 
                   routes: List[List[int]], 
                   distance_matrix: Optional[List[List[float]]] = None) -> Tuple[bool, str]:
    if len(routes) > K:
        return False, f"Number of routes ({len(routes)}) exceeds number of available taxis ({K})."
        
    visited_points = set()
    max_route_length = 0.0
    
    for k, route in enumerate(routes):
        if not route or route[0] != 0 or route[-1] != 0:
            return False, f"Route {k+1} must start and end at the depot (0). Route: {route}"
            
        current_weight = 0
        active_parcels = set()
        
        if distance_matrix is not None:
            route_dist = sum(distance_matrix[route[i]][route[i+1]] for i in range(len(route) - 1))
            if route_dist > max_route_length:
                max_route_length = route_dist
        
        idx = 1
        while idx < len(route) - 1:
            point = route[idx]
            
            if point in visited_points:
                return False, f"Point {point} visited more than once."
            visited_points.add(point)
            
            if 1 <= point <= N:
                dropoff = point + N + M
                if idx + 1 >= len(route) - 1 or route[idx+1] != dropoff:
                    return False, f"Passenger {point} not served directly. Expected immediate drop-off at {dropoff}."
                if dropoff in visited_points:
                    return False, f"Point {dropoff} visited more than once."
                visited_points.add(dropoff)
                idx += 2
            elif N + 1 <= point <= N + M:
                parcel_idx = point - N
                weight = q[parcel_idx - 1]
                current_weight += weight
                if current_weight > Q[k]:
                    return False, f"Taxi {k+1} capacity exceeded at point {point}. Capacity: {Q[k]}, Current weight: {current_weight}"
                active_parcels.add(parcel_idx)
                idx += 1
            elif 2 * N + M + 1 <= point <= 2 * N + 2 * M:
                parcel_idx = point - (2 * N + M)
                if parcel_idx not in active_parcels:
                    return False, f"Parcel {parcel_idx} (point {point}) dropped off before pickup or not in taxi {k+1}."
                weight = q[parcel_idx - 1]
                current_weight -= weight
                active_parcels.remove(parcel_idx)
                idx += 1
            elif N + M + 1 <= point <= 2 * N + M:
                return False, f"Passenger drop-off {point} encountered without a direct pickup beforehand."
            else:
                return False, f"Invalid point {point} encountered in route."
                
        if active_parcels:
            return False, f"Route {k+1} ends with undelivered parcels: {active_parcels}"
            
    expected_visited_count = 2 * N + 2 * M
    if len(visited_points) != expected_visited_count:
        missing = set(range(1, 2 * N + 2 * M + 1)) - visited_points
        return False, f"Not all requests were served. Missing points: {missing}"
        
    return True, str(max_route_length) if distance_matrix is not None else "Valid"

def measure_time(func):
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        return result, end - start
    return wrapper

def check_constraint(routes, N, M, K):
    for route in routes:
        for i, node in enumerate(route):
            if i == 0 and node != 0:
                return False
            if node == 0 and i != len(route) - 1:
                return False
            if (node <= N) and (route[i+1] > N + M):
                return False
            if (node > N and node <= 2*N) and (route[i+1] <= N):
                return False
    return True
if __name__ == "__main__":


    for i in range(10, 200, 10):
        # FIXED: i - 1 ensures N always leaves at least 1 for M
        N = random.randint(1, i - 1)
        M = i - N
        
        K = random.randint(1, min(100, (N + M)))
        
        input_size = (1 + 2 * (N + M))
        print(input_size)
        
        distance, q, Q = generate_input(N, M, K, seed=42)
        
        # --- USAGE INSTRUCTIONS ---
        # The following block evaluates multiple algorithms to solve the routing problem.
        # Each function (e.g., greedy_passenger_first) returns a solution representing the taxis' routes (stored in resX).
        # The `measure_time` decorator also captures the execution duration (stored in timeX).
        # 
        # To verify the constraints of any algorithm's output, pass its result to the `check_solution` function:
        # 
        # is_valid, max_len_or_error = check_solution(N, M, K, q, Q, res1, distance)
        # if not is_valid:
        #     print(f"Error in greedy_passenger_first: {max_len_or_error}")
        # else:
        #     print(f"greedy_passenger_first valid! Max route length: {max_len_or_error}")
        # --------------------------
        # Your algorithms here
        # For example:
        # res1, time1 = measure_time(greedy_passenger_first)(N, M, K, q, Q, distance)
        # ...
        
        # Example usage of check_solution:
        # is_valid, max_len_or_error = check_solution(N, M, K, q, Q, res1, distance)
        # if not is_valid:
        #     print(f"Error in greedy_passenger_first: {max_len_or_error}")
        # else:
        #     print(f"greedy_passenger_first valid! Max route length: {max_len_or_error}")

        res1, time1 = measure_time(bnb)(N,M,K,q,Q,distance)
        
        # FIXED: Added 'if res1:' to prevent crashing if the solver times out and returns None
        if res1: 
            is_valid, max_len_or_error = check_solution(N, M, K, q, Q, res1, distance)
            if not is_valid:
                print(f"Error in bnb: {max_len_or_error}")
            else:
                print(f"bnb valid! Max route length: {max_len_or_error}")
                for route in res1:
                    print(len(route), route)
        

        res2, time2 = measure_time(solve_cvrp_pd)(N,M,K,q,Q,distance)
        
        # FIXED: Added 'if res2:' to prevent crashing if the solver times out and returns None
        if res2:
            is_valid, max_len_or_error = check_solution(N, M, K, q, Q, res2, distance)
            if not is_valid:
                print(f"Error in solve_cvrp_pd: {max_len_or_error}")
            else:
                print(f"solve_cvrp_pd valid! Max route length: {max_len_or_error}")
                for route in res2:
                    print(len(route), route)
                    
        print(f"N={N}, M={M}, K={K} -> ... \n")
        print(f"bnb time: {time1}")
        print(f"solve_cvrp_pd time: {time2}")