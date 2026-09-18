# Devotion bots

A family of Telegram channels that each receive a daily devotion. One AWS Lambda serves all of
them; an EventBridge schedule per channel invokes it with `{"channel": "<name>"}` at that channel's
delivery time, it looks up today's entry in the channel's data file and posts it with the Telegram
Bot API. Python 3.12 standard library plus `tzdata` (so `zoneinfo` works on the Lambda runtime).

| Channel          | Source                                        | Telegram                                     | Delivery             |
|------------------|-----------------------------------------------|----------------------------------------------|----------------------|
| `psalms`         | *Thru' the Psalms in one year* (Isaac Ong)    | [@thruthepsalms](https://t.me/thruthepsalms) | 06:00 Asia/Singapore |
| `our_daily_walk` | *Our Daily Walk* (F.B. Meyer)                 | [@ourdailywalkdevo](https://t.me/ourdailywalkdevo) | 06:00 Asia/Singapore |

## Layout

```
template.yaml            SAM stack: the function, one schedule per channel, log group, error alarm
src/
  handler.py             Lambda entry point
  channels.py            channel registry — chat id, data file, renderer, timezone
  telegram.py            sendMessage client
  renderers/             one module per data shape: FIELDS + render(key, entry) -> Telegram HTML
  data/                  one JSON per channel, keyed "D MONTH" (e.g. "2 MAY"), one entry per day of a leap year
tests/                   python3 -m unittest
tools/                   scripts that (re)generate the data files
deploy/                  IAM policy documents for the GitHub Actions deploy role
```

## Data provenance

Data files are generated, not hand-edited.

**`psalms.json`** comes from *Thru' the Psalms in one year
with Spurgeon's Treasury of David* (Isaac Ong, Calvary Bible-Presbyterian Church, 2012), read
straight from the PDF's text layer by [tools/extract_psalms.py](tools/extract_psalms.py). Small-caps
LORD, accents, paragraph and poem line breaks are preserved from the print; two typos in the
placement of a verse citation's full stop are corrected in `VERSE_FIXES`. The PDF is not committed.
To regenerate after a source update:

```bash
python3 -m venv .venv && .venv/bin/pip install pymupdf
.venv/bin/python tools/extract_psalms.py ~/Downloads/CBPC-Psalm-ver2.pdf
python3 -m unittest
```

Failures are loud and private: if anything goes wrong (unknown channel, missing date, Telegram
rejects the message) the function raises, nothing reaches subscribers, the invocation is recorded
as failed, and the `ErrorsAlarm` emails you if `AlarmEmail` is set. Lambda's async retries are
turned off so a retry can never post a devotion twice; after a failure, re-send with `make invoke`.

## Adding a channel

1. Put its data file in `src/data/`, keyed `"D MONTH"` with an entry for every day including
   `29 FEBRUARY`.
2. Add a renderer in `src/renderers/` if the data shape is new (see `psalms.py`: export `FIELDS`
   and `render(key, entry)`).
3. Add it to `CHANNELS` in [src/channels.py](src/channels.py).
4. Add a `ScheduleV2` event under `Events:` in [template.yaml](template.yaml), copying the
   `Psalms` block and changing the name, cron, and `Input`.
5. Make the bot an admin of the new Telegram channel.
6. `make test`, then push. The generic tests in `tests/test_channels.py` cover the new channel
   automatically.

## Deploying

Pushing to `master` runs the tests and, if they pass, `sam deploy`s the stack — see
[.github/workflows/deploy.yml](.github/workflows/deploy.yml). Pull requests only run the tests.

### One-time AWS setup

1. **Do the first deploy from your machine** so SAM can create its artifact bucket with your own
   credentials (needs the [SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html)):

   ```bash
   BOT_TOKEN=123456:ABC... ALARM_EMAIL=you@example.com make deploy
   ```

   Confirm the SNS subscription email that arrives, or you won't get alarms.

2. **Create the GitHub OIDC identity provider** in IAM (Identity providers → Add → OpenID Connect,
   URL `https://token.actions.githubusercontent.com`, audience `sts.amazonaws.com`). Skip if the
   account already has one.

3. **Create the deploy role**: IAM → Roles → Create → Custom trust policy, paste
   [deploy/github-oidc-trust-policy.json](deploy/github-oidc-trust-policy.json) with `ACCOUNT_ID`
   filled in. Attach an inline policy from
   [deploy/github-deploy-role-policy.json](deploy/github-deploy-role-policy.json), again with
   `ACCOUNT_ID` filled in. The trust policy only allows the `master` branch of this repository to
   assume it.

4. **Add repository secrets** on GitHub (Settings → Secrets and variables → Actions):

   | Secret                | Value                                   |
   |-----------------------|-----------------------------------------|
   | `AWS_DEPLOY_ROLE_ARN` | ARN of the role from step 3             |
   | `BOT_TOKEN`           | Telegram bot token                      |
   | `ALARM_EMAIL`         | Optional; where to send failure alerts  |

5. **Retire the old hand-made function**: once a test invocation (below) succeeds, disable its
   EventBridge rule, and delete it after the new stack has posted for a day or two.

### Day to day

```bash
make test                                       # run the test suite
make deploy                                     # deploy from your machine (needs BOT_TOKEN)
make invoke CHANNEL=psalms DATE=2024-05-02 CHAT_ID=@yourtestchannel   # dry run to a test channel
make invoke CHANNEL=psalms                      # send today's devotion for real
make logs                                       # tail the function's logs
```

`make invoke` uses `sam remote invoke`; the `DATE` and `CHAT_ID` overrides are optional and go
straight into the event, so the same thing works from the Lambda console with
`{"channel": "psalms", "date": "2024-05-02", "chat_id": "@yourtestchannel"}`.

## Configuration

Stack parameters (set on `sam deploy`, or via the secrets above in CI):

| Parameter    | Purpose                                                              |
|--------------|----------------------------------------------------------------------|
| `BotToken`   | Telegram bot token. The bot must be an admin of every channel.       |
| `AlarmEmail` | Optional. Email subscribed to the failure alarm.                     |

Per-channel settings (chat id, timezone, data file) live in `src/channels.py`; delivery times live
in `template.yaml`.
