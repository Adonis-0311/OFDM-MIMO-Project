param(
    [string]$FigureDir = (Join-Path $PSScriptRoot '..\figures')
)

$ErrorActionPreference = 'Stop'

function Set-CellFormula {
    param($Shape, [string]$Cell, [string]$Formula)
    try {
        $Shape.CellsU($Cell).FormulaU = $Formula
    }
    catch {
        throw "Visio formula failed: cell=$Cell formula=$Formula; $($_.Exception.Message)"
    }
}

function Set-PageSize {
    param($Page, [double]$Width, [double]$Height)
    Set-CellFormula $Page.PageSheet 'PageWidth' "$Width in"
    Set-CellFormula $Page.PageSheet 'PageHeight' "$Height in"
    Set-CellFormula $Page.PageSheet 'PrintPageOrientation' '2'
    Set-CellFormula $Page.PageSheet 'ShdwPattern' '0'
}

function Add-Box {
    param(
        $Page,
        [double]$X1, [double]$Y1, [double]$X2, [double]$Y2,
        [string]$Text, [string]$Fill, [string]$Line,
        [double]$FontSize = 8.5
    )
    $shape = $Page.DrawRectangle($X1, $Y1, $X2, $Y2)
    $shape.Text = $Text
    Set-CellFormula $shape 'FillForegnd' $Fill
    Set-CellFormula $shape 'FillPattern' '1'
    Set-CellFormula $shape 'LineColor' $Line
    Set-CellFormula $shape 'LineWeight' '0.9 pt'
    Set-CellFormula $shape 'Char.Font' 'FONT("Arial")'
    Set-CellFormula $shape 'Char.Size' "$FontSize pt"
    Set-CellFormula $shape 'Char.Color' 'RGB(23,32,51)'
    Set-CellFormula $shape 'Para.HorzAlign' '1'
    Set-CellFormula $shape 'VerticalAlign' '1'
    Set-CellFormula $shape 'LeftMargin' '0.06 in'
    Set-CellFormula $shape 'RightMargin' '0.06 in'
    Set-CellFormula $shape 'TopMargin' '0.03 in'
    Set-CellFormula $shape 'BottomMargin' '0.03 in'
    return $shape
}

