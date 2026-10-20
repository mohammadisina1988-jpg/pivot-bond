# StudioNet proofs

Live scenario runs are pending. A deployment alone will not count as a passing auction.

Planned scenarios:

| Scenario | Consequential result |
| --- | --- |
| split | Singleton specialists beat a complementary bundle; payments are bidder-removal externalities; holder transfer and nonholder rejection |
| bundle | Strong complementarity wins both rights and pays the displaced specialists' welfare |
| review | Conditional bundle value stays unresolved (`-1`); signed approval is rejected; veto returns another bidder's escrow; settlement after abort is rejected |

Each run verifies exact source bytes, complete final votes, signer/target/calldata, expected rejection bytes, and every complete state before/after each call. Independent disjoint-bundle enumeration checks the chosen and all counterfactual allocations. Read-only RPC retries never replay signed sends.
