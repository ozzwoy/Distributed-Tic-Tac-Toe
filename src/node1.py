import datetime
import grpc
import time
import tictactoe_pb2
import tictactoe_pb2_grpc

from concurrent import futures


class Node(tictactoe_pb2_grpc.TicTacToeServicer):
    def __init__(self, id_, ids_to_ips):
        self.id = id_
        self.num_nodes = 3
        self.ids_to_ips = ids_to_ips

    def StartElection(self, request, context):
        print(f"Received election message from Node {[-1]}.")
        nodes = list(request.nodes)
        print(f"Current list of visited nodes: {nodes}.")

        next_node = (self.id + 1) % self.num_nodes + (self.id + 1) // self.num_nodes

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

    def ReportLeader(self, request, context):
        print(f"Elections finished! New leader: Node {request.leader}.")
        nodes = list(request.nodes)
        print(f"Current list of visited nodes: {nodes}.")

        next_node = (self.id + 1) % self.num_nodes + (self.id + 1) // self.num_nodes

        if self.id in request.nodes:
            if request.leader in nodes:
                print(f"All nodes notified of the new leader. The leader is active.")
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


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    ids_to_ips = {1: 'localhost:20048',
                  2: 'localhost:20049',
                  3: 'localhost:20050'}

    tictactoe_pb2_grpc.add_TicTacToeServicer_to_server(Node(1, ids_to_ips), server)
    server.add_insecure_port('[::]:20048')
    server.start()
    print("Server started listening on DESIGNATED port")
    try:
        while True:
            time.sleep(86400)
    except KeyboardInterrupt:
        server.stop(0)
