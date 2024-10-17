# Loop invariant code motion

## Steps

- I first converted bril into SSA form using the provided `to_ssa` function
- Next, I found the natural loops by looking at the backedges

```python
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
```

- Instead of just directly performing loop invariant code motion, I decided to normalize the loops to make things easier
    - I just added the loop predecessor block and the loop exit block
    - I decided not to perform loop peeling to make things simple for now

```python
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
```


- Finally, I implemented the `loop_invariant_code_motion` by moving instructions to the loop header if possible
```python
def loop_invariant_code_motion(blocks, natural_loops, successors, predecessors):
    for loop in natural_loops:
        header = loop[0]
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
```


## Results


- Unfortunately, a lot of the results are incorrect :(
- Also, they don't do much optimization. There probably is some bug in my code. Also, the number of instructions actually increased due to SSA conversion

- Looking at some benchmarks:
    - Mat inv: seems like it didn't change that much. Probably because there isn't much to move around when inverting matrices
    ```
    mat-inv,baseline,1044
    mat-inv,loop,1281
    ```

    - Mat mul: Uh oh. The number of instructions increased quite a lot. Again, probably because my code is buggy
    ```
    mat-mul,baseline,1990407
    mat-mul,loop,3504402
    ```

```
benchmark,run,result
sum-divisors,baseline,159
sum-divisors,loop,incorrect
ackermann,baseline,1464231
ackermann,loop,1464232
bitwise-ops,baseline,1690
bitwise-ops,loop,2409
primes-between,baseline,574100
primes-between,loop,incorrect
sum-sq-diff,baseline,3038
sum-sq-diff,loop,incorrect
gcd,baseline,46
gcd,loop,incorrect
mod_inv,baseline,558
mod_inv,loop,incorrect
hanoi,baseline,99
hanoi,loop,152
palindrome,baseline,298
palindrome,loop,incorrect
armstrong,baseline,133
armstrong,loop,incorrect
fizz-buzz,baseline,3652
fizz-buzz,loop,incorrect
orders,baseline,5352
orders,loop,8533
is-decreasing,baseline,127
is-decreasing,loop,242
collatz,baseline,169
collatz,loop,incorrect
lcm,baseline,2326
lcm,loop,incorrect
catalan,baseline,659378
catalan,loop,1023511
perfect,baseline,232
perfect,loop,incorrect
up-arrow,baseline,252
up-arrow,loop,483
pascals-row,baseline,146
pascals-row,loop,281
fact,baseline,229
fact,loop,230
euclid,baseline,563
euclid,loop,880
factors,baseline,72
factors,loop,incorrect
pythagorean_triple,baseline,61518
pythagorean_triple,loop,incorrect
bitshift,baseline,167
bitshift,loop,191
fitsinside,baseline,10
fitsinside,loop,11
reverse,baseline,46
reverse,loop,incorrect
birthday,baseline,484
birthday,loop,923
check-primes,baseline,8468
check-primes,loop,incorrect
digital-root,baseline,247
digital-root,loop,incorrect
sum-bits,baseline,73
sum-bits,loop,incorrect
sum-check,baseline,5018
sum-check,loop,8023
recfact,baseline,104
recfact,loop,175
totient,baseline,253
totient,loop,547
quadratic,baseline,785
quadratic,loop,1447
loopfact,baseline,116
loopfact,loop,incorrect
binary-fmt,baseline,100
binary-fmt,loop,145
relative-primes,baseline,1923
relative-primes,loop,4188
rectangles-area-difference,baseline,14
rectangles-area-difference,loop,19
binary-search,baseline,78
binary-search,loop,85
vsmul,baseline,86036
vsmul,loop,106526
fib,baseline,121
fib,loop,incorrect
sieve,baseline,3482
sieve,loop,incorrect
csrmv,baseline,121202
csrmv,loop,184080
quicksort,baseline,264
quicksort,loop,422
major-elm,baseline,47
major-elm,loop,incorrect
adj2csr,baseline,56629
adj2csr,loop,91066
quickselect,baseline,279
quickselect,loop,459
adler32,baseline,6851
adler32,loop,11887
primitive-root,baseline,11029
primitive-root,loop,12328
bubblesort,baseline,253
bubblesort,loop,361
max-subarray,baseline,193
max-subarray,loop,272
dot-product,baseline,88
dot-product,loop,incorrect
quicksort-hoare,baseline,27333
quicksort-hoare,loop,40667
eight-queens,baseline,1006454
eight-queens,loop,1845093
two-sum,baseline,98
two-sum,loop,179
mat-mul,baseline,1990407
mat-mul,loop,3504402
euler,baseline,1908
euler,loop,3264
norm,baseline,505
norm,loop,incorrect
ray-sphere-intersection,baseline,142
ray-sphere-intersection,loop,143
cordic,baseline,517
cordic,loop,3613
riemann,baseline,298
riemann,loop,473
mandelbrot,baseline,2720947
mandelbrot,loop,incorrect
sqrt,baseline,322
sqrt,loop,incorrect
pow,baseline,36
pow,loop,65
n_root,baseline,733
n_root,loop,incorrect
newton,baseline,217
newton,loop,incorrect
conjugate-gradient,baseline,1999
conjugate-gradient,loop,incorrect
leibniz,baseline,12499997
leibniz,loop,incorrect
function_call,baseline,timeout
function_call,loop,timeout
dead-branch,baseline,1196
dead-branch,loop,incorrect
cholesky,baseline,3761
cholesky,loop,7730
mat-inv,baseline,1044
mat-inv,loop,1281
```
