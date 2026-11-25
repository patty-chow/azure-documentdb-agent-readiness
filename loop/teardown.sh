#!/usr/bin/env bash
# Delete every billable resource the samples factory created. The resource group stays.
# Usage: loop/teardown.sh [--yes]
set -euo pipefail
RG="${FACTORY_RG:-documentdb-samples-rg}"
CLUSTER="${FACTORY_CLUSTER:-ddb-samples-shared}"
OPENAI="${FACTORY_OPENAI_ACCOUNT:-ddbsf-65447d}"
LOCATION="${FACTORY_LOCATION:-eastus}"

echo "This deletes, in resource group $RG:"
echo "  - DocumentDB cluster      $CLUSTER"
echo "  - Azure OpenAI account    $OPENAI (and purges it, so the name can be reused)"
echo "  - anything else the builder created there with tag purpose=samples-factory"
if [[ "${1:-}" != "--yes" ]]; then
  read -r -p "Type the resource group name to continue: " confirm
  [[ "$confirm" == "$RG" ]] || { echo "aborted"; exit 1; }
fi

az documentdb mongocluster delete -g "$RG" -n "$CLUSTER" --yes --no-wait -o none 2>/dev/null && echo "cluster delete requested" || echo "cluster not found"
az cognitiveservices account delete -g "$RG" -n "$OPENAI" -o none 2>/dev/null && echo "openai account deleted" || echo "openai account not found"
az cognitiveservices account purge -g "$RG" -n "$OPENAI" -l "$LOCATION" -o none 2>/dev/null && echo "openai account purged" || true

# Anything the builder provisioned during write-enabled runs.
ids=$(az resource list -g "$RG" --tag purpose=samples-factory --query "[].id" -o tsv)
if [[ -n "$ids" ]]; then
  echo "$ids" | xargs -n1 az resource delete --ids -o none && echo "tagged builder resources deleted"
fi

echo "Remaining resources in $RG:"
az resource list -g "$RG" --query "[].{name:name, type:type}" -o table
