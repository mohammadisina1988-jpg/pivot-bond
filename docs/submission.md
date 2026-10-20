Category: Builder → Intelligent Contracts

Title: PivotBond: Consensus bundle bids with counterfactual payments

Notes / Description:

> PivotBond is a GenLayer combinatorial VCG auction for native rights. Bidders sign commit-pinned prose bids. Leader and validators independently fetch full texts, interpret all bundle totals and audit source anchors. Exact amount/unresolved agreement keeps conditional bids in REVIEW. Each bidder consents to the full vector and escrows its maximum bid. Settlement maximizes declared welfare, recomputes allocations without each bidder, charges their externality, transfers rights and refunds unused reserves atomically. Counterfactuals explain every charge. Three StudioNet auctions show specialists paying 8/7, a bundle paying 21, and an unresolved bid blocked before veto refunds. All 33 finalized MAJORITY_AGREE receipts match fresh state, including a holder transfer and three expected rejections. Tests cover 729 exhaustive profiles, 19,683 deviations and 64 generated cases; 64 direct tests plus seven transport tests pass. Native endowments are synthetic, not GEN or delivery claims.

Evidence:

- [Public repository](https://github.com/mohammadisina1988-jpg/pivot-bond)
- [GenLayer contract source](https://github.com/mohammadisina1988-jpg/pivot-bond/blob/main/contracts/pivot_bond.py)
- [Primary GenLayer contract explorer](https://explorer-studio.genlayer.com/address/0xF586AD81fbd5B5a475D29042b7dda67fc14cF689)
- [Onchain scenario proofs](https://github.com/mohammadisina1988-jpg/pivot-bond/blob/main/proofs/README.md)
- [Deployment transaction](https://explorer-studio.genlayer.com/tx/0x451ffcfd8eb8053071d93207344fb6b985c32678934ce4e5971f0fe9d53f596f)
- [Passing CI](https://github.com/mohammadisina1988-jpg/pivot-bond/actions/runs/39405803321)
