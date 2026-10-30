"""fix-20261030: channel types of nm000373 from source evidence.

Evidence:
- Source README (sourcedata/dryad-q573n5tph/README.md): channels labelled "ECG" do not contain EEG data. The
  converter mapped only the exact names ECG/EMG, so ECG1, ECG2, "ECG 2", EMG1, EMG2 stayed EEG. They become ECG/EMG.
- Paper Table 1 (participants.tsv implant_type): sub-07 and sub-08 had depth electrodes only. Their channels that are
  contacts of an electrode in the authors' contact table (sourcedata/.../allContacts_MNIcoords.csv), i.e. the name is
  <electrode prefix><number> and that prefix has a listed contact, are depth contacts: EEG -> SEEG.
- Remaining EEG channels whose electrode is not in the contact table keep type EEG; their description now says so.
- Combined-implant participants (sub-01..06): the release does not say which electrodes are grids, strips or depths,
  so their intracranial contacts keep the source label EEG (README).
The *_ieeg.json channel counts are recomputed. Usage: python fix-20261030_channel_types.py <bids_root>
"""
import collections, csv, glob, json, os, re, sys

root = sys.argv[1]
con = collections.defaultdict(set)
for r in csv.reader(open(os.path.join(root, "sourcedata/dryad-q573n5tph/allContacts_MNIcoords.csv"))):
    if r and r[0].startswith("sub-"):
        con[r[0]].add(r[1].strip())
prefixes = {s: {re.match(r"(.*?)(\d+)$", c).group(1) for c in cs if re.match(r".*?\d+$", c)} for s, cs in con.items()}
depth_only = {p["participant_id"] for p in csv.DictReader(open(os.path.join(root, "participants.tsv")), delimiter="\t")
              if p["implant_type"] == "depth"}
D_ECG = "Electrocardiogram (non-neural; source README: channels labelled ECG do not contain EEG data)"
D_EMG = "Electromyogram (non-neural; disregard for neural analyses)"
D_SEEG = "Depth (stereo-EEG) contact: participant implanted with depth electrodes only (paper Table 1) and electrode listed in allContacts_MNIcoords.csv"
D_NOTC = "Not an electrode of the authors' contact table (allContacts_MNIcoords.csv); kind of electrode not stated in the release (type kept EEG)"
COUNT = {"EEG": "EEGChannelCount", "SEEG": "SEEGChannelCount", "ECOG": "ECOGChannelCount", "ECG": "ECGChannelCount",
         "EMG": "EMGChannelCount", "EOG": "EOGChannelCount", "MISC": "MiscChannelCount", "TRIG": "TriggerChannelCount"}
changes = collections.Counter()
for ch in sorted(glob.glob(os.path.join(root, "sub-*/ieeg/*_channels.tsv"))):
    sub = os.path.basename(ch).split("_")[0]
    rows = list(csv.DictReader(open(ch, newline=""), delimiter="\t"))
    header = list(rows[0].keys())
    for r in rows:
        if r["type"] != "EEG":
            continue
        n = r["name"]
        m = re.match(r"(.*?)(\d+)$", n)
        if n.upper().startswith("ECG"):
            r["type"], r["description"] = "ECG", D_ECG
        elif n.upper().startswith("EMG"):
            r["type"], r["description"] = "EMG", D_EMG
        elif m and m.group(1) in prefixes[sub]:
            if sub in depth_only:
                r["type"], r["description"] = "SEEG", D_SEEG
            else:
                continue
        else:
            r["description"] = D_NOTC
        changes[(sub, r["type"])] += 1
    with open(ch, "w", newline="") as f:
        w = csv.DictWriter(f, header, delimiter="\t", lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    js = ch.replace("_channels.tsv", "_ieeg.json")
    d = json.load(open(js))
    cnt = collections.Counter(r["type"] for r in rows)
    for t, k in COUNT.items():
        if k in d or cnt.get(t):
            d[k] = cnt.get(t, 0)
    first = open(js).read().split("\n")[1]
    with open(js, "w") as f:
        json.dump(d, f, indent=len(first) - len(first.lstrip(" ")), ensure_ascii=False)
        f.write("\n")
for k, v in sorted(changes.items()):
    print(k, v)
