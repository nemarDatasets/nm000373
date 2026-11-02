"""fix-20261030 (nm000373): verify the voxel-index convention of allContacts_MNIcoords.csv against the paper's own
atlas statistics (Sherman et al. 2023 bioRxiv 10.1101/2023.01.11.523605 = JoCN 10.1162/jocn_a_02012):
 - visual cortex ROI (MNI structural Occipital Lobe + 11 Harvard-Oxford cortical ROIs, each prob>=10%): 116 contacts
 - Table 2 'Total' contacts per Harvard-Oxford cortical ROI (maxprob thr0)
 - hippocampus: 5 contacts across all patients
 - 1310 contacts in total (1194 outside the visual ROI)
Atlases: FSL 5.0.7 data packages (NeuroDebian fsldata 5.0.7-2), original FSL NIfTI headers.
"""
import io, json, os, re, sys, tarfile, csv, itertools
import numpy as np, nibabel as nib
import xml.etree.ElementTree as ET

# Usage: python fix-20261030_verify_voxel_convention.py <bids_root> <dir with the NeuroDebian fsldata 5.0.7-2 .deb files:
#   fsl-harvard-oxford-atlases, fsl-mni-structural-atlas, fsl-mni152-templates> <output dir>
# (http://neuro.debian.net/debian/pool/non-free/f/fsldata/). Needs numpy and nibabel.
REPO, FSL, OUT = sys.argv[1], sys.argv[2], sys.argv[3]; os.makedirs(OUT, exist_ok=True)

def deb_extract(deb, dest):
    b = open(deb, 'rb').read(); assert b[:8] == b'!<arch>\n'; p = 8
    while p < len(b):
        name = b[p:p+16].decode().strip(); size = int(b[p+48:p+58].decode().strip()); data = b[p+60:p+60+size]
        p += 60 + size + (size % 2)
        if name.startswith('data.tar'):
            tarfile.open(fileobj=io.BytesIO(data)).extractall(dest, filter='data')
X = os.path.join(FSL, 'x')
if not os.path.isdir(X):
    for d in sorted(os.listdir(FSL)):
        if d.endswith('.deb'): deb_extract(os.path.join(FSL, d), X)
def find(name):
    for root, _, files in os.walk(X):
        if name in files: return os.path.join(root, name)
    raise FileNotFoundError(name)

T1 = nib.load(find('MNI152_T1_2mm.nii.gz')); MASK = nib.load(find('MNI152_T1_2mm_brain_mask.nii.gz'))
cmax = nib.load(find('HarvardOxford-cort-maxprob-thr0-2mm.nii.gz')); smax = nib.load(find('HarvardOxford-sub-maxprob-thr0-2mm.nii.gz'))
cprob = nib.load(find('HarvardOxford-cort-prob-2mm.nii.gz')); mprob = nib.load(find('MNI-prob-2mm.nii.gz'))
def labels(xml):
    r = ET.parse(find(xml)).getroot(); return {int(l.get('index')) + 1: l.text.strip() for l in r.iter('label')}
CL = labels('HarvardOxford-Cortical.xml'); SL = labels('HarvardOxford-Subcortical.xml'); ML = labels('MNI.xml')
hdr = {}
for n, im in [('MNI152_T1_2mm', T1), ('brain_mask', MASK), ('HO-cort-maxprob-thr0', cmax), ('HO-sub-maxprob-thr0', smax), ('HO-cort-prob', cprob), ('MNI-prob', mprob)]:
    hdr[n] = {'shape': list(im.shape), 'sform': np.round(im.get_sform(), 4).tolist(), 'sform_code': int(im.header['sform_code']), 'qform': np.round(im.get_qform(), 4).tolist(), 'qform_code': int(im.header['qform_code'])}
    print(n, im.shape, 'sform', np.round(im.get_sform(), 3).tolist(), 'codes', int(im.header['sform_code']), int(im.header['qform_code']))

