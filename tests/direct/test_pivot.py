import ast
import hashlib
import itertools
import json
from pathlib import Path
import random
import re
import subprocess
import pytest

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'contracts/pivot_bond.py'
REPO = 'mohammadisina1988-jpg/pivot-bond'
ITEMS = ['Amber', 'Cobalt']
CASES = {'split': ['split-zero', 'amber-one', 'cobalt-two'], 'bundle': ['bundle-zero', 'amber-one', 'cobalt-two'], 'review': ['split-zero', 'review-one']}
VALUES = {'split-zero': [0, 0, 18], 'bundle-zero': [0, 0, 24], 'amber-one': [11, 0, 11], 'cobalt-two': [0, 10, 10], 'review-one': [11, 0, None]}
ANCHORS = {'split-zero': [[1], [1], [2]], 'bundle-zero': [[1], [1], [2]], 'amber-one': [[0], [0], [1]], 'cobalt-two': [[0], [0], [1]], 'review-one': [[0], [0], []]}


def record(name):
    raw = (ROOT / 'fixtures' / (name + '.json')).read_bytes()
    return f'https://raw.githubusercontent.com/{REPO}/' + 'a' * 40 + f'/fixtures/{name}.json', hashlib.sha256(raw).hexdigest(), raw


def deploy(factory, vm, accounts, case='split', credits=None):
    vm.sender = accounts[0]
    return factory(str(SOURCE), REPO, 'rights-auction', ITEMS, accounts[1:1 + len(CASES[case])], credits or [30] * len(CASES[case]))


def mocks(vm, name, answer=None, audit=None, body=None, status=200):
    vm.clear_mocks()
    url, _, raw = record(name)
    vm.mock_web(re.escape(url), {'status': status, 'body': raw if body is None else body})
    vm.mock_llm(r'.*PIVOTBOND-EXTRACT.*', json.dumps(answer if answer is not None else {'values': VALUES[name], 'anchors': ANCHORS[name]}))
    vm.mock_llm(r'.*PIVOTBOND-AUDIT.*', json.dumps({'valid': [True] * 3} if audit is None else audit))


def prepare(c, vm, accounts, case='split', approve=True):
    for i, name in enumerate(CASES[case]):
        vm.sender = accounts[i + 1]
        url, digest, _ = record(name)
        c.submit(url, digest)
        mocks(vm, name)
        c.interpret(i)
        assert vm.run_validator() is True
        if approve and None not in VALUES[name]:
            c.approve(VALUES[name])


def conserved(state):
    assert sum(state['credits']) + sum(state['escrow']) + state['seller_credits'] == sum(state['configuration']['initial_credits'])


def functions():
    names = {'integer', 'valid_bid', 'bundles', 'optimum', 'pivot'}
    tree = ast.parse(SOURCE.read_text())
    namespace = {'fail': lambda message: (_ for _ in ()).throw(ValueError(message))}
    exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in names], type_ignores=[]), str(SOURCE), 'exec'), namespace)
    return namespace


def independent(vectors, m, excluded=-1):
    # Enumerate bidder bundle masks, not item-owner strings used by the contract.
    candidates = []
    n = len(vectors)
    for masks in itertools.product(range(1 << m), repeat=n):
        if excluded >= 0 and masks[excluded]:
            continue
        occupied = 0
        for mask in masks:
            if occupied & mask:
                break
            occupied |= mask
        else:
            owners = [next((i for i, mask in enumerate(masks) if mask & (1 << item)), n) for item in range(m)]
            value = sum(vectors[i][mask] for i, mask in enumerate(masks) if i != excluded)
            candidates.append(((-value, occupied.bit_count(), tuple(owners)), {'welfare': value, 'owners': owners, 'masks': list(masks)}))
    return min(candidates, key=lambda c: c[0])[1]


