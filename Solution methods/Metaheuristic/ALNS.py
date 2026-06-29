'''
FUNCTION ALNS_SA():

    S = Initial_Solution()
    Initialize Weights
    Initialize Temperature

    FOR each iteration:

        Select Destroy Operator
        Destroy Solution

        Select Repair Operator
        Repair Solution

        Evaluate Solution

        IF Better OR Accepted by SA:
            Update Current Solution

        Update Operator Weights
        Cool Temperature

    RETURN Best Solution
'''


import sys
import random
import math
import copy

def read_input():
    data = sys.stdin.read().strip().split()
    it = iter(data)
    N = int(next(it))
    M = int(next(it))
    K = int(next(it))
    q = [0] + [int(next(it)) for _ in range(M)]
    Q = [0] + [int(next(it)) for _ in range(K)]
    total_points = 2*N + 2*M + 1
    dist = [[0]*total_points for _ in range(total_points)]
    for i in range(total_points):
        for j in range(total_points):
            dist[i][j] = int(next(it))
    return N, M, K, q, Q, dist

def route_length(route, dist):
    if len(route) < 2:
        return 0
    total = 0
    for i in range(len(route)-1):
        total += dist[route[i]][route[i+1]]
    total += dist[route[-1]][0]
    return total

def is_feasible_route(route, k, N, M, q, Q):
    if route[0] != 0 or route[-1] != 0:
        return False
    # Kiểm tra trùng lặp điểm (trừ 0)
    non_zero = [p for p in route if p != 0]
    if len(non_zero) != len(set(non_zero)):
        return False
    # Kiểm tra passenger pairs (pickup và dropoff liền kề)
    for i in range(1, N+1):
        pickup = i
        dropoff = i + N + M
        try:
            pos = route.index(pickup)
        except ValueError:
            return False
        if pos + 1 >= len(route) or route[pos+1] != dropoff:
            return False
    # Kiểm tra parcel (pickup trước dropoff)
    for i in range(1, M+1):
        pickup = i + N
        dropoff = i + 2*N + M
        try:
            pos_p = route.index(pickup)
            pos_d = route.index(dropoff)
        except ValueError:
            return False
        if pos_p > pos_d:
            return False
    # Kiểm tra tải trọng
    capacity = 0
    for i in range(1, M+1):
        pickup = i + N
        if pickup in route:
            capacity += q[i]
    if capacity > Q[k]:
        return False
    return True

def total_makespan(solution, dist):
    max_len = 0
    for route in solution:
        length = route_length(route, dist)
        if length > max_len:
            max_len = length
    return max_len

def initial_solution(N, M, K, q, Q, dist):
    solution = [[0,0] for _ in range(K+1)]
    requests = []
    for i in range(1, N+1):
        requests.append(('p', i))
    for i in range(1, M+1):
        requests.append(('r', i))
    random.shuffle(requests)
    
    for typ, idx in requests:
        assigned = False
        if typ == 'p':
            pickup = idx
            dropoff = idx + N + M
            for k in random.sample(range(1, K+1), K):
                route = solution[k]
                for pos in range(1, len(route)):
                    new_route = route[:pos] + [pickup, dropoff] + route[pos:]
                    if is_feasible_route(new_route, k, N, M, q, Q):
                        solution[k] = new_route
                        assigned = True
                        break
                if assigned:
                    break
        else:
            pickup = idx + N
            dropoff = idx + 2*N + M
            for k in random.sample(range(1, K+1), K):
                route = solution[k]
                for i in range(1, len(route)):
                    for j in range(i, len(route)):
                        new_route = route[:i] + [pickup] + route[i:j] + [dropoff] + route[j:]
                        if is_feasible_route(new_route, k, N, M, q, Q):
                            solution[k] = new_route
                            assigned = True
                            break
                    if assigned:
                        break
                if assigned:
                    break
        if not assigned:
            print(f"Warning: Cannot assign request {typ}{idx}", file=sys.stderr)
    return solution[1:]

def random_removal(solution, num_removals, N, M):
    all_points = []
    for route in solution:
        for point in route:
            if point != 0:
                all_points.append(point)
    if len(all_points) < num_removals:
        num_removals = len(all_points)
    removed_points = random.sample(all_points, num_removals)
    
    expanded_removed = set()
    for p in removed_points:
        if 1 <= p <= N:  # passenger pickup
            dropoff = p + N + M
            expanded_removed.add(p)
            expanded_removed.add(dropoff)
        elif N + M < p <= 2*N + M:  # passenger dropoff
            pickup = p - (N + M)
            expanded_removed.add(p)
            expanded_removed.add(pickup)
        elif N < p <= N + M:  # parcel pickup
            expanded_removed.add(p)
        elif 2*N + M < p <= 2*N + 2*M:  # parcel dropoff
            expanded_removed.add(p)
        else:
            expanded_removed.add(p)
    
    for route in solution:
        for p in expanded_removed:
            while p in route:
                route.remove(p)
    
    for k in range(len(solution)):
        if len(solution[k]) == 0:
            solution[k] = [0,0]
        elif solution[k][0] != 0:
            solution[k].insert(0,0)
        if solution[k][-1] != 0:
            solution[k].append(0)
    return solution, list(expanded_removed)

