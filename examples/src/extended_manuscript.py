"""Current chapter 1/11/20 literal source adapters; helper contracts in the tests/README.

No copied loop, source branch rewrite, B-number or fence-position dependency.
"""
from .manuscript import function_source, statement_source


def additional_sources(blocks):
    return {
        "minimal_loop": statement_source(blocks, "for step in range(max_steps):", "minimal_loop"),
        "delegate": function_source(blocks, "delegate", replacements=(
            ("assert spec.objective is bounded", "assert objective_is_bounded(spec.objective)"),
            ("assert spec.expected_output_schema exists", "assert spec.expected_output_schema is not None"),
            ("assert spec.acceptance_checks not empty", "assert spec.acceptance_checks"),
            ("except error:", "except Exception as error:"),
        )),
        "integrate": function_source(blocks, "integrate"),
        "frontier_search": statement_source(
            blocks, "frontier = queue([(baseline_state, depth=0)])", "frontier_search", replacements=(
                ("paid(kind, operation):", "def paid(kind, operation):"),
                ("(baseline_state, depth=0)", "(baseline_state, 0)"),
                ("progressed = false", "progressed = False"),
                ("progressed = true", "progressed = True"),
            )),
    }