@pytest.mark.parametrize('case', ['split', 'bundle'])
def test_full_consensus_counterfactual_payments(direct_deploy, direct_vm, direct_accounts, case):
    c = deploy(direct_deploy, direct_vm, direct_accounts, case)
    prepare(c, direct_vm, direct_accounts, case)
    assert c.get_state()['phase'] == 'READY'
    conserved(c.get_state())
    direct_vm.sender = direct_accounts[4]  # settlement is permissionless
    c.settle()
    s = c.get_state()
    conserved(s)
    assert s['escrow'] == [0, 0, 0] and s['phase'] == 'SETTLED'
    if case == 'split':
        assert s['settlement']['welfare'] == 21 and s['settlement']['payments'] == [0, 8, 7]
        assert s['credits'] == [30, 22, 23] and s['seller_credits'] == 15
        assert s['settlement']['owners'] == [1, 2]
    else:
        assert s['settlement']['welfare'] == 24 and s['settlement']['payments'] == [21, 0, 0]
        assert s['credits'] == [9, 30, 30] and s['seller_credits'] == 21
        assert s['settlement']['owners'] == [0, 0]
    vectors = [[0] + VALUES[name] for name in CASES[case]]
    for i, alternative in enumerate(s['settlement']['counterfactuals']):
        assert alternative == independent(vectors, 2, i)


def test_uncertain_exact_bundle_cannot_be_consent_filled(direct_deploy, direct_vm, direct_accounts):
    c = deploy(direct_deploy, direct_vm, direct_accounts, 'review')
    prepare(c, direct_vm, direct_accounts, 'review')
    before = c.get_state()
    assert before['bids'][1]['status'] == 'REVIEW' and before['escrow'] == [18, 0]
    with direct_vm.expect_revert('Complete valuation required'):
        c.approve([11, 0, 20])
    assert c.get_state() == before
    c.abort()
    s = c.get_state()
    assert s['phase'] == 'ABORTED' and s['credits'] == [30, 30] and s['escrow'] == [0, 0] and s['seller_credits'] == 0
    conserved(s)


@pytest.mark.parametrize('count', [0, 1, 3])
def test_veto_refunds_reserve_including_ready(direct_deploy, direct_vm, direct_accounts, count):
    c = deploy(direct_deploy, direct_vm, direct_accounts)
    prepare(c, direct_vm, direct_accounts, approve=False)
    for i in range(count):
        direct_vm.sender = direct_accounts[i + 1]
        c.approve(VALUES[CASES['split'][i]])
    c.abort()
    s = c.get_state()
    assert s['credits'] == [30] * 3 and s['escrow'] == [0] * 3 and s['phase'] == 'ABORTED'
    conserved(s)
    with direct_vm.expect_revert('Every bidder must approve'):
        c.settle()


@pytest.mark.parametrize('entry', [0, 1, 2])
def test_validator_rejects_each_changed_amount(direct_deploy, direct_vm, direct_accounts, entry):
    c = deploy(direct_deploy, direct_vm, direct_accounts)
    prepare(c, direct_vm, direct_accounts, approve=False)
    # Re-execute the last (bidder two) callback with an independent different amount.
    values = VALUES['cobalt-two'].copy()
    values[entry] += 1
    mocks(direct_vm, 'cobalt-two', {'values': values, 'anchors': ANCHORS['cobalt-two']})
    assert direct_vm.run_validator() is False


@pytest.mark.parametrize('verdict', [{'valid': [True, False, True]}, {'valid': [True, True, False]}, {'valid': ['true'] * 3}, {'valid': [True] * 3, 'extra': True}, {'valid': [True]}])
def test_full_source_audit_is_consequential(direct_deploy, direct_vm, direct_accounts, verdict):
    c = deploy(direct_deploy, direct_vm, direct_accounts)
    prepare(c, direct_vm, direct_accounts, approve=False)
    mocks(direct_vm, 'cobalt-two', audit=verdict)
    assert direct_vm.run_validator() is False


def test_null_anchor_still_requires_substantive_audit(direct_deploy, direct_vm, direct_accounts):
    c = deploy(direct_deploy, direct_vm, direct_accounts, 'review')
    prepare(c, direct_vm, direct_accounts, 'review', approve=False)
    mocks(direct_vm, 'review-one', audit={'valid': [True, True, False]})
    assert direct_vm.run_validator() is False


def test_validator_refetches_exact_committed_bytes(direct_deploy, direct_vm, direct_accounts):
    c = deploy(direct_deploy, direct_vm, direct_accounts)
    prepare(c, direct_vm, direct_accounts, approve=False)
    mocks(direct_vm, 'cobalt-two', body=b'{}')
    assert direct_vm.run_validator() is False


