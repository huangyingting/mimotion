# mimotion

[![Update Steps](https://github.com/huangyingting/mimotion/actions/workflows/run.yml/badge.svg)](https://github.com/huangyingting/mimotion/actions/workflows/run.yml)

Personal Zepp Life step automation with encrypted login-token storage. Independently maintained in a private repository, with no upstream synchronization.

## Schedule and steps

The only workflow, **Update Steps**, runs at **07:00, 15:00, and 23:00 Beijing time** each day. Its UTC cron is `0 7,15,23 * * *`. GitHub may delay scheduled runs; manual runs are additional.

Step calculation and the submitted date use `Asia/Shanghai`, even on UTC runners:

```text
bonus_limit = floor((MAX_STEP - MIN_STEP) * minutes_since_midnight / 1440)
steps = MIN_STEP + random_integer(0, bonus_limit)
```

With `MIN_STEP=15000` and `MAX_STEP=18000`:

| Beijing time | Random total |
|---|---:|
| 07:00 | 15,000-15,875 |
| 15:00 | 15,000-16,875 |
| 23:00 | 15,000-17,875 |

The bonus window resets at midnight. Each run replaces today's total rather than adding steps; totals can decrease between runs, but stay within the configured limits.

## GitHub Actions setup

Use the `master` branch and enable **Update Steps** in [Actions](https://github.com/huangyingting/mimotion/actions/workflows/run.yml). Add these [repository secrets](https://github.com/huangyingting/mimotion/settings/secrets/actions):

| Secret | Value |
|---|---|
| `PAT` | Repository-scoped GitHub token with Contents read/write permission. Renew it before expiry. |
| `AES_KEY` | Random 16-character ASCII key for encrypting saved login tokens. |
| `CONFIG` | JSON configuration below, using your Zepp Life credentials. |

```json
{
  "USER": "your_email@example.com",
  "PWD": "your_password",
  "MIN_STEP": "15000",
  "MAX_STEP": "18000"
}
```

Use a **Zepp Life account**, not a Xiaomi account. For multiple accounts, separate both `USER` and `PWD` with `#`; their counts must match. Limits must satisfy `0 <= MIN_STEP <= MAX_STEP`.

Optional configuration fields are listed in [`.env.example`](.env.example). Notifications require the corresponding provider tokens; leave unused fields empty.

Select **Run workflow** to test. Check the **Update Steps** job step for the submitted total and account results. Any account failure makes the workflow fail. Successful runs save `encrypted_tokens.data`; unchanged files do not create a commit.

Keep credentials in secrets, never in committed files. Preserve `AES_KEY` and `encrypted_tokens.data` when updating code. Changing the key invalidates saved tokens and requires a fresh login. GitHub cannot reveal saved secret values; keep a secure backup.

## Local use

Install Python 3.10+ and [uv](https://docs.astral.sh/uv/), then:

```sh
cp .env.example .env
# Edit .env with your credentials and an optional encryption key.
uv run --with-requirements requirements.txt python main.py
```

`.env` is ignored by Git. Run tests with:

```sh
uv run --with-requirements requirements.txt python -m unittest discover -s tests
```

## Notes

Zepp accepting a step update does not guarantee WeChat or Alipay synchronization. Configure the account's third-party links in Zepp Life; new accounts may require a bound device. Service rate limits or authentication errors can also prevent updates.

Only `.github/workflows/run.yml` controls the schedule. `cron_change_time` is historical; the old randomization and configuration-export scripts are not used by Actions.

## Credits and license

Based on [TonyJiangWJ/mimotion](https://github.com/TonyJiangWJ/mimotion), with original credits to xunichanghuan/mimotion, [huangshihai/mimotion](https://github.com/huangshihai/mimotion), and [hanximeng/Zepp_API](https://github.com/hanximeng/Zepp_API) for authentication encryption research.

Original attribution is preserved. Licensed under [Apache-2.0](LICENSE).
