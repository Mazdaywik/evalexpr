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
    def __repr__(self):
        return "ID(" + repr(self.name) + ")"

class Number:
    def __init__(self, val):
        self.val = val
    def __repr__(self):
        return "Number(" + repr(self.name) + ")"

class SyntaxError(Exception):
    def __init__(self, filename, row, col, message):
        self.message = "{filename}:{row}:{col}:{message}".format(**locals())

class Lexer:
    OPS = ['+', '-', '*', '/', '(', ')', '=', ';', ',', '<', '>']
    OPS2 = ['<=', '>=', '==', '!=']
    KEYWORDS = ["NONE", "TRUE", "FALSE",
                "if", "then", "else", "end",
                "while", "do",
                ]

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
        elif self.__ch2() in Lexer.OPS2:
            self.token = self.__ch2()
            self.__nextch()
            self.__nextch()
        elif self.__ch() in Lexer.OPS:
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
        if varname in Lexer.KEYWORDS:
            self.token = varname
        else:
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

    def __ch2(self):
        return self.__text[:2]

    def __nextch(self):
        if self.__ch() == '\n':
            self.__row += 1
            self.__col = 1
        elif self.__ch() != '':
            self.__col += 1
        self.__text = self.__text[1:]

## Синтаксический анализ

# program = exprlist
def parse_program(code, lexer):
    parse_exprlist(code, lexer)
    lexer.expects("EOF")

# exprlist = expr { ';' expr }
def parse_exprlist(code, lexer):
    parse_expr(code, lexer)
    while lexer.token == ';':
        lexer.next_token()
        code.append("DROP")
        parse_expr(code, lexer)

RELOP = ["<", "<=", ">", ">=", "==", "!="]
# expr = arexpr [RELOP arexpr]
def parse_expr(code, lexer):
    parse_arexpr(code, lexer)
    if lexer.token in RELOP:
        relop = lexer.token
        lexer.next_token()
        parse_arexpr(code, lexer)
        code.append(relop)

# arexpr = ['+' | '-'] term { ('+' | '-') term }
def parse_arexpr(code, lexer):
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

# factor = primary {args} | NUMBER | '(' exprlist ')'
def parse_factor(code, lexer):
    if start_primary(lexer.token):
        parse_primary(code, lexer)
        while lexer.token == '(':
            parse_args(code, lexer)
    elif type(lexer.token) == Number:
        code.append(RValue(lexer.token.val))
        lexer.next_token()
    elif lexer.token == '(':
        lexer.next_token()
        parse_exprlist(code, lexer)
        lexer.expects(')')
    else:
        lexer.error("Expected number, varname or '(', but got "
                    + repr(lexer.token))

def start_primary(token):
    return (type(token) == ID
            or token in VALKEYWORD
            or token in STATKEYWORD)

STATKEYWORD = ['if', "while"]

VALKEYWORD = {
    "TRUE" : True,
    "FALSE" : False,
    "NONE" : None,
}

# primary = ID ['=' expr] | valkeyword | statement
# valkeyword = TRUE | FALSE | NONE
def parse_primary(code, lexer):
    if type(lexer.token) == ID:
        varname = lexer.token.name
        lexer.next_token()
        if lexer.token == '=':
            lexer.next_token()
            code.append(LValue(varname))
            parse_expr(code, lexer)
            code.append('=')
        else:
            code.append(ID(varname))
    elif lexer.token in VALKEYWORD:
        code.append(RValue(VALKEYWORD[lexer.token]))
        lexer.next_token()
    elif lexer.token in STATKEYWORD:
        parse_statement(code, lexer)
    else:
        lexer.error("Expected primary, but got " + repr(lexer.token))

# statement = if_statement | while_statement
def parse_statement(code, lexer):
    if lexer.token == "if":
        parse_if_statement(code, lexer)
    elif lexer.token == "while":
        parse_while_statement(code, lexer)
    else:
        lexer.error("expected statement, but got " + repr(lexer.token))

