[![DOI](https://img.shields.io/badge/DOI-10.82901%2Fnemar.nm000373-blue)](https://doi.org/10.82901/nemar.nm000373)

# Intracranial entrainment reveals statistical learning across levels of abstraction

## Overview
Raw intracranial EEG (iEEG) from 8 neurosurgical patients with electrodes implanted for seizure monitoring, recorded
while they viewed rapid streams of scene photographs with statistical structure at the category or exemplar level.
The study measured neural entrainment (phase coherence) at the image frequency (2 Hz) and at the pair frequency (1 Hz)
to track online statistical learning of exemplar-level and category-level regularities (Sherman et al., 2023).

## Source
- Dryad: Sherman B, Aljishi A, Graves K, Quraishi I, Sivaraju A, Damisah E, Turk-Browne N. Data for: Intracranial
  entrainment reveals statistical learning across levels of abstraction. doi:10.5061/dryad.q573n5tph (version
  3, published 2023-07-07). License: CC0 1.0 (Dryad record
  `https://spdx.org/licenses/CC0-1.0.html`; the Zenodo replica record 8018664 also states cc-zero).
- Article: Sherman et al. (2023) J Cogn Neurosci, doi:10.1162/jocn_a_02012. Preprint: doi:10.1101/2023.01.11.523605.
- Acquired from the Zenodo replica of the Dryad record (community "dryad", same DOI); every file matched the Dryad
  API sha-256 digest. The original files are kept unchanged in `sourcedata/dryad-q573n5tph/`.

## Participants
- 8 patients (7 male, 1 female; age range 21-61 years, mean 37.8 years) surgically implanted with intracranial
  electrodes for localization of the seizure onset zone, recruited through the Yale Comprehensive Epilepsy Center; all
  data were collected at Yale New Haven Hospital (paper, Methods, Participants).
- Implants: 6 patients had depth electrodes combined with subdural grid/strip electrodes ("combined"), 2 had depth
  electrodes only; coverage was left, right, primarily left/right or bilateral depending on the patient. Electrode
  placement was determined solely by the clinical care team. Contacts were in the visual cortex ROI in 7 of 8 patients.
- `participants.tsv`: age, sex, implant type, hemisphere and number of contacts are taken from Table 1 of the paper
  (age, sex and handedness are not given in the Dryad release itself; handedness is not reported in the paper either,
  so it stays n/a). Paper patient ID N corresponds to release participant `sub-N` (BIDS `sub-0N`): the hemisphere
  distribution of each participant's contacts in `allContacts_MNIcoords.csv`, the presence/absence of grid (G*)
  electrode labels and the relative contact counts match Table 1 one-to-one (details in the NEMAR enrichment notes).
- Recording dates/years are not given (the source randomized the date information in the EDF metadata).

## Task (from the release and the paper)
- Category-level Structured (task-categorySL): trial-unique scene images whose categories were paired across
  repetitions (e.g., beach always followed by canyon). 6/8 participants completed two runs (run-1, run-2).
- Exemplar-level Structured (task-exemplarSL): 6 repeating scene images presented in fixed pairs.
- Random (task-random): the same kind of 6-image set in random order (baseline).
- Each image 250 ms, followed by a 250 ms inter-stimulus interval.
- Paper (Methods, Stimuli and Procedure): 720 unique outdoor scene images from 18 subcategories (40 per subcategory),
  6 subcategories randomly assigned to each condition per participant; images 600 x 800 pixels, presented with MATLAB
  and the Psychophysics Toolbox on a laptop while the patient sat in the hospital bed. SOA fixed at 500 ms (fixation
  cross during the ISI); each run was 240 trials (2 min of viewing). Participants passively viewed the stream and were
  asked to pay attention to each image. Before category-level runs they were told the names of the six categories, but
  not that the sequence contained pairs. Condition order: category-level structured run(s) first (two back-to-back runs
  with the same sequence when possible), then one exemplar-level structured and one random run, counterbalanced.
  Each category pair / exemplar pair occurred 40 times per run.

## Recording (from the Dryad methods and the paper)
- Natus NeuroWorks EEG system, 4096 Hz. Reference: an electrode chosen by the clinical team to minimize noise.
- Triggers: a custom DAQ converted signals from the research computer into 8-bit triggers inserted into an open EEG
  channel (TRIG). The authors state the iEEG files are the raw data, unprocessed except that the date information
  in the file metadata was randomized for anonymity (EDF start date 01.01.85, patient field anonymized).
- Electrode localization (paper): post-operative CT and MRI, reconstruction in BioImage Suite, registration to the
  pre-operative MRI, conversion to native-space coordinates with FieldTrip, one-voxel-per-contact masks in FSL, linear
  registration (FLIRT, 12 dof) to the MNI T1 2 mm template.

## Preprocessing
- None in this dataset (raw data). For reference, the paper's analysis (FieldTrip) applied a 60 Hz notch filter, no
  re-referencing, downsampling to 256 Hz and segmentation into trials; it excluded the first two trials of every run
  because of a computer-based timing error that shortened the first trial's ISI in some runs.

## Conversion (what changed and what did not)
- EDF files are byte-identical copies of the source files (sha-256 listed in `code/source_to_bids_mapping.tsv`).
  No filtering, resampling, re-referencing or channel removal.
- Renaming: sub-N -> sub-0N; task-categorySL1/2 -> task-categorySL run-1/2; task-exemplarSL1 -> task-exemplarSL
  run-1; task-random1 -> task-random run-1; datatype eeg -> ieeg.
- channels.tsv: names, units, cut-offs and status from the source channels.tsv. Intracranial contacts keep the
  source type label `EEG` because the release does not say which electrodes are grids, strips or depths. Channels
  the source README says to disregard (C*, DC*, OSAT, PR, Pleth) are typed MISC, ECG/EMG as such, TRIG as TRIG.
  The `group` column is the electrode prefix of the contact name.
- events.tsv: one row per TRIG pulse (onset = first sample away from the run's resting TRIG level, duration = until it
  returns, value = the sequence of TRIG levels in the pulse),
  plus the rows of the source events.tsv where the release has one (sub-3).
- Electrodes: `allContacts_MNIcoords.csv` copied verbatim into `*_space-MNI152NLin6Asym_electrodes.tsv`. The values
  are positive integers consistent with FSL MNI152 2 mm voxel indices, so units are declared n/a and the values are
  not converted (see coordsystem.json for the affine, an unverified assumption). For sub-01 the labels R1 and R2 each
  appear twice in the source file with different coordinates and are not among the recorded channels; these 4
  ambiguous rows are left out of electrodes.tsv (the original file is in sourcedata).
- participants.tsv: age, sex and handedness are not given in the Dryad release (n/a); age, sex and implant details
  were added from Table 1 of the paper (2026-10-07, see CHANGES).

## Files
- `sub-0N/ieeg/`: EDF recordings, `*_channels.tsv`, `*_events.tsv`, `*_ieeg.json` per run; MNI electrode table and
  coordsystem per participant. `sub-0N/sub-0N_scans.tsv` lists the original Dryad file name of every recording.
- `sourcedata/dryad-q573n5tph/`: the unchanged Dryad files; `code/`: conversion script and reports.

## Known caveats
- Stimulus photographs are not part of the release and not included here.
- The meanings of the TRIG codes are not documented in the release; source events.tsv files exist for sub-3 only.
- Electrode coordinates are voxel indices (see Conversion); the electrode type of each contact (grid/strip/depth) is
  not given per contact in the release.
- Contact counts in the release are slightly higher than the nContacts column of the paper's Table 1 (kept as
  published in `n_contacts_paper`).
- Two patients were tested a second time, 2 days later, because their first data set was unusable (eye irritation in
  one, a trigger error in the other); the paper does not say which patients (the release contains one set of runs per
  participant).
- The first trial's ISI was shorter than intended in some runs (paper); the authors dropped the first two trials.

## How to load
```python
from mne_bids import BIDSPath, read_raw_bids
bp = BIDSPath(root=".", subject="01", task="categorySL", run="1", datatype="ieeg", suffix="ieeg", extension=".edf")
raw = read_raw_bids(bp)
```

## Citation
Sherman BE, Aljishi A, Graves KN, Quraishi IH, Sivaraju A, Damisah EC, Turk-Browne NB (2023). Intracranial Entrainment
Reveals Statistical Learning across Levels of Abstraction. Journal of Cognitive Neuroscience 35(8):1312-1328.
doi:10.1162/jocn_a_02012. Data: doi:10.5061/dryad.q573n5tph.

## Provenance of the metadata
- Dryad record and release README (sourcedata), and the article full text (Methods: Participants, Table 1, iEEG
  Recordings, iEEG Preprocessing, Electrode Localization, Stimuli, Procedure; Acknowledgments; Funding Information),
  read on direct.mit.edu on 2026-10-07.

## Ethics approval

Verbatim from Sherman BE, Aljishi A, Graves KN, Quraishi IH, Sivaraju A, Damisah EC, Turk-Browne NB (2023). Intracranial Entrainment Reveals Statistical Learning across Levels of Abstraction. Journal of Cognitive Neuroscience 35(8):1312-1328. https://doi.org/10.1162/jocn_a_02012, Methods, "Participants":

> Patients were recruited through the Yale Comprehensive Epilepsy Center and provided informed consent in a manner approved by the Yale University Human Subjects Committee.

## Atlas labels of the electrode positions (added 2026-10-08)

Each `electrodes.tsv` that has coordinates now has two derived columns, `atlas_label_AAL3v1` and `atlas_label_DesikanKilliany`. They are an atlas lookup of the coordinates already in the file (voxel indices in the MNI152 2 mm template converted to mm with the FSL MNI152_T1_2mm affine (x=-2i+90, y=2j-126, z=2k-72); whether the release indices are 0- or 1-based is not stated (<= 2 mm per axis)), made for NEMAR; they are not labels given by the authors, and the coordinates themselves are unchanged. Method and caveats: `electrodes.json`. 1121 of 1344 contacts received a label.
