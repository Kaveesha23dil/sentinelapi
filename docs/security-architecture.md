# DemoCommerce security boundaries

Step 3.3 is incomplete. Windows clients reach the HTTPS WSO2 gateway, which
enforces OAuth and application subscriptions before forwarding over Docker HTTP
to `democommerce:8000`. Live Publisher inspection on 2026-10-22 confirmed OAuth2
and `Application & Application User` security on all six operations. Never
disable resource security or subscription checks to make a test pass.

Threats: missing, invalid or expired credentials; unsubscribed clients; excess
authenticated traffic; and direct backend access bypassing gateway enforcement.
The current loopback publication still permits the last threat from Windows.

Isolation design: remove only the DemoCommerce `ports` mapping after the Step 3.2
route decision. Preserve the internal 8000 listener, Dockerfile EXPOSE, health
check and sentinelapi-network. Compose has no dependent services, but the old
smoke, export and environment scripts use the host port. Use the new
isolation-aware security verifier after removal. Apply only the stateless backend
with `docker compose up -d --no-deps democommerce`; this resets in-memory orders.
Never recreate WSO2, delete volumes or run compose down. No apply occurred.

Authorized containers on the shared network remain able to reach the backend
without gateway authentication. Docker administrators also remain trusted.
Network membership is a security boundary, not backend identity verification.
Production segmentation, mTLS, user identity propagation and secret management
remain future work. Demo identity is fixed, orders are in memory, payments simulated.

Rate-limit design: discover and reuse an existing 10PerMin application policy
with a dedicated SentinelAPIRateLimitClient. Preserve the normal smoke client.
WSO2 application limits apply per token; test a single token with at most 25 GETs,
stopping at 429. Require a prior 200 and an observed 429, not a configured quota
alone. Asynchronous enforcement can overshoot; do not require exactly request 11.
See [WSO2 4.5 policy documentation](https://apim.docs.wso2.com/en/4.5.0/manage-apis/design/rate-limiting/adding-new-throttling-policies/).

The new verifier accepts credentials via runtime environment or hidden prompt,
keeps tokens in memory, validates TLS, rejects redirects and restricts gateway
tests to HTTPS localhost:8243. Its finally block submits issued-token revocation.
Use only dedicated test credentials: revoking a cached application token can
affect other users of that application. Revocation submission does not prove
immediate gateway cache invalidation. Optional expired/unsubscribed tokens must
be genuine issued tokens, not edited JWTs. Missing optional tests remain pending.
