# Service registration

Auto-registration submits a background convergence command during FastAPI
lifespan startup. Explicit registration uses `await nacos.register_instance(app)`.
Both use the same last-command-wins state machine, finite retries, conservative
failure classification and low-frequency recovery for proven transient errors.

At most one worker and one Naming RPC are active per app/PID. A successful
registration caches its exact service, group, cluster, IP, port and ephemeral
flag. Deregistration always uses that cached identity even if configuration is
later changed. Shutdown waits only within a bounded SDK timeout.

