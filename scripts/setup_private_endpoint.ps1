# ==============================================================================
# RamGAP — Azure Private Endpoint Setup
# ==============================================================================
# Setter opp:
#   - VNet med to subnets
#   - Private endpoint for backend App Service
#   - Private DNS zone (privatelink.azurewebsites.net)
#   - VNet Integration for frontend App Service (utgående trafikk via VNet)
#   - Deaktiverer public access på backend
#
# KRAV:
#   - Azure CLI installert
#   - App Service Plan må være Standard (S1) eller Premium for VNet Integration
#     (Basic B1 støtter IKKE VNet Integration)
#
# Kjør:
#   .\scripts\setup_private_endpoint.ps1
#
# Oppgi -ResourceGroup og -Location hvis de avviker fra standardverdiene.
# ==============================================================================

param(
    [string]$ResourceGroup      = "ramgap-rg",
    [string]$Location           = "swedencentral",
    [string]$BackendAppName     = "app-ramgap-backend",
    [string]$FrontendAppName    = "app-ramgap-frontend",
    [string]$VNetName           = "vnet-ramgap",
    [string]$VNetAddressPrefix  = "10.10.0.0/16",
    # Subnet for private endpoint (ingen delegering, private endpoint policies disabled)
    [string]$PeSubnetName       = "snet-pe-backend",
    [string]$PeSubnetPrefix     = "10.10.1.0/24",
    # Subnet for VNet Integration (frontend utgående trafikk)
    [string]$VIntSubnetName     = "snet-vint-frontend",
    [string]$VIntSubnetPrefix   = "10.10.2.0/24",
    [string]$PrivateEndpointName = "pe-ramgap-backend",
    [string]$DnsZoneName        = "privatelink.azurewebsites.net",
    [string]$DnsZoneLinkName    = "link-vnet-ramgap"
)

# ---------------------------------------------------------------------------
# Hjelpefunksjoner
# ---------------------------------------------------------------------------
function Write-Step([string]$msg) {
    Write-Host "`n==> $msg" -ForegroundColor Cyan
}
function Write-OK([string]$msg) {
    Write-Host "    OK: $msg" -ForegroundColor Green
}
function Fail([string]$msg) {
    Write-Host "`nFEIL: $msg" -ForegroundColor Red
    exit 1
}

# ---------------------------------------------------------------------------
# 0. Forutsetninger
# ---------------------------------------------------------------------------
Write-Step "Sjekker Azure CLI og innlogging"

if (-not (Get-Command az -ErrorAction SilentlyContinue)) {
    Fail "Azure CLI ikke funnet. Last ned: https://aka.ms/installazurecliwindows"
}

$loginCheck = az account show 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "    Logger inn i Azure..." -ForegroundColor Yellow
    az login
    if ($LASTEXITCODE -ne 0) { Fail "Innlogging feilet" }
}

$subscription = (az account show --query "name" -o tsv)
Write-OK "Subscription: $subscription"

# Hent backend app service plan og sjekk tier
Write-Step "Sjekker App Service Plan tier for VNet Integration-støtte"

$backendPlanId = az webapp show `
    --resource-group $ResourceGroup `
    --name $BackendAppName `
    --query "appServicePlanId" -o tsv 2>&1

if ($LASTEXITCODE -ne 0) {
    Fail "Fant ikke backend-appen '$BackendAppName' i ressursgruppe '$ResourceGroup'. Kjør skriptet på nytt med riktig -ResourceGroup."
}

$frontendPlanId = az webapp show `
    --resource-group $ResourceGroup `
    --name $FrontendAppName `
    --query "appServicePlanId" -o tsv 2>&1

if ($LASTEXITCODE -ne 0) {
    Fail "Fant ikke frontend-appen '$FrontendAppName' i ressursgruppe '$ResourceGroup'."
}

# Sjekk tier — VNet Integration krever Standard eller Premium (ikke Free/Shared/Basic)
$frontendPlanSku = az appservice plan show --ids $frontendPlanId --query "sku.tier" -o tsv 2>&1
Write-Host "    Frontend App Service Plan tier: $frontendPlanSku" -ForegroundColor White

$unsupportedTiers = @("Free", "Shared", "Basic", "free", "shared", "basic")
if ($frontendPlanSku -in $unsupportedTiers) {
    Write-Host @"

    ADVARSEL: '$frontendPlanSku' støtter IKKE VNet Integration.
    Du må oppgradere App Service Plan til Standard (S1) eller Premium (P1v3).

    Kjør dette for å oppgradere:
      az appservice plan update --ids $frontendPlanId --sku S1

    Deretter kjør dette skriptet på nytt.
"@ -ForegroundColor Yellow
    exit 1
}

Write-OK "App Service Plan støtter VNet Integration"

# ---------------------------------------------------------------------------
# 1. Opprett VNet
# ---------------------------------------------------------------------------
Write-Step "Oppretter VNet '$VNetName'"

