class TicTacToe:

    def __init__(self):
        self.currentPlayer = "X"
        self.gameBoard = ["-", "-", "-", "-", "-", "-", "-", "-", "-"]


    def get_board(self):
        print(self.gameBoard[0] + "  |  " + self.gameBoard[1] + "  |  " + self.gameBoard[2])
        print("-----------------" )
        print(self.gameBoard[3] + "  |  " + self.gameBoard[4] + "  |  " + self.gameBoard[5])
        print("-----------------" )
        print(self.gameBoard[6] + "  |  " + self.gameBoard[7] + "  |  " + self.gameBoard[8])
        print("-----------------" )

    def set_symbol(self , symbol):
        global currentPlayer

        if(symbol >= 1 and symbol <= 9 and self.gameBoard[symbol - 1] == "-"):
            self.gameBoard[symbol - 1] = self.currentPlayer

            self.is_finished()
        
            if(self.currentPlayer == "X"):
                self.currentPlayer = "O"
            else:
                self.currentPlayer = "X"
            self.get_board()
        else:
            print("Wrong cell! Choose another one")
            self.get_board()
            self.set_symbol(int(input()))

    def is_finished(self):
        if self.is_horizontal_win() or self.is_vertical_win() or self.is_diagonal_win():
            print(currentPlayer + " player wins")

        elif self.is_board_full():
            print("Game over")

    def is_horizontal_win(self):
        return (self.gameBoard[0] == self.gameBoard[1] == self.gameBoard[2] == self.currentPlayer)  or (self.gameBoard[3] == self.gameBoard[4] == self.gameBoard[5] == self.currentPlayer)  or (self.gameBoard[1] == self.gameBoard[2] == self.gameBoard[3] == self.currentPlayer) 

    def is_vertical_win(self):
        return (self.gameBoard[0] == self.gameBoard[3] == self.gameBoard[6] == self.currentPlayer)  or (self.gameBoard[1] == self.gameBoard[4] == self.gameBoard[7] == self.currentPlayer)  or (self.gameBoard[2] == self.gameBoard[5] == self.gameBoard[8] == self.currentPlayer) 

    def is_diagonal_win(self):
        return (self.gameBoard[0] == self.gameBoard[4] == self.gameBoard[8] == self.currentPlayer)  or (self.gameBoard[2] == self.gameBoard[4] == self.gameBoard[6] == self.currentPlayer)

    def is_board_full(self):
        if "-" not in self.gameBoard:
            return True
            

p = TicTacToe()
p.set_symbol(int(input()))
p.get_board()