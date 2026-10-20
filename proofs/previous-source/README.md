# Earlier source: excluded from the primary proof count

Revision `274e115d316833c19f0c28961ea9d8ff4f21d7a8` deployed source SHA-256 `72ffcc60664d3073ad9b23723b42da0438f22fae58f25f5cfe426263df70d35a`.

| Workflow | Scenario | Outcome |
| --- | --- | --- |
| [39402108998](https://github.com/mohammadisina1988-jpg/pivot-bond/actions/runs/39402108998) | split | 13 verified finalized receipts; native payments `[0,8,7]` |
| [39402114397](https://github.com/mohammadisina1988-jpg/pivot-bond/actions/runs/39402114397) | bundle | 11 verified finalized receipts; native payments `[21,0,0]` |
| [39402119173](https://github.com/mohammadisina1988-jpg/pivot-bond/actions/runs/39402119173) | review | Stops at its fifth receipt, rejected interpretation |

Review interpretation transaction `0x1c97d207ca09b333b985096f193f1c6f0fd4fd9afd5fdf3ca22bdb22d0e1e1e4` finalized `MAJORITY_DISAGREE` after three rotations: zero agree, three disagree, two idle. Its final leader raised `[LLM_ERROR] Invalid bundle valuation`. The receipt does not expose the malformed model output, so its exact schema defect is unknown. This is a failed proof, not a passing uncertain-bid result.

The next source supplied an explicit JSON shape, excluded the implicit empty-bundle entry, requested actual null instead of an uncertainty string, permitted one bounded formatting-repair call, and reported bounded malformed output if repair failed. Numeric/null agreement, strict schema, bidder consent and full-source audit were unchanged. Two repair-branch tests were added.

## Second attempt: diagnostic identifies the missing array entry

Revision `4d7d4651af898a0c939e35bc2fb3929df779e35b`, source SHA-256 `aa3d937c292dcf8d88712b60bfaa9bd068494026b34a3a44cc9367d6df9cdf8f`:

| Workflow | Scenario | Outcome |
| --- | --- | --- |
| [39403658719](https://github.com/mohammadisina1988-jpg/pivot-bond/actions/runs/39403658719) | split | 13 verified finalized receipts |
| [39403672237](https://github.com/mohammadisina1988-jpg/pivot-bond/actions/runs/39403672237) | bundle | 11 verified finalized receipts |
| [39403690576](https://github.com/mohammadisina1988-jpg/pivot-bond/actions/runs/39403690576) | review | Stops at fifth receipt, rejected interpretation |

Transaction `0xfe5964a13634f1df81767ce1c8c4a7bb57735510af251bac242e3f37ecee9529` finalized `MAJORITY_DISAGREE` after three rotations, with zero agree, three disagree and two idle. Its final error contains the actual malformed extraction: `{"anchors":[[0],[0],[1]],"values":[11,0]}`. It has three anchor entries but only two amounts. The receipt establishes the missing unresolved entry; it does not establish whether omission happened in the model or a transport layer.

The final source uses integer `-1` as an explicit unresolved marker instead of null. Exact-vector agreement and full-source audit now include that marker. Such a vector remains REVIEW and cannot be approved or passed to the economic solver. JSON null, strings and incomplete vectors are rejected; tests cover those cases. All three primary scenarios are redeployed with the final source. None of these 58 earlier-source receipts contributes to the primary count.
