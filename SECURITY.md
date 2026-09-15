# Security Policy

## Supported versions

The project is currently pre-1.0. Security fixes are applied to the latest
version on the `main` branch.

## Reporting a vulnerability

Please do not open a public issue for a suspected vulnerability. Report it
privately to the repository maintainers with:

- A clear description of the issue and its impact.
- The affected version, operating system, and Python version.
- Reproduction steps or a minimal proof of concept.
- Any suggested mitigation.

The maintainers will acknowledge the report, investigate it, and coordinate a
fix and disclosure timeline with the reporter.

## Security model

`wintask` registers tasks using the current Windows user's interactive token.
The library does not elevate privileges and does not bypass Windows access
control. Applications remain responsible for validating task names, script
paths, generated XML, and any configuration received from untrusted sources.
