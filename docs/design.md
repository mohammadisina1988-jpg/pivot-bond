# Protocol

## Consensus boundary

Signed bidder action → frozen public URL/SHA-256 → contract fetches complete prose → leader interprets all exact-bundle totals → validators independently re-fetch, hash-check and interpret → exact value-vector agreement plus a full-source audit → bidder signs exact values and reserves credits → permissionless counterfactual allocation and atomic ledger changes.

There is no frontend/backend authority. The source author supplies willingness-to-pay declarations. These are preferences, not assertions that an external service was delivered. A hash binds bytes; bidder signatures plus explicit vector consent bind those bytes and their interpretation to the bidder. Validators do not see just hashes.

Documents are JSON envelopes containing only `auction`, `bidder` and prose `clauses`. URLs must be HTTPS raw GitHub files within the constructor's fixed repository, a full commit SHA and one fixture basename. The path is a bounded demonstration source policy, not a proof that GitHub content is independently true. Response size, source keys, scope, clause lengths and duplicate JSON keys are checked.

The extraction returns an amount or null, with clause anchors, for masks 1 through `2^m-1`. Item index i is bit `1<<i`. For `[Amber,Cobalt]`, the entries are `[Amber], [Cobalt], [Amber,Cobalt]`. No monotonicity or additivity is presumed. A bundle value is a total, never an inferred surcharge. Explicit additive/default rules are permitted. Historical estimates and conditional offers do not establish current unconditional bids.

Validators compare every integer and null exactly. They separately audit the leader's entries and anchors against the complete source, including zero/null entries. Numeric answers need anchors; null may use empty anchors but still requires full-source audit. Audit answers must be actual JSON booleans, all true. No confidence tolerance exists. Malformed model outputs force disagreement/rotation; deterministic external errors compare exactly; both transient errors may agree on a failed transaction. No failed transaction can approve or allocate a right.

An invalid extraction schema gets one bounded model repair request with the complete task and prior output. The same strict schema applies afterwards; strings such as `"UNKNOWN"` are not silently coerced to null. A second malformed output raises an LLM error with bounded diagnostic output. Repair never substitutes for independent interpretation or the full-source audit.

## State and authority

The seller is deployer and must be distinct from all 2–4 bidders. Constructor endowments are 0–10,000 native credits per bidder. The seller initially owns each of 1–3 unique rights. Bid amounts are 0–1,000. Every bidder gets one immutable signed source commitment; anyone may interpret it once while OPEN. APPROVAL requires a complete interpreted vector, its exact signed integer copy, and sufficient balance for its maximum amount. Approval cannot be repeated or changed.

All approvals make READY. Any bidder can abort OPEN or READY; all escrow returns and the seller keeps all original rights. This veto is an explicit liveness/fairness choice, with a race against permissionless settlement. There is no deadline or seller override. Settled and aborted instances cannot settle again. Only the current native owner can transfer a terminal right to a different nonzero address.

## Allocation and counterfactual charges

For n bidders and m items enumerate `(n+1)^m` ownership strings; owner n means unsold. Each bidder receives a disjoint mask and values that exact mask. Empty value is zero. Maximize the sum of declared values. Tie policy: fewer allocated rights, then lexicographically smaller owner vector in item order. This leaves zero-welfare rights with the seller and is independent of bid amounts.

For each bidder i, solve again with i unable to receive any item. Store the full maximizing counterfactual allocation, not just its score. Charge

`payment_i = welfare_without_i - (selected_welfare - value_i(selected_mask_i))`.

Nonnegative normalized values imply `0 <= payment_i <= value_i(selected_mask_i) <= max_bid_i`. The contract explicitly checks those bounds and the funded escrow. Settlement atomically changes every owner, credits each bidder's unused reserve and increases the seller's credit balance by total charges. At every credit mutation:

`sum(bidder_balances) + sum(escrows) + seller_credits == sum(initial_endowments)`.

The maximum case enumerates 125 allocations for the choice and another 125 per removed bidder. All integer arithmetic; no generated code, floating point, external optimizer or owner-chosen winning portfolio.

### Worked counterfactual

Bidder A values only the pair at 18. B values Amber at 11 and the pair at 11. C values Cobalt at 10 and the pair at 10; the other singleton values are zero. B and C win with welfare 21. Without B, A could create welfare 18; C gets welfare 10 in the selected allocation, so B pays `18-10=8`. C pays `18-11=7`. A loses and pays zero. Increasing A's pair value to 24 makes A win both rights and pay `21-0=21`. Neither case is a uniform-price marginal-order matching problem.

## Distinct mechanism

CrossLedger matches two-sided marginal limit orders at one uniform price. EvidenceCover minimizes procurement cost for requirement coverage. EndowSwap clears endowed ordinal barter cycles. PivotBond instead allocates indivisible bundle-valued rights by welfare and computes separate bidder-removal externalities; the paid price can differ from a winning declaration and from every singleton bid. It has no graph proposal, versioned transition owner, certificate lifecycle or service-delivery claim.

## Practical limits

VCG is not Sybil-proof, collusion-proof, budget-balanced redistribution or a claim of truthful prose. Fixed invitations and source scope do not solve identity. Documents are public and approval/veto is sequential, so no end-to-end dominant-strategy claim is made. Tests of fixed-profile quasilinear deviations concern only the mathematical settlement function, without budgets, veto, privacy or strategic participation.

No real asset is escrowed. Native credits cannot be redeemed or withdrawn as GEN. Seller revenue is an internal balance; adding real payment custody would require a separate funded integration and security review. Synthetic documents exercise parsing, including old figures, conditional amounts and bundle totals, not production issuer trust. GitHub/web/model availability and exact semantic agreement can block interpretation; bidders can abort to recover reserves.
