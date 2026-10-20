# StudioNet proofs

**33 primary receipts verified: 30 successful executions and three expected execution errors.** Every primary receipt is FINALIZED with MAJORITY_AGREE on gasless StudioNet, chain 61999. Full fresh verification started at `2026-10-20T10:24:50.690Z`; [verification.json](verification.json) records `scope: all` and `live_state_match: true`.

Deployed source SHA-256: `356186106247322f3d4c8c0e9871b60525b3fd4810c83d31cb0b8e3a53f8a21d`. [Exact deployed source](https://github.com/mohammadisina1988-jpg/pivot-bond/blob/5b3014174f3c35f53666ca182d374afdcf92fb43/contracts/pivot_bond.py). Source/test revision: `5b3014174f3c35f53666ca182d374afdcf92fb43`. Commit-pinned fixture revision: `d8fa97ef5d93de6cb1455154c2b0303b75ff5517`.

| Scenario | Contract explorer | Receipts | Verified final effect |
| --- | --- | --- | --- |
| split | [0xF586…F689](https://explorer-studio.genlayer.com/address/0xF586AD81fbd5B5a475D29042b7dda67fc14cF689) | 13 | Welfare 21; masks `[0,1,2]`; payments `[0,8,7]`; bidder credits `[30,22,23]`, seller credits 15. A purchased right is subsequently transferred by its holder. |
| bundle | [0x50D5…4E37](https://explorer-studio.genlayer.com/address/0x50D5cdccB02DaBb1b801AD228E5b7bb9455A4E37) | 11 | Welfare 24; masks `[3,0,0]`; payments `[21,0,0]`; bidder credits `[9,30,30]`, seller credits 21. |
| review | [0x8be8…de60](https://explorer-studio.genlayer.com/address/0x8be86ef09A884AE97b217476472222508fCade60) | 9 | Valuation `[11,0,-1]` stays REVIEW. Approval fails, bidder veto refunds reserved credits, final balances `[30,30]`, seller credits 0, phase ABORTED. |

Every final escrow is zero. Rights in the aborted instance remain with its seller. These are synthetic native endowments, not GEN balances or delivery proofs.

## Decisive transaction links

| Proof | Explorer transaction |
| --- | --- |
| Specialist deployment | [deploy](https://explorer-studio.genlayer.com/tx/0x451ffcfd8eb8053071d93207344fb6b985c32678934ce4e5971f0fe9d53f596f) |
| Specialist counterfactual settlement | [settle](https://explorer-studio.genlayer.com/tx/0x42969e3991c940b99d5c18d988766475e1670b7c715e9b238e346d152e973d08) |
| Nonholder transfer rejection | [expected error](https://explorer-studio.genlayer.com/tx/0x0de1ecbcd64f01073d18d8fdb6f2936856eb359287e37cb15323ff0cb1d31138) |
| Signed holder transfer | [transfer](https://explorer-studio.genlayer.com/tx/0xf015cbd09618d52dcfb0805217151d3fb032946d296804585613e6e11c473c72) |
| Complementary-bundle deployment | [deploy](https://explorer-studio.genlayer.com/tx/0x09212649ea02af8d479bd8b6c0a64a3f8d61c9396161885389c8ac769928e578) |
| Complementary-bundle externality charge | [settle](https://explorer-studio.genlayer.com/tx/0xdd243d25360a1ccbbd1b32934c7c6b61d213e18029a90ac6062d3c8dcbacc5de) |
| Unresolved-bid deployment | [deploy](https://explorer-studio.genlayer.com/tx/0x7d58051aa211db6bee3a79c93089a99b20baa3b1e96bb932d3c6949afcd9c21c) |
| Independently agreed unresolved valuation | [interpret](https://explorer-studio.genlayer.com/tx/0x1a36ecf9f68d1df73fa62c296f4ffafcaa99df4fd710eedb28c2cd4a8a804b4c) |
| Caller cannot fill in an unresolved bid | [expected error](https://explorer-studio.genlayer.com/tx/0x9b075534dc4192742b1b15eec49fb2c5becf12a6632d655e1bf53801769c32d8) |
| Veto returns all reserves | [abort](https://explorer-studio.genlayer.com/tx/0x9656948827982bf88b6450399a2d2fb95b15b7d27f10a5dd57e1dbbefb95a09f) |
| Settlement after abort is rejected | [expected error](https://explorer-studio.genlayer.com/tx/0x358fc2a9e5ec2aa882e276f0dcbc27017ac5e4e6f1fe3dde28e555943762aa28) |

Each run verifies exact source bytes, complete final votes, signer/target/calldata, expected rejection bytes, and every complete state before/after each call. Independent disjoint-bundle enumeration checks the chosen and all counterfactual allocations. Read-only RPC retries never replay signed sends.

## Receipt and test provenance

All 33 labels/hashes are in [transactions.json](transactions.json); instance addresses and constructor args are in [suite.json](suite.json). The `*-trace.json` files retain every before/after state, while `*-receipt.json` files retain source-bound calldata, execution results and complete final votes. Each expected error is checked byte-for-byte with unchanged state.

Vote distributions `(agree/disagree/idle)` are `5/0/0` for 8 receipts, `3/0/2` for 23, `4/0/1` for 1, and `3/2/0` for 1. This is majority agreement, not unanimity; dissent and idle votes are preserved.

- [Specialist workflow](https://github.com/mohammadisina1988-jpg/pivot-bond/actions/runs/39405819040)
- [Bundle workflow](https://github.com/mohammadisina1988-jpg/pivot-bond/actions/runs/39405839231)
- [Unresolved-bid workflow](https://github.com/mohammadisina1988-jpg/pivot-bond/actions/runs/39405853727)
- [Passing CI](https://github.com/mohammadisina1988-jpg/pivot-bond/actions/runs/39405803321)

The local and all three hosted JUnit reports contain 64 direct tests with zero failures, errors or skips. Seven read-only transport retry tests also pass. Direct tests explicitly invoke validator callbacks but mock web/model answers; live receipts exercise real acquisition and consensus. Successful fixed-profile settlement incentives are property-tested, not claimed for the complete public-document/veto workflow.

The [58 earlier-source receipts](previous-source/README.md), including two rejected interpretation attempts, are retained separately and excluded from the primary count.

## Reproduce verification

Install GenLayer CLI `0.39.2`; set `GENLAYER_CLI_PATH` to its absolute `dist/index.js` path. `node scripts/verify-proofs.cjs --offline` verifies the complete saved receipt set. With a configured read account in `PIVOT_ACCOUNT`, `node scripts/verify-proofs.cjs` independently re-fetches all receipts, exact source and final full state. It does not send transactions. Use the manual StudioNet workflow to deploy fresh instances with new encrypted disposable wallets.
