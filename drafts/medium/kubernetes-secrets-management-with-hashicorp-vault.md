# Kubernetes Secrets Management with HashiCorp Vault

> Medium draft — tags to add: devops, ai, kubernetes, security

Hardcoding secrets in Kubernetes is a ticking time bomb for security breaches.

---

### The Problem: Managing Secrets in Kubernetes with HashiCorp Vault
In production environments, managing secrets such as API keys, database credentials, and TLS certificates is crucial for security. Hardcoding these secrets into container images or source code repositories is a critical security vulnerability. However, manually managing secrets using native Kubernetes Secrets can lead to issues with rotation, access control, and auditing. This is where HashiCorp Vault comes in, providing a centralized secrets management system. But, integrating Vault with Kubernetes can be complex, especially when dealing with dynamic secrets and lease management.

### Technical Breakdown: Integrating HashiCorp Vault with Kubernetes
To integrate Vault with Kubernetes, we need to use the Vault Agent Injector. This injector automatically injects Vault secrets into Kubernetes pods. Here's an example configuration snippet:
```yml
apiVersion: v1
kind: Pod
metadata:
  name: example-pod
spec:
  containers:
  - name: example-container
    image: example-image
    env:
    - name: DATABASE_URL
      value: vault:database/creds/example-cred
```
In this example, the `DATABASE_URL` environment variable is populated with a secret from Vault. The `vault:database/creds/example-cred` path refers to a credential stored in Vault.

To use the Vault Agent Injector, we need to create a Kubernetes service account and bind it to a Vault policy. Here's an example of how to create a service account and bind it to a Vault policy:
```bash
kubectl create sa vault-agent
kubectl annotate sa vault-agent vault.hashicorp.com/agent-inject: "true"
vault policy write vault-agent - <<EOF
path "database/creds/*" {
  capabilities = ["read"]
}
EOF
vault auth kube create sa vault-agent -policy=vault-agent
```
This configuration allows the Vault Agent Injector to inject secrets into pods running with the `vault-agent` service account.

### The Fix / Pattern: Dynamic Secrets and Lease Management
To manage dynamic secrets and leases, we need to use the Vault Kubernetes Auth Backend. This backend allows us to authenticate Kubernetes service accounts with Vault and manage leases for secrets. Here's an example of how to configure the Kubernetes Auth Backend:
```hcl
path "auth/kubernetes/*" {
  capabilities = ["read", "list"]
}

path "database/creds/*" {
  capabilities = ["read"]
}

path "sys/leases/revoke" {
  capabilities = ["update"]
}
```
In this example, the `auth/kubernetes/*` path allows Kubernetes service accounts to authenticate with Vault. The `database/creds/*` path allows the Vault Agent Injector to read secrets from Vault. The `sys/leases/revoke` path allows the Vault Agent Injector to revoke leases for secrets.

To use dynamic secrets and lease management, we need to create a Kubernetes deployment with the Vault Agent Injector. Here's an example deployment configuration:
```yml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: example-deployment
spec:
  selector:
    matchLabels:
      app: example-app
  template:
    metadata:
      labels:
        app: example-app
    spec:
      serviceAccountName: vault-agent
      containers:
      - name: example-container
        image: example-image
        env:
        - name: DATABASE_URL
          value: vault:database/creds/example-cred
```
In this example, the `example-deployment` deployment uses the `vault-agent` service account and injects secrets from Vault using the Vault Agent Injector.

### Key Takeaway
When managing secrets in Kubernetes with HashiCorp Vault, using the Vault Agent Injector with dynamic secrets and lease management provides a secure and scalable solution for secrets management, allowing for fine-grained access control and auditing of sensitive data.