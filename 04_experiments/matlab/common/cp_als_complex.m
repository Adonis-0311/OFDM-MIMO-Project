function [recon, factors] = cp_als_complex(Y, L, sweeps, seed)
%CP_ALS_COMPLEX fixed-sweep complex PARAFAC-ALS (rank L), matched-campaign comparator.
  shape = size(Y); if numel(shape)==2, shape(3)=1; end
  F = cell(1,3);
  for d = 1:3
    z = pr_randn(seed*16+d, 2*shape(d)*L);
    F{d} = reshape(complex(z(1:shape(d)*L), z(shape(d)*L+1:end)), shape(d), L)/sqrt(2);
  end
  for s = 1:sweeps
    for d = 1:3
      idx = setdiff(1:3, d);
      K = khatri_rao(F{idx(2)}, F{idx(1)});          % (prod others) x L
      Yd = unfold(Y, d);                              % Nd x prod(others)
      G = (F{idx(1)}'*F{idx(1)}) .* (F{idx(2)}'*F{idx(2)});
      F{d} = (Yd * conj(K)) / G.';
    end
  end
  K = khatri_rao(F{3}, F{2});
  recon = fold(F{1} * K.', 1, shape);
  factors = F;
end
function Yd = unfold(Y, d)
  shape = size(Y); if numel(shape)==2, shape(3)=1; end
  Yd = reshape(permute(Y, [d, setdiff(1:3,d)]), shape(d), []);
end
function Y = fold(Yd, d, shape)
  order = [d, setdiff(1:3,d)];
  Y = ipermute(reshape(Yd, shape(order)), order);
end
function K = khatri_rao(A, B)
  [ra, L] = size(A); rb = size(B,1);
  K = zeros(ra*rb, L);
  for l = 1:L, K(:,l) = kron(A(:,l), B(:,l)); end
end
