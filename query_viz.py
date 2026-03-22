"""
Query Execution Model Visualizer — renders iterator trees, vectorized pipelines,
and JIT compilation flows using graphviz.
"""

from __future__ import annotations
import subprocess
import shutil
import os


def _render_dot(dot_src: str, filename: str, output_dir: str, fmt: str = "png") -> str:
    dot_path = os.path.join(output_dir, f"{filename}.dot")
    img_path = os.path.join(output_dir, f"{filename}.{fmt}")
    with open(dot_path, "w") as f:
        f.write(dot_src)
    if shutil.which("dot"):
        subprocess.run(["dot", f"-T{fmt}", dot_path, "-o", img_path],
                       check=True, capture_output=True)
        return img_path
    return dot_path


def render_volcano_model(
    operators: list[dict],  # [{name, description}] bottom-to-top
    filename: str = "volcano",
    output_dir: str = ".",
    title: str = "Iterator (Volcano) Model — Pull-Based, Tuple-at-a-Time",
) -> str:
    """Render the Volcano/iterator execution model."""
    dot = ['digraph Volcano {']
    dot.append('    rankdir=BT;')  # bottom to top
    dot.append('    node [fontname="Courier", fontsize=10];')
    dot.append(f'    labelloc="t"; label="{title}"; fontsize=13; fontname="Helvetica Bold";')
    dot.append('')

    for i, op in enumerate(operators):
        color = op.get("color", "lightblue")
        dot.append(f'    op{i} [shape=box, style="filled,rounded", fillcolor="{color}", '
                   f'label="{op["name"]}\\n{op.get("description", "")}"];')
        if i > 0:
            dot.append(f'    op{i-1} -> op{i} [label="  next() → 1 tuple", '
                       f'color=blue, style=bold];')

    # Add annotation
    dot.append(f'    note [shape=plaintext, label='
               f'"Each next() call:\\n'
               f'1. Virtual function dispatch\\n'
               f'2. Process ONE tuple\\n'
               f'3. Return to caller\\n'
               f'\\n'
               f'N tuples = N × next() calls\\n'
               f'per operator in the tree"];')

    dot.append('}')
    return _render_dot("\n".join(dot), filename, output_dir)


def render_vectorized_model(
    operators: list[dict],
    batch_size: int = 1024,
    filename: str = "vectorized",
    output_dir: str = ".",
    title: str = "Vectorized Model — Pull-Based, Batch-at-a-Time",
) -> str:
    """Render the vectorized execution model."""
    dot = ['digraph Vectorized {']
    dot.append('    rankdir=BT;')
    dot.append('    node [fontname="Courier", fontsize=10];')
    dot.append(f'    labelloc="t"; label="{title}"; fontsize=13; fontname="Helvetica Bold";')
    dot.append('')

    for i, op in enumerate(operators):
        color = op.get("color", "lightgreen")
        dot.append(f'    op{i} [shape=box, style="filled,rounded", fillcolor="{color}", '
                   f'label="{op["name"]}\\n{op.get("description", "")}"];')
        if i > 0:
            dot.append(f'    op{i-1} -> op{i} [label="  next() → {batch_size} tuples", '
                       f'color=darkgreen, style=bold];')

    dot.append(f'    note [shape=plaintext, label='
               f'"Each next() call:\\n'
               f'1. Virtual function dispatch (once)\\n'
               f'2. Process {batch_size} tuples in tight loop\\n'
               f'3. Return vector/batch to caller\\n'
               f'\\n'
               f'N tuples = N/{batch_size} × next() calls\\n'
               f'Tight loops → SIMD + cache friendly"];')

    dot.append('}')
    return _render_dot("\n".join(dot), filename, output_dir)


def render_jit_model(
    query: str,
    pipeline_stages: list[str],
    filename: str = "jit",
    output_dir: str = ".",
    title: str = "JIT Compilation — Push-Based, Compiled Pipeline",
) -> str:
    """Render the JIT/code-generation execution model."""
    dot = ['digraph JIT {']
    dot.append('    rankdir=TB;')
    dot.append('    node [fontname="Courier", fontsize=10];')
    dot.append(f'    labelloc="t"; label="{title}"; fontsize=13; fontname="Helvetica Bold";')
    dot.append('')

    # Query
    dot.append(f'    query [shape=box, style="filled,rounded", fillcolor=lightyellow, '
               f'label="SQL Query:\\n{query}"];')

    # Code generation
    dot.append(f'    codegen [shape=box, style="filled,rounded", fillcolor=orange, '
               f'label="JIT Compiler\\n(generate native code)"];')
    dot.append('    query -> codegen [label="  parse + optimize"];')

    # Generated pipeline
    dot.append('    subgraph cluster_pipeline {')
    dot.append('        label="Generated Native Code (no virtual calls)";')
    dot.append('        style=rounded; color=red; fontsize=11;')

    for i, stage in enumerate(pipeline_stages):
        dot.append(f'        stage{i} [shape=box, style=filled, fillcolor=salmon, '
                   f'label="{stage}"];')
        if i > 0:
            dot.append(f'        stage{i-1} -> stage{i} [label="  push", style=bold];')

    dot.append('    }')

    dot.append(f'    codegen -> stage0 [label="  compile"];')

    dot.append(f'    note [shape=plaintext, label='
               f'"Push-based: data flows DOWN\\n'
               f'No virtual dispatch\\n'
               f'No interpretation overhead\\n'
               f'Tight loop with inlined operators\\n'
               f'CPU pipeline-friendly"];')

    dot.append('}')
    return _render_dot("\n".join(dot), filename, output_dir)