def worst_removal(solution, num_removals, dist, N, M):
    benefits = []
    for route_idx, route in enumerate(solution):
        if len(route) <= 2:
            continue
        for pos in range(1, len(route)-1):
            point = route[pos]
            prev = route[pos-1]
            nxt = route[pos+1]
            benefit = dist[prev][point] + dist[point][nxt] - dist[prev][nxt]
            benefits.append((benefit, route_idx, pos, point))
    benefits.sort(reverse=True, key=lambda x: x[0])
    removed_points = []
    for benefit, r_idx, pos, point in benefits[:num_removals]:
        if point in solution[r_idx]:
            solution[r_idx].remove(point)
            removed_points.append(point)
    
    expanded_removed = set()
    for p in removed_points:
        if 1 <= p <= N:
            dropoff = p + N + M
            expanded_removed.add(p)
            expanded_removed.add(dropoff)
        elif N + M < p <= 2*N + M:
            pickup = p - (N + M)
            expanded_removed.add(p)
            expanded_removed.add(pickup)
        elif N < p <= N + M:
            expanded_removed.add(p)
        elif 2*N + M < p <= 2*N + 2*M:
            expanded_removed.add(p)
        else:
            expanded_removed.add(p)
    
    for route in solution:
        for p in expanded_removed:
            while p in route:
                route.remove(p)
    
    for k in range(len(solution)):
        if len(solution[k]) == 0:
            solution[k] = [0,0]
        elif solution[k][0] != 0:
            solution[k].insert(0,0)
        if solution[k][-1] != 0:
            solution[k].append(0)
    return solution, list(expanded_removed)

def segment_removal(solution, num_removals, dist, N, M):
    routes_with_length = [(i, route) for i, route in enumerate(solution) if len(route) > 3]
    if not routes_with_length:
        return solution, []
    route_idx, route = random.choice(routes_with_length)
    max_removals = len(route) - 2
    if num_removals > max_removals:
        num_removals = max_removals
    if num_removals <= 0:
        return solution, []
    max_start = len(route) - num_removals - 1
    if max_start < 1:
        start = 1
        end = len(route) - 1
    else:
        start = random.randint(1, max_start)
        end = start + num_removals - 1
    removed_segment = route[start:end+1]
    new_route = route[:start] + route[end+1:]
    solution[route_idx] = new_route
    
    expanded_removed = set()
    for p in removed_segment:
        if p != 0:
            expanded_removed.add(p)
    
    for p in list(expanded_removed):
        if 1 <= p <= N:
            dropoff = p + N + M
            expanded_removed.add(dropoff)
        elif N + M < p <= 2*N + M:
            pickup = p - (N + M)
            expanded_removed.add(pickup)
    
    for route in solution:
        for p in expanded_removed:
            while p in route:
                route.remove(p)
    
    for k in range(len(solution)):
        if len(solution[k]) == 0:
            solution[k] = [0,0]
        elif solution[k][0] != 0:
            solution[k].insert(0,0)
        if solution[k][-1] != 0:
            solution[k].append(0)
    return solution, list(expanded_removed)

def random_insertion(solution, removed_points, N, M, q, Q, dist):
    points_to_insert = set()
    for p in removed_points:
        if p == 0:
            continue
        if 1 <= p <= N:
            points_to_insert.add(p)
        elif N < p <= N + M:
            points_to_insert.add(p)
        elif N + M < p <= 2*N + M:
            pickup = p - (N + M)
            if 1 <= pickup <= N:
                points_to_insert.add(pickup)
        else:
            pickup = p - (N + M)
            if N < pickup <= N + M:
                points_to_insert.add(pickup)
    points_to_insert = list(points_to_insert)
    random.shuffle(points_to_insert)

    for p in points_to_insert:
        if 1 <= p <= N:
            pickup = p
            dropoff = p + N + M
            candidates = []
            for r_idx, route in enumerate(solution):
                L = len(route)
                for pos in range(1, L):
                    new_route = route[:pos] + [pickup, dropoff] + route[pos:]
                    if is_feasible_route(new_route, r_idx+1, N, M, q, Q):
                        candidates.append((r_idx, pos))
            if candidates:
                r_idx, pos = random.choice(candidates)
                route = solution[r_idx]
                solution[r_idx] = route[:pos] + [pickup, dropoff] + route[pos:]
        else:
            pickup = p
            dropoff = p + N + M
            candidates = []
            for r_idx, route in enumerate(solution):
                L = len(route)
                for pos_p in range(1, L):
                    for pos_d in range(pos_p, L):
                        new_route = route[:pos_p] + [pickup] + route[pos_p:pos_d] + [dropoff] + route[pos_d:]
                        if is_feasible_route(new_route, r_idx+1, N, M, q, Q):
                            candidates.append((r_idx, pos_p, pos_d))
            if candidates:
                r_idx, pos_p, pos_d = random.choice(candidates)
                route = solution[r_idx]
                solution[r_idx] = route[:pos_p] + [pickup] + route[pos_p:pos_d] + [dropoff] + route[pos_d:]
    return solution

