# Terraform Drift Detection and Remediation Tactics

> Medium draft — tags to add: devops, ai, terraform, aws

Terraform drift is a silent killer of infrastructure reliability, causing outages and breakages without warning.

---

### Terraform Drift: The Silent Production Risk
#### The Problem
Terraform drift is a silent production risk that can cause outages and breakages in infrastructure provisioning. It occurs when the actual infrastructure configuration deviates from the intended state defined in Terraform configurations. This mismatch can lead to unexpected behavior, security vulnerabilities, and compliance issues. Drift can happen due to various reasons such as emergency hotfixes in the console, forgotten manual changes during incidents, resources created outside IaC, or teams moving faster than governance.

#### Technical Breakdown
To understand how Terraform drift occurs, let's consider a simple example. Suppose we have a Terraform configuration that provisions an AWS EC2 instance:
```terraform
# File: main.tf
provider "aws" {
  region = "us-west-2"
}

resource "aws_instance" "example" {
  ami           = "ami-abc123"
  instance_type = "t2.micro"
}
```
In this example, the Terraform configuration defines an AWS EC2 instance with a specific AMI and instance type. However, if someone manually updates the instance type in the AWS console to `t2.large`, the actual infrastructure configuration will deviate from the intended state defined in Terraform. This creates a drift between the two states.

To detect drift, Terraform provides the `terraform plan` command, which generates an execution plan that describes the changes required to reach the desired state. However, this command only detects changes that are visible to Terraform. If changes are made outside of Terraform, such as through the AWS console, `terraform plan` will not detect them.

#### The Fix / Pattern
To prevent or mitigate Terraform drift, several strategies can be employed:

1. **Use a remote backend**: Store Terraform state in a remote backend, such as AWS S3, to ensure that the state is persisted and versioned. This allows multiple team members to collaborate on infrastructure changes without overwriting each other's changes.
2. **Implement GitOps**: Use Git as the single source of truth for infrastructure configuration. This ensures that all changes are versioned and tracked, making it easier to detect and prevent drift.
3. **Use automated testing and validation**: Implement automated testing and validation to ensure that infrastructure changes are correct and consistent with the intended state.
4. **Monitor for drift**: Use tools like AWS Config or Spacelift to monitor for drift and alert on any changes that deviate from the intended state.

To detect and correct drift, you can use the following Terraform command:
```terraform
terraform apply -target=aws_instance.example
```
This command will update the EC2 instance to match the configuration defined in Terraform.

#### Key Takeaway
Terraform drift can be mitigated by implementing a combination of remote state storage, GitOps, automated testing and validation, and monitoring for drift, allowing teams to ensure that their infrastructure configuration remains consistent and up-to-date.