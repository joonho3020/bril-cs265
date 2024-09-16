import json
import sys

from pathlib import Path
sys.path.append(str(Path(f"{__file__}").parent.parent))
from form_blocks import form_blocks

class LVN:
    def __init__(self):
        self.value_table = {}
        self.var_map = {}
        self.next_value_num = 0

    def get_value_number(self, expr):
        if expr in self.value_table:
            return self.value_table[expr]
        else:
            # Assign a new value number
            value_num = self.next_value_num
            self.value_table[expr] = value_num
            self.next_value_num += 1
            return value_num

    def process_instruction(self, instr):
        if instr["op"] == "const":
            value_num = self.get_value_number(("const", instr["value"]))
            self.var_map[value_num] = instr["dest"]
        elif instr["op"] in {"add", "mul", "sub", "div"}:
            args = tuple(instr["args"])
            expr = (instr["op"], args)
            value_num = self.get_value_number(expr)
            if value_num in self.var_map:
                # Expression has been computed before, replace it
                instr["op"] = "id"
                instr["args"] = [self.var_map[value_num]]
            else:
                # New expression, update variable map
                self.var_map[value_num] = instr["dest"]

    def lvn(self, block):
        for instr in block:
            self.process_instruction(instr)
        return block

if __name__ == "__main__":
    prog = json.load(sys.stdin)
    for fn in prog["functions"]:
      blocks = form_blocks(fn['instrs'])
      new_fn = []
      for block in blocks:
        lvn = LVN()
        new_block = lvn.lvn(block)
        for inst in block:
          new_fn.append(inst)
      fn['instrs'] = new_fn
    json.dump(prog, sys.stdout, indent=2)
