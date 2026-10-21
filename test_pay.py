import argparse
import json
import os
import subprocess
import sys
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pay  # noqa: E402

PY = sys.executable
SCRIPT = "pay.py"

# A real, long-settled TRC20 address with known historical transfers — used only
# for the smoke test below, same tradeoff test_currency.py documents for its one
# network-dependent case (this repo's whole point is talking to TronGrid for real).
ADDRESS = "TSDqzM1aAc5FKWUnmZQBtajLzgW7uneYhh"


def run(*args):
    return subprocess.run([PY, SCRIPT, *args], capture_output=True, text=True)


class Skipped(Exception):
    pass


def skip_if_rate_limited(r):
    # TronGrid's free tier rate-limits shared CI-runner IP ranges (observed live
    # in this repo's own CI: HTTP 429 on a run that had nothing wrong with it).
    # A real 429 isn't something this suite can fix or should fail the build
    # over — surface it as inconclusive instead of a false "FAIL".
    if "429" in r.stderr or "Too Many Requests" in r.stderr:
        raise Skipped(r.stderr.strip())


def test_unknown_token_fails_cleanly_no_network_needed():
    r = run("check", ADDRESS, "--token", "doge")
    assert r.returncode == 1
    assert "error:" in r.stderr
    assert "unknown --token" in r.stderr
    assert "Traceback" not in r.stderr


def test_qr_basic_url():
    r = run("qr", ADDRESS)
    assert r.returncode == 0, r.stderr
    assert "api.qrserver.com" in r.stdout
    assert ADDRESS in r.stdout


def test_qr_with_amount_embeds_it():
    r = run("qr", ADDRESS, "--amount", "15")
    assert r.returncode == 0, r.stderr
    assert "amount%3D15" in r.stdout or "amount=15" in r.stdout


def test_missing_required_address_fails():
    r = run("check")
    assert r.returncode != 0


def test_check_with_bad_since_fails_cleanly_via_subprocess():
    # Needs a real network round-trip (fetch happens before --since is validated),
    # so a TronGrid hiccup could make this fail on the network path instead of the
    # date-parse path (observed once in CI: a transient run hit "couldn't reach
    # TronGrid" instead). Only assert on the failure being clean, not its exact
    # cause — test_bad_since_message_is_specific below pins the exact message
    # deterministically, with no network dependency.
    r = run("check", ADDRESS, "--since", "not-a-date")
    skip_if_rate_limited(r)
    assert "Traceback" not in r.stderr
    if r.returncode != 0:
        assert "error:" in r.stderr


def test_bad_since_message_is_specific():
    # In-process, with fetch_transfers mocked out, so this can't be flaky on
    # network/rate-limit conditions the way the subprocess version above can.
    args = argparse.Namespace(address=ADDRESS, token="usdt", contract=None,
                               min=None, since="not-a-date", limit=20, json=False)
    with mock.patch.object(pay, "fetch_transfers", return_value=[]):
        try:
            pay.cmd_check(args)
            raise AssertionError("expected ValueError for bad --since")
        except ValueError as e:
            assert "invalid --since" in str(e)


def test_check_smoke_real_network():
    r = run("check", ADDRESS, "--limit", "3")
    skip_if_rate_limited(r)
    assert r.returncode == 0, r.stderr
    assert "USDT" in r.stdout


def test_check_json_output_is_valid_json():
    r = run("check", ADDRESS, "--limit", "2", "--json")
    skip_if_rate_limited(r)
    assert r.returncode == 0, r.stderr
    data = json.loads(r.stdout)
    assert isinstance(data, list)


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    failed = 0
    skipped = 0
    for t in tests:
        try:
            t()
            print(f"PASS: {t.__name__}")
        except Skipped as e:
            skipped += 1
            print(f"SKIP: {t.__name__}: {e}")
        except AssertionError as e:
            failed += 1
            print(f"FAIL: {t.__name__}: {e}")
    print(f"\n{len(tests) - failed - skipped}/{len(tests)} passed ({skipped} skipped)")
    raise SystemExit(1 if failed else 0)
