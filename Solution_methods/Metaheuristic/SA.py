import sys 
import os
import math
import time
import random

# Set time limit max to 29000ms
TIME_LIMIT_MS = float(os.environ.get("SARP_TIME_MS", "29000"))

random.seed(1) # for reproducible purpose

# ==========================================================================================
# Instance class
# ==========================================================================================
class Instance:
    def __init__(self, N, M, K, q, Q, d):
        self.N = N
        self.M = M
        self.K = K
        self.q = q # quantiy of each parcel requests from q[1] to q[M]
        self.Q = Q # Q[0...K-1]
        self.d = d # d[i][j], points 0 .. 2N + 2M

    def nodes_of(self, token):
        '''Decode the token of type ('P', i) or ('+/-', j) to its actual point index'''
        kind, idx = token
        if kind == 'P':
            return (idx, idx + self.N + self.M) # pickup, dropoff
        if kind == '+':
            return (self.N + idx, ) # parcel pickup
        if kind == '-':
            return (2 * self.N + self.M + idx, ) # parcel dropoff
    
    def route_length(self, tokens):
        '''Compute the length of a route'''
        d = self.d
        prev = 0
        total = 0
        for tk in tokens:
            for node in self.nodes_of(tk):
                total += d[prev][node]
                prev = node
        total += d[prev][0] # back to depot
        return total
    
    def peak_load(self, tokens):
        '''Compute the maximum load on the current route'''
        q = self.q
        load = 0
        peak = 0
        for kind, idx in tokens:
            if kind == '+':
                load += q[idx]
                if load > peak:
                    peak = load
            elif kind == '-':
                load -= q[idx]
        return peak
    
    def evaluate(self, sol, changes):
        '''Evaluate the changes of the new solution.
        Return new_len - the new routes_length of taxis that been adjusted, 
        makespan - the new makespan, total - the new total length of all taxis.
        '''
        new_len = {}
        for k, toks in changes.items():
            if self.peak_load(toks) > self.Q[k]:
                return None # this changes cause taxi k to be overloaded
            new_len[k] = self.route_length(toks)
        
        makespan = 0
        for k in range(self.K):
            L = new_len[k] if k in new_len else sol.length[k]
            if L > makespan:
                makespan = L
        total = sol.total + sum(new_len[k] - sol.length[k] for k in new_len)
        
        return new_len, makespan, total

# ==========================================================================================
# Solution class
# ==========================================================================================
class Solution:
    __slots__ = ("routes", "length", "makespan", "total")

    def __init__(self, routes, length, makespan, total):
        self.routes = routes # list[list[token]]; token is of type ('P', i) or ('+/-', j)
        self.length = length # list[int] cached route lengths
        self.makespan = makespan # int max(length); actual objective value
        self.total = total # int sum(length); sub objective value

def clone(sol):
    '''Make a clone of a solution'''
    clone_routes = [list(r) for r in sol.routes]
    clone_length = list(sol.length)
    clone_makespan, clone_total = sol.makespan, sol.total
    return Solution(clone_routes, clone_length, clone_makespan, clone_total)

def is_better(m1, t1, m2, t2):
    '''Check if new solution is better'''
    # Prioritize minimizing makespan then total length
    # m1 and m2 is makespan of new and old solution respectively
    # t1 and t2 is total length of new and old solution respectively

    return m1 < m2 or (m1 == m2 and t1 < t2)

# ==========================================================================================
# Input / Output
# ==========================================================================================
def read_input():
    data = sys.stdin.buffer.read().split()
    it = iter(data)

    def nxt_int():
        return int(next(it))
    
    N = nxt_int()
    M = nxt_int()
    K = nxt_int()

    q = [0] + [nxt_int() for _ in range(M)]
    Q = [nxt_int() for _ in range(K)]

    P = 2 * N + 2 * M + 1
    d = [[0] * P for _ in range(P)]
    for i in range(P):
        row = d[i]
        for j in range(P):
            row[j] = nxt_int()
    
    return Instance(N, M, K, q, Q, d)

