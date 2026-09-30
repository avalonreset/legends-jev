param(
  [Parameter(Mandatory=$true)][string]$Python,
  [Parameter(ValueFromRemainingArguments=$true)][string[]]$JevArgs
)
$ErrorActionPreference = 'Stop'
$previous = $env:TYPESAFE_API_KEY
$secure = $null
$ptr = [IntPtr]::Zero
try {
  if (-not $previous -and ($JevArgs -contains '--execute')) {
    $credentialPath = Join-Path $env:LOCALAPPDATA 'Legends\TypeSafe\api-key.dpapi'
    if (-not (Test-Path -LiteralPath $credentialPath)) { throw 'Jev credential is not provisioned for this Windows user.' }
    $secure = (Get-Content -LiteralPath $credentialPath -Raw).Trim() | ConvertTo-SecureString
    $ptr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
    $env:TYPESAFE_API_KEY = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr)
  }
  & $Python -m legends_jev @JevArgs
  $code = $LASTEXITCODE
} finally {
  $env:TYPESAFE_API_KEY = $previous
  if ($ptr -ne [IntPtr]::Zero) { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr) }
  if ($secure) { $secure.Dispose() }
}
exit $code
