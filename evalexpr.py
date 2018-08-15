#!/usr/bin/env python3
import sys
import math

def main(argv):
    if len(argv) < 2:
        print("Expected filename", file=sys.stderr)
        sys.exit(1)

    lexer = Lexer(argv[1])
    try:
        code = []
        parse_program(code, lexer)
        evaluate(code)
    except SyntaxError as e:
        print(e.message, file=sys.stderr)

## Лексический анализ

class ID:
    def __init__(self, name):
        self.name = name

class Number:
    def __init__(self, val):
        self.val = val

class SyntaxError(Exception):
    def __init__(self, filename, row, col, message):
        self.message = "{filename}:{row}:{col}:{message}".format(**locals())

class Lexer:
    def __init__(self, filename):
        fin = open(filename, encoding="UTF-8")
        self.__text = fin.read()
        fin.close()
        self.__filename = filename
        self.__row = 1
        self.__col = 1
        self.next_token()

    def next_token(self):
        while self.__ch().isspace():
            self.__nextch()
            
        if self.__ch().isalpha():
            self.__variable()
        elif self.__ch().isdigit():
            self.__number()
        elif self.__ch() in ['+', '-', '*', '/', '(', ')']:
            self.token = self.__ch()
            self.__nextch()
        elif self.__ch() == "":
            self.token = "EOF"
        else:
            self.error("Bad string '" + self.__text[:3] + "...'")

    def __variable(self):
        varname = ""
        while self.__ch().isalnum():
            varname += self.__ch()
            self.__nextch()
        self.token = ID(varname)

    def __number(self):
        number = ""
        while self.__ch().isdigit():
            number += self.__ch()
            self.__nextch()
        if self.__ch() == '.':
            number += '.'
            self.__nextch()
            while self.__ch().isdigit():
                number += self.__ch()
                self.__nextch()
            self.token = Number(float(number))
        else:
            self.token = Number(int(number))

    def error(self, message):
        raise SyntaxError(self.__filename,
                          self.__row,
                          self.__col,
                          message)

    def expects(self, token):
        if self.token != token:
            self.error("Expected {token}, but got {self.token}"
                       .format(**locals()))
        else:
            self.next_token()

    def __ch(self):
        return self.__text[:1]

    def __nextch(self):
        if self.__ch() == '\n':
            self.__row += 1
            self.__col = 1
        elif self.__ch() != '':
            self.__col += 1
        self.__text = self.__text[1:]

## Синтаксический анализ

# program = expr
def parse_program(code, lexer):
    parse_expr(code, lexer)
    lexer.expects("EOF")

# expr = ['+' | '-'] term { ('+' | '-') term }
def parse_expr(code, lexer):
    sign = '+'
    if lexer.token in ['+', '-']:
        sign = lexer.token
        lexer.next_token()
        
    parse_term(code, lexer)

    if sign == '-':
        code.append('NEG')

    while lexer.token in ['+', '-']:
        sign = lexer.token
        lexer.next_token()
        parse_term(code, lexer)
        code.append(sign)

# term = factor { ('*' | '/') factor }
def parse_term(code, lexer):
    parse_factor(code, lexer)
    while lexer.token in ['*', '/']:
        sign = lexer.token
        lexer.next_token()
        parse_factor(code, lexer)
        code.append(sign)

# factor = ID | NUMBER | '(' expr ')'
def parse_factor(code, lexer):
    if type(lexer.token) in [ID, Number]:
        code.append(lexer.token)
        lexer.next_token()
    elif lexer.token == '(':
        lexer.next_token()
        parse_expr(code, lexer)
        lexer.expects(')')
    else:
        lexer.error("Expected number, varname or '('")

## Виртуальная машина

BINARY = {
    '+' : lambda x, y : x + y,
    '-' : lambda x, y : x - y,
    '*' : lambda x, y : x * y,
    '/' : lambda x, y : x / y,
}

def evaluate(code):
    stack = []
    env = { "pi" : math.pi, "e" : math.e }
    pc = 0
    while pc < len(code):
        cur = code[pc]
        if type(cur) == Number:
            stack.append(cur.val)
        elif type(cur) == ID:
            stack.append(env[cur.name])
        elif cur in ['+', '-', '*', '/']:
            y = stack.pop()
            x = stack.pop()
            stack.append(BINARY[cur](x, y))
        elif cur == "NEG":
            stack.append(-stack.pop())
        pc += 1
    print(stack.pop())

if __name__ == "__main__":
    #main(sys.argv)
    main(["evalexpr.py", "example.txt"])
