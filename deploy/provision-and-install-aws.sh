#!/usr/bin/env bash
# End to end: create a GPU machine on AWS, then install GroundX on it,
# using NVIDIA's hosted Nemotron as the language model.
#
# ── REQUIRED ─────────────────────────────────────────────────────────────────
#   export NVIDIA_API_KEY=nvapi-...       free at https://build.nvidia.com
#   export SUBNET_ID=subnet-...           a subnet with internet access
#   export SECURITY_GROUP_ID=sg-...       no inbound rules needed
#   AWS CLI logged in, allowed to launch EC2 instances
#   An instance profile allowing Systems Manager access (the default
#   "AmazonSSMRoleForInstancesQuickSetup" works) — that's how this script
#   runs commands on the machine, no SSH keys involved
# ── OPTIONAL ─────────────────────────────────────────────────────────────────
#   INSTANCE_TYPE      default g6e.2xlarge (~$2.25/hr — stop it when idle)
#   INSTANCE_PROFILE   default AmazonSSMRoleForInstancesQuickSetup
# ─────────────────────────────────────────────────────────────────────────────
#
# Usage:  ./provision-and-install-aws.sh
#
# Note: your NVIDIA key is delivered to the machine through AWS Systems
# Manager and is visible in your own account's command history. Use your
# secrets manager instead for anything beyond a demo.
set -euo pipefail
: "${NVIDIA_API_KEY:?export NVIDIA_API_KEY first (free at build.nvidia.com)}"
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
\"sudo -u ubuntu env NVIDIA_API_KEY=$NVIDIA_API_KEY /home/ubuntu/deploy/single-node-install.sh 2>&1 | tail -30\"]" \
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