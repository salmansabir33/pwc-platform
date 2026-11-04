# C1 product-owner decision — P4-C1-20261104.1

**Status: PRODUCT ACCEPTED — C1-R01 through C1-R08 exactly as proposed.**
**Not an implementation/security/privacy/transport approval.**

## Decision and provenance

Source: the explicit product-owner instruction in this Arena conversation titled
**“PWC — C1 Product Decision Accepted; Proceed Toward Live Membership Category
Management”**, against merged baseline `27d445824f7f62114cd592e119250b3f92e14c21`.
The instruction states:

> The product owner has accepted **C1-R01 through C1-R08 exactly as proposed** in:
>
> `docs/reviews/PWC-P4-C1-CATEGORY-POLICY-DISPOSITIONS-v1.0.md`
>
> Proposal identity: `P4-C1-20261104.1`.

This record attributes the decision to the product owner **as explicitly
communicated in that instruction**. It does not infer a person's legal identity
from the repository account or from agent-authored GitHub comments. No reviewer
name, signature, signing timestamp or external approval URL was supplied; none
is manufactured here. An accountable identity/charter, actual decision date and
immutable evidence link remain to be attached by the owner/review custodian for
the formal evidence worksheet. This evidence gap does not reopen or erase the
explicit product decision already communicated.

Accepted artifact at the baseline above:

