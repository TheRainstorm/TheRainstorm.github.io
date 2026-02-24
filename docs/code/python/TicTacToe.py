# coding: utf-8

# Date: 2020/02/11
# License: BSD
# Author: wwh
# Contributors: yfy

from random import randint

def Num2Letter(boardNum):
    boardLetter = []
    for i in range(10):
        boardLetter .append('X' if boardNum[i]==1 else 'O' if boardNum[i]==-1 else ' ')
    return boardLetter

def drawBoard(boardNum):
    board = Num2Letter(boardNum)
    print(board[7]+'|'+board[8]+'|'+board[9])
    print('-+-+-')
    print(board[4]+'|'+board[5]+'|'+board[6])
    print('-+-+-')
    print(board[1]+'|'+board[2]+'|'+board[3])

def inputPlayerLetter():
    letter = ' '
    while not (letter == 'X' or letter == 'O'):
        print('Do you want to be X or O? (X will be first)')
        letter=input().upper()
    if letter =='X':
        return [1,-1]
    else:
        return [-1,1]

def makeMove(board,letter,move):
    board[int(move)]=letter

def isWinner( bo,le ):
    compare = 3 if le==1 else -3
    return (bo[7] + bo[8] + bo[9]==compare) or\
           (bo[4] + bo[5] + bo[6]==compare) or\
           (bo[1] + bo[2] + bo[3]==compare) or\
           (bo[7] + bo[4] + bo[1]==compare) or\
           (bo[8] + bo[5] + bo[2]==compare) or\
           (bo[3] + bo[6] + bo[9]==compare) or\
           (bo[7] + bo[5] + bo[3]==compare) or\
           (bo[9] + bo[5] + bo[1]==compare)

def getBoardCopy(board):
    return board[:]

def isSpaceFree(board,move):
    return  board[move]==0

def getPlayerMove(board):
    move=' '
    while move not in '1 2 3 4 5 6 7 8 9'.split() or not isSpaceFree(board,int(move)):
        print('what is your next move?(1~9), q to quit')
        move=input()
        if move=='q':
            move = -1
            break
    return int(move)

def gen_game_tree(board, choices, player):
    '''
    generate the all possibility game tree when the specific player play the first within the given board and choices
    the leaf node value is the result related to the specific player: player-> win, -player-> lose, 0 tie
    
    board: list, numerical board
    choices: list, the possible move index
    player: int, -1 or 1(not the char 'X' or 'O')

    return: dict, the game tree, like {1:{...}, 2:-1, ...}
    '''
    if len(choices)==0:
        return 0    # no winner
    #DSF
    tree = {} 
    for i in range(len(choices)):
        #make copy
        choices_next = choices[:]
        board_next = board[:]

        del choices_next[i]
        makeMove(board_next, player, choices[i])
        if isWinner(board_next, player):
            tree[choices[i]]= player
        else:
            tree[choices[i]]=gen_game_tree(board_next, choices_next, -player)
    return tree

def maxminmize(tree, isMAX):
    '''
    Search the tree and generate the internal-node value. since there is no Level restriction, the
    computer will search the whole tree. So you will never win the computer in this game!!!

    isMAX: bool, whether is the MAX layer. MAX mean the first player, need to maximize his value.
           MIN mean the latter player, need to minimize the first player value.
    '''
    if type(tree)==int:
        return tree

    if isMAX:
        the_max = -2 # negative infinite (compare to -1, 0, 1)
        for move, subtree in tree.items():
            value = maxminmize(subtree, not isMAX)
            if value > the_max:
                the_max = value
                move_list = [move]
            elif value == the_max: #record all the move to get the max value
                move_list.append(move)
            else:
                pass
        tree[0]=[move_list, the_max] #since 0 is not in 1~9, use it to record the max or min value.
    else:
        the_min = 2 # infinite (compare to -1, 0, 1)
        for move, subtree in tree.items():
            value = maxminmize(subtree, not isMAX)
            if value < the_min:
                the_min = value
                move_list = [move]
            elif value == the_min:
                move_list.append(move)
            else:
                pass
        tree[0]=[move_list, the_min] #since 0 is not in 1~9, use it to record the max or min value.
    return tree[0][1]

