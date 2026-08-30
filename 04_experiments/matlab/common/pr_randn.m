function z = pr_randn(seed, n)
%PR_RANDN Portable standard normals via Box-Muller on pr_stream.
  m = ceil(n/2);
  u = pr_stream(seed, 2*m);
  u1 = u(1:m); u2 = u(m+1:end);
  r = sqrt(-2*log(u1));
  z = [r.*cos(2*pi*u2); r.*sin(2*pi*u2)];
  z = z(1:n);
end
