"""fix-20261030: electrode coordinates of nm000373 converted from MNI152 2-mm voxel indices to millimetres.

Source: sourcedata/dryad-q573n5tph/allContacts_MNIcoords.csv gives each contact "in MNI 2mm standard space" as positive
integers (x 7-83, y 11-106, z 9-82): voxel indices of the FSL MNI152_T1_2mm template (91 x 109 x 91), onto which the
authors registered one-voxel-per-contact masks with FSL FLIRT (paper Methods, "Electrode localization").

Verification (code/fix-20261030_verify_voxel_convention.py, result code/fix-20261030_verify_voxel_convention.json):
- Affine read from the FSL 5.0.7 NIfTI headers (MNI152_T1_2mm, HarvardOxford and MNI structural 2-mm atlases, all
  91x109x91): sform = [[-2,0,0,90],[0,2,0,-126],[0,0,2,-72]], i.e. x = 90 - 2i, y = 2j - 126, z = 2k - 72 for 0-based i,j,k.
- 0-based indices reproduce the paper's own atlas numbers exactly for the recorded contacts: 116 contacts in the
  visual-cortex ROI (paper: 116), 5 in the hippocampus (paper: 5), Harvard-Oxford Table 2 totals within 18 contacts
  summed over 10 ROIs. 1-based indices give 16 hippocampal contacts and a Table 2 deviation of 72; among all 125
  shifts of -2..+2 voxels per axis the 0-based reading fits best. Every index lies inside 0..90 / 0..108 / 0..90.
- Hemisphere of each patient (paper Table 1) and the L/R prefix of contact names agree with the sign of x (281/287
  named contacts; the 6 others are reference contacts REF1/2 and midline contacts at x = 0 or -2 mm).

Change: x, y, z become millimetres in MNI152NLin6Asym (FSL MNI152 2 mm); the original indices are kept in voxel_i,
voxel_j, voxel_k. Atlas label columns are unchanged (they were already looked up with the 0-based affine).
Idempotent. Usage: python fix-20261030_coords_mm.py <bids_root>
"""
import csv, glob, json, os, sys

root = sys.argv[1]
src = {}
for r in csv.DictReader(open(os.path.join(root, "sourcedata/dryad-q573n5tph/allContacts_MNIcoords.csv"))):
    if r["Participant"].strip():
        src.setdefault((r["Participant"].strip(), r["Electrode"].strip()), []).append((int(r["MNI X"]), int(r["MNI Y"]), int(r["MNI Z"])))

def to_mm(i, j, k):
    return 90 - 2 * i, 2 * j - 126, 2 * k - 72

n_conv = 0
for f in sorted(glob.glob(os.path.join(root, "sub-*/ieeg/*_space-MNI152NLin6Asym_electrodes.tsv"))):
    sub = os.path.basename(f).split("_")[0]
    rows = list(csv.DictReader(open(f, newline=""), delimiter="\t"))
    cols = list(rows[0].keys())
    if "voxel_i" in cols:
        continue
    out_cols = cols[:cols.index("group") + 1] + ["voxel_i", "voxel_j", "voxel_k"] + cols[cols.index("group") + 1:]
    for r in rows:
        ijk = (int(r["x"]), int(r["y"]), int(r["z"]))
        assert src.get((sub, r["name"])) == [ijk], (sub, r["name"], ijk)  # unique, verbatim copy of the release
        r["voxel_i"], r["voxel_j"], r["voxel_k"] = (str(v) for v in ijk)
        r["x"], r["y"], r["z"] = (str(v) for v in to_mm(*ijk))
        n_conv += 1
    with open(f, "w", newline="") as fh:
        w = csv.DictWriter(fh, out_cols, delimiter="\t", lineterminator="\n")
        w.writeheader(); w.writerows(rows)