function Add-Text {
    param(
        $Page,
        [double]$X1, [double]$Y1, [double]$X2, [double]$Y2,
        [string]$Text, [string]$Color = 'RGB(23,32,51)',
        [double]$FontSize = 8.0, [string]$Font = 'Arial',
        [int]$Bold = 0
    )
    $shape = $Page.DrawRectangle($X1, $Y1, $X2, $Y2)
    $shape.Text = $Text
    Set-CellFormula $shape 'FillPattern' '0'
    Set-CellFormula $shape 'LinePattern' '0'
    Set-CellFormula $shape 'Char.Font' "FONT(`"$Font`")"
    Set-CellFormula $shape 'Char.Size' "$FontSize pt"
    Set-CellFormula $shape 'Char.Color' $Color
    Set-CellFormula $shape 'Char.Style' "$Bold"
    Set-CellFormula $shape 'Para.HorzAlign' '1'
    Set-CellFormula $shape 'VerticalAlign' '1'
    Set-CellFormula $shape 'LeftMargin' '0'
    Set-CellFormula $shape 'RightMargin' '0'
    Set-CellFormula $shape 'TopMargin' '0'
    Set-CellFormula $shape 'BottomMargin' '0'
    return $shape
}

function Add-Arrow {
    param(
        $Page,
        [double]$X1, [double]$Y1, [double]$X2, [double]$Y2,
        [string]$Color = 'RGB(23,32,51)',
        [double]$Weight = 1.0,
        [bool]$ArrowHead = $true
    )
    $line = $Page.DrawLine($X1, $Y1, $X2, $Y2)
    Set-CellFormula $line 'LineColor' $Color
    Set-CellFormula $line 'LineWeight' "$Weight pt"
    Set-CellFormula $line 'BeginArrow' '0'
    Set-CellFormula $line 'EndArrow' $(if ($ArrowHead) { '4' } else { '0' })
    Set-CellFormula $line 'EndArrowSize' '2'
    return $line
}

function Export-Diagram {
    param($Document, $Page, [string]$BaseName)
    $source = Join-Path $PSScriptRoot "$BaseName.vsdx"
    $pdf = Join-Path $FigureDir "$BaseName.pdf"
    $svg = Join-Path $FigureDir "$BaseName.svg"
    $png = Join-Path $FigureDir "$BaseName.png"
    $Document.SaveAs($source) | Out-Null
    $Page.Export($svg)
    $Page.Export($png)
    $Document.ExportAsFixedFormat(1, $pdf, 1, 0, 1, 1, $false, $true, $true, $true, $false)
}

function Build-SystemModel {
    param($Application)
    $doc = $Application.Documents.Add('')
    try {
        $page = $doc.Pages.Item(1)
        $page.Name = 'Tensor estimation interface'
        Set-PageSize $page 10.0 3.00

        $text = 'RGB(23,32,51)'
        $blue = 'RGB(11,92,173)'
        $green = 'RGB(15,118,110)'
        $gold = 'RGB(183,121,31)'
        $lightBlue = 'RGB(232,240,248)'
        $lightGreen = 'RGB(230,243,239)'
        $lightGold = 'RGB(252,243,217)'
        $outputFill = 'RGB(249,241,224)'

        Add-Text $page 2.40 2.30 9.30 2.54 'Rank-L separable observation model' $text 8.2 'Arial' 1 | Out-Null

        Add-Box $page 0.18 2.18 1.42 2.72 "Spatial ULA`nN_a" $lightBlue $blue 8.5 | Out-Null
        Add-Box $page 0.18 1.40 1.42 1.94 "Frequency`nN_τ" $lightGreen $green 8.5 | Out-Null
        Add-Box $page 0.18 0.62 1.42 1.16 "Slow time`nN_ν" $lightGold $gold 8.5 | Out-Null

        Add-Box $page 1.82 1.15 3.30 2.17 "Separable tensor`n𝒴: N_a × N_τ × N_ν" $lightBlue $text 8.2 | Out-Null
        Add-Box $page 3.66 1.15 4.92 2.17 "Orthonormal FFT`n+ top-L bins" $lightBlue $text 8.2 | Out-Null
        Add-Box $page 5.28 1.15 6.62 2.17 "3DL triplet samples`n+ axis-wise Candan" $lightGreen $text 8.2 | Out-Null
        Add-Box $page 6.98 1.15 8.28 2.17 "Candan joint LS`n+ FFT/grid energy" $lightGold $text 8.2 | Out-Null
        Add-Box $page 8.66 1.15 9.84 2.17 "Coordinates`nGains`nReconstruction" $outputFill $text 8.0 | Out-Null

        Add-Arrow $page 1.42 2.45 1.82 1.82 $text 1.0 | Out-Null
        Add-Arrow $page 1.42 1.67 1.82 1.67 $text 1.0 | Out-Null
        Add-Arrow $page 1.42 0.89 1.82 1.52 $text 1.0 | Out-Null
        Add-Arrow $page 3.30 1.66 3.66 1.66 $text 1.0 | Out-Null
        Add-Arrow $page 4.92 1.66 5.28 1.66 $text 1.0 | Out-Null
        Add-Arrow $page 6.62 1.66 6.98 1.66 $text 1.0 | Out-Null
        Add-Arrow $page 8.28 1.66 8.66 1.66 $text 1.0 | Out-Null

        Add-Text $page 1.82 0.18 9.84 0.48 'Projection score: normalized fitted-subspace energy gain (refined − grid)' 'RGB(107,114,128)' 8.0 'Arial' | Out-Null
        Export-Diagram $doc $page 'tsp_system_model'
    }
    finally {
        $doc.Close()
        [Runtime.InteropServices.Marshal]::FinalReleaseComObject($doc) | Out-Null
    }
}