- Path: `docs/reviews/PWC-P4-C1-CATEGORY-POLICY-DISPOSITIONS-v1.0.md`
- SHA256: `f59bcf944ac040375632a35a7850e3206ec56719e77f9b481959ab67ad8c1537`
- [Immutable source](https://github.com/salmansabir33/pwc-platform/blob/27d445824f7f62114cd592e119250b3f92e14c21/docs/reviews/PWC-P4-C1-CATEGORY-POLICY-DISPOSITIONS-v1.0.md)

The historical proposal is unchanged, including its then-PENDING review statuses.
This later scoped record is the current product disposition; it is not a rewrite
or blanket closure of the proposal's other accountable charters.

## Scope locked by the decision

All eight rows are accepted without amendments. In particular:

- **R04:** one current category per same-NGO membership in the initial member
  slice; its person/identity/member constraints still belong to the affected C2
  implementation contract, not to C1 category storage alone.
- **R05:** every new aggregate policy version requires explicit re-review of all
  older pending applications, including unrelated additions and display-only
  changes. No exception is inferred for “harmless” changes.
- **R08:** ALL fee and renewal configuration is deferred from C1; not configured
  does not mean zero/free/permanent membership.

R01–R03 and R06–R07 retain their exact identity, normalization, lifecycle,
revision, deactivation and history/effective-time choices. Do not reopen these
product choices without an explicit change request. C3/C4 are not C1 dependencies.

## Exact remaining accountable acceptance / operation boundaries

| Contract / accountable charter | Outstanding concrete acceptance | Operations blocked |
| --- | --- | --- |
| P4-03 + trusted issuer owners, IAM/security and NGO governance; underlying 04C/GM/root owners | Actual trusted issuer/root and authenticated source; versioned action/bundle/subject/tenant/target bindings for the five C1 literal actions in parent §4; assurance class, single-actor/independent review and conflict rules per command; current expiry/revocation | Private reads, policy changes, create/rename/deactivate; installing any membership grant |
| P4-06 DB/API + auth/security | Full lock order against existing auth helpers, deadlines/isolation/primary DB clock, revocation linearization; restricted runtime/writer/verifier principals and signatures; create-slot/replay/rollback/unknown-outcome contract; atomic business/history/audit/receipt rules | Persistent model/writer/migration installation under the assignment's implementation gate; transactional writes and receipts |
| Category-only disclosure, privacy/legal + NGO governance + DB/API | Exact fields/audiences for current definitions and historical policy values; actor representation, history/audit/receipt minimization, retention/access and legal hold where applicable | All private projections and retained audit/receipt disclosure; no roster or person data implied |
| P4-09 API/auth/security + web/mobile owners + privacy | Exact endpoint/request/response/error/pagination/revision/receipt contract; CSRF browser transport; approved native transport/permissions/privacy and revocation/cache handling | Actual React management and Flutter networking/actions |
| Remaining non-product P4-01 charters | NGO governance/DB/API and affected history privacy acceptance in the original row scopes | No assertion that the entire cross-owner P4-01 gate is closed |

PR39 has no accountable reviews; its agent-authored reconciliation comments are
explicitly technical evidence only. No authorized technical reviewer designation
or independent sign-off was supplied in the current instruction. The agent may
verify implementation, but cannot self-appoint to these charters or impersonate
reviewers. The implementation PR requests those exact reviews; no activation
switch, dormant privileged migration or grant is installed while they are absent.

## Permitted engineering in this change

Extract R02 label validation/comparison and R05 mode vocabulary into an
independent authority-free domain module, reused by the existing 05A foundation.
Tests cover Unicode/code-point limits, compatibility/case/whitespace collisions,
invalid input and display preservation. This is reusable value validation, not
another demonstration, database uniqueness, a privileged service or a management
UI. No new demo, schema, endpoint, permission or client transport is added.

## C2 dependency boundary

R04 and R05 product direction is settled, but C2 unclaimed admission additionally
needs P4-02 eligibility/actor/event decisions, P4-05 authoritative person/source/
revision/conflict rules, P4-04 minimized person/intake/retention acceptance and the
applicable P4-03/06/09 contracts. No name/contact match may link accounts. C1 value
validation can be reused; live C2 admission is not authorized by this decision.

## Founder direction — coordinated C1 continuation

Source: the explicit instruction in this Arena conversation titled **“PWC —
Finalize C1 Governance, Authorization and Technical Contracts”**. This records
Founder-level product/governance direction, not an authenticated technical issuer,
verified appointment instrument or independent execution sign-off. No legal name,
signature, decision timestamp or private evidence reference was supplied or inferred.

The Founder approves permanent Founder oversight and protected emergency authority;
separate Governance, Technical, Membership, Finance and Operations roles; one
personal identity with compatible roles; compatible interim Founder assignments;
future elected-official reassignment without password sharing; explicit NGO scope
and departmental separation; secure PostgreSQL/audit/revision controls; restricted
private data; authenticated Django/React/Flutter communication; and unchanged
C1-R01–R08. Authenticated communication is direction, not acceptance of a new
credential transport or permission boundary.

**Scoped interpretation:** permanent oversight is an enduring governance function,
not an immortal credential, nonrevocable grant or universal NGO reader. Individual
sessions, role assignments and proofs remain scoped, expiring/revocable and audited.
Emergency authority does not imply private-data disclosure, impersonation, grant
issuance or bypass of independent verification. Pending its exact accepted responder
contract it confers no executable power; recommend restrict-only incident containment.
Elected successors receive their own verified personal assignments and explicit
scope; revoke superseded assignments and rotate/revoke affected sessions/intents,
not transfer passwords. None of these directions appoints an actual human to a
technical/security/privacy charter.

**Existing independence requirements preserved:** the 04C governance/reviewer
arrangements require two distinct natural persons for Super Admin and Verification
Officer and an independent provisioning confirmer separate from executor and
beneficiary. Founding authority cannot independently approve its own beneficial
grant. Compatible interim roles cannot collapse these specific separations.
Locked F1–F9/E05 and the §12 D3–D6/minimum-D12 pending acceptance are not amended.
A change to genuinely independent-person requirements needs an explicit change
request; it is not implied by compatible-role approval.

The five existing requests in issue #42 carry the coordinated executable proposals
and acceptance conditions. Product/governance directions above are recorded as
communicated; technical proposals remain proposals until the actual accountable
reviewers accept their exact immutable version with scope, evidence and exclusions.
No privilege-bearing schema, writer, endpoint, grant or native adapter follows
from this record. Do not open another product approval cycle for R01–R08.

## Founder trust establishment — AbuBakr nomination

**Recorded direction:** in the explicit Arena instruction **“PWC — Founder Trust
Establishment and Independent Verification”**, the Founder nominates **AbuBakr**
as independent verifier. This is a nomination, not completed identity proofing,
verified natural-person independence, acceptance of the role, appointment as the
04C Verification Officer, technical/legal qualification or an activated grant.
No account UUID/email, legal identity, signature, timestamp or external evidence
was supplied; none is inferred from the name or a GitHub account. No lookup,
account creation or privilege assignment by display name is authorized.

**Precisely limited proposed responsibility:** inspect the Founder's identity and
claimed founding governance instrument using the independently accepted evidence
rubric; confirm the exact personal account-to-person binding via approved channels;
declare actual-person independence/conflicts; record accept/reject/needs-information
against the immutable evidence/case revision and scope. The Founder cannot submit
and approve their own verification. AbuBakr cannot self-certify the authority of
his own nomination or the trust root. A distinct account alone is not independence.
This review is not an NGO verification, departmental appointment, database/security/
legal sign-off or grant issuer. It grants no NGO-private data, finance, membership,
impersonation, password reset or emergency disclosure power. Restrict any future
case reader to this assigned case's minimized evidence under an accepted scope.

**AbuBakr's steps:** use his own existing PWC personal identity, or the ordinary
approved registration flow when legitimately available; retain sole control of his
password/MFA. Accept the bounded responsibility, independently establish identity
and conflicts through the appointed trust custodian, then review the exact Founder
case only after authenticated assignment and accepted evidence/reader/command
contracts exist. Return a revision-bound decision with real provenance through the
accepted channel. Never receive the Founder's password, TOTP seed or recovery codes.

**Founder's steps:** use the Founder's own personal account and MFA; provide the
actual founding instrument and identity/account-binding evidence to the approved
custodian, not public GitHub/chat; establish the lawful appointing source and the
separate authorized executor/confirmer arrangements. Nomination does not supply
that chain. Do not approve the Founder's own case or activate either participant's
authority by a role label. Elected successors receive individual scoped assignments;
permanent Founder governance oversight remains separate from revocable credentials
and departmental/private-data permissions.

**Execution boundary and dependencies:** issue #42 tracks AUTH-01/02 real trust
anchor and issuer/executor/confirmer/source evidence; AUTH-04/GM06 and §12 D3/D4
operation-bound assurance; AUTH-05 and §12 D5/D6 restricted reader/writer, lock,
revocation, audit and receipts; AUTH-08/minimum-D12 case evidence/privacy/custody
and retention. No new production actor, source key, personal evidence store,
verification endpoint or provisioning command is installed. Existing personal
identity/MFA/session flows may be used only in their accepted environment/transport;
04B case preparation is not a Founder trust or approval workflow.

**Can verification begin?** Nomination acknowledgement and offline coordination can
begin without transferring private evidence. Authenticated authoritative Founder
verification cannot begin in the application yet: accepted actual trust source,
verified reviewer binding/independence, case evidence policy and protected execution
contracts are not evidenced. Nomination narrows the reviewer candidate; it does not
close those gates. Locked F1–F9/E05 and distinct-person appointment rules remain
unchanged. No new generic governance report or demonstration is introduced.
