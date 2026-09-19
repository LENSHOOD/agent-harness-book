"""Extract current manuscript fences by unique names, preserving literal control flow.

Only syntax translation: 'function name' or 'name(...)' -> Python 'def'.
The anonymous appendix loop gets a wrapper. Helpers are explicit deterministic doubles.
"""
import ast
import hashlib
from pathlib import Path
import re
import sys
import textwrap


def fences(root):
    blocks = []
    for path in sorted((root / "manuscript").rglob("*.md")):
        active = None
        lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
        for index, line in enumerate(lines):
            if active is None:
                match = re.match(r"^ {0,3}(`{3,}|~{3,})([^\r\n]*)", line)
                if match:
                    marker, info = match.groups()
                    active = index, marker, info.strip().split()[0].lower() if info.strip() else "text"
            else:
                start, marker, language = active
                if re.fullmatch(r" {0,3}" + re.escape(marker[0]) + "{" + str(len(marker)) + r",}\s*", line):
                    raw = "".join(lines[start + 1:index])
                    blocks.append({"file": str(path.relative_to(root)), "line": start + 1,
                                   "language": language, "raw": raw,
                                   "sha256": hashlib.sha256(raw.encode()).hexdigest()})
                    active = None
        if active is not None:
            raise ValueError(f"UNCLOSED_FENCE: {path}:{active[0] + 1}")
    return blocks


def function_source(blocks, name, *, replacements=()):
    pattern = re.compile(r"^(?:(?:function|def) )?" + re.escape(name) + r"\([^\n]*\):\s*$", re.M)
    matches = [(b, m) for b in blocks for m in pattern.finditer(b["raw"])]
    if len(matches) != 1:
        raise ValueError(f"EXPECTED_UNIQUE_FUNCTION {name}, got {len(matches)}")
    block, match = matches[0]
    lines = block["raw"][match.start():].splitlines(keepends=True)
    selected = [lines[0]]
    for line in lines[1:]:
        if line.strip() and not line[0].isspace():
            break
        selected.append(line)
    source = "".join(selected)
    if source.startswith("function "):
        source = "def " + source[len("function "):]
    elif not source.startswith("def "):
        source = "def " + source
    source = translate_exact(source, replacements)
    ast.parse(source)
    metadata = {k: block[k] for k in ("file", "line", "sha256")}
    if replacements:
        metadata["syntax_translations"] = list(replacements)
    return source, metadata


def translate_exact(source, replacements):
    """Explicit one-occurrence DSL translations; drift fails instead of guessing."""
    for before, after in replacements:
        if source.count(before) != 1:
            raise ValueError("EXPECTED_UNIQUE_SYNTAX: " + before)
        source = source.replace(before, after)
    return source


def statement_source(blocks, statement, name, *, replacements=()):
    """Wrap the whole unique fence containing an exact top-level statement."""
    matches = [block for block in blocks if statement in block["raw"].splitlines()]
    if len(matches) != 1 or matches[0]["raw"].splitlines().count(statement) != 1:
        raise ValueError("EXPECTED_UNIQUE_STATEMENT: " + statement)
    block = matches[0]
    source = "def " + name + "():\n" + textwrap.indent(translate_exact(block["raw"], replacements), "    ")
    ast.parse(source)
    return source, {**{k: block[k] for k in ("file", "line", "sha256")},
                    "statement_anchor": statement, "syntax_translations": list(replacements)}


def appendix_loop_source(blocks):
    named = [b for b in blocks if re.search(r"^(?:function |def )?run_attempt\(", b["raw"], re.M)]
    if named:
        return (*function_source(blocks, "run_attempt"), "run_attempt")
    matches = [b for b in blocks if re.search(r"^while attempt.active:\s*$", b["raw"], re.M)]
    if len(matches) != 1:
        raise ValueError("EXPECTED_UNIQUE_APPENDIX_RUN_LOOP")
    block = matches[0]
    source = "def appendix_run_loop():\n" + textwrap.indent(block["raw"], "    ")
    ast.parse(source)
    return source, {k: block[k] for k in ("file", "line", "sha256")}, "appendix_run_loop"


def compile_function(source, name, namespace):
    # Reject imports and dunder access: source execution is only this teaching DSL.
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom, ast.Global, ast.Nonlocal)):
            raise ValueError("UNSUPPORTED_PSEUDOCODE_STATEMENT")
        if isinstance(node, ast.Attribute) and node.attr.startswith("__"):
            raise ValueError("UNSUPPORTED_PSEUDOCODE_ATTRIBUTE")
    constants = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name) and node.id.isupper()}
    scope = {key: key for key in constants}
    scope.update(namespace)
    scope["__builtins__"] = {"len": len, "range": range, "Exception": Exception}
    exec(compile(tree, "<current-manuscript-" + name + ">", "exec"), scope)
    return scope[name]


def bounded_call(function, *args):
    """External watchdog is an audit guard, not a claimed manuscript budget guard."""
    events = 0
    old = sys.gettrace()

    def guard(frame, event, arg):
        nonlocal events
        if event == "line" and frame.f_code.co_filename.startswith("<current-manuscript-"):
            events += 1
            if events > 1000:
                raise RuntimeError("REFERENCE_AUDIT_WATCHDOG: source did not terminate")
        return guard

    try:
        sys.settrace(guard)
        return function(*args)
    finally:
        sys.settrace(old)
