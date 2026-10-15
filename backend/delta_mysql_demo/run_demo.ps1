param(
    [ValidateSet('delta','mysql','all')][string]$Step = 'all',
    [string]$Source,
    [string]$Run,
    [string]$MysqlUser = 'root',
    [string]$MysqlHost = '127.0.0.1',
    [int]$MysqlPort = 3306
)
$demoPython = Join-Path $PSScriptRoot '.venv/Scripts/python.exe'
if (-not (Test-Path -LiteralPath $demoPython)) { throw '가상환경이 없습니다. README의 설치 명령부터 실행하세요.' }
$demoScript = Join-Path $PSScriptRoot 'price_demo.py'
if ($Step -eq 'mysql') {
    if (-not $Run) {
        $demoRunRoot = Join-Path $PSScriptRoot 'runs'
        $demoRuns = @(Get-ChildItem -LiteralPath $demoRunRoot -Directory | Where-Object { Test-Path -LiteralPath (Join-Path $_.FullName 'delta_validation.json') } | Sort-Object Name)
        if ($demoRuns.Count -ne 1) { throw '실행 폴더가 여러 개이거나 없습니다. -Run으로 명시하세요.' }
        $Run = $demoRuns[0].FullName
    }
    & $demoPython $demoScript --load-existing $Run --mysql-host $MysqlHost --mysql-port $MysqlPort --mysql-user $MysqlUser
} else {
    if (-not $Source) {
        $demoProject = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
        $Source = Join-Path $demoProject 'data/silver/03_C_integration_20261014/03_C_integration_20261014/04_output/silver/s_stock_daily_prc.csv'
    }
    if ($Step -eq 'delta') { & $demoPython $demoScript --source $Source --delta-only }
    else { & $demoPython $demoScript --source $Source --mysql-host $MysqlHost --mysql-port $MysqlPort --mysql-user $MysqlUser }
}
if ($LASTEXITCODE -ne 0) { throw "실습 실패 (exit code $LASTEXITCODE). 출력된 사유를 확인하세요." }
