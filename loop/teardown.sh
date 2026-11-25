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
# Every Azure OpenAI account in the group (there is one per region used for model quota), purged so the names can be reused.
az cognitiveservices account list -g "$RG" --query "[?kind=='OpenAI'].[name,location]" -o tsv | while read -r name loc; do
  az cognitiveservices account delete -g "$RG" -n "$name" -o none 2>/dev/null && echo "openai account $name deleted"
  az cognitiveservices account purge -g "$RG" -n "$name" -l "$loc" -o none 2>/dev/null && echo "openai account $name purged" || true
done

# Anything the builder provisioned during write-enabled runs.
ids=$(az resource list -g "$RG" --tag purpose=samples-factory --query "[].id" -o tsv)
if [[ -n "$ids" ]]; then
  echo "$ids" | xargs -n1 az resource delete --ids -o none && echo "tagged builder resources deleted"
fi

echo "Remaining resources in $RG:"
az resource list -g "$RG" --query "[].{name:name, type:type}" -o table
