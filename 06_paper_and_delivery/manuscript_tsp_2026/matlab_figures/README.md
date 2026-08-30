# MATLAB figure source

The single entry point is generate_tsp_figures.m. It reads registered CSV
artifacts under 05_results and writes matching PDF, SVG, PNG, and TIFF files
to the manuscript figures folder.

Run from MATLAB R2025a:

    cd('D:\Prepare\LYH\OFDM-MIMO_Radar_Estimation\06_paper_and_delivery\manuscript_tsp_2026\matlab_figures')
    generate_tsp_figures

The palette is color-vision-friendly, comparisons use distinct markers,
PDF/SVG exports are vector, and raster companions use 300/600 dpi.
The active generator rebuilds six paper figures: system model, method flow,
local-family comparison, full-offset evidence, the pure-Candan 48-cell stress
map, and calibration-free projection selection. The last two read the
seventh-round registered CSV artifacts directly. Legacy exploratory sources
remain for provenance but are not called by the active entry point.
