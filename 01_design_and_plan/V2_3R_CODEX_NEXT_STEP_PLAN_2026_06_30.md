# v2.3R → Submission-Ready Next-Step Plan (Codex execution brief)

> Generated: 2026-06-30
> Author of brief: review pass over PLAN.md, route decision (E12, 2026-06-29), independent review (review.md), build report, all LaTeX sections, evidence table, and figure assets.
> **Two locked decisions (do not re-open):**
> - **D1 — Scientific strategy: Reframe + matched Pareto.** Keep the narrowed "learned bounded refinement" paper. Fold the NOMP-inspired result in as a *compute–accuracy trade-off + external-robustness* story, AND run the E12 matched-accuracy comparison at paper scale with an NMSE-vs-runtime Pareto display. **Do NOT build an integrated K-stage estimator (EXP-R1/E11) for this submission.**
> - **D2 — Venue: IEEE, keep IEEEtran.** Target IEEE Systems Journal / IEEE TVT. Keep the current 8-page two-column IEEEtran build. **No MDPI Sensors template switch, no English+Chinese bilingual requirement** for this round.
> - **Goal: reach `submission-ready` (internal score ≥ 7.5/10) on the fastest defensible path.**

---

## 0. How to use this brief

Each task block has: **Files**, **Action**, **Acceptance**, **Verify**. Execute phases in order; within a phase, tasks may run in parallel unless a dependency is noted. Do not mark a task done until its **Verify** step passes. Preserve the project's existing discipline:

- **Every result is attributed to its real executable path.** Three distinct paths exist and must never be fused: (1) one-scalar local G2 layer (`03_active_modules/tompnet/torch_layer.py`), (2) 210-parameter CDL feature controller (`03_active_modules/tompnet/feature_controller.py`), (3) deterministic A4 radius-schedule diagnostic. There is **no** integrated K-stage network — never imply one.
- **No truth-tuned test-time parameters.** Source-trained / validation-selected only. Keep all failure cells visible (CDL-D, A4 SNR sweep, L=16 boundaries).
- **Every run writes a durable manifest** (seeds, config, environment, CSVs) via `03_active_modules/common/manifest.py`, lands in `05_results/<run_name>/`, and is then folded into the evidence table and claim ledger.
- **Runs are CPU-capable** (Sionna/scipy/torch available). The repo's Linux execution path is the source of truth for timings.

Key paths:

| Purpose | Path |
|---|---|
| Manuscript (LaTeX, the deliverable) | `06_paper_and_delivery/manuscript_v2_3r/latex/` |
| Sections | `latex/sections/0X_*.tex`, appendix `latex/appendix/*.tex` |
| References | `02_literature_and_refs/v2_3r_references.bib` (42 cited, 39 with DOI) |
| Figures | `06_paper_and_delivery/manuscript_v2_3r/displays/figures/` |
| Display builder | `06_paper_and_delivery/manuscript_v2_3r/displays/scripts/build_v2_3r_paper_displays.py` |
| Evidence table + aggregator | `05_results/v2_3r_paper_evidence_table/paper_evidence_table.md`, `04_experiments/eval/aggregate_v2_3r_paper_evidence_table.py` |
| Claim ledger | `06_paper_and_delivery/manuscript_v2_3r/claim_evidence_ledger.json` |
| E12 NOMP harness | `04_experiments/eval/run_e12_tensor_nomp_matched_pilot.py`, `aggregate_e12_tensor_nomp_campaign.py`, baseline `03_active_modules/baseline/tensor_nomp.py` |
| Complexity benchmark | `04_experiments/eval/run_complexity_benchmark.py` (timing-only today) |
| G2 strengthening | `04_experiments/eval/run_stage2_torch_locked_scale_g2_seed_sweep.py` |
| A4 strengthening | `04_experiments/eval/run_stage3_a4_cross_l_plateau_gate_seed_sweep.py` |
| Tests | `04_experiments/tests/` (`pytest -q`, currently 24 passing) |

