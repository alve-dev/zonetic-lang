from .severity import Severity
from zonc.location_file import FileMap
from zonc.location_file import Span
from .diagnostic import Diagnostic

class DiagnosticRenderer:
    def __init__(self, code: str, file_map: FileMap):
        self.code = code
        self.file_map = file_map
    
    
    def get_lines(self, line_start: int, line_end: int) -> list[str]:
        return self.code[self.file_map.line_starts[line_start-1] : self.file_map.line_starts[line_end]].split('\n')
    
    
    def note_clean(self, text: str, num_line: int) -> str:
        if not text or not text.strip():
            return ""
        
        lines = text.splitlines()
        while lines and not lines[0].strip(): lines.pop(0)
        while lines and not lines[-1].strip(): lines.pop(-1)
        
        if not lines: return ""

        indent_base = len(lines[0]) - len(lines[0].lstrip())

        cleaned_lines = []
        for i, line in enumerate(lines):
            content = line[indent_base:] if len(line) >= indent_base else line.lstrip()
            
            if i == 0:
                cleaned_lines.append(content.rstrip())
            else:
                cleaned_lines.append((" " * (9 + num_line)) + content.lstrip())
                
        return "\n".join(cleaned_lines)
    
    
    def render(self, diag: Diagnostic, is_repeated: bool) -> str:
        err_def = diag.error_definition
        args = diag.args
        span_codes: list[Span] = diag.span_code
        span_error = diag.span_errors
        name_file  = diag.name_file
        msg_rendered = []
        
        # Formateo de argumentos
        if not args is None:
            msg = err_def.message.format_map(args)
            
        else:
            msg = err_def.message
        
        # Header de error
        if err_def.severity == Severity.ERROR:
            msg_rendered.append(f"error[{err_def.error_code.name}]: {msg}\n--> {name_file}:{span_error[0][0].line_start}:{span_error[0][0].column_start}\n")
        else:
            msg_rendered.append(f"warning[{err_def.error_code.name}]: {msg}\n--> {name_file}:{span_error[0][0].line_end}:{span_error[0][0].column_end}\n")
        
        num_lines = []
        for i in range(len(span_codes)):
            num_lines.append(span_codes[i].line_end)
        
        num_lines.sort()
        size_line = len(str(num_lines[-1]))
        
        for i in range(len(span_codes)):
            # Lineas de todo el codigo de inicio a final
            lines = self.get_lines(span_codes[i].line_start, span_codes[i].line_end)
            
            if len(self.file_map.line_starts) != span_codes[i].line_end + 1:
                lines.pop()
            
            space_line = ' ' * size_line
            
            # Las tres formas de mostrar errores de zonetic
            if len(lines) == 1:
                msg_rendered.append(f"{span_codes[i].line_start} {' ' * (size_line - (len(str(span_codes[i].line_start))))}| {lines[0]}\n")
                paddings = " " * (span_error[i][0].column_start)
                pointers = "^" * (span_error[i][0].column_end - span_error[i][0].column_start)
                msg_rendered.append(f"{space_line} |{paddings}{pointers}")
                
                if not(span_error[i][1] is None):
                    msg_rendered.append(f"-- {span_error[i][1].format_map(args)}")
                
            elif len(lines) <= 6:
                count = 0
                for line in lines:
                    msg_rendered.append(f"{span_codes[i].line_start+count} {' ' * (size_line - (len(str(span_codes[i].line_start))))}| {line}\n")
                    count += 1
                    
                paddings = " " * (span_error[i][0].column_start)
                pointers = "^" * (span_error[i][0].column_end - span_error[i][0].column_start)
                msg_rendered.append(f"{space_line} |{paddings}{pointers}")
                
                if not(span_error[i][1] is None):
                    msg_rendered.append(f"-- {span_error[i][1].format_map(args)}")
            
            else:
                count = 0
                for line in lines:
                    msg_rendered.append(f"{span_codes[i].line_start+count} {' ' * (size_line - len(str(span_codes[i].line_start)))}| {line}\n")
                    
                    if count == 2:
                        break
                        
                    count += 1
                
                msg_rendered.append(f"{space_line} |\n{space_line} ...|\n{space_line} |\n")
                msg_rendered.append(f"{span_codes[i].line_end} | {lines[span_codes[i].line_end-span_codes[i].line_start]}\n")
                paddings = " " * (span_error[i][0].column_start)
                pointers = "^" * (span_error[i][0].column_end - span_error[i][0].column_start)
                msg_rendered.append(f"{space_line} |{paddings}{pointers}")
                
                if not(span_error[i][1] is None):
                    msg_rendered.append(f"-- {span_error[i][1].format_map(args)}")
            
            if i != len(span_codes)-1:
                msg_rendered.append(f"\n{space_line} |\n{space_line} ...|\n{space_line} |\n")
            
        if not is_repeated:
            msg_rendered.append(f"\n{space_line} |\n")
            if args is None:
                msg_rendered.append(f"{space_line} = note: {self.note_clean(err_def.note, size_line)}\n\n")
                msg_rendered.append(f"{err_def.zonny}")
            else:
                msg_rendered.append(f"{space_line} = note: {self.note_clean(err_def.note.format_map(args), size_line)}\n\n")
                msg_rendered.append(f"{err_def.zonny.format_map(args)}")
                
                
        return "".join(msg_rendered)