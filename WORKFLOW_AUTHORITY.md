# Workflow authority

Effective after the Linear → GitHub migration, the active workflow model for Curren is:

```text
GitHub Issues (`sangtrx/sang-workspace`) = task status, workflow checkpoints, blockers, next actions, user gates, active execution/session/worktree refs, writer ownership and completion evidence
GitHub repositories / PRs / commits          = source and artifact authority
ChatGPT Web                                  = primary orchestrator/control plane
BigLinux / Alpha-Linux / other runners       = bounded execution infrastructure
Linear                                       = retired read-only historical archive
```

Do not create, update, comment on, checkpoint, or route active Curren work through Linear. For migrated work, continue from the corresponding GitHub Issue in `sangtrx/sang-workspace`.

## Historical documents

Dated fundraising, research and delivery packets may contain `SAN-*`, “Linear issue”, “Linear checkpoint”, or similar wording because those documents captured the workflow state that existed when the packet was produced. Those references are retained as **historical provenance only**. They do not override this file and must not be used to determine current status, priority, blockers, next action, approval state or completion.

When a historical packet says to read/update Linear, interpret the active-work equivalent as: read/update the corresponding `sangtrx/sang-workspace` GitHub Issue. Do not rewrite historical evidence merely to make the old tracker name disappear.

Current source truth still comes from the relevant repository documents and exact GitHub SHA; workflow truth comes from `sangtrx/sang-workspace` GitHub Issues.