---

## 1. Review verdict in one paragraph (why this plan exists)

The manuscript is **further along than the stale trackers imply**. Already done in the LaTeX: title downgraded to "Learned Bounded Off-Grid Refinement…" (no "deep unfolding T-OMP-Net"); abstract/intro honestly separate the three paths; method §4 and theory §5 carry the implemented equations (Eqs. 1–12); Fig. 2 redrawn as three separate evidence paths; Fig. 3 redrawn with seed points + admissible-region scatter (no dual axes); related-work nearest-neighbor table present; 42 refs / 39 DOI; E4 15-row complexity table; CDL-A/C scaled result with 95% CI and CDL-D failure retained. **`CHECKLIST.md`, `revision_log.md`, and `claim_evidence_ledger.json` are stale and under-report this.**

The **one genuinely unresolved scientific risk** is that the 2026-06-29 route decision ran a NOMP-inspired comparator that **beats the learned scalar by ~41–47 dB on accuracy** (while being ~7.6× slower), and the manuscript still presents "+6.17 dB over grid" as a headline accuracy win with NOMP listed only as "not done." A reviewer who runs a standard NOMP/off-grid-SBL baseline would reject the accuracy framing. Per D1, the fix is to **reframe around compute–accuracy trade-off + external robustness and report the matched comparison at paper scale.** Secondary blockers: thin G2/A4 statistics, a missing forward-model equation in §3, and stale state files. Internal score today ≈ **5/10**; after Phase 2 (writing) ≈ **6.5/10**; after Phase 3 (matched Pareto) target ≈ **7.5/10**.

---

## Phase 1 — Reframe the scientific narrative (writing-only, BLOCKING, ~0 compute)

Do this first; it is independent of new runs and removes the critical rejection risk. Use **"compute–accuracy trade-off"** and **"external/standards-aligned robustness"** as the two value axes. The learned scalar is an **amortized, ~7.6× cheaper approximate refinement**, NOT an accuracy winner against strong continuous recovery.

### T1.1 — Reframe abstract + introduction + contributions
- **Files:** `latex/main.tex` (abstract), `latex/sections/01_introduction.tex`.
- **Action:** Re-lead the abstract: the contribution is (a) a bounded, **inspectable, low-compute** post-support refinement and (b) standards-aligned held-out CDL-A/C physical evidence with explicit failure boundaries. Keep the +6.1726 dB-over-grid and CDL numbers, but **immediately bound them**: state that a strong oversampled continuous optimizer (NOMP-inspired) attains far lower NMSE on the matched synthetic regime at materially higher runtime, so the learned layer's value is amortized cost, not accuracy supremacy. Rewrite contribution C2/C3 to say "bounded low-cost refinement" and "compute–accuracy positioning against continuous recovery," not "improves accuracy."
- **Acceptance:** No sentence claims state-of-the-art or best accuracy. The accuracy-vs-grid claim is never stated without the NOMP/continuous-recovery bound in the same paragraph. Abstract ≤ ~250 words (IEEE soft limit).
- **Verify:** Grep the abstract+intro for "improve"/"gain"/"outperform" and confirm each is scoped by either "over grid Tensor-OMP" + a NOMP caveat, or "held-out CDL-A/C."

### T1.2 — Convert the closest-work table row from "not done" to the real result
- **Files:** `latex/sections/02_related_work.tex` (Table `tab:closest_work`), `latex/sections/07_limitations.tex`.
- **Action:** Change the ours-row "no matched NOMP accuracy result" to a forward pointer to the new §6 matched comparison. In limitations, replace "The complexity table lacks matched-accuracy NOMP/off-grid-SBL comparisons" with the honest finding: matched comparison now exists; NOMP-inspired dominates accuracy in the matched synthetic regime; the learned path's defensible value is runtime/amortization and external robustness.
- **Acceptance:** Related work and limitations agree with §6 and the abstract; no residual "comparison absent" wording.
- **Verify:** Grep repo LaTeX for "lacks matched" / "no matched NOMP" — zero hits remain.

