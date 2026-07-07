function A = design_matrix(shape, bins)
  A = zeros(prod(shape), size(bins,1));
  for l = 1:size(bins,1)
    At = tensor_atom(shape, bins(l,:));
    A(:,l) = At(:);
  end
end
