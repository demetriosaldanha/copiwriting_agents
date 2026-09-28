# Engineering Instructions

## Security

Security is a release requirement, not an optional improvement.

Before providing deployment instructions or considering this project
production-ready:

1. Read `docs/SECURITY_CHECKLIST.md`.
2. Perform the security review defined there.
3. Report CRITICAL, HIGH, MEDIUM and LOW findings.
4. Do not consider production deployment ready while unresolved
   CRITICAL findings exist.
5. Explain HIGH findings and remediation before deployment.
6. Never expose secrets found during analysis.
7. Never weaken authentication, authorization, validation, TLS,
   IAM or other security controls merely to make deployment easier.

## Development rules

When generating or modifying code:

- Never hardcode secrets or credentials.
- Use environment variables or appropriate secret management.
- Apply least privilege.
- Validate untrusted input.
- Use parameterized database queries.
- Treat RAG documents and external content as untrusted input.
- Do not allow LLM output alone to determine authorization.
- Restrict agent tool permissions.
- Add appropriate timeout, retry, rate and cost limits.
- Avoid exposing stack traces or sensitive information.
- Keep development and production configuration separated.

## Deployment

Before recommending deployment:

1. Run applicable tests.
2. Run applicable security checks.
3. Review dependencies.
4. Review secrets/configuration.
5. Review public endpoints.
6. Review authentication and authorization.
7. Review agent/tool permissions.
8. Review production configuration.
9. Produce the pre-deployment security report.

Detailed requirements:
`docs/SECURITY_CHECKLIST.md`