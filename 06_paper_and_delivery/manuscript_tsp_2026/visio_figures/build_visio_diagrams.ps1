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
        [bool]$ArrowHead = $true,
        [int]$Pattern = 1
    )
    $line = $Page.DrawLine($X1, $Y1, $X2, $Y2)
    Set-CellFormula $line 'LineColor' $Color
    Set-CellFormula $line 'LineWeight' "$Weight pt"
    Set-CellFormula $line 'LinePattern' "$Pattern"
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

function Build-EstimatorOverview {
    param($Application)
    $doc = $Application.Documents.Add('')
    try {
        $page = $doc.Pages.Item(1)
        $page.Name = 'Projection-selected Candan estimator'

        # IEEE two-column text width.  Drawing at final size keeps all labels at
        # their intended 7.2--8.6 pt size instead of relying on later scaling.
        Set-PageSize $page 7.16 3.30

        $text = 'RGB(23,32,51)'
        $blue = 'RGB(11,92,173)'
        $teal = 'RGB(0,120,107)'
        $gold = 'RGB(163,104,20)'
        $orange = 'RGB(213,94,0)'
        $muted = 'RGB(93,101,116)'
        $lightBlue = 'RGB(232,240,248)'
        $lightTeal = 'RGB(229,243,239)'
        $lightGold = 'RGB(252,243,217)'
        $lightOrange = 'RGB(250,235,224)'

        # The title is close to the diagram and centered on the final page.
        Add-Text $page 0.20 3.08 6.96 3.27 'Projection-selected multidimensional Candan estimator' $text 8.6 'Arial' 1 | Out-Null
        Add-Text $page 0.20 2.84 6.96 3.01 'Observation and closed-form coordinate refinement' $muted 7.3 'Arial' 1 | Out-Null

        # Three physical sampling axes.  Their distinct borders remain separable
        # in gray scale, while the shared pale fill identifies them as inputs.
        Add-Box $page 0.18 2.44 0.96 2.72 "Spatial ULA`nNₐ" $lightBlue $blue 7.2 | Out-Null
        Add-Box $page 0.18 2.12 0.96 2.40 "Frequency`nNτ" $lightBlue $teal 7.2 | Out-Null
        Add-Box $page 0.18 1.80 0.96 2.08 "Slow time`nNν" $lightBlue $gold 7.2 | Out-Null

        Add-Box $page 1.26 1.82 2.32 2.68 "Rank-L separable`ntensor observation`nspatial × frequency × slow time" $lightBlue $blue 7.3 | Out-Null
        Add-Box $page 2.63 1.82 3.61 2.68 "Orthonormal`n3-D FFT`nTop-L coarse bins" $lightBlue $blue 7.6 | Out-Null
        Add-Box $page 3.92 1.82 5.03 2.68 "Per-axis neighborhoods`n3DL complex triplets" $lightTeal $teal 7.5 | Out-Null
        Add-Box $page 5.34 1.82 6.98 2.68 "Closed-form Candan corrections`n(δa, δτ, δν) for each target" $lightTeal $teal 7.5 | Out-Null

        Add-Arrow $page 0.96 2.58 1.26 2.45 $text 1.0 | Out-Null
        Add-Arrow $page 0.96 2.26 1.26 2.25 $text 1.0 | Out-Null
        Add-Arrow $page 0.96 1.94 1.26 2.05 $text 1.0 | Out-Null
        Add-Arrow $page 2.32 2.25 2.63 2.25 $text 1.0 | Out-Null
        Add-Arrow $page 3.61 2.25 3.92 2.25 $text 1.0 | Out-Null
        Add-Arrow $page 5.03 2.25 5.34 2.25 $text 1.0 | Out-Null

        Add-Text $page 0.20 1.54 6.96 1.71 'Joint fitting, fitted-subspace selection, and full estimate' $muted 7.3 'Arial' 1 | Out-Null

        # The second lane continues from right to left.  The vertical hand-off
        # makes the reading order explicit without a long return connector.
        Add-Box $page 5.34 0.58 6.98 1.35 "Joint least-squares gain estimate`nat refined coordinates" $lightTeal $teal 7.6 | Out-Null
        Add-Box $page 3.73 0.58 5.03 1.35 "Fitted-subspace`nenergy selector`nΔρ ≥ 0?" $lightGold $gold 7.7 | Out-Null
        Add-Box $page 1.88 0.94 3.35 1.38 "Full refined estimate`ncoordinates, gains, reconstruction" $lightTeal $teal 7.3 | Out-Null
        Add-Box $page 1.88 0.40 3.35 0.84 "Full grid estimate`ncoordinates, gains, reconstruction" $lightOrange $orange 7.3 | Out-Null

        Add-Arrow $page 6.16 1.82 6.16 1.35 $text 1.0 | Out-Null
        Add-Arrow $page 5.34 0.97 5.03 0.97 $text 1.0 | Out-Null

        # Refined branch: solid teal.  Grid fallback: dashed vermillion.  Labels
        # sit in dedicated whitespace and never intersect the connectors.
        Add-Arrow $page 3.73 1.12 3.55 1.16 $teal 1.15 $false 1 | Out-Null
        Add-Arrow $page 3.55 1.16 3.35 1.16 $teal 1.15 $true 1 | Out-Null
        Add-Text $page 3.38 1.27 3.68 1.43 'yes' $teal 7.2 'Arial' 1 | Out-Null

        Add-Arrow $page 3.73 0.78 3.55 0.62 $orange 1.15 $false 2 | Out-Null
        Add-Arrow $page 3.55 0.62 3.35 0.62 $orange 1.15 $true 2 | Out-Null
        Add-Text $page 3.38 0.40 3.68 0.56 'no' $orange 7.2 'Arial' 1 | Out-Null

        Add-Text $page 0.20 0.12 6.96 0.31 'Projection score = (refined fitted energy − grid fitted energy) / received energy' $muted 7.2 'Arial' | Out-Null
        Export-Diagram $doc $page 'tsp_estimator_overview'
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
    Build-EstimatorOverview $visio
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