@pytest.mark.parametrize('answer', [
    {'values': [0, 0, True], 'anchors': [[1], [1], [2]]},
    {'values': [0, 0, -1], 'anchors': [[1], [1], [2]]},
    {'values': [0, 0, 1001], 'anchors': [[1], [1], [2]]},
    {'values': [0, 0, '18'], 'anchors': [[1], [1], [2]]},
    {'values': [0, 0], 'anchors': [[1], [1]]},
    {'values': [0, 0, 18], 'anchors': [[1], [1], []]},
    {'values': [0, 0, 18], 'anchors': [[1], [1], [99]]},
    {'values': [0, 0, 18], 'anchors': [[1], [1], [2, 2]]},
    {'values': [0, 0, 18], 'anchors': [[True], [1], [2]]},
    {'values': [0, 0, 18], 'anchors': [[1], [1], [2]], 'confidence': 0.9},
])
def test_malformed_extraction_cannot_enter_state(direct_deploy, direct_vm, direct_accounts, answer):
    c = deploy(direct_deploy, direct_vm, direct_accounts)
    direct_vm.sender = direct_accounts[1]
    c.submit(*record('split-zero')[:2])
    mocks(direct_vm, 'split-zero', answer=answer)
    before = c.get_state()
    with direct_vm.expect_revert('Invalid bundle valuation'):
        c.interpret(0)
    assert c.get_state() == before


@pytest.mark.parametrize('expected', [[0, 0, 19], [0, 0], [False, 0, 18]])
def test_consent_requires_exact_integer_vector(direct_deploy, direct_vm, direct_accounts, expected):
    c = deploy(direct_deploy, direct_vm, direct_accounts)
    prepare(c, direct_vm, direct_accounts, approve=False)
    direct_vm.sender = direct_accounts[1]
    before = c.get_state()
    with direct_vm.expect_revert('Exact valuation consent required'):
        c.approve(expected)
    assert c.get_state() == before


def test_maximum_bid_not_payment_is_reserved(direct_deploy, direct_vm, direct_accounts):
    c = deploy(direct_deploy, direct_vm, direct_accounts, credits=[17, 30, 30])
    prepare(c, direct_vm, direct_accounts, approve=False)
    direct_vm.sender = direct_accounts[1]
    before = c.get_state()
    with direct_vm.expect_revert('Insufficient maximum-bid reserve'):
        c.approve([0, 0, 18])
    assert c.get_state() == before


@pytest.mark.parametrize('method,args', [('submit', ('https://invalid', 'a' * 64)), ('approve', ([0, 0, 0],)), ('abort', ())])
def test_seller_and_outsiders_cannot_act_as_bidder(direct_deploy, direct_vm, direct_accounts, method, args):
    c = deploy(direct_deploy, direct_vm, direct_accounts)
    for actor in [direct_accounts[0], direct_accounts[4]]:
        direct_vm.sender = actor
        with direct_vm.expect_revert('Bidder only'):
            getattr(c, method)(*args)


@pytest.mark.parametrize('url', ['https://evil.example/x', f'https://raw.githubusercontent.com/{REPO}/main/fixtures/a.json', f'https://raw.githubusercontent.com/{REPO}/' + 'a' * 40 + '/fixtures/../a.json'])
def test_url_scope_and_commit_required(direct_deploy, direct_vm, direct_accounts, url):
    c = deploy(direct_deploy, direct_vm, direct_accounts)
    direct_vm.sender = direct_accounts[1]
    with direct_vm.expect_revert('Commit-pinned bid required'):
        c.submit(url, 'a' * 64)


def test_bid_commitment_is_immutable_and_approval_once(direct_deploy, direct_vm, direct_accounts):
    c = deploy(direct_deploy, direct_vm, direct_accounts)
    prepare(c, direct_vm, direct_accounts, approve=False)
    direct_vm.sender = direct_accounts[1]
    with direct_vm.expect_revert('Bid already frozen'):
        c.submit(*record('bundle-zero')[:2])
    with direct_vm.expect_revert('Bid already interpreted'):
        c.interpret(0)
    c.approve([0, 0, 18])
    with direct_vm.expect_revert('Unapproved valued bid required'):
        c.approve([0, 0, 18])


