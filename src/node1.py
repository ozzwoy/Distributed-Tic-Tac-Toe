import inspect

import config
import datetime
import grpc
import time
import tictactoe_pb2
import tictactoe_pb2_grpc

from concurrent import futures
from model.model import TicTacToe
from threading import Thread


class Node(tictactoe_pb2_grpc.TicTacToeServicer):
    def __init__(self, id_, num_nodes, ids_to_ips):
        self.id = id_
        self.num_nodes = num_nodes
        self.ids_to_ips = ids_to_ips
        self.leader = None
        self.synchronized = False
        self.timedelta = datetime.timedelta()

        self.game = None
        self.game_started = False
        self.game_finished = False
        self.winner = None

    def StartElection(self, request, context):
        nodes = list(request.nodes)

        if len(nodes) == 0:
            print("\nInitiating elections.")
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

        self.leader = request.leader

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
        current_time = self.get_time().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3] + "Z"
        return tictactoe_pb2.TimeResponse(timestamp=current_time)

    def SynchTime(self, request, context):
        new_time = datetime.datetime.strptime(request.timestamp, "%Y-%m-%d %H:%M:%S.%fZ")
        real_time = self.get_time()
        self.timedelta = new_time - real_time
        self.synchronized = True

        return tictactoe_pb2.TimeSynchResponse()

    def SetSymbol(self, request, context):
        if self.game.set_symbol(request.cell, request.symbol):
            return tictactoe_pb2.SetSymbolResponse(successful=True, message='')
        else:
            message = ''

            if self.game.current_turn() != request.symbol:
                message = 'Not your turn!'
            elif self.game.is_finished():
                message = 'Game is finished!'
            elif self.game.get_cell(request.cell) != self.game.empty_cell:
                message = 'The cell is already occupied!'

            return tictactoe_pb2.SetSymbolResponse(successful=False, message=message)

    def ListBoard(self, request, context):
        return tictactoe_pb2.ListBoardResponse(timestamp = (datetime.datetime.utcnow() +
                                                            self.timedelta).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
                                               board=self.game.get_board_str())

    def SetNodeTime(self, request, context):
        real_time = self.get_time()
        new_time = datetime.datetime(year=real_time.year, month=real_time.month, day=real_time.day,
                                     hour=request.hh, minute=request.mm, second=request.ss)
        self.timedelta = new_time - real_time

        return tictactoe_pb2.SetNodeTimeResponse()

    def ReportWinner(self, request, context):
        self.game_started = False
        self.game_finished = True
        self.winner = request.winner
        self.leader = None

        return tictactoe_pb2.WinnerMessageResponse()

    def conduct_elections(self):
        with grpc.insecure_channel(config.IDS_TO_IPS[self.id]) as channel:
            stub = tictactoe_pb2_grpc.TicTacToeStub(channel)
            try:
                stub.StartElection(tictactoe_pb2.ElectionMessage(nodes=[]))
            except grpc.RpcError:
                pass

    def get_time(self):
        return datetime.datetime.utcnow() + self.timedelta

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


        reference_time = datetime.timedelta()
        # average_time = reference_time + sum([_time - reference_time for _time in node_times.values()],
        #                                     datetime.timedelta()) / config.NUM_NODES
        average_time = self.get_time().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3] + "Z"

        for node in config.IDS_TO_IPS.values():
            with grpc.insecure_channel(node) as channel:
                stub = tictactoe_pb2_grpc.TicTacToeStub(channel)
                stub.SynchTime(tictactoe_pb2.TimeSynchRequest(timestamp=average_time))

        print(f"Synchronization finished. Synchronized time: {datetime.datetime.utcnow() + self.timedelta}.")

    def init_game(self):
        self.game = TicTacToe()


