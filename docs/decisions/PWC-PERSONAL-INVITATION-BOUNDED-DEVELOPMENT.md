# Personal invitations — product decisions and bounded development permission

## Provenance and scope

Recorded 5 November 2026 against baseline
`ee298bae3d3110d0d38557097584b4f63c9a9fc5`, from explicit instructions and answers
in this Arena conversation. This records the communicated product decisions,
not an inferred legal identity, charter, signature or independent review.
No authenticated external evidence reference was supplied.

Accepted product scope: invitation-only personal enrollment; Founder and AbuBakr
are the initial intended recipients; issuance by an explicitly authorized PWC
officer; recipient-bound, single-use invitations; email confirmation, personally
chosen password and MFA; ordinary personal permissions only. Founder appointment,
independent verifier authority and NGO permissions remain separate.

The user explicitly selected **Authorize bounded development**: additive invitation
storage and service implementation/tests are permitted while non-test execution
stays hard-closed, the real issuer resolver fails closed, SMTP remains unwired,
and institutional grants are excluded. This is a narrow development exception to
the previous PE-CONTRACT prohibition on invitation tables/writers, not acceptance
of a live source, deployment, privacy/retention terms or real enrollment.

The user selected **All steps within 24 hours**: email confirmation, password
creation AND MFA must complete before invitation expiry. Expiry must not silently
be interpreted as only the token-consumption deadline. Handling of an expired
partially created account needs an explicit safe contract before that writer is
implemented; no automatic account deletion, linking or privileged recovery follows.

## Historical first slice (commit 9f8bdc5; extended below)

`PersonalInvitation` and `personal_invitations.py` implement bounded storage,
24-hour expiry, authorized-source seam, recipient normalization, encrypted pending
mail material, purpose-separated token/proof digests, cancellation, bounded bad
proof attempts, email confirmation with single-use proof, atomic audit and row
locking. Every service entry rejects non-test profiles before database I/O. The
actual source resolver always denies; only test fixtures patch it. There is no
issuer endpoint, account creation/password/MFA completion writer, delivery worker,
SMTP wiring, new HTTP contract or native operation allowlist expansion.

Positive tests exercise the actual PostgreSQL service with synthetic source
fixtures. They do not authenticate an officer or prove a live source's revocation
fence. A future accepted source adapter must lock its authoritative source and
revocation rows through commit; a cached boolean check cannot satisfy that fence.

Current lock order: issuer User, invitation. Proof/delivery abuse-budget spends
complete before the invitation transaction; issuance budgets run inside the
issuer transaction. Audit failures roll back the invitation change. A duplicate
pending recipient is rejected by a partial unique constraint, not merely a query.
An expired row is cancelled/its pending secrets erased on authorized reissue.
No retention period for invitation/audit metadata is invented or activated.

## Remaining completion work and accountable gates

- Account/password/MFA state machine, safe expired-partial-account behavior,
  transactional consumption, current-session MFA binding and deadline fences.
- Approved browser request/error schemas, accessible EN/UR integration and actual
  browser tests; no independent native transport permission is implied.
- Bounded delivery leasing/retries/expiry erasure and approved SMTP composition.
- PE-ISSUER: actual scoped officer identity, authenticated source/version,
  recipient binding and source revocation transaction contract.
- PE-CONTRACT live writer/security review; O4 eligibility, lawful basis, notice,
  audiences, retention/hold/erasure; O1/O2 provider/sender/budget/worker;
  O3/W2 exact ingress, browser transport, least-privilege DB and host acceptance.
- Deployment and real invitations require explicit authorization. C1-R01–R08,
  Issue #42 institutional dependencies and distinct-human requirements are unchanged.

No accountable review, real invitation, real account, mail send or deployment is
represented by this development permission or implementation.

## End-to-end implementation update

The subsequent explicit “Complete PR #46 End-to-End Invitation Enrollment”
instruction authorizes finishing the bounded workflow without live activation.
The [current runbook](../runbooks/PWC-INVITATION-ENROLLMENT.md) replaces the
historical unfinished-implementation inventory above. Full password/MFA account
creation now happens only at final successful confirmation; an abandoned setup
has no partial User to delete or activate. All steps commit within 24 hours.
The original product and narrow development permissions are preserved. Real
source/privacy/mail/transport/deployment and independent review remain separate;
no agent or merge supplies those approvals.
