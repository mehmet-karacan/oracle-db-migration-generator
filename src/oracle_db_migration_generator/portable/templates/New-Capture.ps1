#requires -Version 5.1
[CmdletBinding()]
param(
    [string[]]$Schemas=@(),
    [string[]]$ObjectTypes=@('TABLE','INDEX','SEQUENCE','VIEW','PACKAGE_SPEC','PACKAGE_BODY','PROCEDURE','FUNCTION','TRIGGER','TYPE_SPEC','TYPE_BODY','SYNONYM','COMMENT','MATERIALIZED_VIEW','MATERIALIZED_VIEW_LOG'),
    [string[]]$ObjectNames=@(),
    [string[]]$TableNames=@(),
    [string[]]$DataTypes=@(),
    [switch]$NoRelated,
    [switch]$IncludeTechnicalObjects,
    [ValidateSet('AUTO','OWN','CATALOG','VISIBLE')][string]$ReaderMode='AUTO',
    [ValidateSet('SOURCE','TARGET')][string]$FilterSide='SOURCE',
    [ValidateRange(30,7200)][int]$TimeoutSeconds=900,
    [ValidateRange(1,100000)][int]$MaxObjects=10000,
    [string]$Environment='',
    [Parameter(Mandatory=$true)][string]$OutputDirectory
)
$ErrorActionPreference='Stop'
$validTypes=@('TABLE','INDEX','SEQUENCE','VIEW','PACKAGE_SPEC','PACKAGE_BODY','PROCEDURE','FUNCTION','TRIGGER','TYPE_SPEC','TYPE_BODY','SYNONYM','COMMENT','GRANT','MATERIALIZED_VIEW','MATERIALIZED_VIEW_LOG')
function Convert-Names([string[]]$Values) {
    if ($Values.Count -gt 100) { throw 'CAPTURE_FILTER_LIST_INVALID' }
    $result=@()
    foreach ($item in $Values) {
        $value=$item.Trim()
        if ($value -match '^"(?:[^"\x00-\x1f]|"")+"$') { $value=$value.Substring(1,$value.Length-2).Replace('""','"') }
        elseif ($value -match '^[A-Za-z][A-Za-z0-9_$#]*$') { $value=$value.ToUpperInvariant() }
        else { throw 'CAPTURE_FILTER_VALUE_INVALID' }
        if ([Text.Encoding]::UTF8.GetByteCount($value) -gt 128 -or $value.Contains(',')) { throw 'CAPTURE_FILTER_VALUE_INVALID' }
        if ($result -cnotcontains $value) { $result+=,$value }
    }
    return ,@($result | Sort-Object -CaseSensitive)
}
if ($TableNames.Count) {
    if ($ObjectNames.Count -or ($PSBoundParameters.ContainsKey('ObjectTypes') -and ($ObjectTypes.Count -ne 1 -or $ObjectTypes[0] -ne 'TABLE'))) { throw 'CAPTURE_TABLE_FILTER_CONFLICT' }
    $ObjectTypes=@('TABLE'); $ObjectNames=$TableNames
}
if ($DataTypes.Count -and -not $PSBoundParameters.ContainsKey('ObjectTypes') -and -not $TableNames.Count) { $ObjectTypes=@('TABLE','VIEW','MATERIALIZED_VIEW') }
$Schemas=Convert-Names $Schemas
$ObjectNames=Convert-Names $ObjectNames
$ObjectTypes=@($ObjectTypes | ForEach-Object { $_.Trim().ToUpperInvariant().Replace(' ','_') } | Sort-Object -Unique)
$DataTypes=@($DataTypes | ForEach-Object { $_.Trim().ToUpperInvariant() } | Sort-Object -Unique)
if ($DataTypes.Count -gt 100) { throw 'CAPTURE_FILTER_LIST_INVALID' }
if ($Schemas.Count -gt 20 -or -not $ObjectTypes.Count -or @($ObjectTypes | Where-Object { $_ -notin $validTypes }).Count) { throw 'CAPTURE_OBJECT_TYPES_INVALID' }
if (-not @($ObjectTypes | Where-Object { $_ -notin @('COMMENT','GRANT','MATERIALIZED_VIEW_LOG') }).Count) { throw 'CAPTURE_ROOT_TYPES_REQUIRED' }
if ($DataTypes.Count -and @($ObjectTypes | Where-Object { $_ -notin @('TABLE','VIEW','MATERIALIZED_VIEW') }).Count) { throw 'CAPTURE_DATA_TYPE_SCOPE_INVALID' }
if (@($DataTypes | Where-Object { $_ -notmatch '^[A-Z][A-Z0-9_$# ]{0,127}$' }).Count) { throw 'CAPTURE_DATA_TYPE_INVALID' }
if ($Environment.Length -gt 80 -or $Environment -match '[\x00-\x1f]') { throw 'CAPTURE_ENVIRONMENT_INVALID' }
$selection=[ordered]@{schemas=@($Schemas);object_types=@($ObjectTypes);object_names=@($ObjectNames);data_types=@($DataTypes);include_related=(-not $NoRelated.IsPresent);exclude_system_generated=(-not $IncludeTechnicalObjects.IsPresent);environment=$Environment;reader_mode=$ReaderMode;filter_side=$FilterSide;timeout_seconds=$TimeoutSeconds;max_objects=$MaxObjects}
foreach ($key in @('schemas','object_types','object_names','data_types')) {
    if ([Text.Encoding]::UTF8.GetByteCount(($selection[$key] -join ',')) -gt 4000) { throw 'CAPTURE_FILTER_BYTE_LIMIT' }
}
$scriptText="SET DEFINE OFF`nSET SQLBLANKLINES ON`nSET ECHO OFF`nWHENEVER OSERROR EXIT FAILURE ROLLBACK`nWHENEVER SQLERROR EXIT FAILURE ROLLBACK`n"
foreach ($key in $selection.Keys) {
    $value=$selection[$key]
    $numeric=($value -is [bool] -or $value -is [int])
    $scriptText+='VARIABLE p_'+$key+$(if ($numeric) { " NUMBER`n" } else { " CLOB`n" })
}
$scriptText+="VARIABLE odmg_exit_code NUMBER`nBEGIN`n"
foreach ($key in $selection.Keys) {
    $value=$selection[$key]
    if ($value -is [bool]) { $scriptText+='    :p_'+$key+' := '+$(if ($value) {'1'} else {'0'})+";`n"; continue }
    if ($value -is [int]) { $scriptText+='    :p_'+$key+' := '+$value.ToString([Globalization.CultureInfo]::InvariantCulture)+";`n"; continue }
    if ($value -is [array]) { $value=$value -join ',' }
    if (-not $value) { $scriptText+='    :p_'+$key+" := NULL;`n"; continue }
    $encoded=([BitConverter]::ToString([Text.Encoding]::UTF8.GetBytes($value))).Replace('-','')
    $parts=@();for ($i=0;$i -lt $encoded.Length;$i+=1800) { $parts+="'"+$encoded.Substring($i,[Math]::Min(1800,$encoded.Length-$i))+"'" }
    $scriptText+='    :p_'+$key+" := UTL_I18N.RAW_TO_CHAR(HEXTORAW(`n"+($parts -join " ||`n")+"`n), 'AL32UTF8');`n"
}
$scriptText+="END;`n/`n@collect.sql`nEXIT :odmg_exit_code ROLLBACK`n"
$targetPath=[IO.Path]::GetFullPath($OutputDirectory)
if (Test-Path -LiteralPath $targetPath) { throw 'CAPTURE_OUTPUT_ALREADY_EXISTS' }
New-Item -ItemType Directory -Path $targetPath | Out-Null
$utf8=New-Object Text.UTF8Encoding($false)
[IO.File]::WriteAllText((Join-Path $targetPath 'run_export.sql'),$scriptText,$utf8)
$documentation=[ordered]@{}
foreach ($key in $selection.Keys) { $documentation[$key]=$selection[$key] }
foreach ($key in @('schemas','object_names')) {
    $documentation[$key]=@($selection[$key] | ForEach-Object { if ($_ -cmatch '^[A-Z][A-Z0-9_$#]*$') { $_ } else { '"'+$_.Replace('"','""')+'"' } })
}
[IO.File]::WriteAllText((Join-Path $targetPath 'selection.json'),($documentation | ConvertTo-Json -Depth 5),$utf8)
foreach ($name in @('collect.sql','README.md','New-Capture.ps1')) { Copy-Item -LiteralPath (Join-Path $PSScriptRoot $name) -Destination (Join-Path $targetPath $name) }
Write-Output ('Hazirlanan paket: '+$targetPath)
Write-Output 'Mevcut SQL*Plus veya SQLcl oturumunda @run_export.sql ile calistirin. Parola bu araca verilmez.'