CS = {
    "iEEGCoordinateSystem": "MNI152NLin6Asym",
    "iEEGCoordinateUnits": "mm",
    "iEEGCoordinateSystemDescription": "FSL MNI152 T1 2 mm template space (MNI152NLin6Asym), millimetres. The release file allContacts_MNIcoords.csv gives each contact 'in MNI 2mm standard space' as 0-based voxel indices of the FSL MNI152_T1_2mm grid (91x109x91); they were converted for NEMAR (Oct 2026) with the template's sform, x = 90 - 2*i, y = 2*j - 126, z = 2*k - 72, read from the FSL NIfTI header. The original indices are kept in the voxel_i, voxel_j, voxel_k columns of electrodes.tsv. The 0-based convention was verified against the paper's own atlas counts: 0-based indices give 116 contacts in the authors' visual-cortex ROI (paper: 116) and 5 hippocampal contacts (paper: 5), and fit the Harvard-Oxford totals of the paper's Table 2 best among all shifts of up to 2 voxels per axis; 1-based indices give 16 hippocampal contacts. Script and result: code/fix-20261030_coords_mm.py, code/fix-20261030_verify_voxel_convention.py, code/fix-20261030_verify_voxel_convention.json.",
    "iEEGCoordinateProcessingDescription": "Authors' method (Dryad record and paper): contact locations identified on post-operative CT and MRI, reconstructed in BioImage Suite, registered to the pre-operative MRI, converted from .MGRID to native-space coordinates with FieldTrip, written as a one-voxel-per-contact mask in FSL native space, and transformed to the MNI T1 2 mm standard brain with a linear (FLIRT, 12 dof) registration of the pre-operative scan. Positions are therefore on the 2 mm grid (precision about 2 mm).",
    "iEEGCoordinateProcessingReference": "Sherman BE, Aljishi A, Graves KN, Quraishi IH, Sivaraju A, Damisah EC, Turk-Browne NB (2023). Intracranial entrainment reveals statistical learning across levels of abstraction. J Cogn Neurosci. doi:10.1162/jocn_a_02012",
}
for f in sorted(glob.glob(os.path.join(root, "sub-*/ieeg/*_space-MNI152NLin6Asym_coordsystem.json"))):
    with open(f, "w") as fh:
        json.dump(CS, fh, indent=2, ensure_ascii=False); fh.write("\n")

ej = os.path.join(root, "electrodes.json")
E = json.load(open(ej))
new = {
    "x": {"Description": "x position in MNI152NLin6Asym (FSL MNI152 2 mm), converted from voxel_i as x = 90 - 2*voxel_i (see coordsystem.json).", "Units": "mm"},
    "y": {"Description": "y position in MNI152NLin6Asym (FSL MNI152 2 mm), converted from voxel_j as y = 2*voxel_j - 126 (see coordsystem.json).", "Units": "mm"},
    "z": {"Description": "z position in MNI152NLin6Asym (FSL MNI152 2 mm), converted from voxel_k as z = 2*voxel_k - 72 (see coordsystem.json).", "Units": "mm"},
    "voxel_i": {"LongName": "Voxel index i (release value)", "Description": "First voxel index of the contact in the FSL MNI152_T1_2mm grid (0-based), copied verbatim from column 'MNI X' of sourcedata/dryad-q573n5tph/allContacts_MNIcoords.csv."},
    "voxel_j": {"LongName": "Voxel index j (release value)", "Description": "Second voxel index of the contact in the FSL MNI152_T1_2mm grid (0-based), copied verbatim from column 'MNI Y' of allContacts_MNIcoords.csv."},
    "voxel_k": {"LongName": "Voxel index k (release value)", "Description": "Third voxel index of the contact in the FSL MNI152_T1_2mm grid (0-based), copied verbatim from column 'MNI Z' of allContacts_MNIcoords.csv."},
}
OLD = "; whether the release indices are 0- or 1-based is not stated (<= 2 mm per axis)"
NEWTXT = "; the 0-based reading was verified in Oct 2026 (see coordsystem.json), and x, y, z now hold these millimetre values"
for k in ("atlas_label_AAL3v1", "atlas_label_DesikanKilliany"):
    if k in E:
        E[k]["Description"] = E[k]["Description"].replace(OLD, NEWTXT).replace(" Coordinates in this file are unchanged.", "")
out = {**{k: v for k, v in new.items()}, **{k: v for k, v in E.items() if k not in new}}
with open(ej, "w") as fh:
    json.dump(out, fh, indent=2, ensure_ascii=False); fh.write("\n")
print("contacts converted:", n_conv)
