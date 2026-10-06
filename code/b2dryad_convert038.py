"""IEEG038 (Dryad doi:10.5061/dryad.q573n5tph, Sherman et al. 2023 JoCN) -> iEEG-BIDS.

Source = MNE-BIDS-style EDF release (sub-N_task-X_eeg.edf + channels.tsv + eeg.json, some events.tsv),
plus allContacts_MNIcoords.csv. The EDF files are copied byte-for-byte (no rewrite, no filtering, no resampling,
no re-referencing, no channel dropping). Only BIDS naming/sidecars change:
  sub-N            -> sub-0N (matches the coordinate file's participant labels sub-01..sub-08)
  task-categorySL1 -> task-categorySL_run-1 ; task-categorySL2 -> task-categorySL_run-2
  task-exemplarSL1 -> task-exemplarSL_run-1 ; task-random1 -> task-random_run-1
  datatype eeg     -> ieeg (intracranial recordings)
Events: decoded from the source TRIG channel (rising edges of TRIG > 0), plus the source events.tsv rows where present.
Electrodes: allContacts_MNIcoords.csv values copied verbatim (integer voxel indices in the FSL MNI152 2 mm template
according to the release README/methods); units are therefore declared "n/a" with a description, not converted.
Usage: python b2dryad_convert038.py <src_dir> <bids_root>
"""
import csv
import hashlib
import json
import os
import re
import shutil
import sys
from collections import Counter, defaultdict

import mne
import numpy as np

SRC, OUT = sys.argv[1], sys.argv[2]
DOI = "10.5061/dryad.q573n5tph"
TASKMAP = {"categorySL1": ("categorySL", 1), "categorySL2": ("categorySL", 2),
           "exemplarSL1": ("exemplarSL", 1), "random1": ("random", 1)}
TASKDESC = {
    "categorySL": "Category-level Structured condition: trial-unique scene photographs whose scene categories were paired across repetitions (e.g., beach always followed by canyon). Each image 250 ms, then 250 ms inter-stimulus interval.",
    "exemplarSL": "Exemplar-level Structured condition: a sequence of 6 repeating scene images (non-overlapping scene categories) presented in fixed pairs (image A always followed by image B). Each image 250 ms, then 250 ms inter-stimulus interval.",
    "random": "Random (baseline) condition: the 6 repeating scene images presented in random temporal order. Each image 250 ms, then 250 ms inter-stimulus interval.",
}
NONNEURAL = {"TRIG": "TRIG", "ECG": "ECG", "EMG": "EMG", "OSAT": "MISC", "PR": "MISC", "Pleth": "MISC"}


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 22), b""):
            h.update(b)
    return h.hexdigest()


def wtsv(path, header, rows):
    with open(path, "w", newline="") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        w.writerow(header)
        for r in rows:
            w.writerow(["n/a" if (v is None or v == "") else v for v in r])


def wjson(path, obj):
    with open(path, "w") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)
        f.write("\n")


def chan_type(name):
    if name in NONNEURAL:
        return NONNEURAL[name]
    if re.fullmatch(r"DC\d+", name) or re.fullmatch(r"C\d+", name):
        return "MISC"
    return "EEG"  # intracranial contact; source does not state grid/strip/depth per electrode


os.makedirs(OUT, exist_ok=True)
files = sorted(f for f in os.listdir(SRC) if f.endswith("_eeg.edf"))
mapping, scans = [], defaultdict(list)
coords = defaultdict(list)
with open(os.path.join(SRC, "allContacts_MNIcoords.csv"), encoding="utf-8-sig") as f:
    for r in csv.DictReader(f):
        coords[r["Participant"]].append(r)
