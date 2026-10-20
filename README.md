# PivotBond

A bounded GenLayer combinatorial VCG auction with independently interpreted prose bids, explicit bidder consent, maximum-bid escrow and actual contract-native ownership/payment changes.

**Deployed and exercised on gasless StudioNet.** [Primary contract explorer](https://explorer-studio.genlayer.com/address/0xF586AD81fbd5B5a475D29042b7dda67fc14cF689) · [33 verified onchain receipts](proofs/README.md) · [Passing CI](https://github.com/mohammadisina1988-jpg/pivot-bond/actions/runs/39405803321).

The seller creates 1–3 indivisible native rights and invites 2–4 distinct bidder wallets. Each bidder publishes a commit-pinned bid document, signs its URL/hash, then approves the exact consensus-interpreted total value of every nonempty bundle. Empty bundle value is zero. Missing or conditional values remain `REVIEW`; consent cannot fill them in.

The intended consumer is another contract or application that enforces scarce native entitlements by reading ownership. Bundle valuations capture complementary rights whose combined value cannot be inferred from their individual values. Labels alone confer no external access.

Once every bidder has reserved its maximum bundle value, anyone can settle. Exhaustive allocation maximizes declared welfare. Each charge is the best welfare others could get without that bidder minus their welfare in the selected allocation. Winners receive native rights, unused reserves are refunded, and payments increase the seller's native-credit balance. Holders can later transfer individual rights. A bidder may veto before settlement, returning every reserve.

**Scope:** native rights and endowed credits are abstract contract state. They are not GEN, cash, redeemable tokens, external property or evidence of delivery. Prose bids declare preferences; consensus does not prove a bidder's private true valuation. This is an open-document mechanism, not a sealed-bid protocol. The pre-settlement veto means textbook VCG incentive conclusions do not apply to the complete workflow.

- [Contract](contracts/pivot_bond.py)
- [Architecture, consensus and limitations](docs/design.md)
- [Tests](tests/direct/test_pivot.py)
- [Deployment proofs](proofs/README.md)
- [Contribution text](docs/submission.md)

## Verify locally

```sh
python -m pip install -r requirements-dev.txt
genvm-lint download --version v0.2.16
genvm-lint check contracts/pivot_bond.py --json
python -m pytest tests/direct -q
node --test tests/rpc-preflight.test.cjs
```

The direct suite runs validator callbacks explicitly using mocked web/model answers. Economic property tests compare item-owner enumeration with independent disjoint-bundle enumeration. Live proofs use actual GenVM, web acquisition, validator models, four signing wallets and fresh full-state verification.

64 direct tests and seven transport tests pass. Coverage includes 729 exhaustive valuation profiles, 19,683 unilateral deviation checks for the fixed-profile settlement rule, 64 generated four-bidder/three-right cases, and JavaScript replay of all three direct scenario traces.

## Attribution

VCG and Clarke pivot payments are established mechanism-design techniques, not a new economic invention. See [Procaccia's CMU lecture, VCG combinatorial auctions](https://www.cs.cmu.edu/~arielpro/summer/slides/eva1.pdf). GenLayer's [equivalence-principle documentation](https://docs.genlayer.com/developers/intelligent-contracts/equivalence-principle) describes independent substantive validator checks. Generic CLI transport, receipt decoding and the Windows direct-test workaround are reused under the included MIT license from earlier repositories, including [CrossLedger](https://github.com/mohammadisina1988-jpg/cross-ledger). The auction, economic oracle, source protocol and tests are implemented here.
