__author__ = 'Salandora'

programmers = dict()
boards = []

def register_programmer(instance):
    global programmers
    programmers[instance._identifier] = instance

def register_board(board):
    global boards
    boards.append(board)

def get_programmer(name):
    global programmers
    return programmers[name]