report = {"runs": [], "electrodes": {}}
subjects = set()
for fn in files:
    m = re.fullmatch(r"sub-(\d+)_task-([A-Za-z0-9]+)_eeg\.edf", fn)
    sn, stask = m.group(1), m.group(2)
    task, run = TASKMAP[stask]
    sub = f"sub-{int(sn):02d}"
    subjects.add(sub)
    stem = f"{sub}_task-{task}_run-{run}"
    d = os.path.join(OUT, sub, "ieeg")
    os.makedirs(d, exist_ok=True)
    src_edf = os.path.join(SRC, fn)
    dst_edf = os.path.join(d, f"{stem}_ieeg.edf")
    if not (os.path.exists(dst_edf) and os.path.getsize(dst_edf) == os.path.getsize(src_edf)):
        shutil.copyfile(src_edf, dst_edf)
    s_hash, d_hash = sha256(src_edf), sha256(dst_edf)
    assert s_hash == d_hash, fn
    # source sidecars
    base = fn[:-len("_eeg.edf")]
    sj = json.load(open(os.path.join(SRC, base + "_eeg.json")))
    with open(os.path.join(SRC, base + "_channels.tsv"), encoding="utf-8-sig") as f:
        sch = list(csv.DictReader(f, delimiter="\t"))
    raw = mne.io.read_raw_edf(dst_edf, preload=False, verbose="error")
    names = raw.ch_names
    assert [r["name"] for r in sch] == names, f"channel order mismatch {fn}"
    sf = raw.info["sfreq"]
    assert abs(sf - float(sj["SamplingFrequency"])) < 1e-9
    # channels.tsv
    rows, cnt = [], Counter()
    for r in sch:
        t = chan_type(r["name"])
        cnt[t] += 1
        grp = re.sub(r"\d+$", "", r["name"]) if t == "EEG" else "n/a"
        desc = {"EEG": "Intracranial contact (source type label EEG; electrode type not stated in the release)",
                "TRIG": "Trigger channel: above 0 during the screen flip at each image onset (see README)",
                "ECG": "Electrocardiogram (non-neural; disregard for neural analyses per source README)",
                "EMG": "Electromyogram (non-neural; disregard per source README)",
                "MISC": "Non-EEG channel (C/DC/OSAT/PR/Pleth); source README: disregard, does not contain EEG data"}[t]
        units = r["units"] if r["units"] not in ("", "n/a") else "n/a"
        rows.append([r["name"], t, units, r["low_cutoff"], r["high_cutoff"], r["sampling_frequency"], grp,
                     r["status"], r["status_description"], desc])
    wtsv(os.path.join(d, f"{stem}_channels.tsv"),
         ["name", "type", "units", "low_cutoff", "high_cutoff", "sampling_frequency", "group", "status", "status_description", "description"], rows)
    # events from TRIG
    tr = np.round(raw.get_data(picks=["TRIG"])[0], 6)
    vals, cnts = np.unique(tr, return_counts=True)
    trig_base = vals[np.argmax(cnts)]  # resting TRIG level (mode); differs across participants (0, 8 or 16)
    on = tr != trig_base
    edges = np.flatnonzero(on[1:] & ~on[:-1]) + 1
    if on[0]:
        edges = np.r_[0, edges]
    offs = np.flatnonzero(~on[1:] & on[:-1]) + 1
    ev = []
    for e in edges:
        nxt = offs[offs > e]
        end = int(nxt[0]) if len(nxt) else len(tr)
        seg = tr[e:end]
        codes = [seg[0]] + [v for a, v in zip(seg[:-1], seg[1:]) if v != a]
        ev.append((e / sf, (end - e) / sf, "trigger", "|".join("%g" % c for c in codes), int(e), "TRIG", "%g" % trig_base))
    src_ev = os.path.join(SRC, base + "_events.tsv")
    if os.path.exists(src_ev):
        with open(src_ev, encoding="utf-8-sig") as f:
            for r in csv.DictReader(f, delimiter="\t"):
                ev.append((float(r["onset"]), float(r["duration"]), r["trial_type"], r["value"], int(r["sample"]), "source_events_tsv", "n/a"))
    ev.sort(key=lambda x: (x[0], x[5]))
    wtsv(os.path.join(d, f"{stem}_events.tsv"), ["onset", "duration", "trial_type", "value", "sample", "source", "trig_baseline"],
         [["%.9f" % a, "%.9f" % b, c, v, s, src, bl] for a, b, c, v, s, src, bl in ev])
    # ieeg.json
    ij = {
        "TaskName": task,
        "TaskDescription": TASKDESC[task],
        "Instructions": "n/a",
        "SamplingFrequency": sf,
        "PowerLineFrequency": 60,
        "SoftwareFilters": "n/a",
        "HardwareFilters": "n/a",
        "Manufacturer": "Natus",
        "ManufacturersModelName": "NeuroWorks",
        "iEEGReference": "Signals were referenced to an electrode chosen by the clinical team to minimize noise in the recording (Dryad methods).",
        "RecordingDuration": raw.n_times / sf,
        "RecordingType": "continuous",
        "EEGChannelCount": cnt.get("EEG", 0),
        "ECGChannelCount": cnt.get("ECG", 0),
        "EMGChannelCount": cnt.get("EMG", 0),
        "MiscChannelCount": cnt.get("MISC", 0),
        "TriggerChannelCount": cnt.get("TRIG", 0),
        "ElectricalStimulation": False,
    }
    wjson(os.path.join(d, f"{stem}_ieeg.json"), ij)
    scans[sub].append((f"ieeg/{stem}_ieeg.edf", "n/a", fn))
    mapping.append([fn, f"{sub}/ieeg/{stem}_ieeg.edf", s_hash, raw.n_times, len(names), sf, len(edges)])
    report["runs"].append({"source": fn, "bids": f"{sub}/ieeg/{stem}_ieeg.edf", "sha256": s_hash, "n_times": raw.n_times,
                           "n_channels": len(names), "sfreq": sf, "n_trig_events": int(len(edges)),
                           "trig_baseline": float(trig_base), "trig_code_sequences": dict(Counter(e[3] for e in ev if e[5] == "TRIG").most_common(12))})
    print("run", fn, "->", stem, raw.n_times, len(names), len(edges), flush=True)

