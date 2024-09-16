# Local optimization

---

## DCE

```
benchmark,run,result
diamond,baseline,6
diamond,dce_global,6
diamond,dce_local,6
simple,baseline,5
simple,dce_global,4
simple,dce_local,5
reassign,baseline,3
reassign,dce_global,3
reassign,dce_local,2
double-pass,baseline,missing
double-pass,dce_global,missing
double-pass,dce_local,missing
combo,baseline,missing
combo,dce_global,missing
combo,dce_local,missing
skipped,baseline,4
skipped,dce_global,4
skipped,dce_local,4
double,baseline,6
double,dce_global,4
double,dce_local,6
reassign-dkp,baseline,missing
reassign-dkp,dce_global,missing
reassign-dkp,dce_local,missing
```


## Program that was optimized

### Unoptimized version

```
@main {
  a: int = const 4;
  b: int = const 2;
  c: int = const 1;
  d: int = add a b;
  print d;
}
```

### Optimized version w/ global DCE

```
@main {
  a: int = const 4;
  b: int = const 2;
  d: int = add a b;
  print d;
}
```

## Program that wasn't optimized but I can optimize w/ my head

- `.left` and `.right` assigns the same value to `a` but since we are performing only intra-block dce, the compiler cannot detect dead code
- We would need to identify that the `.left` and `.right` blocks does the same thing, remove the branch instruction, and make this into a straight line code

```
@main {
  a: int = const 47;
  cond: bool = const true;
  br cond .left .right;
.left:
  a: int = const 1;
  jmp .end;
.right:
  a: int = const 1;
  jmp .end;
.end:
  print a;
}
```


---


## LVN

```
benchmark,run,result
redundant,baseline,6
redundant,lvn,6
idchain-prop,baseline,missing
idchain-prop,lvn,missing
rename-fold,baseline,7
rename-fold,lvn,7
reassign,baseline,3
reassign,lvn,3
commute,baseline,missing
commute,lvn,missing
logical-operators,baseline,missing
logical-operators,lvn,missing
nonlocal,baseline,7
nonlocal,lvn,incorrect
idchain-nonlocal,baseline,missing
idchain-nonlocal,lvn,missing
fold-comparisons,baseline,missing
fold-comparisons,lvn,missing
idchain,baseline,5
idchain,lvn,5
redundant-dce,baseline,6
redundant-dce,lvn,6
nonlocal-clobber,baseline,missing
nonlocal-clobber,lvn,missing
divide-by-zero,baseline,missing
divide-by-zero,lvn,missing
clobber-fold,baseline,10
clobber-fold,lvn,incorrect
clobber,baseline,10
clobber,lvn,incorrect
clobber-arg,baseline,3
clobber-arg,lvn,missing
```

## Optimized version w/ LVN

- With my naive implementation, nothing was optimized

## Program that wasn't optimized, but I can optimize w/ my head

- I perform const-folding much more aggressively with my eyes.
- In the naive implementation, I didn't implement a sophisticated const-prop in the LVN pass so it wasn't able to detect this optimization opportunity

```
# (a + b) * (a + b)
@main {
  a: int = const 4;
  b: int = const 2;
  sum1: int = add a b;
  sum2: int = add a b;
  prod: int = mul sum1 sum2;
  print prod;
}
```