def write_output(inst, sol):
    out = [str(inst.K)]
    for k in range(inst.K):
        seq = [0]
        for tk in sol.routes[k]:
            seq.extend(inst.nodes_of(tk))
        seq.append(0)

        out.append(str(len(seq)))
        out.append(" ".join(map(str, seq)))
    sys.stdout.write("\n".join(out) + "\n")

# ==========================================================================================
# Initial Solution
# ==========================================================================================
def initial_solution(inst):
    '''Use Greedy to initialize the first solution before SA'''
    K = inst.K
    routes = [[] for _ in range(K)]
    length = [0] * K

    # Heaviest parcel first
    for j in sorted(range(1, inst.M + 1), key = lambda j: -inst.q[j]):
        feasible = [k for k in range(K) if inst.Q[k] >= inst.q[j]] # taxis that available of picking parcel j
        if not feasible:
            # No taxi can carry this parcel which should not happen
            raise ValueError(f"parcel {j} (q={inst.q[j]}) exceeds every taxi capacity")
        else:
            k = min(feasible, key = lambda k: length[k])
        routes[k].extend([('+', j), ('-', j)])
        length[k] = inst.route_length(routes[k])

    # Passengers next, shortest taxi
    for i in range(1, inst.N + 1):
        k = min(range(K), key = lambda k: length[k])
        routes[k].append(('P', i))
        length[k] = inst.route_length(routes[k])

    return Solution(routes, length, max(length), sum(length))

# ==========================================================================================
# Neighbourhood
# ==========================================================================================
def requests_in(tokens):
    '''Make a proper form of requests'''
    reqs = []
    seen = set()
    for kind, idx in tokens:
        if kind == 'P':
            reqs.append(('P', idx))
        elif idx not in seen:
            seen.add(idx)
            reqs.append(('C', idx))
    return reqs

def pick_request(tokens):
    '''Randomly pick a request'''
    return random.choice(requests_in(tokens))

def remove_request(tokens, req):
    '''Remove a request in a route of a taxi'''
    kind, idx = req
    if kind == 'P':
        target = ('P', idx)
        return [t for t in tokens if t != target]
    # parcel: drop both ('+', idx) and ('-', idx)
    return [t for t in tokens if not (t[1] == idx and t[0] in ('+', '-'))]

def insert_request(tokens, req):
    '''Randomly insert a request to a route of a taxi, preserve the precedence constraint'''
    kind, idx = req
    n = len(tokens)
    if kind == 'P':
        a = random.randint(0, n)
        return tokens[:a] + [('P', idx)] + tokens[a:]
    # parcel: pickup at gap a, dropoff at gap b >= a -> '+' before '-'
    a = random.randint(0, n)
    b = random.randint(a, n)
    return tokens[:a] + [('+', idx)] + tokens[a:b] + [('-', idx)] + tokens[b:]

def nonempty(sol):
    '''Find taxis that are not empty'''
    return [k for k in range(len(sol.routes)) if sol.routes[k]]

def op_relocate(sol):
    '''
    Neighbour Operation 1: Relocate
    Randomly pick 2 taxis, randomly move a request from 1 taxi to the other
    The whole process preserve Precedence Constraint but not Capacity Constraint(check later)
    Return the new adjusted routes of 2 selected taxis
    '''
    busy = nonempty(sol)
    if not busy:
        return None
    src = random.choice(busy)
    req = pick_request(sol.routes[src])

    K = len(sol.routes)
    if K < 2:
        return None
    dst = random.randrange(K)
    while dst == src:
        dst = random.randrange(K)
    
    return {src: remove_request(sol.routes[src], req),
            dst: insert_request(sol.routes[dst], req)}