# electrodes + coordsystem per subject
for sub in sorted(subjects):
    d = os.path.join(OUT, sub, "ieeg")
    rows = coords.get(sub, [])
    chans = set()
    for fn in os.listdir(d):
        if fn.endswith("_channels.tsv"):
            with open(os.path.join(d, fn)) as f:
                chans |= {r["name"] for r in csv.DictReader(f, delimiter="\t")}
    matched = sum(1 for r in rows if r["Electrode"] in chans)
    if rows:
        wtsv(os.path.join(d, f"{sub}_space-MNI152NLin6Asym_electrodes.tsv"), ["name", "x", "y", "z", "size", "group"],
             [[r["Electrode"], r["MNI X"], r["MNI Y"], r["MNI Z"], "n/a", re.sub(r"\d+$", "", r["Electrode"])] for r in rows])
        wjson(os.path.join(d, f"{sub}_space-MNI152NLin6Asym_coordsystem.json"), {
            "iEEGCoordinateSystem": "MNI152NLin6Asym",
            "iEEGCoordinateUnits": "n/a",
            "iEEGCoordinateSystemDescription": "Values copied verbatim from the release file allContacts_MNIcoords.csv, described by the authors as coordinates 'in MNI 2mm standard space'. All values are positive integers (x 7-83, y 11-106, z 9-82), consistent with voxel indices of the FSL MNI152 T1 2 mm template (FSL MNI152_T1_2mm, i.e. MNI152NLin6Asym at 2 mm), not millimetres. They were not converted. If they are 0-based FSL voxel indices, millimetre coordinates follow from the template affine: x_mm = 90 - 2*x, y_mm = 2*y - 126, z_mm = 2*z - 72 (unverified assumption).",
            "iEEGCoordinateProcessingDescription": "Authors' method (Dryad record): contact locations identified on post-operative CT and MRI, reconstructed in BioImage Suite, registered to the pre-operative MRI, converted from .MGRID to native-space coordinates with FieldTrip, written as a one-voxel-per-contact mask in FSL native space, and linearly registered to the MNI T1 2 mm standard brain.",
            "iEEGCoordinateProcessingReference": "Sherman BE, Aljishi A, Graves KN, Quraishi IH, Sivaraju A, Damisah EC, Turk-Browne NB (2023). Intracranial entrainment reveals statistical learning across levels of abstraction. J Cogn Neurosci. doi:10.1162/jocn_a_02012",
        })
    report["electrodes"][sub] = {"coord_rows": len(rows), "matched_channel_names": matched, "channels_union": len(chans)}
    wtsv(os.path.join(OUT, sub, f"{sub}_scans.tsv"), ["filename", "acq_time", "source_file"], scans[sub])

wtsv(os.path.join(OUT, "participants.tsv"), ["participant_id", "source_id", "age", "sex", "handedness"],
     [[s, f"sub-{int(s[4:])}", "n/a", "n/a", "n/a"] for s in sorted(subjects)])
wjson(os.path.join(OUT, "participants.json"), {
    "participant_id": {"Description": "BIDS participant label (zero-padded to match allContacts_MNIcoords.csv)"},
    "source_id": {"Description": "Participant label used in the Dryad file names"},
    "age": {"Description": "Age in years (not given in the Dryad release)", "Units": "year"},
    "sex": {"Description": "Sex (not given in the Dryad release)", "Levels": {"M": "male", "F": "female"}},
    "handedness": {"Description": "Handedness (not given in the Dryad release)"},
})
os.makedirs(os.path.join(OUT, "code"), exist_ok=True)
wtsv(os.path.join(OUT, "code", "source_to_bids_mapping.tsv"),
     ["source_file", "bids_file", "sha256_identical_bytes", "n_samples", "n_channels", "sfreq", "n_trig_events"], mapping)
shutil.copy(__file__, os.path.join(OUT, "code", os.path.basename(__file__)))
json.dump(report, open(os.path.join(OUT, "code", "conversion_report.json"), "w"), indent=1, default=lambda o: o.item() if hasattr(o, "item") else str(o))
print("DONE", len(files), "runs", len(subjects), "subjects")
print(json.dumps(report["electrodes"], indent=1))
