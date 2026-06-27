import sys
import os
import time
import random
from array import array

# set time limit
TIME_LIMIT_MS = 29000.0
random.seed(1) # for reducible purpose

# ===========================================================================
#  Instance
# ===========================================================================
class Instance:
    def __init__(self, N, M, K, q, Q, d):
        self.N = N
        self.M = M
        self.K = K
        self.q = q                   # q[1....M], 1-indexed
        self.Q = Q                   # Q[0....K - 1]
        self.d = d                   # distance matrix d[i][j]
        self.S = 2 * N + 2 * M + 1   # number of points

    #node-id classifier
    def is_pass_pickup(self, v): return 1 <= v <= self.N
    def is_parcel_pickup(self, v): return self.N < v <= self.N + self.M
    def is_parcel_drop(self, v): return v > 2 * self.N + self.M

# ===========================================================================
#  Input / Output
# ===========================================================================

def read_input():
    data = sys.stdin.buffer.read().split()
    it = iter(data)
    nxt = lambda: int(next(it))

    N, M, K = nxt(), nxt(), nxt()
    q = [0] + [nxt() for _ in range(M)]
    Q = [nxt() for _ in range(K)]

    P = 2 * N + 2 * M + 1
    d = [[nxt() for _ in range(P)] for _ in range(P)]
    return Instance(N, M, K, q, Q, d)

def write_output(inst, routes):
    out = [str(inst.K)]
    for k in range(inst.K):
        seq = routes[k]
        out.append(str(len(seq)))
        out.append(" ".join(map(str, seq)))
    sys.stdout.write("\n".join(out) + "\n")

# ===========================================================================
#  Ant construction
# ---------------------------------------------------------------------------
#  One ant builds all K taxi routes simultaneously.  At every step it extends
#  the taxi with the SMALLEST current distance (this is the min-max heuristic
#  that balances the makespan), choosing the next physical node with the
#  Ant-System rule  p(j) ~ tau[i][j]^alpha * (1/d[i][j])^beta.
#
#  Constraints are enforced BY CONSTRUCTION:
#    - passenger pickup is always followed immediately by its drop-off
#      (direct-trip);
#    - a parcel pickup is only offered while it fits the remaining capacity;
#    - a parcel drop-off is only offered to the taxi currently carrying it
#      (so pickup precedes drop-off, same vehicle).
# ===========================================================================
def construct(inst, tau, alpha, beta):
    '''One ant constructs a full solution'''
    N, M, K, S, d, q, Q = inst.N, inst.M, inst.K, inst.S, inst.d, inst.q, inst.Q

    routes = [[0] for _ in range(K)]          # each taxi starts at the depot
    pos = [0] * K                             # current physical position
    dist = [0] * K                            # accumulated route length
    load = [0] * K                            # current on-board parcel load
    loaded = [set() for _ in range(K)]        # parcel indices currently on board
    done = [False] * K

    visited = bytearray(S)                          # visited[v] = 1 once served
    remaining_pass = set(range(1, N + 1))           
    remaining_parc = set(range(N + 1, N + M + 1))
    n_left = N + M
    
    def candidates(k):
        '''Return all feasible candidates for next position of taxi k'''
        cur_load = load[k]
        cands = list(remaining_pass)
        for node in remaining_parc:
            if q[node - N] <= Q[k] - cur_load:
                cands.append(node)
        for j in loaded[k]:
            cands.append(2 * N + M + j)
        return cands
    
    def choose(cur, cands):
        '''Choose the next move based on Transition Rule'''
        weights = []
        row = cur * S
        drow = d[cur]
        tot = 0.0
        for c in cands:
            eta = 1.0 / drow[c] if drow[c] > 0 else 1.0
            w = (tau[row + c] ** alpha) *  (eta ** beta)
            weights.append(w)
            tot += w
        r = random.random() * tot
        upto = 0.0
        for c, w in zip(cands, weights):
            upto += w
            if upto >= r:
                return c
        return cands[-1]
    
    # Keep extending until every pickup is dispatched and every parcel dropped
    while True:
        active = [k for k in range(K) if not done[k]]
        if not active:
            break
        k = min(active, key = lambda k: dist[k]) # min-max balancing
        cur = pos[k]
        cands = candidates(k)

        if not cands: # nothing left for this taxi
            dist[k] += d[cur][0]
            routes[k].append(0)
            done[k] = True
            continue
        
        nxt = choose(cur, cands)

        if inst.is_pass_pickup(nxt):                     # passenger pickup + dropoff
            drop = nxt + N + M
            dist[k] += d[cur][nxt] + d[nxt][drop]
            routes[k].extend((nxt, drop))
            visited[nxt] = visited[drop] = 1
            pos[k] = drop
            remaining_pass.discard(nxt)
            n_left -= 1
        elif inst.is_parcel_pickup(nxt):                # parcel pickup
            j = nxt - N
            dist[k] += d[cur][nxt]
            routes[k].append(nxt)
            visited[nxt] = 1
            load[k] += q[j]
            loaded[k].add(j)
            pos[k] = nxt
            remaining_parc.discard(nxt)
            n_left -= 1
        else:                                           # parcel dropoff
            j = nxt - (2 * N + M)
            dist[k] += d[cur][nxt]
            routes[k].append(nxt)
            visited[nxt] = 1
            load[k] -= q[j]
            loaded[k].discard(j)
            pos[k] = nxt

        # If all pickups dispatched, drive any taxi still carrying nothing home
        if n_left == 0 and not loaded[k]:
            dist[k] += d[pos[k]][0]
            routes[k].append(0)
            done[k] = True
        
    # Close any route that did not return to the depot
    for k in range(K):
        if routes[k][-1] != 0:
            dist[k] += d[pos[k]][0]
            routes[k].append(0)
    
    return routes, dist

# ===========================================================================
#  Ant Colony Optimization
# ===========================================================================

def aco(inst, deadline, n_ants = 20, alpha = 1.0, beta = 3.0, rho = 0.1):
    S = inst.S
    tau0 = 1.0
    tau = array('d', [tau0]) * (S * S)  # Initialize pheronmone matrix (flatened)

    best_routes = None
    best_make = float("inf")
    best_total = float("inf")

    while time.time() < deadline:
        iter_best_routes = None
        iter_best_make = float("inf")
        iter_best_total = float("inf")

        for _ in range(n_ants):
            if time.time() >= deadline:
                break
            routes, dist = construct(inst, tau, alpha, beta)
            make = max(dist)
            total = sum(dist)
            # lexicographic: makespan first, then total length
            if (make, total) < (iter_best_make, iter_best_total):
                iter_best_make, iter_best_total, iter_best_routes = make, total, routes
            if (make, total) < (best_make, best_total):
                best_make, best_total, best_routes = make, total, routes
            
        if iter_best_routes is None:
            break

        # evaporation
        keep = 1 - rho
        for i in range(S * S):
            tau[i] *= keep
        
        # deposit: global_best + iteration_best 
        for routes, make in ((best_routes, best_make), (iter_best_routes, iter_best_make)):
            dep = 1.0 / make if make > 0 else 1.0
            for k in range(inst.K):
                seq = routes[k]
                for a, b in zip(seq, seq[1:]):
                    tau[a * S + b] += dep

    return best_routes

def main():
    start = time.time()
    inst = read_input()
    routes = aco(inst, deadline = start + TIME_LIMIT_MS / 1000.0)
    write_output(inst, routes)

if __name__ == "__main__":
    main()

