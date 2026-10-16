# Private VM deployment

Prepared configuration; no host has been selected or deployed. This release is a
private workspace, not an authenticated public multi-tenant service. Docker
access gives the controller powerful host privileges. Use a dedicated VM, keep
port 8501 private, and access through SSH. Do not publish the Docker socket or
mount it inside candidate containers.

## Prepare your chosen host

Use a Linux VM with Python 3.11+, venv support, Git and a Linux Docker engine.
For hosted inference a CPU VM is sufficient; size it for concurrent sandboxes.
For local inference allow roughly 16 GB RAM and install a local Ollama runtime
separately. GPU training belongs in the Colab notebook, not this service.

1. Create a dedicated `vericode` user and place this repository at `/opt/vericode`,
   owned by that user. Give only this trusted operator access to the Docker
   engine (the supplied unit expects a `docker` group). Keep SSH restricted to
   approved users; do not add a public inbound rule for port 8501 or Docker.
2. As `vericode`, run `bash deploy/bootstrap.sh` from the checkout. This installs
   the pinned UI dependency and builds the trusted runner image. It does not
   create cloud infrastructure, download model weights or send API requests.
3. Review `/opt/vericode` and the user/group names in `deploy/vericode.service`.
   Install and start the unit as the host administrator:

   ```bash
   sudo install -m 0644 deploy/vericode.service /etc/systemd/system/vericode.service
   sudo systemctl daemon-reload
   sudo systemctl enable --now vericode
   sudo systemctl status vericode
   ```

4. On your laptop, open the tunnel and then visit `http://127.0.0.1:8501`:

   ```bash
   ssh -L 8501:127.0.0.1:8501 YOUR_USER@YOUR_SERVER
   ```

5. In Models & API, enter your own key, verify it, choose a model and explicitly
   authorize a USD limit. Select the provider and Docker sandbox in Repair
   workbench. Verify an example repair before using your own code.

## Data and operating limits

API keys stay in each Streamlit server session's memory. They are not saved in
environment files, run records or candidate containers. Disconnect to forget a
key. A new session after a server restart requires reconnecting. Browser tabs
with separate sessions have separate connections; this is not user authentication.

The private SQLite ledger at `artifacts/private/usage.sqlite3` records only a
provider/key hash, authorized cap, reservation IDs, amounts and states. Preserve
this directory during upgrades; deleting it discards local spending history.
Do not copy it between unrelated operators. Restrict backups to the operator.
Run history is session memory: export records before closing the session.

An unresolved HTTP/timeout/billing outcome retains its entire reservation and
blocks further requests with that key, including after restart. An operator
must compare provider activity against the request time and reconcile offline;
there is intentionally no browser button that silently refunds uncertain calls.
Limits cover this app's requests only; set provider-side limits too. OpenAI
costs are estimates at fetched standard rates, not the organization's invoice.

The systemd unit and SSH recipe were statically reviewed on Windows. Linux
installation and end-to-end host validation remain deployment acceptance steps.
Do not expose this controller publicly. Public SaaS requires authentication,
tenant authorization, isolated worker hosts/queues, secret storage, audited
retention and a separate security review.

Update by stopping the service, preserving `artifacts/private`, reviewing the
new code, rerunning the bootstrap and starting the service. Roll back by
checking out the previous reviewed commit and reinstalling it; preserve the
ledger. Never run unreviewed repository code as the service user.
