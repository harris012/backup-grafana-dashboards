## A Simple Python script to backup grafana dashboards



### Vault Agent Injector

Vault Agent Injector is a controller (custom implementation) that can add sidecar and init containers to kubernetes pods in runtime.
The job of the init container is to authenticate and retrieve secrets from the vault server using the pod service account place them in a shared location (In memory volume) where the application container can access them. You can use this implementation for kubernetes standalone pods, deployments, Statefuset, and Kubernetes jobs.

### How Does Vault Injector Work

The Vault Agent Injector is a Kubernetes Mutation Webhook Controller.
Meaning, it is a custom piece of code (controller) and a webhook that gets deployed in kubernetes that intercepts pod events like create and update to check if any agent-specific annotation is applied to the pod.
For example, if a pod gets deployed with an annotation.”vault.hashicorp.com/agent-inject: 'true'“, here is what happens.

1. Custom MutatingWebhookConfiguration sends a webhook with all pod information to the injector controller deployment.
2. Then the controller modifies the Pod spec in runtime to introduce a sidecar and init container agents to the actual pod specification.
3. Controller then returns the modifed object for object validation.
4. After validation the modified pod spec gets deloyed with a sidecar and init container.


So when the pod comes up, it will have the application container, a sidecar, and a init container.
So when the pod comes up, it will have the application container, a sidecar, and a init container.
The init container is responsible for retrieving the secrets. In addition, a sidecar container is required if your application uses dynamic secrets. Dynamic secrets are secrets that are created on-demand with expiration time. The sidecar container ensures that the latest secrets are present inside the pod after every secret renewal.
If your application does not use dynamic secrets, then the sidecar container is not required.