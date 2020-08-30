# -*- coding: utf-8 -*-
"""
Created on Tue Jun 23 08:58:06 2020

@author: rohan
"""
from functools import partial

class Func:
    pass

class HFunction(Func):
    def __init__(self, precedence, associativity, func, noOfArgs,
                 name = 'None', inputs = []):
        self.name = name
        self.precedence = precedence
        self.associativity = associativity 
        self.func = func
        self.noOfArgs = noOfArgs
        self.inputs =  inputs
        
    def apply(self, arg1 = None, arg2 = None):
        if self.noOfArgs == 0:
            return self.func()
            
        func = self.func
        noOfArgs = self.noOfArgs 
        name = self.name 
        if arg1 != None:
            #name += ' ' + str(arg1)
            if self.noOfArgs == 1:
                return func(arg1)
            
            func = partial(func, arg1)
            noOfArgs -= 1
            self.inputs.append(arg1)
            
        if arg2 != None or self.name == '..':
            #name += ' ' + str(arg2)
            if (noOfArgs == 1):
                return func(arg2)

            func = partial(func, b = arg2)
            noOfArgs -= 1
            self.inputs.append(arg2)
            
        return HFunction(self.precedence, self.associativity, func, noOfArgs,
                         name, self.inputs) 
    
    def simplify(self):
        if (self.noOfArgs == 0):
            return self.func()
        return self
    
    def __str__(self):
        # + ' ' + ' '.join(list(map(str, self.inputs)))
        return self.name
    
    def clone(self):
        return HFunction(self.precedence, self.associativity, self.func,
                         self.noOfArgs, self.name)
    
class Composition(Func):
    def __init__(self, second, first):        
        self.first = first.simplify()
        self.second = second.simplify()
        #self.precedence = first.precedence
        #self.associativity = first.associativity
        self.name = str(second) + '~' + str(first)
    
    def simplify(self):
        return self
    
    def __str__(self):
        return self.name
    
    def apply(self, arg1 = None):
        if arg1 != None or self.first.name == '..':
            return self.second.apply(self.first.apply(arg1))
        return self

class Function(Func):
    def __init__(self, name, cases = [], inputs = []):
        self.name = name
        self.cases = cases
        self.inputs = inputs
        from Operators import Associativity
        self.associativity = Associativity.LEFT 
        self.precedence = 8
    
    def clone(self):
        return Function(self.name,
                        cases = map(lambda case: case.clone(), self.cases),
                        inputs = self.inputs.copy())
        
    def simplify(self):
        value = self.checkCases(self.inputs)
        if value != None:
            return value
        return self
    
    def __str__(self):
        return self.name
    
    def apply(self, arg1 = None, arg2 = None):
        inputs = self.inputs.copy()
        if arg1 != None:
            if len(inputs) > 2 and inputs[-2] == None:
                inputs[-1] = arg1
            else:
                inputs.append(arg1)
            if arg2 != None:
                inputs.append(arg2)

        elif arg2 != None:
            inputs.append(None)
            inputs.append(arg2)

        value = self.checkCases(inputs)
        if value != None:
            return value
        
        return Function(self.name, cases = self.cases, inputs = inputs)
    
    def checkCases(self, inputs):
        for case in self.cases:
            arguments = case.arguments
            if len(arguments) == len(inputs):
                if self.matchCase(arguments, inputs):
                    for i in range(len(arguments)):
                        case = case.apply(inputs[i].simplify()) 
                    if case == None:
                        continue
                    return case.simplify()
        #raise Exception('''Pattern match on arguments failed for all 
                        #definitions of function''', self.name) 
        return None

    def matchCase(self, arguments, inputs):
        from utils import patternMatch
        if len(inputs) != len(arguments):
            return False
        for i in range(len(arguments)):
            if not patternMatch(arguments[i], inputs[i]):
                return False
        return True

class Lambda(Func):
    def __init__(self, name = '\\', arguments = [], expr = None, state = {}):
        self.name = name
        self.arguments = arguments
        self.expr = expr
        self.state = state
        self.noOfArgs = len(arguments)
        
    def apply(self, arg1 = None, arg2 = None):
        from Operator_Functions import assign
        state = self.state.copy()
        arguments = self.arguments.copy()
        if arg1 != None:
            assign(arguments[0], arg1, state)
            arguments = arguments[1:]
            if arguments == []:
                return self.returnValue(state)
            if arg2 != None:
                assign(arguments[0], arg2, state)
                arguments = arguments[1:]

        elif arg2 != None:
            assign(arguments[1], arg2, state)
            arguments = arguments[0] + arguments[2:]
            
        if arguments == []:
            return self.returnValue(state)
        
        return Lambda(arguments = arguments, expr = self.expr, state = state)

    def __str__(self):
        string = '\\' + ' '.join(list(map(str, self.arguments)))
        if self.expr != None:
            string += ' -> ' + str(self.expr)
        return string
    
    def simplify(self):
        if self.arguments == []:
            return self.returnValue({}).simplify()
        return self

    def returnValue(self, state):
        import utils 
        utils.frameStack.append(state)
        if self.expr != None:
            value = self.expr.simplify()
            #value = utils.replaceVariables(self.expr)
        else:
            value = None
        utils.frameStack.pop(-1)
        if (utils.return_value != None):
            utils.return_value = None
        return value
