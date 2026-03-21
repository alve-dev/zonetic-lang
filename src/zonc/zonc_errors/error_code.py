from enum import Enum, auto

class ErrorCode(Enum):
    # Lexer Errors
    E0001 = auto()
    E0002 = auto()
    E0003 = auto()
    E0004 = auto()
    E0005 = auto()
    
    # Lexer Warnings
    W0001 = auto()
    
    # Normalizer Errors
    E1001 = auto()
    E1002 = auto()
    
    # Parser Errors
    E2001 = auto()
    E2002 = auto()
    E2003 = auto()
    E2004 = auto()
    E2005 = auto()
    E2006 = auto()
    E2007 = auto()
    E2008 = auto()
    E2009 = auto()
    E2010 = auto()
    E2011 = auto()
    E2012 = auto()
    
    # Parser Warnings
    W2001 = auto()
    
    # Semantic Errors
    E3001 = auto()
    E3002 = auto()
    E3003 = auto()
    E3004 = auto()
    E3005 = auto()
    E3006 = auto()
    E3007 = auto()
    E3008 = auto()
    E3009 = auto()
    E3010 = auto()
    E3011 = auto()
    E3012 = auto()
    
    # Semantics Warnings
    W3001 = auto()
    W3002 = auto()
    W3003 = auto()
    W3004 = auto()
    
    
    # Runtime Errors
    E4001 = auto()
    
    
# actualmente hay 31 Zonetic Errors y 6 Zonetic Warnings
# 7 Errors son de el Lexer y 1 warning son del lexer
# 2 Errors son del Normalizer
# 12 Errors son del Parser y 1 warning son del parser
# 12 Errors son de Semantic y 4 Warnings son del Semantic
# 1 Error de Runtime 