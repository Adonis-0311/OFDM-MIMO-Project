function rgb = tsp_hex2rgb(value)
value = char(erase(string(value), '#'));
rgb = [hex2dec(value(1:2)), hex2dec(value(3:4)), hex2dec(value(5:6))] / 255;
end