def greedy_insertion(solution, removed_points, N, M, q, Q, dist):
    points_to_insert = set()
    for p in removed_points:
        if p == 0:
            continue
        if 1 <= p <= N:
            points_to_insert.add(p)
        elif N < p <= N + M:
            points_to_insert.add(p)
        elif N + M < p <= 2*N + M:
            pickup = p - (N + M)
            if 1 <= pickup <= N:
                points_to_insert.add(pickup)
        else:
            pickup = p - (N + M)
            if N < pickup <= N + M:
                points_to_insert.add(pickup)
    points_to_insert = list(points_to_insert)
    random.shuffle(points_to_insert)

    for p in points_to_insert:
        if 1 <= p <= N:
            pickup = p
            dropoff = p + N + M
            best_inc = float('inf')
            best_route_idx = -1
            best_pos = -1

            for r_idx, route in enumerate(solution):
                L = len(route)
                for pos in range(1, L):
                    new_route = route[:pos] + [pickup, dropoff] + route[pos:]
                    if is_feasible_route(new_route, r_idx+1, N, M, q, Q):
                        inc = route_length(new_route, dist) - route_length(route, dist)
                        if inc < best_inc:
                            best_inc = inc
                            best_route_idx = r_idx
                            best_pos = pos

            if best_route_idx != -1:
                route = solution[best_route_idx]
                solution[best_route_idx] = route[:best_pos] + [pickup, dropoff] + route[best_pos:]

        else:
            pickup = p
            dropoff = p + N + M
            best_inc = float('inf')
            best_route_idx = -1
            best_pos_p = -1
            best_pos_d = -1

            for r_idx, route in enumerate(solution):
                L = len(route)
                for pos_p in range(1, L):
                    for pos_d in range(pos_p, L):
                        new_route = route[:pos_p] + [pickup] + route[pos_p:pos_d] + [dropoff] + route[pos_d:]
                        if is_feasible_route(new_route, r_idx+1, N, M, q, Q):
                            inc = route_length(new_route, dist) - route_length(route, dist)
                            if inc < best_inc:
                                best_inc = inc
                                best_route_idx = r_idx
                                best_pos_p = pos_p
                                best_pos_d = pos_d

            if best_route_idx != -1:
                route = solution[best_route_idx]
                solution[best_route_idx] = route[:best_pos_p] + [pickup] + route[best_pos_p:best_pos_d] + [dropoff] + route[best_pos_d:]

    return solution

