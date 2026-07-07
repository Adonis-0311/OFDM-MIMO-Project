function A = tensor_atom(shape, bins)
%TENSOR_ATOM separable rank-1 atom, shape [Na Nt Nv], bins [ba bt bv]
  a = steering_axis(shape(1), bins(1));
  b = steering_axis(shape(2), bins(2));
  c = steering_axis(shape(3), bins(3));
  A = reshape(a,[],1,1) .* reshape(b,1,[],1) .* reshape(c,1,1,[]);
end
