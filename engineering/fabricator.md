# Fabricator profile (reference only, no order)

2 copper layers, FR4 1.6 mm, explicit stackup in design/main.kicad_pcb (35 um copper, 1.51 mm core). Min track 0.23-0.3 mm, min clearance 0.2 mm, via 0.6/0.3, header holes 1.0 mm drill, M2 NPTH 2.2 mm, copper-to-edge 0.3 mm. All far above JLCPCB 1 oz capabilities (0.1/0.1 mm, 0.3 mm drill). Silkscreen strokes 0.15 mm (JLCPCB floor). No fiducials/rails: nothing is ordered or machine-assembled. Outline 22 x 52 mm rectangle with 4 mounts exactly as the contract (x 38..60, y -26..26 contract frame).

## Ignored ERC/DRC categories (the tile's defaults; this project adds none, relaxes no severity)
* DRC missing_courtyard / footprint_type_mismatch / footprint_filters_mismatch / tuning_profile_track_geometries / track_not_centered_on_via: library-style checks (the mounting holes have no courtyard of electrical meaning; U1 is a custom header footprint). Geometric clearance, short, unconnected, edge, hole, silk and mask checks are all active and clean.
* ERC single_global_label: every net label is a global label by design of kicadpy.author (one label per pin stub); four_way_junction, simulation_model_issue, footprint_filter: not applicable (no sim, no junction).