rows = list(csv.DictReader(open(os.path.join(REPO, 'sourcedata/dryad-q573n5tph/allContacts_MNIcoords.csv'))))
rows = [r for r in rows if r['Participant'].strip()]
ijk = np.array([[int(r['MNI X']), int(r['MNI Y']), int(r['MNI Z'])] for r in rows])
subj = np.array([r['Participant'] for r in rows]); names = [r['Electrode'] for r in rows]
print('contacts', len(rows), 'min', ijk.min(0).tolist(), 'max', ijk.max(0).tolist())
shape = np.array(T1.shape[:3])
bounds = {'0-based_inside_0..dim-1': bool(((ijk >= 0) & (ijk <= shape - 1)).all()), '1-based_inside_1..dim': bool(((ijk >= 1) & (ijk <= shape)).all()),
          'n_index_eq_0': int((ijk == 0).sum()), 'n_index_eq_dim': int((ijk == shape).sum()), 'dims': shape.tolist()}
print('bounds', bounds)

# used contacts = contacts whose name is a channel in the subject's BIDS channels.tsv (any run)
used = np.zeros(len(rows), bool)
for s in sorted(set(subj)):
    chans = set()
    d = os.path.join(REPO, s, 'ieeg')
    for f in os.listdir(d):
        if f.endswith('_channels.tsv'):
            for line in open(os.path.join(d, f)).read().splitlines()[1:]:
                chans.add(line.split('\t')[0])
    for n_, (ss, nm) in enumerate(zip(subj, names)):
        if ss == s and nm in chans: used[n_] = True
print('contacts with a matching channel', int(used.sum()))

cm = np.asarray(cmax.dataobj).astype(int); sm = np.asarray(smax.dataobj).astype(int); bm = np.asarray(MASK.dataobj) > 0
cp = np.asarray(cprob.dataobj); mp = np.asarray(mprob.dataobj)
vis_names = ['Inferior Temporal Gyrus, temporooccipital part', 'Lateral Occipital Cortex, superior division', 'Lateral Occipital Cortex, inferior division',
             'Intracalcarine Cortex', 'Cuneal Cortex', 'Parahippocampal Gyrus, posterior division', 'Lingual Gyrus', 'Temporal Occipital Fusiform Cortex',
             'Occipital Fusiform Gyrus', 'Supracalcarine Cortex', 'Occipital Pole']
inv = {v: k for k, v in CL.items()}
missing = [v for v in vis_names if v not in inv]; assert not missing, missing
vis = np.zeros(cm.shape, bool)
for v in vis_names: vis |= cp[..., inv[v] - 1] >= 10
occ = [k for k, v in ML.items() if v.lower().startswith('occipital')][0]
vis |= mp[..., occ - 1] >= 10
PAPER_T2 = {'Frontal Pole': 176, 'Insular Cortex': 59, 'Middle Frontal Gyrus': 65, 'Precentral Gyrus': 52, 'Temporal Pole': 51,
            'Middle Temporal Gyrus, posterior division': 45, 'Postcentral Gyrus': 47, 'Lateral Occipital Cortex, superior division': 36,
            'Lingual Gyrus': 13, 'Occipital Pole': 21}
for k in PAPER_T2: assert k in inv, k
hippo = [k for k, v in SL.items() if 'Hippocampus' in v]
wm = [k for k, v in SL.items() if 'White Matter' in v]; ctx = [k for k, v in SL.items() if 'Cortex' in v]

def lookup(arr, off, sel):
    p = ijk[sel] + np.array(off); ok = ((p >= 0) & (p < shape)).all(1)
    out = np.full(len(p), -1); q = p[ok]; out[ok] = arr[q[:, 0], q[:, 1], q[:, 2]]; return out