# if_statement = "if" expr "then" exprlist [ "else" exprlist ] "end"
def parse_if_statement(code, lexer):
    lexer.expects("if")
    parse_expr(code, lexer)
    lexer.expects("then")
    to_else = OnFalseJump(0)
    code.append(to_else)
    parse_exprlist(code, lexer)
    to_end = Jump(0)
    code.append(to_end)
    to_else.target = len(code)
    if lexer.token == "else":
        lexer.next_token()
        parse_exprlist(code, lexer)
    else:
        code.append(LValue(None))
    to_end.target = len(code)
    lexer.expects("end")

# while_statement = "while" expr "do" exprlist "end"
def parse_while_statement(code, lexer):
    lexer.expects("while")
    code.append(LValue(None))
    start_loop = len(code)
    parse_expr(code, lexer)
    lexer.expects("do")
    to_exit = OnFalseJump(0)
    code.append(to_exit)
    code.append("DROP")
    parse_exprlist(code, lexer)
    code.append(Jump(start_loop))
    to_exit.target = len(code)
    lexer.expects("end")

# args = '(' [expr {',' expr}] ')'
def parse_args(code, lexer):
    lexer.expects('(')
    code.append("[]")
    if lexer.token != ')':
        parse_expr(code, lexer)
        code.append("APPEND")
        while lexer.token == ',':
            lexer.next_token()
            parse_expr(code, lexer)
            code.append("APPEND")
    lexer.expects(')')
    code.append("CALL")

## Виртуальная машина

class LValue:
    def __init__(self, name):
        self.name = name
    def __repr__(self):
        return "LValue(" + repr(self.name) + ")"

class RValue:
    def __init__(self, val):
        self.val = val
    def __repr__(self):
        return "RValue(" + repr(self.val) + ")"

class OnFalseJump:
    def __init__(self, target):
        self.target = target
    def __repr__(self):
        return "OnFalseJump(" + repr(self.target) + ")"

class Jump:
    def __init__(self, target):
        self.target = target
    def __repr__(self):
        return "Jump(" + repr(self.target) + ")"

BINARY = {
    '+' : lambda x, y : x + y,
    '-' : lambda x, y : x - y,
    '*' : lambda x, y : x * y,
    '/' : lambda x, y : x / y,
    "APPEND" : lambda args, arg : args + [arg],
    "CALL" : lambda func, args : func(*args),
    '<' : lambda x, y : x < y,
    '>' : lambda x, y : x > y,
    "<=" : lambda x, y : x <= y,
    ">=" : lambda x, y : x >= y,
    "==" : lambda x, y : x == y,
    "!=" : lambda x, y : x != y,
}

def evaluate(code):
    stack = []
    env = {
        "pi" : math.pi,
        "e" : math.e,
        "sin" : math.sin,
        "print" : print
    }
    pc = 0
    while pc < len(code):
        cur = code[pc]
        if type(cur) == RValue:
            stack.append(cur.val)
        elif type(cur) == ID:
            stack.append(env[cur.name])
        elif cur in BINARY:
            y = stack.pop()
            x = stack.pop()
            stack.append(BINARY[cur](x, y))
        elif cur == "NEG":
            stack.append(-stack.pop())
        elif type(cur) == LValue:
            stack.append(cur.name)
        elif cur == '=':
            value = stack.pop()
            varname = stack.pop()
            env[varname] = value
            stack.append(value)
        elif cur == "DROP":
            stack.pop()
        elif cur == "[]":
            stack.append([])
        elif type(cur) == OnFalseJump:
            if not stack.pop():
                pc = cur.target
                continue
        elif type(cur) == Jump:
            pc = cur.target
            continue
        else:
            raise Exception("Bad instruction '{cur}'".format(**locals()))
        pc += 1

if __name__ == "__main__":
    main(sys.argv)
    #main(["evalexpr.py", "example.txt"])
