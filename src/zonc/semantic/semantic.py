from zonc.ast import *
from zonc.zonc_errors import DiagnosticEngine
from zonc.enviroment import Enviroment, Symbol
from zonc.zonc_errors import ErrorCode
from zonc.location_file import Span, FileMap
from dataclasses import dataclass
    
@dataclass
class DictTemp:
    dict_temp: dict


class Semantic:
    def __init__(self, diag: DiagnosticEngine, file_map: FileMap) -> None:
        self.diag = diag
        self.file_map = file_map
        self.context_stack = []
        
           
    def check_ast(self, ast: Node, is_expr: bool) -> None | ZonType:
        scope: Enviroment = ast.scope
        for node in ast.stmts:
            if isinstance(node, DeclarationStmt):
                self.check_declaration_stmt(node, scope)
                continue
                
            elif isinstance(node, AssignmentStmt):
                self.check_assignment_stmt(node, scope, True)
                continue
            
            elif isinstance(node, BlockExpr):
                self.check_block_expr(node, is_expr)
                continue
                
            elif isinstance(node, GiveStmt):
                if is_expr:
                    return self.infer_expr(node.value, scope)
                break
            
            elif isinstance(node, IfForm):
                self.check_if_form(node, scope, False)
                continue
            
            elif isinstance(node, WhileForm):
                self.context_stack.append("while")
                self.check_while_form(scope, node)
                continue
            
            elif isinstance(node, BreakStmt):
                if not("while" in self.context_stack):
                    self.diag.emit(
                        ErrorCode.E3012,
                        { "keyword" : "break" },
                        [node.span],
                        [(node.span, "`break` is not inside any loop")]
                    )
                    continue
                else:
                    self.context_stack.append("break")
                    break
            
            elif isinstance(node, ContinueStmt):
                if not("while" in self.context_stack):
                    self.diag.emit(
                        ErrorCode.E3012,
                        { "keyword" : "continue" },
                        [node.span],
                        [(node.span, "`continue` is not inside any loop")]
                    )
                    continue
                else:
                    self.context_stack.append("continue")
                
            return None
            
            
    def check_declaration_stmt(self, node: DeclarationStmt, scope: Enviroment):
        scope.define(
            node.name,
            Symbol(
                node.mut,
                node.type,
                True,
                node.span
            )
        )
        
        
    def check_assignment_stmt(self, node: AssignmentStmt, scope: Enviroment, not_empty: bool):
        value_type = self.infer_expr(node.value, scope)
                
        if value_type == ZonType.UNKNOWN:
            return
        
        symbol = scope.get_symbol(node.name)
        
        if symbol is None:
            self.diag.emit(
                ErrorCode.E3001,
                { "name" : node.name },
                [node.span],
                [(node.span_name, "does not exist in this scope")]
            )
            return
        
        if not symbol.mutability and not symbol.is_empty:
            self.diag.emit(
                ErrorCode.E3005,
                { "name" : node.name },
                [node.span],
                [(node.span_name, "is inmutable, it was already assigned a value")]
            )
            return
        
        if symbol.zontype == ZonType.UNKNOWN:
            symbol.zontype = value_type
            
        elif symbol.zontype != value_type:
            if isinstance(node.value, BlockExpr):
                self.diag.emit(
                    ErrorCode.E3006,
                    { "name" : node.name,
                    "expected_type" : symbol.zontype.name.lower(),
                    "found_type" : value_type.name.lower()},
                    [Span(node.span.start, node.value.stmts[node.value.give_address].span.end, self.file_map)],
                    [(node.value.stmts[node.value.give_address].value.span, "this expression returns '{found_type}', but '{name}' expects '{expected_type}'")]
                )
            else:
                self.diag.emit(
                    ErrorCode.E3006,
                    { "name" : node.name,
                    "expected_type" : symbol.zontype.name.lower(),
                    "found_type" : value_type.name.lower()},
                    [node.span],
                    [(node.value.span, "this expression returns '{found_type}', but '{name}' expects '{expected_type}'")]
                )
            return
    
        if symbol.is_empty and not_empty:
            symbol.is_empty = False
                
    
    def check_block_expr(self, node: BlockExpr, is_expr: bool):
        if not(node.give_address is None):
            unreachable = len(node.stmts) - node.give_address - 1
            
            if unreachable == 1:
                self.diag.emit(
                    ErrorCode.W3001,
                    None,
                    [Span(node.span.start, node.stmts[node.give_address].span.end, self.file_map)],
                    [(node.stmts[node.give_address].span, "1 statement below this will never execute")]
                )
                
            elif unreachable > 1:
                self.diag.emit(
                    ErrorCode.W3001,
                    None,
                    [Span(node.span.start, node.stmts[node.give_address].span.end, self.file_map)],
                    [(node.stmts[node.give_address].span, f"{unreachable} statements below this will never execute")]
                )
        
        return self.check_ast(node, is_expr)
    
    
    def check_if_form(
        self,
        if_node: IfForm,
        scope: Enviroment,
        is_expr: bool
    ):
        sym_empty_count = DictTemp({})
        values_give = []
        
        if is_expr:
            values_give.append(self.check_if_branch(if_node.if_branch, scope, sym_empty_count, True, True))
        else:
            self.check_if_branch(if_node.if_branch, scope, sym_empty_count, True, False)
            
        
        if isinstance(if_node.if_branch.cond, BoolLiteral):
            has_unreachable = (if_node.elif_branches or if_node.else_branch)
    
            if if_node.if_branch.cond.value == 1:
                if has_unreachable:
                    self.diag.emit(
                        ErrorCode.W3002,
                        None,
                        [if_node.if_branch.cond.span],
                        [(if_node.if_branch.cond.span, "this condition is always `true`")]
                    )
                    
            else:
                self.diag.emit(
                    ErrorCode.W3003,
                    None,
                    [if_node.if_branch.cond.span],
                    [(if_node.if_branch.cond.span, "this condition is always `false`")]
                )
            
        if if_node.else_branch is None:
            if len(sym_empty_count.dict_temp) > 0:
                last_branch_span: Span
                
                if not if_node.elif_branches is None:
                    last_branch_span = if_node.elif_branches[-1].span
                else:
                    last_branch_span = if_node.if_branch.span
                
                self.diag.emit(
                    ErrorCode.E3008,
                    None,
                    [last_branch_span],
                    [(Span(last_branch_span.end-1, last_branch_span.end, self.file_map), "an `else` branch was expected here")]
                )
                return
        

        if not if_node.elif_branches is None:
            for elif_node in if_node.elif_branches:
                if is_expr:
                    values_give.append(self.check_if_branch(elif_node, scope, sym_empty_count, True, True))
                else:
                    self.check_if_branch(elif_node, scope, sym_empty_count, True, False)
            
        if if_node.else_branch is None:
            if len(sym_empty_count.dict_temp) > 0:
                last_branch_span: Span
                
                if not if_node.elif_branches is None:
                    last_branch_span = if_node.elif_branches[-1].span
                else:
                    last_branch_span = if_node.if_branch.span
                
                self.diag.emit(
                    ErrorCode.E3008,
                    None,
                    [last_branch_span],
                    [(Span(last_branch_span.end-1, last_branch_span.end, self.file_map), "an `else` branch was expected here")]
                )
                return

        else:
            if is_expr:
                values_give.append(self.check_if_branch(if_node.else_branch, scope, sym_empty_count, True, True))
            else:
                self.check_if_branch(if_node.else_branch, scope, sym_empty_count, True, False)

        if len(sym_empty_count.dict_temp) > 0:
            for symbol, branches_span in sym_empty_count.dict_temp.items():
                if branches_span[0] < if_node.len_branch:
                    
                    self.diag.emit(
                        ErrorCode.E3009,
                        { "name" : symbol },
                        [if_node.span,
                         branches_span[1],],
                        [(Span(if_node.span.end-1, if_node.span.end, self.file_map), "`{name}` is first assigned inside this if form, but not in every branch"),
                         (branches_span[1], "`{name}` is declared empty here and may still be empty after the if form")]
                    )
                else:
                    sym = scope.get_symbol(symbol)
                    sym.is_empty = False
        
        if is_expr:
            return values_give
                
    
    def check_if_branch(
        self,
        if_branch: IfBranch,
        scope_back: Enviroment,
        sym_empty_count: DictTemp,
        check_cond: bool,
        is_expr: bool,
    ):
        if check_cond:
            type_condition = self.infer_expr(if_branch.cond, scope_back)
            
            if type_condition == ZonType.UNKNOWN:
                pass
            
            elif type_condition != ZonType.BOOL:
                self.diag.emit(
                    ErrorCode.E3007,
                    { "found_type" : type_condition.name.lower() },
                    [Span(if_branch.span.start, if_branch.cond.span.end, self.file_map)],
                    [(if_branch.cond.span, "this expression returns `{found_type}`, but a condition field expects `bool`")]
            )
        
        scope: Enviroment = if_branch.block.scope
        
        for stmt in if_branch.block.stmts:
            if isinstance(stmt, DeclarationStmt):
                self.check_declaration_stmt(stmt, scope)
                continue
            
            elif isinstance(stmt, AssignmentStmt):
                symbol = scope.get_symbol(stmt.name)
                
                if symbol is None:
                    pass
                
                elif scope.exist_here(stmt.name):
                    pass
                
                elif symbol.is_empty:
                    if stmt.name in sym_empty_count.dict_temp:
                        sym_empty_count.dict_temp[stmt.name][0] += 1
                    else:
                        sym_empty_count.dict_temp.update({stmt.name: [1, symbol.decl_span]})
                        
                    self.check_assignment_stmt(stmt, scope, False)
                    continue
                
                self.check_assignment_stmt(stmt, scope, True)
                continue
            
            elif isinstance(stmt, BlockExpr):
                if is_expr:
                    return self.infer_expr(stmt, scope)
                
                self.check_block_expr(stmt, is_expr)
                
            elif isinstance(stmt, GiveStmt):
                if is_expr:
                    return (self.infer_expr(stmt.value, scope), stmt.span)
                break
            
            elif isinstance(stmt, IfForm):
                if is_expr:
                    return self.infer_expr(stmt, scope)
                else:
                    self.check_if_form(stmt, scope, is_expr)
                    
            elif isinstance(stmt, BreakStmt):
                if not("while" in self.context_stack):
                    #Error E3012
                    continue
                else:
                    self.context_stack.append("break")
                    break
            
            elif isinstance(stmt, ContinueStmt):
                if not("while" in self.context_stack):
                    #Error E3012
                    continue
                else:
                    self.context_stack.append("continue")
                    
            elif isinstance(stmt, WhileForm):
                self.context_stack.append("while")
                self.check_while_form(scope, stmt)
                continue
                
                
    
    def check_while_form(self, scope: Enviroment, while_node: WhileForm):
        type_condition = self.infer_expr(while_node.condition_field, scope)
            
        if type_condition == ZonType.UNKNOWN:
            pass
        
        elif type_condition != ZonType.BOOL:
            self.diag.emit(
                ErrorCode.E3007,
                { "found_type" : type_condition.name.lower() },
                [Span(while_node.span.start, while_node.condition_field.span.end, self.file_map)],
                [(while_node.condition_field.span, "this expression returns `{found_type}`, but a condition field expects `bool`")]
            )
            
        self.check_block_expr(while_node.block_expr, False)
        
        if isinstance(while_node.condition_field, BoolLiteral):
            if while_node.condition_field.value == 1:
                if not("break" in self.context_stack):
                    self.diag.emit(
                        ErrorCode.W3004,
                        None,
                        [while_node.span],
                        [(Span(while_node.span.end - 1, while_node.span.end, self.file_map), "this loop has no exit point")]
                    )
                    pass
            else:
                self.diag.emit(
                    ErrorCode.W3003,
                    None,
                    [while_node.condition_field.span],
                    [(while_node.condition_field.span, "this condition is always `false`")]
                )
                
        for i in range(len(self.context_stack)):
            if self.context_stack[i] == "break" or self.context_stack[i] == "continue":
                self.context_stack.pop(i)
            elif self.context_stack[i] == "while":
                self.context_stack.pop(i)
                break
            
        
    def check_operands_type(
        self,
        operands_type: tuple[tuple[ZonType, Span], tuple[ZonType, Span]] | tuple[tuple[ZonType, Span]],
        return_type: ZonType,
        equal: bool,
        operator: str,
        *zontypes,
    ):    
    
        len_types = len(zontypes)
    
        for i in range(len(operands_type)):
            no_match = 0
            
            for j in range(len_types):
                if operands_type[i][0] != zontypes[j]:
                    no_match += 1
            
            if no_match == len_types:
                valid_types = ""
                
                for j in range(len_types):
                    if j < len_types-1:
                        if j == (len_types-2):
                            valid_types += f"{zontypes[j].name.lower()} or "
                        else:
                            valid_types += f"{zontypes[j].name.lower()}, "
                    
                    elif j == len_types-1:
                        valid_types += f"{zontypes[j].name.lower()}"
                
                self.diag.emit(
                    ErrorCode.E3003,
                    { "operator" : operator, 
                        "valid_types" : valid_types,
                        "found_type" : operands_type[i][0].name.lower()},
                    [operands_type[i][1]],
                    [(operands_type[i][1], "this operand is `{found_type}`, but `{operator}` expects {valid_types}")]
                )
                return ZonType.UNKNOWN
                
        if equal:
            if operands_type[0][0] != operands_type[1][0]:
                self.diag.emit(
                    ErrorCode.E3004,
                    { "operator" : operator,
                      "right_type" : operands_type[1][0].name.lower(),
                      "left_type" :  operands_type[0][0].name.lower()},
                    [operands_type[1][1]],
                    [(operands_type[1][1], "this is `{right_type}`, but `{operator}` expects `{left_type}` to match the left operand")]
                )
                return ZonType.UNKNOWN
            
        return return_type
                
        
    def infer_expr(self, expr: NodeExpr, scope: Enviroment) -> ZonType:
        if isinstance(expr, IntLiteral):
            return ZonType.INT
        
        elif isinstance(expr, FloatLiteral):
            return ZonType.FLOAT
        
        elif isinstance(expr, BoolLiteral):
            return ZonType.BOOL
        
        elif isinstance(expr, StringLiteral):
            return ZonType.STRING
        
        elif isinstance(expr, BinaryExpr):
            op = expr.operator
            left_type = self.infer_expr(expr.left, scope)
            right_type = self.infer_expr(expr.right, scope)
            
            if left_type == ZonType.UNKNOWN or right_type == ZonType.UNKNOWN:
                return ZonType.UNKNOWN
            
            if op == Operator.ADD or op == Operator.SUB or op == Operator.MUL or op == Operator.POW or op == Operator.MOD or op == Operator.DIV:
                op_str: str
                match op:
                    case Operator.ADD: op_str = '+'
                    case Operator.SUB: op_str = '-'
                    case Operator.MUL: op_str = '*'
                    case Operator.DIV: op_str = '/'
                    case Operator.MOD: op_str = '%'
                    case Operator.POW: op_str = "**"
                
                
                return self.check_operands_type(
                    ((left_type, expr.left.span), (right_type, expr.right.span)),
                    left_type,
                    True,
                    op_str,
                    ZonType.INT, ZonType.FLOAT
                )
            
            elif op == Operator.LT or op == Operator.GT or op == Operator.LE or op == Operator.GE:
                op_str: str
                match op:
                    case Operator.LT: op_str = '<'
                    case Operator.GT: op_str = '>'
                    case Operator.LE: op_str = '<='
                    case Operator.GE: op_str = '>='
                
                return self.check_operands_type(
                    ((left_type, expr.left.span), (right_type, expr.right.span)),
                    ZonType.BOOL,
                    True,
                    op_str,
                    ZonType.INT, ZonType.FLOAT
                )
            
            elif op == Operator.AND or op == Operator.OR:
                op_str: str
                match op:
                    case Operator.AND: op_str = 'and/&&'
                    case Operator.OR: op_str = 'or/||'
                
                
                return self.check_operands_type(
                    ((left_type, expr.left.span), (right_type, expr.right.span)),
                    left_type,
                    False,
                    op_str,
                    ZonType.BOOL
                )
            
            elif op == Operator.EQ or op == Operator.NE:
                op_str: str
                match op:
                    case Operator.EQ: op_str = '=='
                    case Operator.NE: op_str = '!='
                
                
                return self.check_operands_type(
                    ((left_type, expr.left.span), (right_type, expr.right.span)),
                    ZonType.BOOL,
                    True,
                    op_str,
                    ZonType.INT, ZonType.FLOAT, ZonType.BOOL, ZonType.STRING
                )
                
        elif isinstance(expr, UnaryExpr):
            op = expr.operator
            value_type = self.infer_expr(expr.value, scope)
            
            if value_type == ZonType.UNKNOWN:
                return ZonType.UNKNOWN
            
            if op == Operator.NEG:
                return self.check_operands_type(
                    ((value_type, expr.value.span),),
                    value_type,
                    False,
                    '-',
                    ZonType.INT, ZonType.FLOAT
                )
            
            else:
                return self.check_operands_type(
                    ((value_type, expr.value.span),),
                    value_type,
                    False,
                    'not/!',
                    ZonType.BOOL
                )
        
        elif isinstance(expr, VariableExpr):
            symbol = scope.get_symbol(expr.name)
            
            if symbol is None:
                self.diag.emit(
                    ErrorCode.E3001,
                    { "name" : expr.name },
                    [expr.span],
                    [(expr.span, "does not exist in this scope")]
                )
                return ZonType.UNKNOWN
            
            elif symbol.is_empty:
                self.diag.emit(
                    ErrorCode.E3002,
                    { "name" : expr.name },
                    [expr.span],
                    [(expr.span, "has no value at this point")]
                )
                return ZonType.UNKNOWN
            
            return symbol.zontype
        
        elif isinstance(expr, BlockExpr):
            self.check_block_expr(expr, True)
                
            return self.infer_expr(expr.stmts[expr.give_address].value, expr.scope)

        elif isinstance(expr, IfForm):
            if expr.else_branch is None:
                last_branch_span: Span
                
                if not expr.elif_branches is None:
                    last_branch_span = expr.elif_branches[-1].span
                else:
                    last_branch_span = expr.if_branch.span
                
                self.diag.emit(
                    ErrorCode.E3010,
                    None,
                    [last_branch_span],
                    [(Span(last_branch_span.end - 1, last_branch_span.end, self.file_map), "an `else` branch is required here when the if form is used as an expression")]
                )
                return ZonType.UNKNOWN
            
            give_values = self.check_if_form(expr, scope, True)
            
            type_first: ZonType
            errors_span: list[tuple[Span, str]] = []
            codes_span: list[Span] = []
            
            for i in range(len(give_values)):
                if i < 1:
                    type_first = give_values[i][0]
                    continue
                
                if give_values[i][0] != type_first:
                    errors_span.append((give_values[i][1], f"this `give` returns `{give_values[i][0].name.lower()}`, but the if form expects `{type_first.name.lower()}`"))
                    codes_span.append(give_values[i][1])
            
            if len(codes_span) > 0:
                self.diag.emit(
                    ErrorCode.E3011,
                    None,
                    codes_span,
                    errors_span
                )
                return ZonType.UNKNOWN
            else:
                return type_first
                
                
                    
                
                

            
            
        
        
 
        
        
    
            
        