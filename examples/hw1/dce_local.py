import json
import sys

from pathlib import Path
sys.path.append(str(Path(f"{__file__}").parent.parent))
from form_blocks import form_blocks

# unused: {var: inst} = {}
# for inst in block:
#     # if it's used, it's not unused
#     for use in inst.uses:
#         del unused[use]
#     if inst.dest 
#         # if this inst defines something
#         # we can kill the unused definition
#         if unused[inst.dest]:
#             remove unused[inst.dest]
#         # mark this def as unused for now
#         unused[inst.dest] = inst


def local_dce(block):
  converge = False

  while not converge:
    to_remove = set()
    unused = dict()
    for (i, instr) in enumerate(block):
        if 'args' in instr:
          for arg in instr['args']:
            if arg in unused:
              unused.pop(arg)
        if 'dest' in instr:
            if instr['dest'] in unused:
              to_remove.add(unused[instr['dest']])
            unused[instr['dest']] = i

    new_block = [inst for idx, inst in enumerate(block) if idx not in to_remove]

    converge =  len(new_block) >= len(block)
    block = new_block

  return block

if __name__ == "__main__":
    prog = json.load(sys.stdin)
    for fn in prog["functions"]:
      blocks = form_blocks(fn['instrs'])
      ldce_fn = list()
      for block in blocks:
        ldce_block = local_dce(block)
        for inst in ldce_block:
          ldce_fn.append(inst)
      fn['instrs'] = ldce_fn
    json.dump(prog, sys.stdout, indent=2)
