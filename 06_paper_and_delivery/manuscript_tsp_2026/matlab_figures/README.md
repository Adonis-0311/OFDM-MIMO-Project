# MATLAB figure source

The single entry point is generate_tsp_figures.m. It reads registered CSV
artifacts under 05_results and writes matching PDF, SVG, PNG, and TIFF files
to the manuscript figures folder.

Run from MATLAB R2025a:

    cd('D:\Prepare\LYH\OFDM-MIMO_Radar_Estimation\06_paper_and_delivery\manuscript_tsp_2026\matlab_figures')
    generate_tsp_figures

The palette is color-vision-friendly, comparisons use distinct markers,
PDF/SVG exports are vector, and raster companions use 300/600 dpi.
The active generator rebuilds five MATLAB bundles: the analytic triplet
mechanism, matched-scene headline evidence, full-offset evidence, the
pure-Candan 48-cell stress map, and calibration-free projection selection.
The page-wide estimator overview is maintained as an editable Microsoft
Visio source in `../visio_figures` so that labels and connectors remain
text-safe at IEEE two-column scale. Legacy exploratory sources remain for
provenance but are not called by the active entry point.
