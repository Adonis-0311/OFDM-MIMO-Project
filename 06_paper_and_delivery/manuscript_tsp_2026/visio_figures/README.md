# Visio figure sources

`tsp_estimator_overview.vsdx` is the editable layout source for the page-wide IEEE estimator overview. It consolidates the former system-model and method-flow diagrams into one end-to-end evidence figure.

Regenerate the figure with local Microsoft Visio:

```powershell
powershell -ExecutionPolicy Bypass -File .\build_visio_diagrams.ps1
```

The script exports PDF, SVG, and PNG files to `../figures`. Algorithm notation and decision logic are unchanged; Visio is used for text-safe layout, alignment, and connector routing.
