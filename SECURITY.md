# Security and data handling

## Persistent travel memory

Persistent memory is intentionally disabled. The legacy memory router is not registered
in the FastAPI application, and the chat agent does not create or accept user identities.
Do not mount the legacy memory router or restore memory writes until an authentication
provider verifies access tokens server-side and every database operation is scoped to the
verified subject.

A client-supplied UUID, email address, or other opaque identifier is not proof of identity.
When memory is reintroduced, add ownership metadata and migrations, enforce subject-scoped
reads and writes, test cross-account read/update/delete denial, and document retention and
account deletion.

Tracking: GitHub issue #13. The issue remains open until an authentication provider and
tenant-scoped persistence are implemented and verified.