def stats(off, sel):
    c = lookup(cm, off, sel); s = lookup(sm, off, sel); v = lookup(vis.astype(int), off, sel); b = lookup(bm.astype(int), off, sel)
    t2 = {k: int((c == inv[k]).sum()) for k in PAPER_T2}
    # variant: only grey matter (subcortical atlas label 'Cerebral Cortex')
    t2gm = {k: int(((c == inv[k]) & np.isin(s, ctx)).sum()) for k in PAPER_T2}
    return {'visual': int((v == 1).sum()), 'visual_subjects': int(len(set(subj[sel][v == 1]))), 'hippocampus': int(np.isin(s, hippo).sum()),
            'in_brain_mask': int((b == 1).sum()), 'outside_volume': int((c == -1).sum()), 'T2': t2, 'T2_gm': t2gm,
            'T2_absdev': int(sum(abs(t2[k] - PAPER_T2[k]) for k in PAPER_T2)), 'T2gm_absdev': int(sum(abs(t2gm[k] - PAPER_T2[k]) for k in PAPER_T2))}

res = {'headers': hdr, 'bounds': bounds, 'n_contacts': len(rows), 'n_used': int(used.sum()), 'paper': {'visual': 116, 'hippocampus': 5, 'T2': PAPER_T2, 'total': 1310}}
for selname, sel in [('all', np.ones(len(rows), bool)), ('used', used)]:
    res[selname] = {}
    for name, off in [('0-based', (0, 0, 0)), ('1-based', (-1, -1, -1))]:
        st = stats(off, sel); res[selname][name] = st
        print(selname, name, json.dumps(st))
    # full shift scan (which single shift best reproduces the paper numbers)
    scan = []
    for off in itertools.product(range(-2, 3), repeat=3):
        st = stats(off, sel); scan.append({'off': off, 'visual': st['visual'], 'vis_dev': abs(st['visual'] - 116), 'T2_absdev': st['T2_absdev'], 'T2gm_absdev': st['T2gm_absdev'], 'hippocampus': st['hippocampus'], 'in_brain_mask': st['in_brain_mask']})
    scan.sort(key=lambda r: (r['T2_absdev'] + r['vis_dev']))
    res[selname]['shift_scan_top10'] = scan[:10]
    print(selname, 'best shifts', scan[:6])
    # rank of the two candidate conventions
    res[selname]['rank_0based'] = [s['off'] for s in scan].index((0, 0, 0)) + 1
    res[selname]['rank_1based'] = [s['off'] for s in scan].index((-1, -1, -1)) + 1
    print(selname, 'rank 0-based', res[selname]['rank_0based'], 'rank 1-based', res[selname]['rank_1based'], 'of', len(scan))

# orientation: hemisphere from L/R name prefix vs x_mm sign (x_mm = 90 - 2i under the FSL sform)
A = T1.get_sform()
mm0 = nib.affines.apply_affine(A, ijk); 
lr = []
for n_, nm in enumerate(names):
    m = re.match(r'^([LR])[A-Z]', nm)
    if m and not nm.startswith('LZ') : lr.append((m.group(1), mm0[n_, 0], subj[n_], nm))
agree = sum(1 for h, x, *_ in lr if (h == 'L' and x < 0) or (h == 'R' and x > 0))
res['hemisphere_check'] = {'n_named_LR': len(lr), 'agree_with_FSL_sform_sign': agree,
                           'disagree_examples': [(s, nm, h, float(x)) for h, x, s, nm in lr if not ((h == 'L' and x < 0) or (h == 'R' and x > 0))][:20]}
print('hemisphere', res['hemisphere_check'])
# per subject hemisphere vs Table 1
res['per_subject_x'] = {s: {'n': int((subj == s).sum()), 'n_left(x<0)': int(((subj == s) & (mm0[:, 0] < 0)).sum()), 'n_right(x>0)': int(((subj == s) & (mm0[:, 0] > 0)).sum())} for s in sorted(set(subj))}
print('per subject', res['per_subject_x'])
json.dump(res, open(os.path.join(OUT, 'fix-20261030_verify_voxel_convention.json'), 'w'), indent=1, default=lambda o: list(o) if isinstance(o, tuple) else str(o))
print('WROTE', OUT)
