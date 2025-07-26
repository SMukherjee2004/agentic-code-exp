# PowerShell script to retry Docker push with backoff
param(
    [string]$ImageName = "smukherjee2004/ai-github-analyzer:latest",
    [int]$MaxRetries = 5
)

$RetryCount = 0

Write-Host "🚀 Starting Docker push with retry logic..." -ForegroundColor Green

while ($RetryCount -lt $MaxRetries) {
    $Attempt = $RetryCount + 1
    Write-Host "📦 Attempt $Attempt of $MaxRetries" -ForegroundColor Yellow
    
    try {
        $result = docker push $ImageName 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Successfully pushed $ImageName to Docker Hub!" -ForegroundColor Green
            exit 0
        } else {
            throw "Docker push failed with exit code $LASTEXITCODE"
        }
    }
    catch {
        $RetryCount++
        if ($RetryCount -lt $MaxRetries) {
            $WaitTime = $RetryCount * 30
            Write-Host "❌ Push failed. Waiting $WaitTime seconds before retry..." -ForegroundColor Red
            Start-Sleep -Seconds $WaitTime
        }
    }
}

Write-Host "❌ Failed to push after $MaxRetries attempts" -ForegroundColor Red
Write-Host "💡 Try the following:" -ForegroundColor Cyan
Write-Host "   1. Check your internet connection"
Write-Host "   2. Make sure you're logged into Docker Hub: docker login"
Write-Host "   3. Try pushing during off-peak hours"
Write-Host "   4. Consider using the local build option in docker-compose.yml"
exit 1
