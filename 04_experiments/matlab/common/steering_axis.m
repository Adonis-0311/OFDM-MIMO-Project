function v = steering_axis(n, b)
%STEERING_AXIS exp(2i*pi*(0:n-1)*b/n)/sqrt(n), mirrors data/offgrid_tensor.py
  idx = (0:n-1)';
  v = exp(2i*pi*idx*b/n) / sqrt(n);
end
