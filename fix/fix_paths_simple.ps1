# Simple PowerShell script to fix absolute paths in HTML files

# Set working directory
$repoRoot = Split-Path $PSScriptRoot -Parent
$workDir = Join-Path $repoRoot 'books'

# Get all HTML files
$htmlFiles = Get-ChildItem -Path $workDir -Filter "*.html" -Recurse

Write-Host "Found $($htmlFiles.Count) HTML files to process..."

# Process each file
$fixedCount = 0
foreach ($file in $htmlFiles) {
    try {
        # Read file content
        $content = Get-Content -Path $file.FullName -Raw
        
        # Replace all absolute paths
        $content = $content -replace '/content/', 'content/'
        $content = $content -replace '/svg/', 'svg/'
        $content = $content -replace '/book.min.css', 'book.min.css'
        $content = $content -replace '/fuse.min.js', 'fuse.min.js'
        $content = $content -replace '/zh.search.min.885edd674035.js', 'zh.search.min.885edd674035.js'
        $content = $content -replace '/manifest.json', 'manifest.json'
        $content = $content -replace '/favicon.png', 'favicon.png'
        
        # Save the file
        Set-Content -Path $file.FullName -Value $content -Encoding UTF8
        $fixedCount++
        Write-Host "Fixed: $($file.FullName)"
    } catch {
        Write-Host "Error processing $($file.FullName): $($_.Exception.Message)"
    }
}

Write-Host "Done! Fixed $fixedCount files."