def render_three_models_comparison(
    filename: str = "three_models",
    output_dir: str = ".",
) -> str:
    """Render side-by-side comparison of all three models."""
    dot = ['digraph ThreeModels {']
    dot.append('    rankdir=TB;')
    dot.append('    node [fontname="Courier", fontsize=9];')
    dot.append('    labelloc="t"; label="Three Execution Models Compared"; '
               'fontsize=13; fontname="Helvetica Bold";')
    dot.append('')

    # Iterator
    dot.append('    subgraph cluster_iter {')
    dot.append('        label="Iterator (Volcano)"; style=rounded; color=blue; fontsize=11;')
    dot.append('        i_scan [shape=box, style=filled, fillcolor=lightblue, label="Scan"];')
    dot.append('        i_filter [shape=box, style=filled, fillcolor=lightblue, label="Filter"];')
    dot.append('        i_agg [shape=box, style=filled, fillcolor=lightblue, label="Aggregate"];')
    dot.append('        i_scan -> i_filter -> i_agg [label=" 1 row", color=blue];')
    dot.append('        i_note [shape=plaintext, fontsize=8, label='
               '"PULL: 1 tuple/call\\nvfunc per operator\\nN×3 calls for N rows"];')
    dot.append('    }')

    # Vectorized
    dot.append('    subgraph cluster_vec {')
    dot.append('        label="Vectorized"; style=rounded; color=darkgreen; fontsize=11;')
    dot.append('        v_scan [shape=box, style=filled, fillcolor=lightgreen, label="Scan"];')
    dot.append('        v_filter [shape=box, style=filled, fillcolor=lightgreen, label="Filter"];')
    dot.append('        v_agg [shape=box, style=filled, fillcolor=lightgreen, label="Aggregate"];')
    dot.append('        v_scan -> v_filter -> v_agg [label=" 1024 rows", color=darkgreen];')
    dot.append('        v_note [shape=plaintext, fontsize=8, label='
               '"PULL: 1024 tuples/call\\nvfunc per batch\\nN/1024×3 calls"];')
    dot.append('    }')

    # JIT
    dot.append('    subgraph cluster_jit {')
    dot.append('        label="JIT Compiled"; style=rounded; color=red; fontsize=11;')
    dot.append('        j_code [shape=box, style=filled, fillcolor=salmon, '
               'label="for row in table:\\n  if filter(row):\\n    agg += row.sal"];')
    dot.append('        j_note [shape=plaintext, fontsize=8, label='
               '"PUSH: fused pipeline\\nzero vfunc calls\\ncompiler-optimized loop"];')
    dot.append('    }')

    dot.append('}')
    return _render_dot("\n".join(dot), filename, output_dir)


def render_cache_behavior(
    filename: str = "cache_behavior",
    output_dir: str = ".",
) -> str:
    """Render CPU cache behavior for iterator vs vectorized."""
    dot = ['digraph CacheBehavior {']
    dot.append('    rankdir=TB;')
    dot.append('    node [fontname="Courier", fontsize=10];')
    dot.append('    labelloc="t"; label="CPU Cache Behavior"; '
               'fontsize=13; fontname="Helvetica Bold";')
    dot.append('')

    # Iterator path
    dot.append('    subgraph cluster_iter {')
    dot.append('        label="Iterator: 1 tuple at a time"; style=rounded; color=blue;')
    dot.append('        it_scan [shape=box, style=filled, fillcolor=lightblue, '
               'label="Scan\\nload row 0"];')
    dot.append('        it_filter [shape=box, style=filled, fillcolor=lightblue, '
               'label="Filter\\ncheck row 0"];')
    dot.append('        it_agg [shape=box, style=filled, fillcolor=lightblue, '
               'label="Aggregate\\nadd row 0"];')
    dot.append('        it_back [shape=box, style=filled, fillcolor=salmon, '
               'label="Back to Scan\\nrow 0 evicted from cache!\\nload row 1..."];')
    dot.append('        it_scan -> it_filter -> it_agg -> it_back [color=blue];')
    dot.append('        it_note [shape=plaintext, label='
               '"Cache thrashing:\\neach operator touches\\ndifferent memory\\n'
               '→ constant cache misses"];')
    dot.append('    }')

    # Vectorized path
    dot.append('    subgraph cluster_vec {')
    dot.append('        label="Vectorized: 1024 tuples at a time"; style=rounded; color=darkgreen;')
    dot.append('        v_scan [shape=box, style=filled, fillcolor=lightgreen, '
               'label="Scan\\nload rows 0-1023\\ninto L1/L2 cache"];')
    dot.append('        v_filter [shape=box, style=filled, fillcolor=lightgreen, '
               'label="Filter\\ncheck rows 0-1023\\n(still in cache!)"];')
    dot.append('        v_agg [shape=box, style=filled, fillcolor=lightgreen, '
               'label="Aggregate\\nadd rows 0-1023\\n(still in cache!)"];')
    dot.append('        v_next [shape=box, style=filled, fillcolor=lightgreen, '
               'label="Next batch\\nload rows 1024-2047"];')
    dot.append('        v_scan -> v_filter -> v_agg -> v_next [color=darkgreen];')
    dot.append('        v_note [shape=plaintext, label='
               '"Cache friendly:\\nsame data stays in cache\\n'
               'across all operators\\n→ minimal cache misses"];')
    dot.append('    }')

    dot.append('}')
    return _render_dot("\n".join(dot), filename, output_dir)