function Build-MethodFlow {
    param($Application)
    $doc = $Application.Documents.Add('')
    try {
        $page = $doc.Pages.Item(1)
        $page.Name = 'Projection-selected Candan flow'
        Set-PageSize $page 10.0 2.55

        $text = 'RGB(23,32,51)'
        $green = 'RGB(0,145,102)'
        $orange = 'RGB(205,92,8)'
        $lightBlue = 'RGB(232,240,248)'
        $lightGreen = 'RGB(230,243,239)'
        $lightGold = 'RGB(252,243,217)'
        $lightOrange = 'RGB(250,235,224)'

        Add-Text $page 2.25 2.04 7.50 2.28 'Closed-form complex three-sample correction on each active axis' $text 8.2 'Arial' 1 | Out-Null

        Add-Box $page 0.18 0.95 1.34 1.92 "Dense observation`ny" $lightBlue $text 8.5 | Out-Null
        Add-Box $page 1.70 0.95 3.00 1.92 "FFT top-L`ncoarse support" $lightBlue $text 8.5 | Out-Null
        Add-Box $page 3.36 0.95 5.06 1.92 "Axis-wise Candan`n3DL complex samples" $lightBlue $text 8.3 | Out-Null
        Add-Box $page 5.42 0.95 6.68 1.92 "Joint LS`nCandan estimate" $lightGreen $text 8.5 | Out-Null
        Add-Box $page 7.04 0.95 8.30 1.92 "Projection selection`nΔρ ≥ 0?" $lightGold $text 8.5 | Out-Null
        Add-Box $page 8.86 1.72 9.84 2.34 "Return local`ncoordinates" $lightGreen $text 8.2 | Out-Null
        Add-Box $page 8.86 0.52 9.84 1.14 "Return grid`ncoordinates" $lightOrange $text 8.2 | Out-Null

        Add-Arrow $page 1.34 1.44 1.70 1.44 $text 1.0 | Out-Null
        Add-Arrow $page 3.00 1.44 3.36 1.44 $text 1.0 | Out-Null
        Add-Arrow $page 5.06 1.44 5.42 1.44 $text 1.0 | Out-Null
        Add-Arrow $page 6.68 1.44 7.04 1.44 $text 1.0 | Out-Null

        Add-Arrow $page 8.30 1.60 8.54 2.03 $green 1.1 $false | Out-Null
        Add-Arrow $page 8.54 2.03 8.86 2.03 $green 1.1 $true | Out-Null
        Add-Text $page 8.31 2.09 8.60 2.31 'yes' $green 7.8 'Arial' 1 | Out-Null

        Add-Arrow $page 8.30 1.28 8.54 0.83 $orange 1.1 $false | Out-Null
        Add-Arrow $page 8.54 0.83 8.86 0.83 $orange 1.1 $true | Out-Null
        Add-Text $page 8.31 0.55 8.60 0.77 'no' $orange 7.8 'Arial' 1 | Out-Null

        Add-Text $page 1.70 0.14 8.30 0.40 'Projection score: normalized fitted-subspace energy gain (refined − grid)' 'RGB(107,114,128)' 8.0 'Arial' | Out-Null
        Export-Diagram $doc $page 'tsp_method_flow'
    }
    finally {
        $doc.Close()
        [Runtime.InteropServices.Marshal]::FinalReleaseComObject($doc) | Out-Null
    }
}

$resolvedFigureDir = [System.IO.Path]::GetFullPath($FigureDir)
$resolvedProjectRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
if (-not $resolvedFigureDir.StartsWith($resolvedProjectRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "FigureDir must remain within $resolvedProjectRoot"
}
New-Item -ItemType Directory -Force -Path $resolvedFigureDir | Out-Null
$FigureDir = $resolvedFigureDir

$visio = $null
try {
    $visio = New-Object -ComObject Visio.Application
    $visio.Visible = $false
    $visio.AlertResponse = 7
    Build-SystemModel $visio
    Build-MethodFlow $visio
}
finally {
    if ($visio) {
        $visio.Quit()
        [Runtime.InteropServices.Marshal]::FinalReleaseComObject($visio) | Out-Null
    }
    [GC]::Collect()
    [GC]::WaitForPendingFinalizers()
}

Write-Output "Visio diagrams exported to $FigureDir"
