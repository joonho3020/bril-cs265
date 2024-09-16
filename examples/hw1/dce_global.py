import json
import sys

# used = {}
# for instr in func:
#     used += instr.args
# 
# for instr in func:
#     if instr.dest not in used and is_pure(instr):
#         del instr

def pure(op):
  return op != 'call' or op != 'print'

def global_dce(fn):
  instrs = fn['instrs']
  converge = False
  while not converge:
    used = set()
    removed = list()

    for inst in instrs:
      if 'args' in inst:
        for arg in inst['args']:
          used.add(arg)

    for inst in instrs:
      if not ('dest' in inst and inst['dest'] not in used and pure(inst['op'])):
        removed.append(inst)

    converge =  len(removed) >= len(instrs)
    instrs = removed
  return instrs

if __name__ == "__main__":
    prog = json.load(sys.stdin)
    for fn in prog['functions']:
        fn['instrs'] = global_dce(fn)
    json.dump(prog, sys.stdout, indent=2)