$vnetExists = az network vnet show --resource-group $ResourceGroup --name $VNetName 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-OK "VNet finnes allerede — hopper over"
} else {
    az network vnet create `
        --resource-group $ResourceGroup `
        --name $VNetName `
        --location $Location `
        --address-prefixes $VNetAddressPrefix | Out-Null
    if ($LASTEXITCODE -ne 0) { Fail "Kunne ikke opprette VNet" }
    Write-OK "VNet opprettet ($VNetAddressPrefix)"
}

# ---------------------------------------------------------------------------
# 2. Opprett subnet for Private Endpoint
# ---------------------------------------------------------------------------
Write-Step "Oppretter subnet '$PeSubnetName' for private endpoint"

$peSubnetExists = az network vnet subnet show `
    --resource-group $ResourceGroup --vnet-name $VNetName --name $PeSubnetName 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-OK "Subnet finnes allerede — hopper over"
} else {
    az network vnet subnet create `
        --resource-group $ResourceGroup `
        --vnet-name $VNetName `
        --name $PeSubnetName `
        --address-prefixes $PeSubnetPrefix | Out-Null
    if ($LASTEXITCODE -ne 0) { Fail "Kunne ikke opprette PE-subnet" }
    Write-OK "PE subnet opprettet ($PeSubnetPrefix)"
}

# Deaktiver private endpoint network policies (kreves for å opprette PE i subnettet)
Write-Step "Deaktiverer PrivateEndpointNetworkPolicies på '$PeSubnetName'"
az network vnet subnet update `
    --resource-group $ResourceGroup `
    --vnet-name $VNetName `
    --name $PeSubnetName `
    --disable-private-endpoint-network-policies true | Out-Null
Write-OK "Policies deaktivert"

# ---------------------------------------------------------------------------
# 3. Opprett subnet for VNet Integration (frontend utgående)
# ---------------------------------------------------------------------------
Write-Step "Oppretter subnet '$VIntSubnetName' for VNet Integration"

$vIntSubnetExists = az network vnet subnet show `
    --resource-group $ResourceGroup --vnet-name $VNetName --name $VIntSubnetName 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-OK "Subnet finnes allerede — hopper over"
} else {
    az network vnet subnet create `
        --resource-group $ResourceGroup `
        --vnet-name $VNetName `
        --name $VIntSubnetName `
        --address-prefixes $VIntSubnetPrefix `
        --delegations "Microsoft.Web/serverFarms" | Out-Null
    if ($LASTEXITCODE -ne 0) { Fail "Kunne ikke opprette VInt-subnet" }
    Write-OK "VInt subnet opprettet ($VIntSubnetPrefix)"
}

# ---------------------------------------------------------------------------
# 4. Opprett Private Endpoint for backend
# ---------------------------------------------------------------------------
Write-Step "Oppretter Private Endpoint '$PrivateEndpointName'"

$peExists = az network private-endpoint show `
    --resource-group $ResourceGroup --name $PrivateEndpointName 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-OK "Private Endpoint finnes allerede — hopper over"
} else {
    $backendResourceId = az webapp show `
        --resource-group $ResourceGroup `
        --name $BackendAppName `
        --query "id" -o tsv

    az network private-endpoint create `
        --resource-group $ResourceGroup `
        --name $PrivateEndpointName `
        --location $Location `
        --vnet-name $VNetName `
        --subnet $PeSubnetName `
        --private-connection-resource-id $backendResourceId `
        --group-id "sites" `
        --connection-name "conn-ramgap-backend" | Out-Null

    if ($LASTEXITCODE -ne 0) { Fail "Kunne ikke opprette Private Endpoint" }
    Write-OK "Private Endpoint opprettet"
}

# ---------------------------------------------------------------------------
# 5. Opprett Private DNS Zone
# ---------------------------------------------------------------------------
Write-Step "Oppretter Private DNS Zone '$DnsZoneName'"

$dnsZoneExists = az network private-dns zone show `
    --resource-group $ResourceGroup --name $DnsZoneName 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-OK "DNS Zone finnes allerede — hopper over"
} else {
    az network private-dns zone create `
        --resource-group $ResourceGroup `
        --name $DnsZoneName | Out-Null
    if ($LASTEXITCODE -ne 0) { Fail "Kunne ikke opprette Private DNS Zone" }
    Write-OK "Private DNS Zone opprettet"
}

# ---------------------------------------------------------------------------
# 6. Koble DNS Zone til VNet
# ---------------------------------------------------------------------------
Write-Step "Kobler DNS Zone til VNet ('$DnsZoneLinkName')"

