#!/usr/bin/env bash
# End to end: create a GPU machine on AWS, then install GroundX on it.
#
# Prerequisites (once per AWS account):
#   - AWS CLI logged in with permission to launch EC2 instances
#   - A subnet with internet access, and a security group (no inbound needed)
#   - An instance profile that allows Systems Manager access, so this script
#     can run commands on the machine without SSH keys
#     (AWS's "AmazonSSMRoleForInstancesQuickSetup" works)
#
# Usage:
#   SUBNET_ID=subnet-xxxx SECURITY_GROUP_ID=sg-xxxx ./provision-and-install-aws.sh
#
# Cost: a g6e.2xlarge is ~$2.25/hour. Stop the instance when not in use.
set -euo pipefail
: "${SUBNET_ID:?set SUBNET_ID}"
: "${SECURITY_GROUP_ID:?set SECURITY_GROUP_ID}"
INSTANCE_TYPE="${INSTANCE_TYPE:-g6e.2xlarge}"
PROFILE_NAME="${INSTANCE_PROFILE:-AmazonSSMRoleForInstancesQuickSetup}"
HERE="$(cd "$(dirname "$0")" && pwd)"

# GPU machine image with NVIDIA drivers and Docker preinstalled
AMI=$(aws ssm get-parameter \
  --name /aws/service/deeplearning/ami/x86_64/base-oss-nvidia-driver-gpu-ubuntu-22.04/latest/ami-id \
  --query 'Parameter.Value' --output text)

echo "launching $INSTANCE_TYPE ..."
INSTANCE=$(aws ec2 run-instances \
  --image-id "$AMI" --instance-type "$INSTANCE_TYPE" \
  --subnet-id "$SUBNET_ID" --security-group-ids "$SECURITY_GROUP_ID" \
  --iam-instance-profile "Name=$PROFILE_NAME" \
  --block-device-mappings '[{"DeviceName":"/dev/sda1","Ebs":{"VolumeSize":500,"VolumeType":"gp3"}}]' \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=groundx-single-node}]' \
  --query 'Instances[0].InstanceId' --output text)
echo "instance: $INSTANCE — waiting for it to accept commands..."

for i in $(seq 1 30); do
  STATE=$(aws ssm describe-instance-information \
    --filters "Key=InstanceIds,Values=$INSTANCE" \
    --query 'InstanceInformationList[0].PingStatus' --output text 2>/dev/null || true)
  [ "$STATE" = "Online" ] && break
  sleep 20
done
[ "$STATE" = "Online" ] || { echo "machine never came online for remote commands"; exit 1; }

echo "copying install files and starting the installation (30-45 minutes)..."
SCRIPT_B64=$(base64 -w0 "$HERE/single-node-install.sh" 2>/dev/null || base64 -i "$HERE/single-node-install.sh")
VALUES_B64=$(base64 -w0 "$HERE/values-single-node.yaml" 2>/dev/null || base64 -i "$HERE/values-single-node.yaml")
CMD=$(aws ssm send-command --instance-ids "$INSTANCE" \
  --document-name AWS-RunShellScript --timeout-seconds 5400 \
  --parameters "commands=[\
\"mkdir -p /home/ubuntu/deploy\",\
\"echo $SCRIPT_B64 | base64 -d > /home/ubuntu/deploy/single-node-install.sh\",\
\"echo $VALUES_B64 | base64 -d > /home/ubuntu/deploy/values-single-node.yaml\",\
\"chmod 755 /home/ubuntu/deploy/single-node-install.sh && chown -R ubuntu:ubuntu /home/ubuntu/deploy\",\
\"sudo -u ubuntu /home/ubuntu/deploy/single-node-install.sh 2>&1 | tail -30\"]" \
  --query 'Command.CommandId' --output text)

while true; do
  S=$(aws ssm get-command-invocation --command-id "$CMD" --instance-id "$INSTANCE" \
      --query 'Status' --output text)
  echo "install: $S"
  [ "$S" != "InProgress" ] && break
  sleep 60
done
aws ssm get-command-invocation --command-id "$CMD" --instance-id "$INSTANCE" \
  --query 'StandardOutputContent' --output text | tail -20
echo ""
echo "Instance: $INSTANCE  (stop it when idle: aws ec2 stop-instances --instance-ids $INSTANCE)"