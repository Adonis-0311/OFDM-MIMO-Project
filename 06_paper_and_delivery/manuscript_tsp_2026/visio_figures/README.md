# Visio figure sources

`tsp_system_model.vsdx` and `tsp_method_flow.vsdx` are the editable layout sources for the two page-wide IEEE workflow diagrams.

Regenerate both figures with local Microsoft Visio:

```powershell
powershell -ExecutionPolicy Bypass -File .\build_visio_diagrams.ps1
```

The script exports PDF, SVG, and PNG files to `../figures`. Quantitative values, algorithm notation, and decision logic are unchanged; Visio is used for text-safe layout, alignment, and connector routing.