def test_holder_transfer_checks_signature_and_native_address(direct_deploy, direct_vm, direct_accounts):
    c = deploy(direct_deploy, direct_vm, direct_accounts)
    prepare(c, direct_vm, direct_accounts)
    c.settle()
    before = c.get_state()
    direct_vm.sender = direct_accounts[1]
    with direct_vm.expect_revert('Right owner only'):
        c.transfer_right(0, direct_accounts[1])
    assert c.get_state() == before
    direct_vm.sender = direct_accounts[2]
    c.transfer_right(0, direct_accounts[1])
    assert c.get_state()['owners'][0] == before['configuration']['bidders'][0]
    with direct_vm.expect_revert('Right owner only'):
        c.transfer_right(0, direct_accounts[0])
    conserved(c.get_state())


@pytest.mark.parametrize('field,value', [(0, 'bad/repo/extra'), (1, '../bad'), (2, ['Amber', 'Amber']), (2, []), (4, [30, -1, 30]), (4, [True, 30, 30])])
def test_constructor_bounds(direct_deploy, direct_vm, direct_accounts, field, value):
    direct_vm.sender = direct_accounts[0]
    args = [REPO, 'rights-auction', ITEMS, direct_accounts[1:4], [30] * 3]
    args[field] = value
    with direct_vm.expect_revert():
        direct_deploy(str(SOURCE), *args)


@pytest.mark.parametrize('indices', [[0, 1], [1, 1]])
def test_constructor_rejects_seller_as_bidder_and_duplicate_wallet(direct_deploy, direct_vm, direct_accounts, indices):
    direct_vm.sender = direct_accounts[0]
    bidders = [direct_accounts[i] for i in indices]
    with direct_vm.expect_revert('Distinct seller and bidders required'):
        direct_deploy(str(SOURCE), REPO, 'rights-auction', ITEMS, bidders, [30, 30])


def test_exhaustive_729_valuation_profiles_against_disjoint_bundle_oracle():
    pivot = functions()['pivot']
    for raw in itertools.product(range(3), repeat=6):
        vectors = [[0] + list(raw[:3]), [0] + list(raw[3:])]
        result = pivot(vectors, 2)
        chosen = independent(vectors, 2)
        assert {k: result[k] for k in chosen} == chosen
        for i in range(2):
            alt = independent(vectors, 2, i)
            assert result['counterfactuals'][i] == alt
            own = vectors[i][result['masks'][i]]
            assert result['payments'][i] == alt['welfare'] - (chosen['welfare'] - own)
            assert 0 <= result['payments'][i] <= own


def test_19683_single_bidder_deviations_never_improve_quasilinear_utility():
    pivot = functions()['pivot']
    all_vectors = [[0] + list(v) for v in itertools.product(range(3), repeat=3)]
    outcomes = {(tuple(a), tuple(b)): pivot([a, b], 2) for a in all_vectors for b in all_vectors}
    for true in all_vectors:
        for opponent in all_vectors:
            truthful = outcomes[tuple(true), tuple(opponent)]
            utility = true[truthful['masks'][0]] - truthful['payments'][0]
            for reported in all_vectors:
                result = outcomes[tuple(reported), tuple(opponent)]
                assert true[result['masks'][0]] - result['payments'][0] <= utility


def test_64_generated_four_bidder_three_right_cases():
    pivot = functions()['pivot']
    rng = random.Random(71024)
    for _ in range(64):
        vectors = [[0] + [rng.randrange(101) for _ in range(7)] for _ in range(4)]
        result = pivot(vectors, 3)
        chosen = independent(vectors, 3)
        assert all(result[k] == chosen[k] for k in chosen)
        for i in range(4):
            assert result['counterfactuals'][i] == independent(vectors, 3, i)


def test_zero_welfare_leaves_every_right_with_seller():
    result = functions()['pivot']([[0] * 8] * 4, 3)
    assert result['owners'] == [4, 4, 4] and result['masks'] == [0] * 4 and result['payments'] == [0] * 4


def test_tie_is_fewer_allocated_rights_then_lexicographic_owners():
    pivot = functions()['pivot']
    assert pivot([[0, 5, 5, 9], [0, 5, 5, 9]], 2)['owners'] == [0, 1]
    assert pivot([[0, 5, 0, 5], [0, 0, 0, 0]], 2)['owners'] == [0, 2]


