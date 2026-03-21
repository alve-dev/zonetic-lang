from zonc.ast import *
from zonc.zonc_errors import DiagnosticEngine, ErrorCode
from .runtime_scope import RuntimeScope, RuntimeValue
from zonc.location_file import Span


class BreakSignal(Exception): pass


class ContinueSignal(Exception): pass


class GiveSignal(Exception):
    def __init__(self, value: NodeExpr):
        self.value = value
        

class ZoneticRuntimeError(Exception):
    def __init__(
        self,
        error_code: ErrorCode,
        args: dict[str, str] | None,
        span_code: list[Span],
        span_error: list[tuple[Span, str]]
    ):
        self.error_code = error_code
        self.span_code = span_code
        self.span_error = span_error
        self.arg = args


class Interpreter:
    def __init__(self, diag: DiagnosticEngine) -> None:
        self.diag = diag
    
    def execute(self, program: Program) -> None:
        scope = RuntimeScope()
        for node in program.stmts:
            self.exec_stmt(node, scope)
    
    def exec_stmt(self, node: NodeStmt, scope: RuntimeScope) -> None:
        match node:
            case DeclarationStmt():
                scope.set(
                    node.name,
                    RuntimeValue(
                        None
                    )
                )
            
            case AssignmentStmt():
                scope.update(
                    node.name,
                    self.eval_expr(node.value, scope)
                )
                
            case BreakStmt():
                raise BreakSignal
            
            case ContinueStmt():
                raise ContinueSignal
            
            case GiveStmt():
                raise GiveSignal(node.value)

            case PrintStmt():
                string = ""
                for arg in node.args:
                    val_arg = self.eval_expr(arg, scope)
                    if isinstance(val_arg, bool):
                        if val_arg == True:
                            string += "true"
                        
                        elif val_arg == False:
                            string += "false"
                        
                    elif isinstance(val_arg, str):
                        string += val_arg
                    
                    else:
                        string += str(val_arg)
                    
                print(string)
                
            case BlockExpr():
                block_scope = RuntimeScope(scope)
                
                while True:
                    try:
                        for stmt in node.stmts:
                            self.exec_stmt(stmt, block_scope)
                            
                        break
                    
                    except GiveSignal:
                        break
                    
            case IfForm():
                if self.eval_expr(node.if_branch.cond, scope):
                    return self.exec_stmt(node.if_branch.block, scope)
                    
                if not(node.elif_branches is None):
                    for branch in node.elif_branches:
                        if self.eval_expr(branch.cond, scope):
                            return self.exec_stmt(branch.block, scope)
                
                if not(node.else_branch is None):
                    return self.exec_stmt(node.else_branch.block, scope)
            
            case WhileForm():
                while self.eval_expr(node.condition_field, scope):
                    iter_scope = RuntimeScope(scope)
                    try:
                        for stmt in node.block_expr.stmts:
                            self.exec_stmt(stmt, iter_scope)
                            
                    except BreakSignal:
                        break
                    
                    except ContinueSignal:
                        continue
                
    
    def eval_expr(self, node: NodeExpr, scope: RuntimeScope) -> any:
        match node:
            case IntLiteral(): return node.value
            case FloatLiteral(): return node.value
            case BoolLiteral(): return bool(node.value)
            case StringLiteral(): return node.value
            case BinaryExpr():
                match node.operator:
                    case Operator.ADD:
                        return self.eval_expr(node.left, scope) + self.eval_expr(node.right, scope)
                    
                    case Operator.SUB:
                        return self.eval_expr(node.left, scope) - self.eval_expr(node.right, scope)
                    
                    case Operator.MUL:
                        return self.eval_expr(node.left, scope) * self.eval_expr(node.right, scope)
                    
                    case Operator.DIV:
                        right = self.eval_expr(node.right, scope)
                        
                        if right == 0:
                            raise ZoneticRuntimeError(
                                ErrorCode.E4001,
                                { "operator" : '/' },
                                [node.right.span],
                                [(node.right.span, "this evaluates to zero at runtime")]
                            )
                            
                        if isinstance(right, int):
                            return int(self.eval_expr(node.left, scope) / right)
                            
                        return self.eval_expr(node.left, scope) / right
                    
                    case Operator.POW:
                        return self.eval_expr(node.left, scope) ** self.eval_expr(node.right, scope)
                    
                    case Operator.MOD:
                        right = self.eval_expr(node.right, scope)
                        
                        if right == 0:
                            raise ZoneticRuntimeError(
                                ErrorCode.E4001,
                                { "operator" : '%' },
                                [node.right.span],
                                [(node.right.span, "this evaluates to zero at runtime")]
                            )
                        
                        return self.eval_expr(node.left, scope) % right
                    
                    case Operator.LT:
                        return self.eval_expr(node.left, scope) < self.eval_expr(node.right, scope)
                    
                    case Operator.GT:
                        return self.eval_expr(node.left, scope) > self.eval_expr(node.right, scope)

                    case Operator.LE:
                        return self.eval_expr(node.left, scope) <= self.eval_expr(node.right, scope)
                    
                    case Operator.GE:
                        return self.eval_expr(node.left, scope) >= self.eval_expr(node.right, scope)
                    
                    case Operator.EQ:
                        return self.eval_expr(node.left, scope) == self.eval_expr(node.right, scope)
                    
                    case Operator.NE:
                        return self.eval_expr(node.left, scope) != self.eval_expr(node.right, scope)
                    
                    case Operator.AND:
                        left = self.eval_expr(node.left, scope)
                        
                        if not left:
                            return False
                        
                        return left and self.eval_expr(node.right, scope)
                    
                    case Operator.OR:
                        left = self.eval_expr(node.left, scope)
                        
                        if left:
                            return True
                        
                        return left or self.eval_expr(node.right, scope)
                
            case UnaryExpr():
                match node.operator:
                    case Operator.NOT:
                        return not(self.eval_expr(node.value, scope))
                    
                    case Operator.NEG:
                        return -(self.eval_expr(node.value, scope))
                    
            case VariableExpr():
                return scope.get(node.name).value
                
            case InputExpr():
                inp = input(node.prompt.value)
                
                match node.zontype:
                    case ZonType.INT:
                        return int(inp)
                    case ZonType.FLOAT:
                        return float(inp)
                    case ZonType.STRING:
                        return inp
                    
            case BlockExpr():
                try:
                    block_scope = RuntimeScope(scope)
                    for stmt in node.stmts:
                        self.exec_stmt(stmt, block_scope)
                        
                except GiveSignal as give:
                    return self.eval_expr(give.value, block_scope)
            
            case IfForm():
                if self.eval_expr(node.if_branch.cond, scope):
                    return self.eval_expr(node.if_branch.block, scope)
                    
                if not(node.elif_branches is None):
                    for branch in node.elif_branches:
                        if self.eval_expr(branch.cond, scope):
                            return self.eval_expr(branch.block, scope)
                        
                if not(node.else_branch is None):
                    return self.eval_expr(node.else_branch.block, scope)
                        
                        
                        
                        
                        
                        