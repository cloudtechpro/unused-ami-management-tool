#!/usr/bin/env python3

import boto3
import argparse
import sys

# Boto3 setup with proper session handling for AWS API calls
def get_instance_amis():
    """Retrieve AMI IDs associated with EC2 instances in any state."""
    ec2 = boto3.client("ec2")
    amis_in_use = set()

    try:
        # Describe all EC2 instances
        response = ec2.describe_instances()

        # Iterate over reservations and instances to collect AMI IDs
        for reservation in response.get("Reservations", []):
            for instance in reservation.get("Instances", []):
                if "ImageId" in instance:
                    amis_in_use.add(instance["ImageId"])
    except Exception as e:
        print(f"Error retrieving instance AMIs: {e}", file=sys.stderr)
        sys.exit(1)

    return list(amis_in_use)

def get_owned_amis(owner_account_id):
    """Retrieve AMI IDs owned by the specified account ID."""
    ec2 = boto3.client("ec2")
    amis_owned = set()

    try:
        if not owner_account_id:
            raise ValueError("The owner_account_id parameter is required and cannot be None.")
        
        # Describe images owned by the account
        response = ec2.describe_images(Owners=[owner_account_id])

        # Collect AMI IDs from the response
        for image in response.get("Images", []):
            if "ImageId" in image:
                amis_owned.add(image["ImageId"])
    except ValueError as ve:
        print(f"Validation Error: {ve}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error retrieving owned AMIs: {e}", file=sys.stderr)
        sys.exit(1)

    return list(amis_owned)

def find_unused_amis(amis_in_use, amis_owned):
    """Find AMIs that are owned but not in use."""
    try:
        # Convert lists to sets for set operations
        amis_in_use_set = set(amis_in_use)
        amis_owned_set = set(amis_owned)

        # Compute the difference to find unused AMIs
        unused_amis = amis_owned_set - amis_in_use_set

        return list(unused_amis)
    except Exception as e:
        print(f"Error calculating unused AMIs: {e}", file=sys.stderr)
        sys.exit(1)

def deregister_unused_amis_and_delete_snapshots(unused_amis, no_op=False):
    """Deregister unused AMIs and delete their associated snapshots, skipping those tagged with 'archive=true'.
    
    If no_op is True, only list the AMIs and snapshots that would be modified.
    """
    ec2 = boto3.client("ec2")

    for ami in unused_amis:
        try:
            # Describe the AMI to get associated snapshot IDs and tags
            response = ec2.describe_images(ImageIds=[ami])
            snapshots = []
            skip_deletion = False

            for image in response.get("Images", []):
                # Check for the 'archive=true' tag
                tags = {tag["Key"]: tag["Value"] for tag in image.get("Tags", [])}
                if tags.get("archive") == "true":
                    print(f"Skipping AMI {ami} as it is tagged with 'archive=true'.")
                    skip_deletion = True
                    break

                for block_device in image.get("BlockDeviceMappings", []):
                    if "Ebs" in block_device and "SnapshotId" in block_device["Ebs"]:
                        snapshots.append(block_device["Ebs"]["SnapshotId"])

            if skip_deletion:
                continue

            # No-op mode: List AMIs and snapshots
            if no_op:
                print(f"[NO-OP] Would deregister AMI: {ami}")
                for snapshot_id in snapshots:
                    print(f"[NO-OP] Would delete snapshot: {snapshot_id}")
                continue

            # Deregister the AMI
            print(f"Deregistering AMI: {ami}")
            ec2.deregister_image(ImageId=ami)

            # Delete associated snapshots
            for snapshot_id in snapshots:
                try:
                    # Check if the snapshot is tagged with 'archive=true'
                    snapshot_response = ec2.describe_snapshots(SnapshotIds=[snapshot_id])
                    snapshot_tags = {tag["Key"]: tag["Value"] for tag in snapshot_response["Snapshots"][0].get("Tags", [])}
                    if snapshot_tags.get("archive") == "true":
                        print(f"Skipping snapshot {snapshot_id} as it is tagged with 'archive=true'.")
                        continue

                    print(f"Deleting snapshot: {snapshot_id}")
                    ec2.delete_snapshot(SnapshotId=snapshot_id)
                except Exception as e:
                    print(f"Error deleting snapshot {snapshot_id}: {e}", file=sys.stderr)

        except Exception as e:
            print(f"Error processing AMI {ami}: {e}", file=sys.stderr)

def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Find and deregister unused AMIs and delete associated snapshots.")
    parser.add_argument("--owner_account_id", required=True, help="AWS account ID of the AMI owner")
    parser.add_argument("--no-op", action="store_true", help="If specified, no modifications will be made; only list operations.")
    args = parser.parse_args()

    owner_account_id = args.owner_account_id
    no_op = args.no_op

    try:
        print("Retrieving AMIs associated with EC2 instances...")
        amis_in_use = get_instance_amis()

        print(f"Retrieving AMIs owned by account {owner_account_id}...")
        amis_owned = get_owned_amis(owner_account_id)

        print("Calculating unused AMIs...")
        unused_amis = find_unused_amis(amis_in_use, amis_owned)

        print("\nSummary:")
        print(f"AMIs in use: {len(amis_in_use)}")
        print(f"AMIs owned by account {owner_account_id}: {len(amis_owned)}")
        print(f"Unused AMIs: {len(unused_amis)}")

        print("\nList of unused AMIs:")
        for ami in unused_amis:
            print(ami)

        print("\nDeregistering unused AMIs and deleting associated snapshots (or listing operations if --no-op is specified)...")
        deregister_unused_amis_and_delete_snapshots(unused_amis, no_op=no_op)

    except Exception as e:
        print(f"An unexpected error occurred in the main function: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()