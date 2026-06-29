# Initialize solution by greedy heuristic, then optimize by local search - first-improvement (insert/relocate)
# Lấy initial solution của greedy algorithm
# Input
def local_search_algorithm(N, M, K, q, Q, d):
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

        return routes, current_distance

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

        return routes, current_distance

    res1, dist1 = distance_based_greedy_algorithm(N, M, K, q, Q, d)
    res2, dist2 = score_based_greedy(N, M, K, q, Q, d)
    routes, current_distance = (
        (res1, dist1) if max(dist1) <= max(dist2) else (res2, dist2)
    )

    # Đã tìm ra initial solution - candidate theo thuật toán greedy

    ## Bắt đầu thuật toán local search: insert thứ tự đi của 1 xe / relocate việc giữa 2 xe

    ### hàm kiểm tra tính hợp lệ của neighbour solution
    def check_valid_and_cost(k, test_route):
        load = 0
        cost = 0
        visited = [0] * (2 * N + 2 * M + 1)
        for visit_order, location in enumerate(test_route):
            #### luật 1: đón khách xong phải trả khách luôn
            if visit_order == 0:
                continue
            if location in range(1, N + 1):
                if test_route[visit_order + 1] != location + N + M:
                    return False, None
            #### luật 2: load trên xe không vượt quá Q[k]
            #### luật 3: phải đến điểm lấy hàng trước khi trả hàng
            if location in range(1 + N, N + M + 1):
                visited[location] = 1
                load += q[location - 1 - N]
                if load > Q[k]:
                    return False, None
                if test_route.index(location + M + N) < visit_order:
                    return False, None
            if location in range(2 * N + M + 1, 2 * N + 2 * M + 1):
                if visited[location - N - M] == 0:
                    return False, None
                load -= q[location - 2 * N - M - 1]
                if test_route.index(location - N - M) > visit_order:
                    return False, None
            cost += d[test_route[visit_order - 1]][location]
        return True, cost

    improve_by_insert = True
    improve_by_relocate = True
    while improve_by_insert or improve_by_relocate:
        improve_by_insert = False
        improve_by_relocate = False
        ## cách 1: insert - rút 1 điểm chèn vào thứ tự khác
        for k in range(K):
            route = routes[k]
            _, current_cost = check_valid_and_cost(k, route)
            for visit_order, location in enumerate(route):
                if location == 0:
                    continue
                if location in range(1, N + 1):
                    test_route = route.copy()
                    test_route.remove(location)
                    test_route.remove(location + N + M)
                    for insert_index in range(1, len(test_route) - 1):
                        test_route.insert(insert_index, location)
                        test_route.insert(insert_index + 1, location + N + M)
                        test_valid, test_cost = check_valid_and_cost(k, test_route)
                        if test_valid and test_cost < current_cost:
                            routes[k] = test_route
                            current_distance[k] = test_cost
                            improve_by_insert = True
                            break
                    if improve_by_insert:
                        break
                elif location in range(N + 1, N + M + 1):
                    test_route = route.copy()
                    test_route.remove(location)
                    for insert_index in range(
                        1, test_route.index(location + M + N) + 1
                    ):
                        test_route.insert(insert_index, location)
                        test_valid, test_cost = check_valid_and_cost(k, test_route)
                        if test_valid and test_cost < current_cost:
                            routes[k] = test_route
                            current_distance[k] = test_cost
                            improve_by_insert = True
                            break
                    if improve_by_insert:
                        break
                elif location in range(2 * N + M + 1, 2 * N + 2 * M + 1):
                    test_route = route.copy()
                    test_route.remove(location)
                    for insert_index in range(
                        test_route.index(location - N - M) + 1, len(test_route)
                    ):
                        test_route.insert(insert_index, location)
                        test_valid, test_cost = check_valid_and_cost(k, test_route)
                        if test_valid and test_cost < current_cost:
                            routes[k] = test_route
                            current_distance[k] = test_cost
                            improve_by_insert = True
                            break
                    if improve_by_insert:
                        break

        ## cách 2: relocate nhiệm vụ giữa xe đang có distance cao nhất giao cho xe thấp nhất
        current_max_distance = max(current_distance)
        taxi_with_highest_distance = current_distance.index(current_max_distance)
        taxi_with_lowest_distance = current_distance.index(min(current_distance))
        route_1 = routes[taxi_with_highest_distance]
        route_2 = routes[taxi_with_lowest_distance]

        for visit_order_1, location_1 in enumerate(route_1):
            ### giao việc đón trả khách
            if location_1 in range(1, N + 1):
                for insert_index in range(1, len(route_2)):
                    test_route_1 = route_1.copy()
                    test_route_2 = route_2.copy()
                    test_route_2.insert(insert_index, location_1)
                    test_route_2.insert(insert_index + 1, location_1 + N + M)
                    test_route_1.remove(location_1)
                    test_route_1.remove(location_1 + N + M)
                    route_1_is_valid, route_1_cost = check_valid_and_cost(
                        taxi_with_highest_distance, test_route_1
                    )
                    route_2_is_valid, route_2_cost = check_valid_and_cost(
                        taxi_with_lowest_distance, test_route_2
                    )
                    if (
                        route_1_is_valid
                        and route_2_is_valid
                        and max(route_1_cost, route_2_cost) < current_max_distance
                    ):
                        improve_by_relocate = True
                        routes[taxi_with_highest_distance] = test_route_1
                        current_distance[taxi_with_highest_distance] = route_1_cost
                        routes[taxi_with_lowest_distance] = test_route_2
                        current_distance[taxi_with_lowest_distance] = route_2_cost
                        break
                if improve_by_relocate:
                    break

            ### giao việc nhận và trả hàng
            elif location_1 in range(1 + N, 1 + N + M):
                for insert_index_pick in range(1, len(route_2)):
                    if route_2[insert_index_pick - 1] in range(1, N + 1):
                        continue
                    for insert_index_drop in range(
                        insert_index_pick + 1, len(route_2) + 1
                    ):
                        if route_2[insert_index_drop - 1] in range(1, N + 1):
                            continue
                        test_route_1 = route_1.copy()
                        test_route_2 = route_2.copy()
                        test_route_2.insert(insert_index_pick, location_1)
                        test_route_2.insert(insert_index_drop, location_1 + M + N)
                        test_route_1.remove(location_1)
                        test_route_1.remove(location_1 + N + M)
                        route_1_is_valid, route_1_cost = check_valid_and_cost(
                            taxi_with_highest_distance, test_route_1
                        )
                        route_2_is_valid, route_2_cost = check_valid_and_cost(
                            taxi_with_lowest_distance, test_route_2
                        )
                        if (
                            route_1_is_valid
                            and route_2_is_valid
                            and max(route_1_cost, route_2_cost) < current_max_distance
                        ):
                            improve_by_relocate = True
                            routes[taxi_with_highest_distance] = test_route_1
                            routes[taxi_with_lowest_distance] = test_route_2
                            current_distance[taxi_with_highest_distance] = route_1_cost
                            current_distance[taxi_with_lowest_distance] = route_2_cost
                            break
                    if improve_by_relocate:
                        break
                if improve_by_relocate:
                    break

    return routes


def main():
    N, M, K = map(int, input().split())
    q = list(map(int, input().split()))
    Q = list(map(int, input().split()))
    d = [list(map(int, input().split())) for _ in range(2 * N + 2 * M + 1)]
    result = local_search_algorithm(N, M, K, q, Q, d)
    print(K)
    for k in range(K):
        print(len(result[k]))
        print(" ".join(map(str, result[k])))


if __name__ == "__main__":
    main()