def getComputerMove(tree,computerletter):
    expression_list = [
        '(⊙﹏⊙)', 
        '○|￣|_', 
        '（°Д°）', 

        '_(≧∇≦」∠)_', 
        '└(^O^)┘', 
        '๑乛◡乛๑', 
        '✿✿ヽ(°▽°)ノ✿', 
        '╮(￣▽￣")╭ ', 
        '( *・ω・)', 
        '(/∇＼*)', 
        '(￣^￣)', 
        '_(:з」∠)_ ', 
        '୧(๑•̀⌄•́๑)૭', 
        '_(ÒωÓ๑ゝ∠)_', 
        '(╯°Д°）╯︵ /', 
        '(* ￣3￣ *)'
    ]

    # 我好中二呀。
    sentence_list = [
        '难道你。。看穿了？',
        '不可能，我怎么会输！',
        'oh，不！！！',

        '快赢了呢。',
        '你已经输了！',
        '哎呀~，一不小心又赢了呢。',
        '给 爷  爪巴'
    ]
    
    move_list, value = tree['0']

    a, b = len(expression_list), len(sentence_list)
    if int(value)==computerletter:
        print('PC: '+expression_list[randint(3, a-1)]+sentence_list[randint(3, b-1)])
    elif int(value)==-computerletter:
        print('PC: '+expression_list[randint(0, 2)]+sentence_list[randint(0, 2)])
    else:
        print('PC: '+expression_list[randint(0,15)])
    return int(move_list[randint(0, len(move_list)-1)])

def isBoardFull(board):
    for i in range(1,10):
        if isSpaceFree(board,i):
            return False
    return True

def load_json():
    import json
    import os
    if os.path.exists('Tic-Tac-Toe-secret.json'):
        with open('Tic-Tac-Toe-secret.json') as fp:
            return json.load(fp)
    else:
        with open('Tic-Tac-Toe-secret.json','w') as fp:
            Tree = gen_game_tree([0]*10, list(range(1,10)), 1)
            maxminmize(Tree, True)
            json.dump(Tree, fp)
        return load_json() #don't return Tree directly, whose node value is int type.

if __name__ == '__main__':
    print('Loading...')
    Tree_ori = load_json()
    print('Finish.\n')
    print('Welcome to TIc-Tac-Toe!')

    while True:
        theboard =[0]*10
        playerLetter,computerLetter =inputPlayerLetter()
        # X will go first
        turn = 'player' if playerLetter==1 else 'computer'
        print('The '+turn +' will go first.')

        if turn=='player':
            drawBoard(theboard)
        Tree = Tree_ori
        while True:
            if turn =='player':
                move =getPlayerMove(theboard)
                if move==-1:
                    break
                makeMove(theboard,playerLetter,move)

                Tree=Tree[str(move)] #move to next subtree

                if isWinner(theboard,playerLetter):
                    print('Hooray! You have won the game!') #However, It's impossible. :-)
                    break
                else:
                    if isBoardFull(theboard):
                        print('The game is Tie')
                        break
                    else:
                        turn = 'computer'
            else:
                move =getComputerMove(Tree,computerLetter)
                makeMove(theboard,computerLetter,move)

                Tree=Tree[str(move)]

                drawBoard(theboard)
                if isWinner(theboard,computerLetter):
                    print('The computer has beaten you! You lose.')
                    break
                else:
                    if isBoardFull(theboard):
                        print('The game is a tie!')
                        break
                    else:
                        turn='player'
        print('Do you want to play again?(yes or no)')
        if not input().lower().startswith('y'):
            break