function crlb_bins = crlb_single_target(shape, bins, gain, noise_var)
%CRLB_SINGLE_TARGET real-parameter FIM for eta=[ba,bt,bv,Re(b),Im(b)], mirrors Eq (13).
  a = cell(1,3); w = cell(1,3);
  for d = 1:3
    a{d} = steering_axis(shape(d), bins(d));
    w{d} = 2i*pi*(0:shape(d)-1)'/shape(d);
  end
  atom = tensor_atom(shape, bins); atom = atom(:);
  D = zeros(numel(atom), 5);
  base = {a{1}, a{2}, a{3}};
  for d = 1:3
    mo = base; mo{d} = w{d}.*mo{d};
    Ax = reshape(mo{1},[],1,1).*reshape(mo{2},1,[],1).*reshape(mo{3},1,1,[]);
    D(:,d) = gain * Ax(:);
  end
  D(:,4) = atom; D(:,5) = 1i*atom;
  F = (2/noise_var) * real(D' * D);
  C = inv(F);
  crlb_bins = diag(C(1:3,1:3))';
end
