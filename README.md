# Unused AMI Management Tool

This tool is a Python script that automates the process of identifying and managing unused Amazon Machine Images (AMIs) in AWS. It retrieves all AMIs owned by a specific AWS account, compares them with the AMIs currently in use by EC2 instances, deregisters the unused AMIs, and deletes their associated EBS volume snapshots.

## Features

- **Identify AMIs in use**: Scans all EC2 instances to collect AMIs currently in use.
- **Find unused AMIs**: Compares owned AMIs against those in use.
- **No-op Mode**: Preview AMIs and snapshots that would be deleted, without making any changes.
- **Deregister unused AMIs**: Automatically deregisters unused AMIs unless tagged with `archive=true`.
- **Delete associated snapshots**: Deletes EBS volume snapshots linked to the deregistered AMIs unless tagged with `archive=true`.
- **Error handling**: Implements robust error handling and descriptive error messages for better debugging and user experience.

---

## Prerequisites

1. **Python 3.11+**:
   - Ensure Python is installed on your system.
   - You can download it from [python.org](https://www.python.org/downloads/).

2. **AWS CLI**:
   - Install the AWS CLI and configure it with the appropriate access credentials.
   - Documentation: [AWS CLI Installation Guide](https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html)

3. **Boto3**:
   - Install the AWS SDK for Python (Boto3) using pip:
     ```bash
     pip install boto3
     ```

4. **IAM Permissions**:
   - Ensure the AWS user/role running this script has the following permissions:
     - `ec2:DescribeInstances`
     - `ec2:DescribeImages`
     - `ec2:DeregisterImage`
     - `ec2:DeleteSnapshot`

---

## Installation

Clone this repository and navigate to the project directory:
```bash
git clone https://github.com/your-username/unused-ami-management-tool.git
cd unused-ami-management-tool
chmod +x unused-ami-management-tool.py
```

## Usage

Run the script with the required --owner_account_id argument to specify the AWS account ID that owns the AMIs:
```bash
python3 unused_ami.py --owner_account_id <your_aws_account_id>
```

### Example:
```bash
python3 unused_ami.py --owner_account_id 123456789012
```

### Expected Output:
The script will:

1. Retrieve and list all AMIs associated with EC2 instances.
2. Retrieve and list all AMIs owned by the provided AWS account.
3. Identify unused AMIs and display a summary.
4. If `--no-op` is provided, it lists AMIs and snapshots that would be modified. Without `--no-op`, the script deregisters unused AMIs and deletes their associated snapshots.

## Error Handling
- **Missing --owner_account_id**: If the --owner_account_id argument is not provided, the script will terminate with a descriptive error message:

```python
Validation Error: The owner_account_id parameter is required and cannot be None.
```
- **AWS API Errors**: All errors related to AWS API calls are logged with details to help with debugging.

- **Snapshot Deletion Failures**: If a snapshot cannot be deleted, the script logs the specific snapshot ID and error message but continues processing other snapshots.

- **Tagging Exceptions**: The script skips AMIs and snapshots tagged with archive=true and logs these as skipped.

## Best Practices
- **Test in a Non-Production Environment**: Always test the script in a non-production environment to ensure it works as expected.

- **Backup Important Data**: Before running the script, ensure critical AMIs and snapshots are backed up if necessary.

- **Audit the Unused AMIs**: Review the list of unused AMIs and snapshots to confirm they are safe to delete.

- **IAM Principle of Least Privilege**: Ensure the AWS user/role running this script has only the necessary permissions to perform its tasks.
