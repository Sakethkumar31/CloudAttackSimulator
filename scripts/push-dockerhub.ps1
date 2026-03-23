param(
    [string]$Namespace = $env:DOCKERHUB_NAMESPACE,
    [string]$Tag = $(if ($env:IMAGE_TAG) { $env:IMAGE_TAG } else { "latest" }),
    [switch]$PushCaldera
)

$ErrorActionPreference = "Stop"

if (-not $Namespace) {
    throw "Set DOCKERHUB_NAMESPACE or pass -Namespace before tagging images."
}

$images = @(
    @{ Local = "cloud-attack-lab-dashboard:latest"; Hub = "$Namespace/cloud-attack-lab-dashboard:$Tag" },
    @{ Local = "cloud-attack-lab-graph-writer:latest"; Hub = "$Namespace/cloud-attack-lab-graph-writer:$Tag" },
    @{ Local = "cloud-attack-lab-neo4j-sync:latest"; Hub = "$Namespace/cloud-attack-lab-neo4j-sync:$Tag" }
)

if ($PushCaldera) {
    $images += @{ Local = "caldera:latest"; Hub = "$Namespace/cloud-attack-lab-caldera:$Tag" }
}

foreach ($image in $images) {
    docker image inspect $image.Local | Out-Null
    Write-Host "Tagging $($image.Local) -> $($image.Hub)"
    docker tag $image.Local $image.Hub
    Write-Host "Pushing $($image.Hub)"
    docker push $image.Hub
}

Write-Host ""
Write-Host "Docker Hub push complete."
Write-Host "Use: docker compose --env-file infra/.env.dockerhub -f docker-compose.hub.yml up -d"