def alns(N, M, K, q, Q, dist, max_iter=1000, temp_init=100, cooling=0.995):
    # Khởi tạo lời giải ban đầu
    solution = initial_solution(N, M, K, q, Q, dist)
    best_solution = copy.deepcopy(solution)
    best_cost = total_makespan(solution, dist)
    current_cost = best_cost
    temp = temp_init

    destroy_ops = ['random', 'worst', 'segment']
    repair_ops = ['greedy', 'random']

    destroy_weights = {op: 1.0 for op in destroy_ops}
    repair_weights = {op: 1.0 for op in repair_ops}

    destroy_scores = {op: 0.0 for op in destroy_ops}
    repair_scores = {op: 0.0 for op in repair_ops}
    destroy_used = {op: 0 for op in destroy_ops}
    repair_used = {op: 0 for op in repair_ops}

    reaction = 0.2         
    update_period = 50      

    reward_best = 10     
    reward_improve = 5     

    for it in range(max_iter):
        total_d = sum(destroy_weights.values())
        if total_d <= 0:  # phòng trường hợp
            destroy_method = random.choice(destroy_ops)
        else:
            r = random.random() * total_d
            cum = 0
            for op in destroy_ops:
                cum += destroy_weights[op]
                if cum >= r:
                    destroy_method = op
                    break
            else:
                destroy_method = destroy_ops[-1]

        total_r = sum(repair_weights.values())
        if total_r <= 0:
            repair_method = random.choice(repair_ops)
        else:
            r = random.random() * total_r
            cum = 0
            for op in repair_ops:
                cum += repair_weights[op]
                if cum >= r:
                    repair_method = op
                    break
            else:
                repair_method = repair_ops[-1]

        destroy_used[destroy_method] += 1
        repair_used[repair_method] += 1

        num_removals = random.randint(1, max(1, int(0.3 * (2 * N + 2 * M))))
        new_solution = copy.deepcopy(solution)

        if destroy_method == 'random':
            new_solution, removed = random_removal(new_solution, num_removals, N, M)
        elif destroy_method == 'worst':
            new_solution, removed = worst_removal(new_solution, num_removals, dist, N, M)
        else:  
            new_solution, removed = segment_removal(new_solution, num_removals, dist, N, M)

        if not removed:
            continue  
  
        if repair_method == 'greedy':
            new_solution = greedy_insertion(new_solution, removed, N, M, q, Q, dist)
        else: 
            new_solution = random_insertion(new_solution, removed, N, M, q, Q, dist)

        new_cost = total_makespan(new_solution, dist)
        reward = 0

        if new_cost < best_cost:
            solution = new_solution
            current_cost = new_cost
            best_solution = copy.deepcopy(new_solution)
            best_cost = new_cost
            reward = reward_best

        elif new_cost < current_cost:
            solution = new_solution
            current_cost = new_cost
            reward = reward_improve

        elif random.random() < math.exp(-(new_cost - current_cost) / temp):
            solution = new_solution
            current_cost = new_cost

        if reward > 0:
            destroy_scores[destroy_method] += reward
            repair_scores[repair_method] += reward

        temp *= cooling
        if temp < 0.01:
            break

        if it % update_period == 0 and it > 0:
            for op in destroy_ops:
                if destroy_used[op] > 0:
                    avg_score = destroy_scores[op] / destroy_used[op]
                    destroy_weights[op] = (1 - reaction) * destroy_weights[op] + reaction * avg_score
                else:
                    destroy_weights[op] = 1.0  

            for op in repair_ops:
                if repair_used[op] > 0:
                    avg_score = repair_scores[op] / repair_used[op]
                    repair_weights[op] = (1 - reaction) * repair_weights[op] + reaction * avg_score
                else:
                    repair_weights[op] = 1.0

            total_d = sum(destroy_weights.values())
            if total_d > 0:
                for op in destroy_ops:
                    destroy_weights[op] /= total_d

            total_r = sum(repair_weights.values())
            if total_r > 0:
                for op in repair_ops:
                    repair_weights[op] /= total_r

            for op in destroy_ops:
                destroy_scores[op] = 0.0
                destroy_used[op] = 0
            for op in repair_ops:
                repair_scores[op] = 0.0
                repair_used[op] = 0

    return best_solution, best_cost

def print_solution(solution):
    K = len(solution)
    print(K)
    for route in solution:
        print(len(route))
        print(' '.join(map(str, route)))

if __name__ == "__main__":
    random.seed(1234)
    N, M, K, q, Q, dist = read_input()
    best_solution, best_cost = alns(N, M, K, q, Q, dist, max_iter=500)
    print_solution(best_solution)

'''
FUNCTION ALNS_SA(N, M, K, q, Q, dist):

    S = Initial_Solution()
    S_best = S
    Cost = Makespan(S)
    BestCost = Cost
    T = Initial_Temperature()

    Initialize Destroy_Operators
    Initialize Repair_Operators
    Initialize Adaptive_Weights

    FOR iter = 1 TO Max_Iterations:

        Destroy = Select_Destroy_By_Weights()
        Repair  = Select_Repair_By_Weights()

        S' = Copy(S)
        Removed = Destroy(S', Destroy)

        IF Removed is empty:
            CONTINUE

        S' = Repair(S', Removed, Repair)
        NewCost = Makespan(S')

        IF NewCost < BestCost:
            S = S'
            S_best = S'
            Cost = NewCost
            BestCost = NewCost
            Reward = Best

        ELSE IF NewCost < Cost:
            S = S'
            Cost = NewCost
            Reward = Improve

        ELSE IF rand() < exp(-(NewCost-Cost)/T):
            S = S'
            Cost = NewCost

        Update_Operator_Scores()

        IF iter mod Update_Period == 0:
            Update_Adaptive_Weights()
            Normalize_Weights()
            Reset_Scores()

        T = T × Cooling

        IF T < Tmin:
            BREAK

    RETURN S_best
'''