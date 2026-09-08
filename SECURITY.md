# Security policy

The optional capture client signs read requests with a user-supplied key. Keep that key outside the repository and pass its path with `--private-key`. Review the requested endpoint and local output path before capture.

The ignore file covers common key and environment-file extensions. It cannot protect secrets already tracked by Git, copied into other files, or printed by another program. Review changes before committing them.

PMQS has no live order-placement module. Any execution service built around it needs its own authorization, limits, and security review.

For a public bug report, include a sanitized reproduction and the affected version. Omit keys, account details, personal data, and exploit details that would expose another system. Arrange a private channel with the maintainer before sharing sensitive material.
