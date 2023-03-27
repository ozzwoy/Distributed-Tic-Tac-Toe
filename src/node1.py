import config
import datetime
import grpc
import time
import tictactoe_pb2
import tictactoe_pb2_grpc

from concurrent import futures


class Node(tictactoe_pb2_grpc.TicTacToeServicer):
    def __init__(self, id_, num_nodes, ids_to_ips):
        self.id = id_
        self.num_nodes = num_nodes
        self.ids_to_ips = ids_to_ips
        self.leader = None
        self.synchronized = False
        self.timedelta = datetime.timedelta()

    def StartElection(self, request, context):
        nodes = list(request.nodes)

        if len(nodes) == 0:
            print("Initiating elections.")
        else:
            print(f"Received election message from Node {nodes[-1]}.")
            print(f"Current list of visited nodes: {nodes}.")

        next_node = self.id % self.num_nodes + 1

        if self.id in request.nodes:
            leader = max(request.nodes)
            print(f"Elections finished! New leader: Node {leader}.")

            with grpc.insecure_channel(self.ids_to_ips[next_node]) as channel:
                stub = tictactoe_pb2_grpc.TicTacToeStub(channel)
                stub.ReportLeader(tictactoe_pb2.LeaderMessage(leader=leader, nodes=[self.id]))
        else:
            print(f"Forwarding election message to Node {next_node}.")

            with grpc.insecure_channel(self.ids_to_ips[next_node]) as channel:
                stub = tictactoe_pb2_grpc.TicTacToeStub(channel)
                stub.StartElection(tictactoe_pb2.ElectionMessage(nodes=nodes + [self.id]))

        return tictactoe_pb2.ElectionResponse()

    def ReportLeader(self, request, context):
        nodes = list(request.nodes)
        print(f"Received leader message from Node {nodes[-1]}. New leader: Node {request.leader}.")
        print(f"Current list of visited nodes: {nodes}.")

        next_node = self.id % self.num_nodes + 1

        self.leader = True if self.id == request.leader else False

        if self.id in request.nodes:
            if request.leader in nodes:
                print(f"All nodes are notified of the new leader. The leader is active.")
            else:
                print("Re-initiating elections. The leader is down.")
                print(f"Forwarding election message to Node {next_node}.")

                with grpc.insecure_channel(self.ids_to_ips[next_node]) as channel:
                    stub = tictactoe_pb2_grpc.TicTacToeStub(channel)
                    stub.StartElection(tictactoe_pb2.ElectionMessage(nodes=[self.id]))
        else:
            print(f"Forwarding leader message to Node {next_node}.")

            with grpc.insecure_channel(self.ids_to_ips[next_node]) as channel:
                stub = tictactoe_pb2_grpc.TicTacToeStub(channel)
                stub.ReportLeader(tictactoe_pb2.LeaderMessage(leader=request.leader, nodes=nodes + [self.id]))

        return tictactoe_pb2.LeaderResponse()

    def GetTime(self, request, context):
        current_time = (datetime.datetime.utcnow() + self.timedelta).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3] + "Z"
        return tictactoe_pb2.TimeResponse(timestamp=current_time)

    def SynchTime(self, request, context):
        new_time = datetime.datetime.strptime(request.timestamp, "%Y-%m-%d %H:%M:%S.%fZ")
        real_time = datetime.datetime.utcnow() + self.timedelta
        self.timedelta = new_time - real_time
        self.synchronized = True

        return tictactoe_pb2.TimeSynchResponse()

    def conduct_elections(self):
        with grpc.insecure_channel(config.IDS_TO_IPS[self.id]) as channel:
            stub = tictactoe_pb2_grpc.TicTacToeStub(channel)
            try:
                stub.StartElection(tictactoe_pb2.ElectionMessage(nodes=[]))
            except grpc.RpcError:
                pass

    @staticmethod
    def christians_algorithm(start_time, end_time, server_time, real_time):
        estimated_time = server_time + datetime.timedelta(seconds=(end_time - start_time) / 2)
        time_diff = estimated_time - real_time

        return estimated_time, real_time, time_diff

    # Berkeley algorithm
    def synchronize_time(self):
        print("Synchronizing time...")

        node_times = {}

        for node in config.IDS_TO_IPS.values():
            with grpc.insecure_channel(node) as channel:
                stub = tictactoe_pb2_grpc.TicTacToeStub(channel)
                leader_time = datetime.datetime.utcnow()
                start = time.time()
                response = stub.GetTime(tictactoe_pb2.TimeRequest())
                end = time.time()
                node_time = datetime.datetime.strptime(response.timestamp, "%Y-%m-%d %H:%M:%S.%fZ")

                node_times[node] = Node.christians_algorithm(start, end, node_time, leader_time)[0]


        # reference_time = datetime.timedelta()
        # average_time = reference_time + sum([_time - reference_time for _time in node_times.values()],
        #                                     datetime.timedelta()) / config.NUM_NODES

        average_time = (datetime.datetime.utcnow() + self.timedelta).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3] + "Z"

        for node in config.IDS_TO_IPS.values():
            with grpc.insecure_channel(node) as channel:
                stub = tictactoe_pb2_grpc.TicTacToeStub(channel)
                stub.SynchTime(tictactoe_pb2.TimeSynchRequest(timestamp=average_time))

        print(f"Synchronization finished. Synchronized time: {datetime.datetime.utcnow() + self.timedelta}.")


def serve():
    node_id = 1

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    node = Node(node_id, config.NUM_NODES, config.IDS_TO_IPS)
    tictactoe_pb2_grpc.add_TicTacToeServicer_to_server(node, server)
    server.add_insecure_port(config.IDS_TO_IPS[node_id])
    server.start()
    print("Server started listening on DESIGNATED port\n")

    node.conduct_elections()

    while node.leader is None:
        time.sleep(0.001)

    if node.leader:
        print("\nI am the Master of the game!")
        node.synchronize_time()
    else:
        print("\nI am the Player!")
        print("Waiting for synchronization...")

    while not node.synchronized:
        time.sleep(0.001)

    print("Ready to play!\n")

    while True:
        command = input(f'Node-{node_id}> ')
        command = command.split(' ')

        if command[0] == 'List-board':
            pass
        elif command[0] == 'Set-symbol':
            cell = int(command[1][0])
            symbol = command[2]

            pass
        elif command[0] == 'Set-node-time':
            time_str = command[1][1:-1]
            time_str = time_str.split(':')
            hh, mm, ss = time_str[0], time_str[1], time_str[2]

            pass
        else:
            print('Wrong command! Please try again.')

    server.wait_for_termination()


if __name__ == '__main__':
    serve()
