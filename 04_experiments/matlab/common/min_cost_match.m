function a = min_cost_match(C)
%MIN_COST_MATCH exact minimum-cost assignment for n<=8 (vectorized brute force).
% Returns a: row i matched to column a(i). Equivalent to Hungarian for small n.
  n = size(C,1);
  if n > 9, error('min_cost_match: n too large'); end
  P = perms(1:n);                      % all permutations
  rows = repmat(1:n, size(P,1), 1);
  lin = sub2ind([n n], rows, P);
  [~, k] = min(sum(C(lin), 2));
  a = P(k,:)';
end
