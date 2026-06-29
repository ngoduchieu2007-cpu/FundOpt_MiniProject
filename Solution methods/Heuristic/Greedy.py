def greedy_algorithm(N, M, K, q, Q, d):
    def distance_based_greedy_algorithm(N, M, K, q, Q, d):
        routes = [[0] for _ in range(K)]
        current_position = [0] * K
        current_distance = [0] * K
        current_load = [0] * K
        carrying_parcels = [[0] * (M) for _ in range(K)]
        assignments = [1] + [0] * (2 * N + 2 * M)
        has_passengers = [0] * K
        done = [0] * K

        # Distance-Based
        while 0 in set(assignments):
            # chọn xe đang có distance là thấp nhất
            active_taxis = [k for k in range(K) if done[k] == 0]
            if not active_taxis:
                ## list xe còn nvu đã trống
                break
            taxi_to_assign = min(active_taxis, key=lambda k: current_distance[k])
            taxi_position = current_position[taxi_to_assign]

            # tính cost các cách để đi: đi đón khách - trả khách / đi lấy hàng / đi trả hàng sẵn trên xe

            ## cách 0.5: trả khách nếu xe đang có khách
            if has_passengers[taxi_to_assign]:
                drop_passenger_cost = d[taxi_position][taxi_position + N + M]
                routes[taxi_to_assign].append(taxi_position + N + M)
                current_distance[taxi_to_assign] += drop_passenger_cost
                current_position[taxi_to_assign] = taxi_position + N + M
                assignments[taxi_position + N + M] = 1
                has_passengers[taxi_to_assign] = 0
                continue

            ## cách 1: đón khách
            pick_up_passenger_cost = 1e10
            passenger_location = None
            for i in range(1, N + 1):
                if assignments[i] != 0:
                    continue
                if d[taxi_position][i] < pick_up_passenger_cost:
                    pick_up_passenger_cost = d[taxi_position][i]
                    passenger_location = i

            ## cách 2: lấy hàng
            pick_up_parcel_cost = 1e10
            pick_up_parcel_location = None
            for i in range(1 + N, 1 + N + M):
                if assignments[i] != 0:
                    continue
                if (
                    d[taxi_position][i] < pick_up_parcel_cost
                    and current_load[taxi_to_assign] + q[i - 1 - N] <= Q[taxi_to_assign]
                ):
                    pick_up_parcel_cost = d[taxi_position][i]
                    pick_up_parcel_location = i

            ## cách 3: trả hàng
            drop_parcel_cost = 1e10
            drop_parcel_location = None
            for i in range(1 + 2 * N + M, 1 + 2 * N + 2 * M):
                if carrying_parcels[taxi_to_assign][i - 2 * N - M - 1] == 0:
                    continue
                if d[taxi_position][i] < drop_parcel_cost:
                    drop_parcel_cost = d[taxi_position][i]
                    drop_parcel_location = i

            # thực hiện nước đi
            ## so sánh chi phí của các cách đi
            ways = [pick_up_passenger_cost, pick_up_parcel_cost, drop_parcel_cost]
            greedy_cost = min(ways)
            ## trong case kẹt xe: tất cả nvu đã xong, chỉ còn nvu trả hàng/khách của 1 số xe có distance cao
            ## -> kẹt xe có distance min vì nhiệm vụ chỉ còn ở xe khác -> cho xe về bến 0 -> done route
            if greedy_cost == 1e10:
                current_distance[taxi_to_assign] += d[taxi_position][0]
                routes[taxi_to_assign].append(0)
                current_position[taxi_to_assign] = 0
                done[taxi_to_assign] = 1
                continue

            index = ways.index(greedy_cost)

            if index == 0:
                routes[taxi_to_assign].append(passenger_location)
                current_position[taxi_to_assign] = passenger_location
                current_distance[taxi_to_assign] += pick_up_passenger_cost
                assignments[passenger_location] = 1
                has_passengers[taxi_to_assign] = 1
            if index == 1:
                routes[taxi_to_assign].append(pick_up_parcel_location)
                current_position[taxi_to_assign] = pick_up_parcel_location
                current_distance[taxi_to_assign] += pick_up_parcel_cost
                current_load[taxi_to_assign] += q[pick_up_parcel_location - N - 1]
                carrying_parcels[taxi_to_assign][pick_up_parcel_location - N - 1] = 1
                assignments[pick_up_parcel_location] = 1
            if index == 2:
                routes[taxi_to_assign].append(drop_parcel_location)
                current_position[taxi_to_assign] = drop_parcel_location
                current_distance[taxi_to_assign] += drop_parcel_cost
                current_load[taxi_to_assign] -= q[drop_parcel_location - 2 * N - M - 1]
                carrying_parcels[taxi_to_assign][
                    drop_parcel_location - 2 * N - M - 1
                ] = 0
                assignments[drop_parcel_location] = 1

        # Kết thúc vòng lặp - tất cả nhiệm vụ đã xong
        ## 1 số xe chỉ mới hoàn thành nhiệm vụ cuối cùng mà chưa về bến -> cho tất cả xe về 0
        for k in range(K):
            if routes[k][-1] != 0:
                routes[k].append(0)
                current_distance[k] += d[current_position[k]][0]

        result = routes
        max_distance = max(current_distance)
        return result, max_distance

    def score_based_greedy(N, M, K, q, Q, d):

        routes = [[0] for _ in range(K)]
        current_position = [0] * K
        current_distance = [0] * K
        current_load = [0] * K
        carrying_parcels = [[0] * (M) for _ in range(K)]
        assignments = [1] + [0] * (2 * N + 2 * M)
        has_passengers = [0] * K
        done = [0] * K

        avg_dist = 0
        count = 0

        def calculate_avg_dist(new_dist):
            nonlocal avg_dist, count
            count += 1
            avg_dist = (avg_dist * (count - 1) + new_dist) / count

        while 0 in set(assignments):
            # chọn xe đang có distance là thấp nhất
            active_taxis = [k for k in range(K) if done[k] == 0]
            if not active_taxis:
                ## list xe còn nvu đã trống
                break
            taxi_to_assign = min(active_taxis, key=lambda k: current_distance[k])
            taxi_position = current_position[taxi_to_assign]

            # tính cost các cách để đi: đi đón khách - trả khách / đi lấy hàng / đi trả hàng sẵn trên xe

            ## cách 0.5: trả khách nếu xe đang có khách
            if has_passengers[taxi_to_assign]:
                drop_passenger_cost = d[taxi_position][taxi_position + N + M]
                calculate_avg_dist(drop_passenger_cost)
                routes[taxi_to_assign].append(taxi_position + N + M)
                current_distance[taxi_to_assign] += drop_passenger_cost
                current_position[taxi_to_assign] = taxi_position + N + M
                assignments[taxi_position + N + M] = 1
                has_passengers[taxi_to_assign] = 0
                continue

            ## cách 1: đón khách
            pick_up_passenger_cost = 1e10
            passenger_location = None
            for i in range(1, N + 1):
                calculate_avg_dist(d[taxi_position][i])
                if assignments[i] != 0:
                    continue
                if d[taxi_position][i] < pick_up_passenger_cost:
                    pick_up_passenger_cost = d[taxi_position][i]
                    passenger_location = i

            ## cách 2: lấy hàng
            penalty = 0.5 * avg_dist
            pick_up_parcel_cost = 1e10
            pick_up_parcel_location = None
            for i in range(1 + N, 1 + N + M):
                calculate_avg_dist(d[taxi_position][i])
                if assignments[i] != 0:
                    continue
                if (
                    current_load[taxi_to_assign] + q[i - 1 - N] <= Q[taxi_to_assign]
                    and d[taxi_position][i]
                    + penalty
                    * (
                        (current_load[taxi_to_assign] + q[i - 1 - N])
                        / Q[taxi_to_assign]
                    )
                    ** 2
                    < pick_up_parcel_cost
                ):
                    pick_up_parcel_cost = (
                        d[taxi_position][i]
                        + penalty
                        * (
                            (current_load[taxi_to_assign] + q[i - 1 - N])
                            / Q[taxi_to_assign]
                        )
                        ** 2
                    )
                    pick_up_parcel_location = i

            ## cách 3: trả hàng
            drop_parcel_cost = 1e10
            drop_parcel_location = None
            for i in range(1 + 2 * N + M, 1 + 2 * N + 2 * M):
                calculate_avg_dist(d[taxi_position][i])
                if carrying_parcels[taxi_to_assign][i - 2 * N - M - 1] == 0:
                    continue
                if (
                    d[taxi_position][i]
                    - penalty * ((current_load[taxi_to_assign]) / Q[taxi_to_assign])
                    < drop_parcel_cost
                ):
                    drop_parcel_cost = d[taxi_position][i] - penalty * (
                        (current_load[taxi_to_assign]) / Q[taxi_to_assign]
                    )
                    drop_parcel_location = i

            # thực hiện nước đi
            ## so sánh chi phí của các cách đi
            ways = [pick_up_passenger_cost, pick_up_parcel_cost, drop_parcel_cost]
            greedy_cost = min(ways)
            ## trong case kẹt xe: tất cả nvu đã xong, chỉ còn nvu trả hàng/khách của 1 số xe có distance cao
            ## -> kẹt xe có distance min vì nhiệm vụ chỉ còn ở xe khác -> cho xe về bến 0 -> done route
            if greedy_cost == 1e10:
                current_distance[taxi_to_assign] += d[taxi_position][0]
                routes[taxi_to_assign].append(0)
                current_position[taxi_to_assign] = 0
                done[taxi_to_assign] = 1
                continue

            index = ways.index(greedy_cost)

            if index == 0:
                routes[taxi_to_assign].append(passenger_location)
                current_position[taxi_to_assign] = passenger_location
                current_distance[taxi_to_assign] += pick_up_passenger_cost
                assignments[passenger_location] = 1
                has_passengers[taxi_to_assign] = 1

            if index == 1:
                routes[taxi_to_assign].append(pick_up_parcel_location)
                current_position[taxi_to_assign] = pick_up_parcel_location
                current_distance[taxi_to_assign] += (
                    pick_up_parcel_cost
                    - penalty
                    * (
                        (
                            current_load[taxi_to_assign]
                            + q[pick_up_parcel_location - 1 - N]
                        )
                        / Q[taxi_to_assign]
                    )
                    ** 2
                )
                current_load[taxi_to_assign] += q[pick_up_parcel_location - N - 1]
                carrying_parcels[taxi_to_assign][pick_up_parcel_location - N - 1] = 1
                assignments[pick_up_parcel_location] = 1

            if index == 2:
                routes[taxi_to_assign].append(drop_parcel_location)
                current_position[taxi_to_assign] = drop_parcel_location
                current_distance[taxi_to_assign] += drop_parcel_cost + penalty * (
                    (current_load[taxi_to_assign]) / Q[taxi_to_assign]
                )
                current_load[taxi_to_assign] -= q[drop_parcel_location - 2 * N - M - 1]
                carrying_parcels[taxi_to_assign][
                    drop_parcel_location - 2 * N - M - 1
                ] = 0
                assignments[drop_parcel_location] = 1

        # Kết thúc vòng lặp - tất cả nhiệm vụ đã xong
        for k in range(K):
            if routes[k][-1] != 0:
                routes[k].append(0)
                current_distance[k] += d[current_position[k]][0]
        result = routes
        max_distance = max(current_distance)
        return result, max_distance

    res1, max_dist1 = distance_based_greedy_algorithm(N, M, K, q, Q, d)
    res2, max_dist2 = score_based_greedy(N, M, K, q, Q, d)
    res = res1 if max_dist1 <= max_dist2 else res2
    return res


def main():
    N, M, K = map(int, input().split())
    q = list(map(int, input().split()))
    Q = list(map(int, input().split()))
    d = [list(map(int, input().split())) for _ in range(2 * N + 2 * M + 1)]
    result = greedy_algorithm(N, M, K, q, Q, d)
    print(K)
    for k in range(K):
        print(len(result[k]))
        print(" ".join(map(str, result[k])))


if __name__ == "__main__":
    main()