def op_swap(sol):
    '''
    Neighbour Operation 2: Swap
    Randomly pick 2 taxis, then swap 2 random requests
    The whole process preserve Precedence Constraint but not Capacity Constraint(check later)
    Return the new adjusted routes of 2 selected taxis
    '''
    busy = nonempty(sol)
    if len(busy) < 2:
        return None
    a, b = random.sample(busy, 2)
    ra = pick_request(sol.routes[a])
    rb = pick_request(sol.routes[b])
    return {a: insert_request(remove_request(sol.routes[a], ra), rb),
            b: insert_request(remove_request(sol.routes[b], rb), ra)}

def op_or_opt(sol):
    '''
    Neighbour Operation 3: Or-opt
    Randomly pick 1 taxi, then pick 1 random request in its route
    and change that request's position in the taxi's route.
    The whole process preserve Precedence Constraint AND Capacity Constraint.
    Return the new adjusted route of the selected taxi.
    '''
    busy = nonempty(sol)
    if not busy:
        return None
    k = random.choice(busy)
    req = pick_request(sol.routes[k])
    new_route = insert_request(remove_request(sol.routes[k], req), req)
    if new_route == sol.routes[k]:
        return None # No change
    return {k: new_route}

OPERATORS = (op_relocate, op_swap, op_or_opt)

def random_neighbour(sol):
    '''Select a random neighbour of the current solution'''
    return random.choice(OPERATORS)(sol)

# ==========================================================================================
# Simulated Annealing
# ==========================================================================================
def estimate_T0(inst, sol, samples = 300, target_accept = 0.8):
    '''Set T0 so a typical worsening move is accepted with prob ~target'''
    deltas = []
    for _ in range(samples):
        changes = random_neighbour(sol)
        if not changes:
            continue
        eval = inst.evaluate(sol, changes)
        if not eval:
            continue
        d = eval[1] - sol.makespan # makespan delta (eval[1] is new makespan)
        if d > 0:
            deltas.append(d)
    if not deltas:
        return 1.0
    avg = sum(deltas) / len(deltas)
    return max(1.0, -avg / math.log(target_accept))

def simulated_annealing(inst, deadline, alpha = 0.99997, t_min = 1e-8):
    """
    Search for a low-makespan solution using Simulated Annealing.
    Runs until deadline, returns the best solution found.
    """
    # Initialize 
    sol = initial_solution(inst) # current solution
    best = clone(sol)            # best solution so far
    T = estimate_T0(inst, sol)   # starting temperature

    iter = 0
    while True:
        # check if deadline meets
        if (iter & 255) == 0 and time.time() >= deadline:
            break
        iter += 1

        # Try make a move
        changes = random_neighbour(sol)
        if changes is None:
            continue
        
        # Evaluate + capacity check
        eval = inst.evaluate(sol, changes)
        if eval is None:
            continue # capacity violated
        new_len, new_makespan, new_total = eval

        # Lexicographic acceptance rule with Metropolis 
        delta_makespan = new_makespan - sol.makespan
        if delta_makespan < 0:
            accept = True
        elif delta_makespan == 0:
            delta_total = new_total - sol.total
            accept = (delta_total <= 0) or (random.random() < math.exp(-delta_total / T))
        else:
            accept = random.random() < math.exp(-delta_makespan / T)

        # commit if accepted
        if accept:
            for k, toks in changes.items():
                sol.routes[k] = toks
                sol.length[k] = new_len[k]
            sol.makespan, sol.total = new_makespan, new_total
            if is_better(sol.makespan, sol.total, best.makespan, best.total):
                best = clone(sol)
        
        # cool down
        if T > t_min:
            T *= alpha 
    return best

# ===========================================================================
# Main
# ===========================================================================
def main():
    start = time.time()
    inst = read_input()
    best = simulated_annealing(inst, deadline = start + TIME_LIMIT_MS / 1000.0)
    write_output(inst, best)

if __name__ == "__main__":
    main()
