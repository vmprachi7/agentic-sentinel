# Killing Kubernetes Pod Failures at Root Cause

> Medium draft — tags to add: devops, ai, kubernetes, monitoring

Kubernetes pod failures often hide a more sinister issue: memory thrashing.

---

### Memory Thrashing vs OOM: Uncovering the Root Cause of Kubernetes Pod Failures
#### The Problem
In a Kubernetes environment, pod failures can occur due to various reasons, including Out-of-Memory (OOM) errors. However, simply treating an OOMKilled event as an isolated failure can lead to incomplete post-mortem analysis. In reality, a kernel-initiated kill is often the final act following a period of severe degradation known as memory thrashing. This occurs when the system spends a disproportionate amount of time attempting to reclaim memory, causing starvation and eventual termination of processes. Understanding the difference between memory thrashing and OOM is crucial for effective troubleshooting and prevention of pod failures.

#### Technical Breakdown
Memory thrashing can be identified by analyzing the Pressure Stall Information (PSI) metrics, which provide insights into the system's memory reclaiming efficiency. A high PSI rate indicates that processes are stalling while the kernel scrambles to free memory pages. In contrast, a low PSI rate suggests that the kernel is efficiently reclaiming memory.

To investigate node-level health and identify potential memory exhaustion, you can use the following `kubectl` command:
```bash
kubectl get events --field-selector=involvedObject.kind=Node --field-selector=involvedObject.name=<node-name>
```
Look for `SystemOOM` or `NodeHasMemoryPressure` events, which can indicate that the pod was a victim of its QoS class or node pressure rather than its own memory leak.

For a more detailed analysis, inspect the kernel logs to determine the exact actions taken by the OOM killer:
```bash
dmesg -T | grep -i -E 'oom-kill|killed process'
```
This will help you understand the sequence of events leading up to the pod failure.

#### The Fix / Pattern
To mitigate memory thrashing and prevent OOM errors, follow these best practices:

1. **Monitor PSI metrics**: Regularly check PSI rates to detect potential memory thrashing issues.
2. **Adjust QoS classes**: Ensure that pods are assigned the correct QoS class based on their memory requirements.
3. **Optimize container memory limits**: Set realistic memory limits for containers to prevent over-allocation and reduce the likelihood of OOM errors.
4. **Implement efficient memory reclaiming**: Use mechanisms like page cache flushing or swapping to reduce memory pressure.

Example configuration snippet to adjust QoS classes and container memory limits:
```yml
apiVersion: v1
kind: Pod
metadata:
  name: example-pod
spec:
  containers:
  - name: example-container
    resources:
      requests:
        memory: 128Mi
      limits:
        memory: 256Mi
  qosClass: Burstable
```
#### Key Takeaway
When investigating pod failures in a Kubernetes environment, it is essential to distinguish between memory thrashing and OOM errors, as the former can be a precursor to the latter, and addressing the root cause of memory thrashing can prevent subsequent OOM errors.