$dnsLinkExists = az network private-dns link vnet show `
    --resource-group $ResourceGroup `
    --zone-name $DnsZoneName `
    --name $DnsZoneLinkName 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-OK "DNS VNet-link finnes allerede — hopper over"
} else {
    az network private-dns link vnet create `
        --resource-group $ResourceGroup `
        --zone-name $DnsZoneName `
        --name $DnsZoneLinkName `
        --virtual-network $VNetName `
        --registration-enabled false | Out-Null
    if ($LASTEXITCODE -ne 0) { Fail "Kunne ikke koble DNS Zone til VNet" }
    Write-OK "DNS VNet-link opprettet"
}

# ---------------------------------------------------------------------------
# 7. Opprett DNS Record Group for Private Endpoint (auto A-record)
# ---------------------------------------------------------------------------
Write-Step "Oppretter DNS Record Group for Private Endpoint"

$dnsGroupExists = az network private-endpoint dns-zone-group show `
    --resource-group $ResourceGroup `
    --endpoint-name $PrivateEndpointName `
    --name "default" 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-OK "DNS Record Group finnes allerede — hopper over"
} else {
    $dnsZoneId = az network private-dns zone show `
        --resource-group $ResourceGroup `
        --name $DnsZoneName `
        --query "id" -o tsv

    az network private-endpoint dns-zone-group create `
        --resource-group $ResourceGroup `
        --endpoint-name $PrivateEndpointName `
        --name "default" `
        --private-dns-zone $dnsZoneId `
        --zone-name "privatelink_azurewebsites_net" | Out-Null

    if ($LASTEXITCODE -ne 0) { Fail "Kunne ikke opprette DNS Record Group" }
    Write-OK "DNS Record Group opprettet — A-record settes automatisk"
}

# ---------------------------------------------------------------------------
# 8. Aktiver VNet Integration på frontend
# ---------------------------------------------------------------------------
Write-Step "Aktiverer VNet Integration på frontend '$FrontendAppName'"

$vIntSubnetId = az network vnet subnet show `
    --resource-group $ResourceGroup `
    --vnet-name $VNetName `
    --name $VIntSubnetName `
    --query "id" -o tsv

az webapp vnet-integration add `
    --resource-group $ResourceGroup `
    --name $FrontendAppName `
    --vnet $VNetName `
    --subnet $VIntSubnetName | Out-Null

if ($LASTEXITCODE -ne 0) { Fail "Kunne ikke aktivere VNet Integration på frontend" }
Write-OK "VNet Integration aktivert på frontend"

# Rut ALL utgående trafikk fra frontend gjennom VNet (viktig for private DNS-oppløsning)
Write-Step "Aktiverer WEBSITE_VNET_ROUTE_ALL på frontend"
az webapp config appsettings set `
    --resource-group $ResourceGroup `
    --name $FrontendAppName `
    --settings WEBSITE_VNET_ROUTE_ALL=1 | Out-Null
Write-OK "WEBSITE_VNET_ROUTE_ALL=1 satt"

# ---------------------------------------------------------------------------
# 9. Deaktiver public access på backend
# ---------------------------------------------------------------------------
Write-Step "Deaktiverer public network access på backend '$BackendAppName'"

az webapp update `
    --resource-group $ResourceGroup `
    --name $BackendAppName `
    --set publicNetworkAccess=Disabled | Out-Null

if ($LASTEXITCODE -ne 0) {
    Write-Host "    NB: Klarte ikke deaktivere public access automatisk." -ForegroundColor Yellow
    Write-Host "    Gjør det manuelt: Azure Portal -> $BackendAppName -> Networking -> Public network access -> Disabled" -ForegroundColor Yellow
} else {
    Write-OK "Public network access deaktivert på backend"
}

# ---------------------------------------------------------------------------
# Ferdig
# ---------------------------------------------------------------------------
Write-Host "`n" + ("=" * 70) -ForegroundColor Green
Write-Host "  OPPSETT FULLFORT!" -ForegroundColor Green
Write-Host ("=" * 70) -ForegroundColor Green
Write-Host @"

Arkitektur:
  Internett -> Frontend ($FrontendAppName) [public]
                    |
               VNet Integration
                    |
              [VNet: $VNetName]
                    |
            Private Endpoint (privat IP)
                    |
              Backend ($BackendAppName) [private]

Neste steg:
  1. Sett API_KEY env var pa begge appene (Azure Portal eller az cli):
       az webapp config appsettings set -g $ResourceGroup -n $BackendAppName --settings API_KEY=<din-nokkel>
       az webapp config appsettings set -g $ResourceGroup -n $FrontendAppName --settings API_KEY=<din-nokkel>

  2. Sjekk at BACKEND_URL peker pa backend (allerede satt):
       https://$BackendAppName.azurewebsites.net

  3. Test frontend:
       az webapp browse -g $ResourceGroup -n $FrontendAppName

  DNS: $BackendAppName.azurewebsites.net loses opp til privat IP nar kallet
       kommer fra VNet (via private DNS zone $DnsZoneName).
       Kall fra internett vil bli avvist (public access disabled).
"@ -ForegroundColor White
