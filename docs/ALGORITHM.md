# Defined semantics, not an unspecified promise of fairness

For each positive-weight recipient i, let c_i be its cap and w_i its weight.
Zero-weight recipients are excluded. Set T = min(budget, sum of eligible caps).
The real-valued ideal is q_i = min(c_i, lambda*w_i), where lambda makes sum(q)=T.
When T=0 all awards are zero; excess over the eligible capacity is unallocated.

## Implementation

1. Validate the fixed-size API: count 1..16, unused suffix zero.
2. Start active recipients with positive weight and positive cap.
3. If `remaining * weight[i] >= cap[i] * total_weight`, award that cap and remove
   the recipient. Subtract its cap and weight immediately before checking the
   next recipient. Repeat until a full pass removes nobody or no weight remains.
   Removal cannot lower the common water level, so a recipient already capped
   remains correctly capped. Each changing pass removes at least one recipient.
4. For active recipients compute the quotient and remainder of
   `remaining * weight[i] / total_weight` using integer arithmetic.
5. Award one extra unit to the largest remainders until the dust is exhausted,
   using ascending original input index for ties. Each recipient is eligible
   for at most one rounding unit.

In the stable active set, q_i < c_i. Since c_i is integral, ceil(q_i) <= c_i.
Thus rounding cannot exceed a cap. The sum of fractional parts is an integer
smaller than the number of active recipients, so fewer than 16 extra units are
needed. Conservation follows from awarding all T units and returning budget-T.

## Integer bounds

Budget and individual caps are at most 2^128-1; weights at most 2^64-1.
There are at most 16 recipients:

- summed capacity < 2^132;
- summed weight < 2^68;
- remaining*weight < 2^192;
- cap*total_weight < 2^196.

All these intermediates are u256. T and every individual award are bounded by
the original u128 budget. Fe checked downcasts retain a runtime guard rather
than relying only on the proof. Ordinary checked arithmetic remains enabled.

## Counterexample to budget monotonicity

With weights [1500,1500,900,500,500,200] and caps [100,100,100,100,100,100]:

- Budget 25 -> [7,7,4,3,3,1]
- Budget 26 -> [8,8,5,2,2,1]

Recipients four and five lose a unit. This is the Alabama paradox of Hamilton
rounding, deliberately retained as a regression fixture, not hidden as a bug.
Do not use this calculator as an incremental vesting rule.

Input order can affect tied results. A caller that controls order, weights,
caps or identity splitting can influence allocations. No mechanism-level
strategyproofness, Sybil resistance or broad fairness theorem is claimed.
