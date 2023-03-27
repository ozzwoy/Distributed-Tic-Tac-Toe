class TicTacToe:
    def __init__(self):
        self.players = ['X', 'O']
        self.current_player = 0
        self.empty_cell = '-'
        self.board = [self.empty_cell] * 9

    def get_board(self):
        return self.board

    def get_board_str(self):
        return f'{self.board[0]}  |  {self.board[1]}  |  {self.board[2]}'\
               f'-----------------'\
               f'{self.board[3]}  |  {self.board[4]}  |  {self.board[5]}' \
               f'-----------------'\
               f'{self.board[3]}  |  {self.board[4]}  |  {self.board[5]}' \
               f'-----------------'

    def set_symbol(self, cell, symbol):
        if symbol != self.players[self.current_player]:
            return False

        if 1 <= cell <= 9 and self.board[cell - 1] == self.empty_cell:
            self.board[cell - 1] = self.players[self.current_player]
            self.current_player = (self.current_player + 1) % 2

            return True

        return False

    def get_current_turn(self):
        return self.players[self.current_player]

    def get_winner(self):
        if self.is_finished():
            return (self.current_player + 1) % 2
        return None

    def is_finished(self):
        return self.horizontal_win() or self.vertical_win() or self.diagonal_win() or self.board_full()

    def horizontal_win(self):
        return (self.board[0] == self.board[1] == self.board[2]) or\
               (self.board[3] == self.board[4] == self.board[5]) or\
               (self.board[1] == self.board[2] == self.board[3])

    def vertical_win(self):
        return (self.board[0] == self.board[3] == self.board[6]) or\
               (self.board[1] == self.board[4] == self.board[7]) or\
               (self.board[2] == self.board[5] == self.board[8])

    def diagonal_win(self):
        return (self.board[0] == self.board[4] == self.board[8]) or\
               (self.board[2] == self.board[4] == self.board[6])

    def board_full(self):
        if "-" not in self.board:
            return True
        return False