### T1.3 — Add the honest compute–accuracy framing to method/system intro
- **Files:** `latex/sections/04_method.tex` (intro paragraph), optionally `08_conclusion.tex`.
- **Action:** One sentence stating the design intent: trade a bounded, known amount of accuracy for a large, amortized reduction in continuous-refinement cost, keeping an inspectable physical support. Conclusion must not re-inflate the claim.
- **Acceptance:** Method/conclusion consistent with T1.1.
- **Verify:** Read §4 intro + §8 end-to-end; claims match abstract.

---

## Phase 2 — Add the forward-model math + finish the mathematical contract (writing-only, ~0 compute)

Closes the residual of review issue REV-002. Method §4 and theory §5 already have equations; the **system model §3 is still prose-only** and an IEEE algorithm reviewer will want the explicit signal model.

### T2.1 — Add the explicit tensor signal/observation model to §3
- **Files:** `latex/sections/03_system_model.tex`.
- **Action:** Add displayed equations for: (i) the separable angle–delay–Doppler atom `a(θ)⊗b(τ)⊗c(ν)` (define each factor's array/subcarrier/Doppler steering form for the FDMA virtual-array regime actually used); (ii) the sparse observation `Y = Σ_{ℓ=1}^{L} β_ℓ · atom(b_ℓ) + N`; (iii) the vectorized/matricized form feeding Tensor-OMP; (iv) the definition of measurement-domain NMSE and the CIR-grounded physical delay (ns) and projected broadside-angle (deg) metrics already used in evaluation. Keep notation consistent with Eqs. 1–7 in §4.
- **Action (guardrail):** Match the implemented generator in `03_active_modules/data/offgrid_tensor.py` and the CDL evaluator — do not introduce a model the code does not realize. Cross-check symbol-by-symbol.
- **Acceptance:** A reader can reproduce the observation model and both physical metrics from §3 alone. Symbols are reused (not redefined) in §4/§5.
- **Verify:** Build (Phase 6) shows no undefined-reference/inconsistent-symbol issues; a quick self-check that `atom()`/NMSE in the equation equals the code's `generate_offgrid_tensor_sample` / `measurement_nmse_db`.

### T2.2 — Promote the A4 plateau gate and CRLB statements to clearly conditional results
- **Files:** `latex/sections/05_theory.tex`.
- **Action:** Ensure each theory statement is explicitly conditional (already largely true): the off-grid mismatch bound is support-conditioned; the depth metric is operational, not optimal; CRLB is single-target high-SNR derivative validation only. Add a one-line assumption list at the top of §5 (separable atoms, correct support, local differentiability).
- **Acceptance:** No statement reads as a global recovery/efficiency theorem.
- **Verify:** Read §5; every claim has a stated condition.

---

## Phase 3 — E12 paper-scale matched-accuracy + NMSE-vs-runtime Pareto (NEW EVIDENCE, ~1 week compute)

This is the core of decision D1 and the largest score lever (→ 7.5/10). Reuse the existing E12 harness; **extend, do not rewrite.**

### T3.1 — Paper-scale matched NOMP-vs-learned campaign
- **Files:** `04_experiments/eval/run_e12_tensor_nomp_matched_pilot.py`, `aggregate_e12_tensor_nomp_campaign.py`, baseline `03_active_modules/baseline/tensor_nomp.py`. New output dir `05_results/tensor_nomp3d_matched_paper_5seed/`.
- **Action:** Run the four matched methods (`grid_fft_topk_plus_ls`, `deterministic_cartesian_local_refinement_plus_ls`, `fixed_source_trained_scalar_interpolation_plus_ls`, `tensor_nomp3d_known_order_v1`) at paper scale: shape `128×16×32`, `L∈{2,4,8}`, **SNR∈{0,10,20,30} dB** (extend beyond the pilot's 20 dB-only), **5 seeds × ≥20 held-out samples/cell**. Same samples, known order, identical LS contract across methods. Record paired NMSE, joint-bin RMSE, half-bin hit fraction, **and per-method wall-clock** per cell.
- **Acceptance:** 5-seed seed-mean 95% CIs for every paired delta; all failure/relative cells retained; runtime ratios reported per L and SNR; no test-truth tuning (scalar α stays at the source value `0.6419…`). Verdict recorded honestly (expected: NOMP dominates accuracy, scalar dominates runtime).
- **Verify:** `verification.md` in the new run dir reproduces the headline (NOMP min gain over grid, NOMP-vs-scalar advantage, runtime ratio) and explicitly states the matched-regime scope (known order, dense tensor, matched sinusoidal generator).

### T3.2 — Add matched-accuracy ESPRIT / PARAFAC rows (not just timing)
- **Files:** `04_experiments/eval/run_complexity_benchmark.py` (currently timing-only), or a new `run_e12_matched_accuracy_comparators.py` that imports the same ESPRIT/PARAFAC implementations.
- **Action:** On the same identifiable parameter contract where mathematically applicable, evaluate separable forward-backward ESPRIT and complex PARAFAC-ALS for **accuracy** (channel NMSE, delay/angle RMSE, failure rate), not only wall-clock. If a method cannot be matched fairly (e.g., ESPRIT has no cross-axis pairing), **report that limitation as a row** rather than dropping it.
- **Acceptance:** Each comparator row has either a matched accuracy number or an explicit, documented reason it is timing-only. No silent omissions.
- **Verify:** Cross-check that the E4 complexity boundary text in the paper matches the new accuracy availability.

### T3.3 — Build the NMSE-vs-runtime Pareto display + a matched-accuracy table
- **Files:** `displays/scripts/build_v2_3r_paper_displays.py` (add a Pareto panel), new figure `displays/figures/v2_3r_pareto_compute_accuracy.pdf` (+ `.png`), new table in `latex/sections/06_experiments.tex` or `latex/appendix/a_experiment_tables.tex`.
- **Action:** Scatter median runtime (x, log) vs NMSE (y) for grid / deterministic refinement / learned scalar / NOMP-inspired (and ESPRIT/PARAFAC if matched), with the learned scalar marked as the low-compute amortized point. Add a compact table: method, NMSE (dB) ± CI, runtime (ms), within-half-bin fraction.
- **Acceptance:** Vector PDF, ≥8 pt fonts, no dual axes, failure points visible, colorblind-safe palette (no red/green-only encoding). The figure makes the trade-off — not an accuracy win — the visual message.
- **Verify:** Render the PNG and visually inspect (see Phase 6 QA); confirm the learned point is clearly the cheap-but-less-accurate corner.

### T3.4 — Wire E12 into §6 Experiments
- **Files:** `latex/sections/06_experiments.tex` (+ abstract number if cited).
- **Action:** Add a "Matched continuous-recovery comparison" subsection reporting the paper-scale NOMP result and the Pareto figure, framed per Phase 1. State the matched-synthetic scope boundary explicitly.
- **Acceptance:** §6 now contains the matched comparison; the headline subsection no longer stands alone as an accuracy claim.
- **Verify:** Section reads consistently with abstract/intro/limitations.

---

## Phase 4 — Statistical strengthening (EXP-R3, compute; can run parallel to Phase 3)

Removes the "anecdotal sample size" rejection risk (G2 n_test=3/cell; A4 n_test=2/cell).

### T4.1 — Enlarge G2 held-out evaluation
- **Files:** `04_experiments/eval/run_stage2_torch_locked_scale_g2_seed_sweep.py`; output `05_results/stage2_torch_locked_scale_g2_seed_sweep/` (new scaled variant dir).
- **Action:** Keep the locked scale and source-trained α; raise held-out scenes per L/seed from 3 to **≥30** (keep 5 seeds, or extend to 10 if cheap). Report gain distribution, 95% CI, and **minimum cell**.
- **Acceptance:** Mean and min-cell gain over grid remain positive with the larger sample; CI reported. (This stays a *vs-grid* statement — accuracy supremacy is not claimed; see Phase 1.)
- **Verify:** New manifest + CI; evidence-table row updated (Phase 5).

### T4.2 — Strengthen A4 cross-L early-stop
- **Files:** `04_experiments/eval/run_stage3_a4_cross_l_plateau_gate_seed_sweep.py`.
- **Action:** Increase seeds and test curves per cell for `L∈{16,32,64}` at 20 dB. Keep the prespecified 25% saving / 0.5 dB gap gate. Report savings/gap distributions.
- **Acceptance:** L≥32 still meets the gate within stated tolerance at the larger sample; L=16 still labeled boundary; SNR-sweep negative result retained.
- **Verify:** Manifest + updated Fig. 3b/3c if numbers move.

---

## Phase 5 — Synchronize durable state (REV-005, ~0 compute; after Phases 3–4 land numbers)

### T5.1 — Regenerate evidence table + claim ledger
- **Files:** `04_experiments/eval/aggregate_v2_3r_paper_evidence_table.py` → `05_results/v2_3r_paper_evidence_table/paper_evidence_table.md`; `06_paper_and_delivery/manuscript_v2_3r/claim_evidence_ledger.json`.
- **Action:** Add rows for the E12 paper-scale matched comparison, matched-accuracy comparators, strengthened G2/A4. Mark resolved blockers (figures, refs, E4, identity correction) as closed. Add the explicit "NOMP dominates accuracy in matched regime" boundary to Claim Discipline.
- **Acceptance:** Evidence table and ledger contain no claim absent from a manifest, and omit no completed result.
- **Verify:** Diff the regenerated table; every new §6 number traces to a `05_results/` artifact.

### T5.2 — Refresh trackers
- **Files:** `CHECKLIST.md`, `PLAN.md`, `06_paper_and_delivery/manuscript_v2_3r/review/revision_log.md`.
- **Action:** Tick the completed identity/figure/equation items; set the current anchor to "matched-Pareto reframe complete; IEEE submission packaging." Mark EXP-R1 (integrated estimator) and EXP-R4 (DeepMIMO trained) as **explicitly deferred future work** for this submission per D1.
- **Acceptance:** Trackers match reality; no stale "in progress" on shipped items.
- **Verify:** Re-read; consistent with build report.

---

## Phase 6 — IEEE packaging, build, and verification gate (BLOCKING for submission)

### T6.1 — IEEE front matter + submission hygiene
- **Files:** `latex/main.tex`, `latex/appendix/b_reproducibility.tex`.
- **Action:** Confirm IEEE-appropriate front/back matter present: keywords (already in `IEEEkeywords`), Acknowledgment placeholder, a Data Availability / code-release statement (GitHub URL placeholder) in the reproducibility appendix, author placeholders acceptable for double-blind. Resolve the **3 references missing DOIs** (39/42) where a DOI exists; for arXiv/3GPP entries that legitimately lack one, keep the URL.
- **Acceptance:** Self-contained IEEE-style submission; refs complete; Data Availability present.
- **Verify:** Grep `.bib` for entries with neither `doi` nor `url`; expect zero.

### T6.2 — Compile + page budget + tests
- **Files:** `latex/`, `04_experiments/tests/`.
- **Action:** `latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex`; keep ≤ the IEEE page target (currently 8 pp — confirm against the chosen journal's limit; Systems Journal/TVT allow more, so the new Pareto figure/table fit). Run `pytest -q`.
- **Acceptance:** 0 errors, 0 unresolved citations, 0 overfull boxes (underfull warnings OK); all tests pass (≥24).
- **Verify:** Read `build_report.md` regenerated; page count and citation count recorded.

### T6.3 — Page-by-page visual QA
- **Files:** compiled `main.pdf`, all `displays/figures/*.png`.
- **Action:** Render the PDF (~140 dpi) and inspect every page and every figure at source resolution for text-outside-frame, label collisions, dual axes, illegible (<8 pt) labels, red/green-only encodings. Pay special attention to the new Pareto figure.
- **Acceptance:** No visual defects; the Pareto figure communicates the trade-off, not an accuracy win.
- **Verify:** Note QA results in `build_report.md`.

### T6.4 — Independent skeptical re-audit (verification gate)
- **Files:** new `06_paper_and_delivery/manuscript_v2_3r/review/review_2026_06_30.md`.
- **Action:** Re-run the same skeptical acceptance audit used in `review.md`: check claim↔manifest attribution, NOMP framing honesty, statistical sufficiency, figure/table integrity, and that no result is fused across the three executable paths. Score against the rubric.
- **Acceptance:** Internal score **≥ 7.5/10**; zero critical issues; the only remaining items are explicitly-scoped future work (integrated estimator, DeepMIMO trained physical eval, hardware impairments, multi-target CRLB, real measurement).
- **Verify:** If score < 7.5, loop back to the failing phase before declaring submission-ready. (Recommended: run this audit as an isolated reviewer pass so it does not inherit drafting bias.)

---

## Definition of Done (submission-ready)

- [ ] Abstract/intro/related-work/limitations/conclusion all frame the learned path as a **compute–accuracy trade-off + external robustness**, never as accuracy SOTA; NOMP dominance disclosed wherever the vs-grid number appears. *(Phase 1)*
- [ ] §3 contains the explicit tensor observation model and metric definitions; §4/§5 equations consistent and conditional. *(Phase 2)*
- [ ] Paper-scale (5-seed, multi-SNR) matched NOMP comparison + NMSE-vs-runtime Pareto figure and table in §6, with retained failure cells. *(Phase 3)*
- [ ] ESPRIT/PARAFAC rows carry matched accuracy or a documented reason they are timing-only. *(Phase 3)*
- [ ] G2 ≥30 held-out/cell and strengthened A4, both with CIs and min-cell reported. *(Phase 4)*
- [ ] Evidence table, claim ledger, CHECKLIST, PLAN, revision log all synchronized; EXP-R1/E11 and E14 marked deferred. *(Phase 5)*
- [ ] IEEEtran compiles clean within page budget; Data Availability present; all refs have DOI or justified URL; `pytest -q` green; page-by-page visual QA clean. *(Phase 6)*
- [ ] Independent re-audit ≥ 7.5/10, zero critical issues. *(Phase 6)*

## Explicitly OUT of scope for this submission (per D1/D2)
- Integrated K-stage / "deep unfolding" estimator (EXP-R1/E11) — keep deferred; only revisit if a future candidate clears the route-decision Pareto gate.
- DeepMIMO trained physical evaluation (EXP-R4/E14) — keep as scalar-transfer proxy + limitation.
- MDPI Sensors template, bilingual EN/ZH, MDPI front matter.
- Real-measurement / hardware-in-the-loop validation, multi-target CRLB tightness, HIR-JL robust-training main claim.

## Suggested order & rough effort
1. **Phase 1** (½–1 day, writing) — unblocks the critical risk immediately.
2. **Phase 3 + Phase 4** in parallel (~1 week, compute) — the new evidence.
3. **Phase 2** (½ day, writing) — can overlap with compute.
4. **Phase 5** (½ day) after numbers land.
5. **Phase 6** (1 day) — package, build, QA, re-audit gate.

> Estimated calendar to submission-ready: **~1.5–2 weeks**, compute-bound by Phase 3.
