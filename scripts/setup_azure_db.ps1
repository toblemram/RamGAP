# ==============================================================================
# RamGAP — Azure PostgreSQL Flexible Server Setup
# ==============================================================================
# Krever: Azure CLI (https://aka.ms/installazurecliwindows)
#
# Kjør:
#   .\scripts\setup_azure_db.ps1
#
# Skriptet oppretter:
#   - Resource group
#   - Azure PostgreSQL Flexible Server
#   - Database "ramgap"
#   - Brannmurregel for din nåværende IP
# ==============================================================================

param(
    [string]$ResourceGroup  = "ramgap-rg",
    [string]$Location       = "norwayeast",
    [string]$ServerName     = "ramgap-db",          # Må være globalt unikt
    [string]$AdminUser      = "ramgapadmin",
    [string]$DatabaseName   = "ramgap",
    [string]$SkuName        = "Standard_B1ms",      # ~170 kr/mnd (Burstable, 1 vCore)
    [string]$StorageGB      = "32"
)

# ---------------------------------------------------------------------------
# 1. Sjekk at Azure CLI er installert og logget inn
# ---------------------------------------------------------------------------
if (-not (Get-Command az -ErrorAction SilentlyContinue)) {
    Write-Error "Azure CLI ikke funnet. Last ned fra: https://aka.ms/installazurecliwindows"
    exit 1
}

$loginCheck = az account show 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "Logger inn i Azure..." -ForegroundColor Yellow
    az login
}

$subscription = (az account show --query "name" -o tsv)
Write-Host "Bruker subscription: $subscription" -ForegroundColor Cyan

# ---------------------------------------------------------------------------
# 2. Be om passord
# ---------------------------------------------------------------------------
$securePassword = Read-Host "Oppgi databasepassord (min 8 tegn, store/sm\u00e5 bokstaver + tall)" -AsSecureString
$AdminPassword  = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
    [Runtime.InteropServices.Marshal]::SecureStringToBSTR($securePassword)
)

if ($AdminPassword.Length -lt 8) {
    Write-Error "Passordet m\u00e5 v\u00e6re minst 8 tegn"
    exit 1
}

# ---------------------------------------------------------------------------
# 3. Opprett Resource Group
# ---------------------------------------------------------------------------
Write-Host "`nOppretter Resource Group '$ResourceGroup' i '$Location'..." -ForegroundColor Yellow
az group create --name $ResourceGroup --location $Location | Out-Null

# ---------------------------------------------------------------------------
# 4. Opprett PostgreSQL Flexible Server
# ---------------------------------------------------------------------------
Write-Host "Oppretter PostgreSQL server '$ServerName' (dette tar 2-5 min)..." -ForegroundColor Yellow
az postgres flexible-server create `
    --resource-group $ResourceGroup `
    --name $ServerName `
    --location $Location `
    --admin-user $AdminUser `
    --admin-password $AdminPassword `
    --sku-name $SkuName `
    --tier Burstable `
    --storage-size $StorageGB `
    --version 16 `
    --public-access 0.0.0.0 `
    --yes

if ($LASTEXITCODE -ne 0) {
    Write-Error "Feil ved opprettelse av server. Sjekk at servernavnet '$ServerName' er ledig (m\u00e5 v\u00e6re globalt unikt)."
    exit 1
}

# ---------------------------------------------------------------------------
# 5. Opprett database
# ---------------------------------------------------------------------------
Write-Host "Oppretter database '$DatabaseName'..." -ForegroundColor Yellow
az postgres flexible-server db create `
    --resource-group $ResourceGroup `
    --server-name $ServerName `
    --database-name $DatabaseName | Out-Null

# ---------------------------------------------------------------------------
# 6. Tillat din n\u00e5v\u00e6rende IP
# ---------------------------------------------------------------------------
Write-Host "Legger til brannmurregel for din IP..." -ForegroundColor Yellow
$myIP = (Invoke-RestMethod "https://api.ipify.org?format=json").ip
az postgres flexible-server firewall-rule create `
    --resource-group $ResourceGroup `
    --name $ServerName `
    --rule-name "MyIP-$(Get-Date -Format 'yyyyMMdd')" `
    --start-ip-address $myIP `
    --end-ip-address $myIP | Out-Null

# ---------------------------------------------------------------------------
# 7. Bygg og vis DATABASE_URL
# ---------------------------------------------------------------------------
$host_fqdn = "${ServerName}.postgres.database.azure.com"
$DATABASE_URL = "postgresql://${AdminUser}:${AdminPassword}@${host_fqdn}:5432/${DatabaseName}?sslmode=require"

Write-Host "`n===========================================================" -ForegroundColor Green
Write-Host " Azure PostgreSQL klar!" -ForegroundColor Green
Write-Host "===========================================================`n" -ForegroundColor Green
Write-Host "Server:        $host_fqdn"
Write-Host "Database:      $DatabaseName"
Write-Host "Bruker:        $AdminUser"
Write-Host ""
Write-Host "DATABASE_URL (legg dette i .env):" -ForegroundColor Cyan
Write-Host $DATABASE_URL -ForegroundColor White
Write-Host ""

# ---------------------------------------------------------------------------
# 8. Skriv .env automatisk
# ---------------------------------------------------------------------------
$envPath = Join-Path $PSScriptRoot "..\\.env"
if (Test-Path $envPath) {
    $envContent = Get-Content $envPath -Raw
    if ($envContent -match "DATABASE_URL=") {
        $envContent = $envContent -replace "DATABASE_URL=.*", "DATABASE_URL=$DATABASE_URL"
        Set-Content $envPath $envContent -NoNewline
        Write-Host ".env oppdatert med ny DATABASE_URL." -ForegroundColor Green
    } else {
        Add-Content $envPath "`nDATABASE_URL=$DATABASE_URL"
        Write-Host "DATABASE_URL lagt til i .env." -ForegroundColor Green
    }
} else {
    Copy-Item (Join-Path $PSScriptRoot "..\.env.example") $envPath
    $envContent = Get-Content $envPath -Raw
    $envContent = $envContent -replace "DATABASE_URL=", "DATABASE_URL=$DATABASE_URL"
    Set-Content $envPath $envContent -NoNewline
    Write-Host ".env opprettet fra .env.example med DATABASE_URL." -ForegroundColor Green
}

Write-Host ""
Write-Host "Kj\u00f8r backend p\u00e5 nytt for \u00e5 initialisere tabellene: python backend/app.py" -ForegroundColor Yellow
Write-Host ""
Write-Host "For \u00e5 gi andre tilgang, legg til deres IP:" -ForegroundColor Cyan
Write-Host "  az postgres flexible-server firewall-rule create --resource-group $ResourceGroup --name $ServerName --rule-name TeamMember --start-ip-address <IP> --end-ip-address <IP>"
