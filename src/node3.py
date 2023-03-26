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

    def StartElection(self, request, context):
        nodes = list(request.nodes)
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

    def ReportLeader(self, request, context):
        nodes = list(request.nodes)
        print(f"Received leader message from Node {nodes[-1]}.")
        print(f"Elections finished! New leader: Node {request.leader}.")
        print(f"Current list of visited nodes: {nodes}.")

        next_node = self.id % self.num_nodes + 1

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


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    tictactoe_pb2_grpc.add_TicTacToeServicer_to_server(Node(3, config.NUM_NODES, config.IDS_TO_IPS), server)
    server.add_insecure_port('[::]:20050')
    server.start()
    print("Server started listening on DESIGNATED port")

    try:
        while True:
            time.sleep(86400)
    except KeyboardInterrupt:
        server.stop(0)


if __name__ == '__main__':
    serve()
