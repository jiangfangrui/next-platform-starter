# Simple PowerShell script to fix absolute paths in books directory

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
        $content = $content -replace 'href="/content/', 'href="../content/'
        $content = $content -replace 'src="/svg/', 'src="../svg/'
        $content = $content -replace 'href="/book.min.css', 'href="book.min.css'
        $content = $content -replace 'src="/fuse.min.js', 'src="fuse.min.js'
        $content = $content -replace 'src="/zh.search.min.885edd674035.js', 'src="zh.search.min.885edd674035.js'
        $content = $content -replace 'href="/manifest.json', 'href="manifest.json'
        $content = $content -replace 'href="/favicon.png', 'href="favicon.png'
        $content = $content -replace 'href="/index.html', 'href="index.html'
        
        # Save the file
        Set-Content -Path $file.FullName -Value $content -Encoding UTF8
        $fixedCount++
        Write-Host "Fixed: $($file.FullName)"
    } catch {
        Write-Host "Error processing $($file.FullName): $($_.Exception.Message)"
    }
}

Write-Host "Done! Fixed $fixedCount files."
