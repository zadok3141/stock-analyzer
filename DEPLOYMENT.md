# Hosting options

**Nothing here is implemented.** These are two candidate ways to run Stock
Analyzer as a hosted web app instead of a local desktop binary, recorded so the
research is not lost. See [TECHNICAL.md](TECHNICAL.md) for how the app is
actually built and shipped today.

GitHub Pages and GitHub Wiki were ruled out: both serve static files only, and
this app needs a live Python process to fetch from Yahoo, run the pandas
analysis, and render the chart PNG server-side.

## What both options need first

The app is already a web app — `main.py` is only a browser-opening wrapper
around `app.py`, and is unused when hosting. The shared prerequisites are small:

- A `Dockerfile` (`python:3.13-slim`, install `requirements.txt` plus gunicorn).
- Serve `app:app` with **gunicorn**, not Flask's development server.
- Bind `0.0.0.0` on the port the platform dictates, rather than the random
  localhost port `main.py` picks.
- Allow ~30s for a request. A slow Yahoo fetch plus chart render is not fast,
  and short default timeouts will cut it off.

## Option 1 — Hugging Face Spaces

Free tier, persistent URL, runs a Dockerfile directly. The lowest-friction way
to put this in front of a few people.

- Create a Space with the **Docker** SDK and push the repo to it.
- Docker Spaces expect the app on **port 7860** by default; either listen there
  or set `app_port` in the Space's README frontmatter.
- Spaces can be public or private.
- Free CPU tier sleeps when idle, so the first request after a quiet period
  pays a start-up delay.

**Good when:** the goal is "let a few people try it without installing
anything," and cost matters more than polish.

## Option 2 — AWS Lambda container + Web Adapter

Scales to zero, so idle cost is effectively nothing. Best value for a tool used
a handful of times a day.

The enabling trick is the [AWS Lambda Web
Adapter](https://github.com/aws/aws-lambda-web-adapter): a small extension
copied into the image that lets Lambda run an ordinary HTTP server. **The Flask
app needs no rewrite** — no Mangum, no ASGI port.

```dockerfile
COPY --from=public.ecr.aws/awsguru/aws-lambda-web-adapter:0.9.1 \
     /lambda-adapter /opt/extensions/lambda-adapter
```

Pin a tag rather than `latest`. The project's newest release was **v1.0.1** as
of 2026-07-19; confirm the matching ECR image tag before using it, as the ECR
tags have historically lagged the GitHub releases.

- Package as a **container image** — numpy, pandas and matplotlib are far too
  large for a zip-based Lambda, but the 10 GB image limit fits them easily.
- Add a **Function URL** for an HTTPS endpoint.
- Raise the function timeout to ~30s; the 3s default will cut requests off.
- Expect a **3–8s cold start** while pandas and matplotlib import. This is the
  real cost of scaling to zero.

**Good when:** traffic is low and sporadic, and a first-request delay is
acceptable in exchange for a near-zero bill.

AWS App Runner is the alternative if cold starts are unacceptable: comparable
setup effort, always warm, but no scale-to-zero and roughly $25/month idle.

## Risks that apply to any hosted deployment

**Yahoo blocks datacenter IPs.** This is the one most likely to sink a hosted
deployment, and AWS ranges are among the most aggressively blocked. yfinance is
a scraper, not an official API. What works reliably from a home connection can
return empty responses or fail outright from a cloud host. Mitigations are a
caching layer so each ticker is fetched once, a NAT address that has not been
burned, or moving to a market-data API with a key.

**There is no caching.** Every page load re-downloads from Yahoo. This is worth
fixing before hosting regardless of the blocking issue — it makes the app slow
and multiplies the traffic that triggers blocks in the first place.

**There is no authentication.** A Function URL or a public Space is open to
anyone who finds it. Options are IAM auth on the Function URL, CloudFront and
WAF in front, a private Space, or simply not sharing the address.

**Yahoo's terms.** Redistributing their data through a public service is not
permitted. A personal instance is a different proposition from an open one.
