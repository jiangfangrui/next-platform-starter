# PowerShell脚本批量修复books目录下HTML文件中的绝对路径问题

# 设置工作目录
$repoRoot = Split-Path $PSScriptRoot -Parent
$workDir = Join-Path $repoRoot 'books'

# 获取所有HTML文件
$htmlFiles = Get-ChildItem -Path $workDir -Filter "*.html" -Recurse

Write-Host "开始修复books目录下的路径问题，共找到 $($htmlFiles.Count) 个HTML文件..."

# 定义需要替换的路径映射
$pathReplacements = @{
    "href=\"/content/" = "href=\"../content/"
    "src=\"/svg/" = "src=\"../svg/"
    "href=\"/book.min.css" = "href=\"book.min.css"
    "src=\"/fuse.min.js" = "src=\"fuse.min.js"
    "src=\"/zh.search.min.885edd674035.js" = "src=\"zh.search.min.885edd674035.js"
    "href=\"/manifest.json" = "href=\"manifest.json"
    "href=\"/favicon.png" = "href=\"favicon.png"
    "href=\"/index.html" = "href=\"index.html"
    "href=\"/content/index.html" = "href=\"content/index.html"
    "href=\"/content/video/" = "href=\"content/video/"
    "href=\"/content/purpose-profit/" = "href=\"content/purpose-profit/"
    "href=\"/content/docs/" = "href=\"content/docs/"
}

# 遍历每个HTML文件
$fixedCount = 0
foreach ($file in $htmlFiles) {
    try {
        # 读取文件内容
        $content = Get-Content -Path $file.FullName -Encoding UTF8 -Raw
        $originalContent = $content
        
        # 执行所有路径替换
        foreach ($replacement in $pathReplacements.GetEnumerator()) {
            $content = $content -replace [regex]::Escape($replacement.Key), $replacement.Value
        }
        
        # 如果内容有变化，则保存文件
        if ($content -ne $originalContent) {
            Set-Content -Path $file.FullName -Value $content -Encoding UTF8
            $fixedCount++
            Write-Host "已修复: $($file.FullName)"
        }
    } catch {
        Write-Host "处理文件时出错: $($file.FullName)" -ForegroundColor Red
        Write-Host "错误信息: $($_.Exception.Message)" -ForegroundColor Red
    }
}

Write-Host "修复完成！共修改了 $fixedCount 个文件。" -ForegroundColor Green
