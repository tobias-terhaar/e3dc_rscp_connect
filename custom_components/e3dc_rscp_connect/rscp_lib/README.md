# Vendored RSCP protocol library

This directory contains `rscp_lib` 1.0.2, copied from
[`tobias-terhaar/rscp-lib`](https://github.com/tobias-terhaar/rscp-lib) at
commit `f7f52e58d78b0dabf64268160b938612a1012f52` (2026-10-05). Its MIT license
is preserved in `LICENSE`.

The local copy changes `RscpConnection.receive()` to reassemble one complete
encrypted RSCP frame from the TCP byte stream before decrypting it. A single
`sock_recv()` call may otherwise contain only the RSCP header, causing a valid
connection to be reported as an identification or RSCP-key error.
