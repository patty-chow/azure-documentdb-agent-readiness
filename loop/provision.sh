#!/usr/bin/env bash
# Create the Azure resources the samples loop needs, idempotently, in one resource group.
# Needs: az login done, the `documentdb` CLI extension (az extension add -n documentdb).
# Usage: loop/provision.sh            then copy the printed lines into .env
set -euo pipefail
RG="${FACTORY_RG:-documentdb-samples-rg}"
LOCATION="${FACTORY_LOCATION:-eastus}"
OPENAI="${FACTORY_OPENAI_ACCOUNT:-ddbsf-$(openssl rand -hex 3)}"
MODEL="${FACTORY_MODEL_NAME:-gpt-5-mini}"
MODEL_VERSION="${FACTORY_MODEL_VERSION:-2025-08-07}"
CAPACITY="${FACTORY_MODEL_CAPACITY:-500}"          # thousands of tokens per minute; check: az cognitiveservices usage list -l $LOCATION
CLUSTER="${FACTORY_CLUSTER:-ddb-samples-shared}"
ADMIN_USER="${FACTORY_CLUSTER_ADMIN:-factoryadmin}"
HERE="$(cd "$(dirname "$0")/.." && pwd)"

az group create -n "$RG" -l "$LOCATION" -o none
PRINCIPAL=$(az ad signed-in-user show --query id -o tsv)

# 1. Azure OpenAI, Entra-only, one deployment, caller granted Cognitive Services OpenAI User.
existing=$(az cognitiveservices account list -g "$RG" --query "[?kind=='OpenAI'].name | [0]" -o tsv)
if [[ -n "$existing" ]]; then
  OPENAI="$existing"; echo "Azure OpenAI account $OPENAI already exists"
else
  az deployment group create -g "$RG" -n "openai-$OPENAI" --template-file "$HERE/infra/azure-openai.json" \
    --parameters accountName="$OPENAI" modelName="$MODEL" modelVersion="$MODEL_VERSION" deploymentSku=GlobalStandard \
                 capacity="$CAPACITY" principalId="$PRINCIPAL" -o none
  echo "Azure OpenAI account $OPENAI created with deployment $MODEL"
fi
ENDPOINT=$(az cognitiveservices account show -g "$RG" -n "$OPENAI" --query properties.endpoint -o tsv)

# 2. One shared DocumentDB cluster (M30: the smallest tier with DiskANN vector indexes).
if az documentdb mongocluster show -g "$RG" -n "$CLUSTER" -o none 2>/dev/null; then
  echo "cluster $CLUSTER already exists"
  PW=""
else
  PW="$(openssl rand -base64 24 | tr -d '/+=' | cut -c1-24)Aa1!"
  az documentdb mongocluster create -n "$CLUSTER" -g "$RG" --location "$LOCATION" \
    --admin-user "$ADMIN_USER" --admin-password "$PW" --tier M30 --storage-size 128 --storage-type PremiumSSDv2 \
    --shard-count 1 --high-availability Disabled --public-network-access Enabled \
    --auth-allowed-modes NativeAuth MicrosoftEntraID --tags purpose=samples-factory -o none
  echo "cluster $CLUSTER created"
fi

# 3. Let this machine reach the cluster.
MY_IP=$(curl -s --max-time 10 https://api.ipify.org)
az documentdb mongocluster firewall-rule create --cluster-name "$CLUSTER" -g "$RG" -n "loop-runner-$(echo "$MY_IP" | tr . -)" \
  --start-ip-address "$MY_IP" --end-ip-address "$MY_IP" -o none
HOST=$(az documentdb mongocluster show -g "$RG" -n "$CLUSTER" --query "properties.connectionString" -o tsv | sed -E 's#^mongodb\+srv://[^@]*@##; s#/.*##')

echo
echo "Put these in .env (never commit it):"
echo "FACTORY_PROVIDER=azure_openai"
echo "FACTORY_MODEL=$MODEL"
echo "AZURE_OPENAI_ENDPOINT=${ENDPOINT%/}"
if [[ -n "$PW" ]]; then
  echo "DOCUMENTDB_URI=mongodb+srv://$ADMIN_USER:<the password printed once below>@$HOST/?tls=true&authMechanism=SCRAM-SHA-256&retrywrites=false&maxIdleTimeMS=120000"
  echo
  echo "Cluster admin password (shown once, store it in a password manager):"
  echo "$PW"
else
  echo "DOCUMENTDB_URI=mongodb+srv://$ADMIN_USER:<existing password>@$HOST/?tls=true&authMechanism=SCRAM-SHA-256&retrywrites=false&maxIdleTimeMS=120000"
fi
