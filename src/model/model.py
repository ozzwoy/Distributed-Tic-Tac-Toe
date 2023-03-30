class TicTacToe:
    def __init__(self):
        self.players = ['X', 'O']
        self.current_player = 0
        self.empty_cell = '-'
        self.board = [self.empty_cell] * 9

    def get_cell(self, i):
        return self.board[i - 1]

    def get_board(self):
        return self.board

    def get_board_str(self):
        return f'{self.board[0]}  |  {self.board[1]}  |  {self.board[2]}\n'\
               f'-----------------\n'\
               f'{self.board[3]}  |  {self.board[4]}  |  {self.board[5]}\n' \
               f'-----------------\n'\
               f'{self.board[6]}  |  {self.board[7]}  |  {self.board[8]}\n' \
               f'-----------------'

    def set_symbol(self, cell, symbol):
        if symbol != self.players[self.current_player]:
            return False

        if 1 <= cell <= 9 and self.board[cell - 1] == self.empty_cell:
            self.board[cell - 1] = self.players[self.current_player]
            self.current_player = (self.current_player + 1) % 2

            return True

        return False

    def current_turn(self):
        return self.players[self.current_player]

    def get_winner(self):
        if self.is_finished():
            return self.players[(self.current_player + 1) % 2]
        return None

    def is_finished(self):
        return self.horizontal_win() or self.vertical_win() or self.diagonal_win() or self.board_full()

    def horizontal_win(self):
        return (self.board[0] == self.board[1] == self.board[2] and self.board[0] != self.empty_cell) or\
               (self.board[3] == self.board[4] == self.board[5] and self.board[3] != self.empty_cell) or\
               (self.board[6] == self.board[7] == self.board[8] and self.board[6] != self.empty_cell)

    def vertical_win(self):
        return (self.board[0] == self.board[3] == self.board[6] and self.board[0] != self.empty_cell) or\
               (self.board[1] == self.board[4] == self.board[7] and self.board[1] != self.empty_cell) or\
               (self.board[2] == self.board[5] == self.board[8] and self.board[2] != self.empty_cell)

    def diagonal_win(self):
        return (self.board[0] == self.board[4] == self.board[8] and self.board[0] != self.empty_cell) or\
               (self.board[2] == self.board[4] == self.board[6] and self.board[2] != self.empty_cell)

    def board_full(self):
        if "-" not in self.board:
            return True
        return False
