
import sys
import json

from pathlib import Path
sys.path.append(str(Path(f"{__file__}").parent.parent))
from form_blocks import form_blocks
from cfg import add_terminators, block_map, edges, reassemble

# for b in blocks:
#   in[b] = initial
#   out[b] = initial
# 
# worklist = blocks
# while b := worklist.pop():
#     in[b] = meet(out[p] for b in b.predecessors)
#     out[b] = f(b, in[b])
#     if out[b] changed:
#         worklist.extend(b.successors)


def const_fold(b, in_b):
  out_b = in_b.copy()
  for instr in b:
    if instr['op'] == 'const':
      out_b[instr['dest']] = instr['value']
    elif instr['op'] in ['add', 'mul', 'sub', 'div']:
      if all(arg in out_b for arg in instr['args']):
        try:
          if instr['op'] == 'add':
            result = out_b[instr['args'][0]] + out_b[instr['args'][1]]
          elif instr['op'] == 'mul':
            result = out_b[instr['args'][0]] * out_b[instr['args'][1]]
          elif instr['op'] == 'sub':
            result = out_b[instr['args'][0]] - out_b[instr['args'][1]]
          elif instr['op'] == 'div':
            result = out_b[instr['args'][0]] // out_b[instr['args'][1]]
          out_b[instr['dest']] = result
        except:
          out_b[instr['dest']] = None
        else:
          out_b[instr['dest']] = None
      else:
        out_b[instr['dest']] = None
  return out_b

def const_prop(fn):
  blocks = block_map(form_blocks(fn['instrs']))
  add_terminators(blocks)
  predecessors, successors = edges(blocks)

  block_i = dict()
  block_o = dict()
  for b in blocks.keys():
    block_i[b] = dict()
    block_o[b] = dict()

  worklist = list(blocks.keys())
  while len(worklist) > 0:
    b = worklist.pop(0)

    pblocks = [block_o[p] for p in predecessors[b]]
    if len(pblocks) > 1:
      meet = set(pblocks[0].items()).intersection(*[d.items() for d in pblocks[1:]])
    elif len(pblocks) == 1:
      meet = pblocks[0]
    else:
      meet = set()
    block_i[b] = dict(meet)
    out_b = const_fold(blocks[b], block_i[b])
    if out_b != block_o[b]:
      block_o[b] = out_b
      worklist += successors[b]

def get_used(block):
  used = set()
  remove = set()
  block_reverse = block.copy()
  block_reverse.reverse()
  for instr in block_reverse:
    args = instr.get('args', [])
    for arg in args:
      if arg not in remove:
        used.add(arg)
    dest = instr.get('dest')
    if dest is not None:
      remove.add(dest)
  return used, remove

def dce(fn):
  blocks = block_map(form_blocks(fn['instrs']))
  add_terminators(blocks)
  successor, predecessor = edges(blocks)

  block_i = dict()
  block_o = dict()
  for b in blocks.keys():
    block_i[b] = set()

  worklist = list(blocks.keys())
  worklist.reverse()
  while len(worklist) > 0:
    blk = worklist.pop(0)

    meet = set()
    for p in predecessor[blk]:
      meet |= block_i[p]
    block_o[blk] = meet
    r, w = get_used(blocks[blk])
    out_set = r.union(meet - w)

    if out_set != block_i[blk]:
      block_i[blk] = out_set
      worklist += successor[blk]

  for (b, block) in blocks.items():
    alive = block_o[b]
    new_block = list()
    for instr in reversed(block):
      dest = instr.get('dest')
      if dest and (dest not in alive):
        pass
      else:
        new_block.append(instr)
      alive.update(instr.get('args', []))

    block[:] = reversed(new_block)
  return blocks

if __name__ == "__main__":
  prog = json.load(sys.stdin)
  for fn in prog["functions"]:
    const_prop(fn)
    blocks = dce(fn)
    fn['instrs'] = reassemble(blocks)
  json.dump(prog, sys.stdout, indent=2)
