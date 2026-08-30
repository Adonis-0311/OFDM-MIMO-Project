function tsp_style_axes(ax)
c = tsp_palette();
ax.FontName = 'Helvetica';
ax.FontSize = 8;
ax.LineWidth = 0.75;
ax.TickDir = 'out';
ax.XColor = c.text;
ax.Layer = 'top';
end
