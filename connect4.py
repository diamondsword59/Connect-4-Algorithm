import asyncio
import websockets
import random
import copy
import time
class Board:
	def __init__(self):
		self.rows = 6;
		self.columns = 7;
		self.board = [[0 for _ in range(self.columns)] for _ in range(self.rows)]

	def print_board(self):
	# Printing the top of the board
		print(" " + " ".join([str(i) for i in range(self.columns)]))

		# Iterate through each row, starting from the top
		for row in range(self.rows - 1, -1, -1):
		    print("|", end='')
		    for col in range(self.columns):
		        # Print the current cell followed by a space
		        # You can modify the print statement to display different symbols for players
		        print(self.board[row][col], end=' ')
		    # Print a pipe at the end of each row and then a new line
		    print("|")

		# Printing the bottom of the board
		print("+" + "---" * self.columns + "+")

	def can_add_disc(self, column):
		return self.board[5][column] == 0

	def add_disc(self, column, player):
		for i in range(self.rows):
		    if self.board[i][column] == 0:
		        self.board[i][column] = player
		        break;

	def __deepcopy__(self, memo):
		new_copy = type(self)()
		new_copy.board = copy.deepcopy(self.board, memo)
		return new_copy

	def copy_board(self):
		return copy.deepcopy(self)

	def is_winner(self, player):
	# Check horizontal locations for win
		for row in range(self.rows):
		    for col in range(self.columns - 3):
		        if all(self.board[row][col + i] == player for i in range(4)):
		            return True

		# Check vertical locations for win
		for col in range(self.columns):
		    for row in range(self.rows - 3):
		        if all(self.board[row + i][col] == player for i in range(4)):
		            return True

		# Check positively sloped diagonals
		for col in range(self.columns - 3):
		    for row in range(3, self.rows):
		        if all(self.board[row - i][col + i] == player for i in range(4)):
		            return True

		# Check negatively sloped diagonals
		for col in range(self.columns - 3):
		    for row in range(self.rows - 3):
		        if all(self.board[row + i][col + i] == player for i in range(4)):
		            return True

		return False


	def remove_disc(self, column):
		i = 5
		while(i>=0):
			if self.board[i][column] != 0:
				self.board[i][column] = 0
				break
			i -= 1

	def possible_outcomes(self, player):
		total = 0;
		i = 0;
		while(i<7):
		    if self.can_add_disc(i):
		    	temp = self.copy_board()
		    	temp.add_disc(i, player)
		    	if self.is_winner(player):
		    		total+= 1
		    i += 1
		return total

	def evaluate_board(self):
		if self.is_winner(1):
			return 100
		elif self.is_winner(-1):
			return -105
		else:
			return self.possible_outcomes(1)-self.possible_outcomes(-1)


	def evaluate_move(self, depth, maximizingPlayer):
		total = 0
		if depth == 0 or self.is_winner(-1) or self.is_winner(1):
			return self.evaluate_board()
		if maximizingPlayer:
			for col in range(self.columns):
				if self.can_add_disc(col):
					self.add_disc(col, 1)
					total += self.evaluate_move(depth - 1, False)
					self.remove_disc(col)
		else:
			for col in range(self.columns):
				if self.can_add_disc(col):
					self.add_disc(col, -1)
					total += self.evaluate_move(depth - 1, True)
					self.remove_disc(col)
		return total


	def best_move(self, depth, maximizingPlayer):
		for col in range(self.columns):
			if self.can_add_disc(col):
				self.add_disc(col, 1 if maximizingPlayer else -1)
				if self.is_winner(1 if maximizingPlayer else -1):
					self.remove_disc(col)
					return col  # Return immediately if this move wins
				self.remove_disc(col)

		best_score = -100000000000 if maximizingPlayer else 100000000000
		columns = [3,4,2,5,1,6,0]
		best_column = None
		for col in columns:
			if self.can_add_disc(col):
			    self.add_disc(col, 1 if maximizingPlayer else -1)
			    score = self.evaluate_move(depth - 1, not maximizingPlayer)
			    self.remove_disc(col)
			    if maximizingPlayer and score > best_score or not maximizingPlayer and score < best_score:
			        best_score = score
			        best_column = col
		return best_column


async def gameloop (socket, created):
  active = True
  board = Board()

  while active:
    message = (await socket.recv()).split(':')

    print(message[0])
    match message[0]:
      case 'OPPONENT':

      	board.add_disc(int(message[1]), -1)
      	col = board.best_move(4, True)
      	board.add_disc(col, 1)
      	time.sleep(0.5)
      	await socket.send(f'PLAY:{col}')

      case 'GAMESTART':
        col = board.best_move(4, True)
        board.add_disc(col, 1)
        time.sleep(0.5)             
        await socket.send(f'PLAY:{col}')
      
      case 'WIN' | 'LOSS' | 'DRAW' | 'TERMINATED':
        print(message[0])

        active = False

async def create_game (server):
  async with websockets.connect(f'ws://{server}/create') as socket:
    await gameloop(socket, True)

async def join_game(server, id):
  async with websockets.connect(f'ws://{server}/join/{id}') as socket:
    await gameloop(socket, False)

if __name__ == '__main__':
  server = input('Server IP: ').strip()

  protocol = input('Join game or create game? (j/c): ').strip()

  match protocol:
    case 'c':
      asyncio.run(create_game(server))
    case 'j':
      id = input('Game ID: ').strip()

      asyncio.run(join_game(server, id))
    case _:
      print('Invalid protocol!')
