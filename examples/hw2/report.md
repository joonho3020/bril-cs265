# Global optimization

---

```
for b in blocks:
  in[b] = initial
  out[b] = initial

worklist = blocks
while b := worklist.pop():
    in[b] = meet(out[p] for b in b.predecessors)
    out[b] = f(b, in[b])
    if out[b] changed:
        worklist.extend(b.successors)
```

## Const folding

- I essentially implemented the above pseudo code

```python
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
```

- `meet` is a intersection for const folding
- The transfer function is as below:
    - It basically checks if a instruction has a operation with a constant, and tries folding it in with other arithmetic operations

```python
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
```


---

## DCE

```python
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
```

- Very similar except that I swapped `block_i` (input to block) and `block_o` (output from block) to perform backward analysis
- The `meet` function is a union now
- The transfer function is computing the used variables starting from the end of the block:
- After performing the analysis, I actually removed the unsed instructions

```python
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
```


---

## Benchmark results

- Benchmarks that my pass did better than the baseline: eight-queens (28975 instructions vs baseline)
- Benchmarks that my pass did not do well: matmut (145107 more instructions vs baseline)
- In total, my pass has 3% more instructions compared to the baseline version

```
benchmark,run,result
sum-divisors,baseline,159
sum-divisors,global_const_fold,160
ackermann,baseline,1464231
ackermann,global_const_fold,1464232
bitwise-ops,baseline,1690
bitwise-ops,global_const_fold,1693
primes-between,baseline,574100
primes-between,global_const_fold,575268
sum-sq-diff,baseline,3038
sum-sq-diff,global_const_fold,3039
gcd,baseline,46
gcd,global_const_fold,48
mod_inv,baseline,558
mod_inv,global_const_fold,565
hanoi,baseline,99
hanoi,global_const_fold,107
palindrome,baseline,298
palindrome,global_const_fold,304
armstrong,baseline,133
armstrong,global_const_fold,135
fizz-buzz,baseline,3652
fizz-buzz,global_const_fold,3701
orders,baseline,5352
orders,global_const_fold,5448
is-decreasing,baseline,127
is-decreasing,global_const_fold,129
collatz,baseline,169
collatz,global_const_fold,174
lcm,baseline,2326
lcm,global_const_fold,2328
catalan,baseline,659378
catalan,global_const_fold,679062
perfect,baseline,232
perfect,global_const_fold,239
up-arrow,baseline,252
up-arrow,global_const_fold,266
pascals-row,baseline,146
pascals-row,global_const_fold,incorrect
fact,baseline,229
fact,global_const_fold,229
euclid,baseline,563
euclid,global_const_fold,564
factors,baseline,72
factors,global_const_fold,74
pythagorean_triple,baseline,61518
pythagorean_triple,global_const_fold,61647
bitshift,baseline,167
bitshift,global_const_fold,171
fitsinside,baseline,10
fitsinside,global_const_fold,11
reverse,baseline,46
reverse,global_const_fold,48
birthday,baseline,484
birthday,global_const_fold,485
check-primes,baseline,8468
check-primes,global_const_fold,8867
digital-root,baseline,247
digital-root,global_const_fold,258
sum-bits,baseline,73
sum-bits,global_const_fold,74
sum-check,baseline,5018
sum-check,global_const_fold,5020
recfact,baseline,104
recfact,global_const_fold,111
totient,baseline,253
totient,global_const_fold,259
quadratic,baseline,785
quadratic,global_const_fold,829
loopfact,baseline,116
loopfact,global_const_fold,117
binary-fmt,baseline,100
binary-fmt,global_const_fold,118
relative-primes,baseline,1923
relative-primes,global_const_fold,2084
rectangles-area-difference,baseline,14
rectangles-area-difference,global_const_fold,16
binary-search,baseline,78
binary-search,global_const_fold,82
vsmul,baseline,86036
vsmul,global_const_fold,90136
fib,baseline,121
fib,global_const_fold,122
sieve,baseline,3482
sieve,global_const_fold,3535
csrmv,baseline,121202
csrmv,global_const_fold,122374
quicksort,baseline,264
quicksort,global_const_fold,278
major-elm,baseline,47
major-elm,global_const_fold,49
adj2csr,baseline,56629
adj2csr,global_const_fold,61563
quickselect,baseline,279
quickselect,global_const_fold,295
adler32,baseline,6851
adler32,global_const_fold,6876
primitive-root,baseline,11029
primitive-root,global_const_fold,11528
bubblesort,baseline,253
bubblesort,global_const_fold,284
max-subarray,baseline,193
max-subarray,global_const_fold,195
dot-product,baseline,88
dot-product,global_const_fold,90
quicksort-hoare,baseline,27333
quicksort-hoare,global_const_fold,29293
eight-queens,baseline,1006454
eight-queens,global_const_fold,977479
two-sum,baseline,98
two-sum,global_const_fold,91
mat-mul,baseline,1990407
mat-mul,global_const_fold,2135514
euler,baseline,1908
euler,global_const_fold,2045
norm,baseline,505
norm,global_const_fold,533
ray-sphere-intersection,baseline,142
ray-sphere-intersection,global_const_fold,143
cordic,baseline,517
cordic,global_const_fold,incorrect
riemann,baseline,298
riemann,global_const_fold,302
mandelbrot,baseline,2720947
mandelbrot,global_const_fold,2724640
sqrt,baseline,322
sqrt,global_const_fold,331
pow,baseline,36
pow,global_const_fold,37
n_root,baseline,733
n_root,global_const_fold,755
newton,baseline,217
newton,global_const_fold,219
conjugate-gradient,baseline,1999
conjugate-gradient,global_const_fold,2051
leibniz,baseline,12499997
leibniz,global_const_fold,12999999
function_call,baseline,timeout
function_call,global_const_fold,timeout
dead-branch,baseline,1196
dead-branch,global_const_fold,1198
cholesky,baseline,3761
cholesky,global_const_fold,3998
mat-inv,baseline,1044
mat-inv,global_const_fold,1061
```