def player_mode(node, stub):
    while not node.game_finished:
        command = input(f'Node-{node.id}> ')
        command = command.split(' ')

        if command[0] == 'List-board':
            response = stub.ListBoard(tictactoe_pb2.ListBoardRequest())
            print(f'Timestamp: {response.timestamp}\n{response.board}\n')
        elif command[0] == 'Set-symbol':
            cell = int(command[1][0])
            symbol = command[2]

            response = stub.SetSymbol(tictactoe_pb2.SetSymbolRequest(cell=cell, symbol=symbol))
            if not response.successful:
                print(response.message)
        elif command[0] == 'Set-node-time':
            node_id = int(command[1].split('-')[1])

            if node_id != node.id:
                print('Only master is allowed to set time of other nodes.')
                continue

            time_str = command[2][1:-1]
            time_str = time_str.split(':')
            hh, mm, ss = int(time_str[0]), int(time_str[1]), int(time_str[2])

            real_time = node.get_time()
            new_time = datetime.datetime(year=real_time.year, month=real_time.month, day=real_time.day,
                                         hour=hh, minute=mm, second=ss)
            node.timedelta = new_time - real_time

            print(f'Time set successfully. Current time: {node.get_time()}.')
        elif command[0] == 'Show-time':
            print(node.get_time())
        else:
            print('Wrong command! Please try again.')

    print(f'Game over! The winner is {node.winner}.\n')
    node.game_finished = False


def game_daemon(node):
    while not node.game.is_finished():
        time.sleep(0.001)

    for player in config.IDS_TO_IPS.values():
        with grpc.insecure_channel(player) as channel:
            stub = tictactoe_pb2_grpc.TicTacToeStub(channel)
            stub.ReportWinner(tictactoe_pb2.WinnerMessage(winner=node.game.get_winner()))


def master_mode(node):
    # monitor winner
    daemon = Thread(target=game_daemon, args=[node])
    daemon.start()

    while not node.game.is_finished():
        command = input(f'Node-{node.id}> ')
        command = command.split(' ')

        if command[0] == 'Set-node-time':
            node_id = int(command[1].split('-')[1])
            time_str = command[2][1:-1]
            time_str = time_str.split(':')
            hh, mm, ss = int(time_str[0]), int(time_str[1]), int(time_str[2])

            with grpc.insecure_channel(config.IDS_TO_IPS[node_id]) as channel:
                stub = tictactoe_pb2_grpc.TicTacToeStub(channel)
                stub.SetNodeTime(tictactoe_pb2.SetNodeTimeRequest(hh=hh, mm=mm, ss=ss))

            print('Time set successfully.')
        elif command[0] == 'Show-time':
            print(node.get_time())
        else:
            print('Wrong command! Please try again.')

    print(f'Game over! The winner is {node.winner}.\n')
    node.game = None


def serve():
    node_id = 1

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    node = Node(node_id, config.NUM_NODES, config.IDS_TO_IPS)
    tictactoe_pb2_grpc.add_TicTacToeServicer_to_server(node, server)
    server.add_insecure_port(config.IDS_TO_IPS[node_id])
    server.start()
    print("Server started listening on DESIGNATED port\n")

    while True:
        print('To start the game write "Start-game".')

        command = input(f'Node-{node.id}> ')

        if command != 'Start-game':
            print('Wrong command! Please try again.')
        else:
            node.conduct_elections()

            while node.leader is None:
                time.sleep(0.001)

            if node.leader == node_id:
                print("\nI am the Master of the game!")
                node.synchronize_time()
            else:
                print("\nI am the Player!")
                print("Waiting for synchronization...")

            while not node.synchronized:
                time.sleep(0.001)

            print("Ready to play!\n")

            if node.leader == node_id:
                node.init_game()
                master_mode(node)
            else:
                with grpc.insecure_channel(config.IDS_TO_IPS[node.leader]) as channel:
                    stub = tictactoe_pb2_grpc.TicTacToeStub(channel)
                    player_mode(node, stub)


if __name__ == '__main__':
    serve()
