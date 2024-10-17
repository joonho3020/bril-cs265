
import sys
import json

from pathlib import Path
sys.path.append(str(Path(f"{__file__}").parent.parent))
from to_ssa import to_ssa
from cfg import add_terminators, block_map, edges, reassemble, add_entry, successors
from form_blocks import form_blocks
from dom import get_dom

def loop_invariant_code_motion_main(ssa):
    for func in ssa['functions']:
        blocks = block_map(form_blocks(func['instrs']))
        add_entry(blocks)
        add_terminators(blocks)
        succ = {name: successors(block[-1]) for name, block in blocks.items()}
        dom = get_dom(succ, list(blocks.keys())[0])

        predecessors, sucessors = edges(blocks)
        natural_loops = find_natural_loops(blocks, predecessors, dom)
        normalize_loops(blocks, predecessors, natural_loops)
        func['instrs'] = reassemble(blocks)

        predecessors, sucessors = edges(blocks)
        loop_invariant_code_motion(blocks, natural_loops, sucessors, predecessors)

        func['instrs'] = reassemble(blocks)
        return ssa

def find_natural_loops(blocks, predecessors, dominators):
    natural_loops = []
    for header in blocks:
        for pred in predecessors[header]:
            if header in dominators[pred]:  # Found a back edge
                loop = [header]
                worklist = [pred]
                while worklist:
                    node = worklist.pop()
                    if node not in loop:
                        loop.append(node)
                        worklist.extend([p for p in predecessors[node] if p not in loop])
                natural_loops.append(loop)
    return natural_loops


def normalize_loops(blocks, predecessors, natural_loops):
    for loop in natural_loops:
        header = next(iter(loop))  # Assume the first block in the loop is the header

        # Add loop header predecessor
        pred_name = f"{header}_pred"
        blocks[pred_name] = [{"op": "jmp", "labels": [header]}]

        # Add exit block
        exit_name = f"{header}_exit"
        blocks[exit_name] = [{"op": "ret"}]

        # Update successors of loop blocks
        for block in loop:
            if block in blocks:
                last_instr = blocks[block][-1]
                if last_instr["op"] in ["jmp", "br"]:
                    for i, label in enumerate(last_instr["labels"]):
                        if label not in loop:
                            last_instr["labels"][i] = exit_name

        # Update predecessors of the loop header to jump to the new predecessor block
        for pred in predecessors[header]:
            if pred not in loop:
                if pred in blocks:
                    last_instr = blocks[pred][-1]
                    if last_instr["op"] in ["jmp", "br"]:
                        for i, label in enumerate(last_instr["labels"]):
                            if label == header:
                                last_instr["labels"][i] = pred_name

def loop_invariant_code_motion(blocks, natural_loops, successors, predecessors):
    for loop in natural_loops:
        header = f"{loop[0]}_pred"
        loop_blocks = set(loop)

        # Find loop exits
        exits = set()
        for block in loop_blocks:
            for succ in successors[block]:
                if succ not in loop_blocks:
                    exits.add(succ)

        # Identify loop-invariant instructions
        invariant_instrs = []
        for block in loop_blocks:
            for instr in blocks[block]:
                if is_loop_invariant(instr, loop_blocks, blocks):
                    invariant_instrs.append((block, instr))

        # Move loop-invariant instructions
        for block, instr in invariant_instrs:
            if dominates_exits(block, exits, predecessors):
                # Move instruction to the loop header
                blocks[header].insert(0, instr)
                blocks[block].remove(instr)

def is_loop_invariant(instr, loop_blocks, blocks):
    if instr['op'] in ['const', 'id']:
        return True
    if 'dest' in instr:
        for block in loop_blocks:
            for other_instr in blocks[block]:
                if other_instr != instr and 'dest' in other_instr and other_instr['dest'] == instr['dest']:
                    return False
    if 'args' in instr:
        for arg in instr['args']:
            if not is_arg_loop_invariant(arg, loop_blocks, blocks):
                return False
    return True

def is_arg_loop_invariant(arg, loop_blocks, blocks):
    for block in loop_blocks:
        for instr in blocks[block]:
            if 'dest' in instr and instr['dest'] == arg:
                return False
    return True

def dominates_exits(block, exits, predecessors):
    visited = set()
    worklist = [block]
    while worklist:
        current = worklist.pop()
        if current in exits:
            return False
        if current not in visited:
            visited.add(current)
            worklist.extend(predecessors[current])
    return True

if __name__ == "__main__":
  bril = json.load(sys.stdin)
  ssa = to_ssa(bril)
  lic = loop_invariant_code_motion_main(ssa)
  json.dump(lic, sys.stdout, indent=2)