@pytest.mark.parametrize('case', ['split', 'bundle', 'review'])
def test_javascript_oracle_replays_actual_direct_state(direct_deploy, direct_vm, direct_accounts, case):
    c = deploy(direct_deploy, direct_vm, direct_accounts, case)
    start = c.get_state()
    accounts = [start['seller']] + start['configuration']['bidders']
    if len(accounts) < 4:
        accounts.append('0x' + bytes(direct_accounts[3]).hex())
    revision = 'a' * 40
    query = "const s=require('./scripts/scenario.cjs');console.log(JSON.stringify(s.plan(process.argv[1],JSON.parse(process.argv[2]),'a'.repeat(40))));"
    process = subprocess.run(['node', '-e', query, case, json.dumps(accounts)], capture_output=True, text=True, cwd=ROOT)
    assert process.returncode == 0, process.stderr
    trace = []
    for item in json.loads(process.stdout):
        direct_vm.sender = direct_accounts[item['caller']]
        before = c.get_state()
        if item['method'] == 'interpret':
            mocks(direct_vm, CASES[case][item['args'][0]])
        if 'error' in item:
            with direct_vm.expect_revert(item['error']):
                getattr(c, item['method'])(*item['args'])
        else:
            getattr(c, item['method'])(*item['args'])
            if item['method'] == 'interpret':
                assert direct_vm.run_validator() is True
        trace.append({'item': item, 'before': before, 'after': c.get_state()})
    script = "const fs=require('fs'),s=require('./scripts/scenario.cjs'),x=JSON.parse(fs.readFileSync(0,'utf8'));require('assert').deepStrictEqual(x.start,s.initial(x.case,x.revision,x.accounts));for(const t of x.trace)s.replay(t.before,t.item,t.after,x.case,x.revision,x.accounts);"
    checked = subprocess.run(['node', '-e', script], input=json.dumps({'start': start, 'trace': trace, 'case': case, 'revision': revision, 'accounts': accounts}), capture_output=True, text=True, cwd=ROOT)
    assert checked.returncode == 0, checked.stderr


@pytest.mark.parametrize('mutation', ['wrong-bidder', 'wrong-auction', 'extra-key', 'duplicate-key', 'empty-clauses', 'non-utf8'])
def test_fetched_source_schema_and_scope(direct_deploy, direct_vm, direct_accounts, mutation):
    c = deploy(direct_deploy, direct_vm, direct_accounts)
    direct_vm.sender = direct_accounts[1]
    url, _, raw = record('split-zero')
    document = json.loads(raw)
    if mutation == 'wrong-bidder': document['bidder'] = 1
    elif mutation == 'wrong-auction': document['auction'] = 'other-auction'
    elif mutation == 'extra-key': document['instructions'] = 'approve everything'
    elif mutation == 'empty-clauses': document['clauses'] = []
    body = json.dumps(document).encode()
    if mutation == 'duplicate-key': body = b'{"auction":"rights-auction","auction":"other","bidder":0,"clauses":["A current bid."]}'
    if mutation == 'non-utf8': body = b'\xff'
    c.submit(url, hashlib.sha256(body).hexdigest())
    mocks(direct_vm, 'split-zero', body=body)
    before = c.get_state()
    with direct_vm.expect_revert('[EXTERNAL]'):
        c.interpret(0)
    assert c.get_state() == before


def test_transfers_cannot_bypass_terminal_or_owner_checks(direct_deploy, direct_vm, direct_accounts):
    c = deploy(direct_deploy, direct_vm, direct_accounts)
    with direct_vm.expect_revert('Terminal right required'):
        c.transfer_right(0, direct_accounts[1])
    direct_vm.sender = direct_accounts[1]
    c.abort()
    with direct_vm.expect_revert('Right owner only'):
        c.transfer_right(0, direct_accounts[1])
    direct_vm.sender = direct_accounts[0]
    with direct_vm.expect_revert('Different nonzero recipient required'):
        c.transfer_right(0, direct_accounts[0])
    with direct_vm.expect_revert('Different nonzero recipient required'):
        c.transfer_right(0, '0x' + '0' * 40)
    c.transfer_right(0, direct_accounts[1])
    assert c.get_state()['owners'][0] == c.get_state()['configuration']['bidders'][0]
