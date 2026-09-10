# Security Policy

**English** | [Simplified Chinese](SECURITY.zh-CN.md)

## Supported Versions

This project is early-stage. Security and privacy fixes should target the
default branch unless release branches are created later.

## Reporting A Problem

If you find a security or privacy issue, avoid posting secrets, private paths,
tokens, or private project data in a public issue. Use GitHub's private security
advisory flow if it is available for the repository. If not, open a minimal
public issue that describes the class of problem without exposing sensitive
details.

## Privacy Expectations

This repository is public and must remain generic. It should not contain:

- Credentials, tokens, keys, or secrets
- Personal active work state
- Private project registries
- Organization-specific paths, hosts, or project names
- Private project files or generated artifacts

Run `scripts\scan-public.ps1` before publishing changes.
