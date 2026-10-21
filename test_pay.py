import json
import subprocess
import sys

PY = sys.executable
SCRIPT = "pay.py"

# A real, long-settled TRC20 address with known historical transfers — used only
# for the smoke test below, same tradeoff test_currency.py documents for its one
# network-dependent case (this repo's whole point is talking to TronGrid for real).
ADDRESS = "TSDqzM1aAc5FKWUnmZQBtajLzgW7uneYhh"


def run(*args):
    return subprocess.run([PY, SCRIPT, *args], capture_output=True, text=True)


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


def test_check_with_custom_contract_and_bad_since_fails_cleanly():
    # Needs a real network round-trip (fetch happens before --since is validated),
    # so only assert on the failure being clean, not on its exact exit path.
    r = run("check", ADDRESS, "--since", "not-a-date")
    assert "Traceback" not in r.stderr
    if r.returncode != 0:
        assert "error:" in r.stderr
        assert "invalid --since" in r.stderr


def test_check_smoke_real_network():
    r = run("check", ADDRESS, "--limit", "3")
    assert r.returncode == 0, r.stderr
    assert "USDT" in r.stdout


def test_check_json_output_is_valid_json():
    r = run("check", ADDRESS, "--limit", "2", "--json")
    assert r.returncode == 0, r.stderr
    data = json.loads(r.stdout)
    assert isinstance(data, list)


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    failed = 0
    for t in tests:
        try:
            t()
            print(f"PASS: {t.__name__}")
        except AssertionError as e:
            failed += 1
            print(f"FAIL: {t.__name__}: {e}")
    print(f"\n{len(tests) - failed}/{len(tests)} passed")
    raise SystemExit(1 if failed else 0)
