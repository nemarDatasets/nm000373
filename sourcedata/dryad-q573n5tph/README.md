# Data for: Intracranial entrainment reveals statistical learning across levels of abstraction
---

The following submission contains the data reported from the manuscript "Intracranial entrainment reveals statistical learning across levels of abstraction". The dataset was obtained from 8 neurosurgical patients who had intracranially implanted electrodes for seizure monitoring. Intracranial EEG (iEEG) data were recorded while the patients viewed a rapid stream of scene images. In the Category-Level Structured condition, patients viewed a series of trial-unique scene images, in which the categories of scenes were paired across repetitions (e.g., images of beach always followed by images of canyons). In the Exemplar-level Structured condition, participants viewed a sequence of 6 repeating scene images (from non-overlapping scene categories), which were paired across repetitions (e.g., image A always followed by image B). In the baseline Random condition, participants again viewed a sequence of 6 repeating scene images, but the images were presented in a random temporal order. Each image was presented for 250 ms, followed by a 250 ms inter-stimulus-interval period. Participants completed at least one run of each of these three conditions. Additionally, 6/8 participants completed two runs of the Category-level Structured condition.

We measured neural entrainment to the frequency of individual photographs, which was expected in all conditions, but critically also at half that frequency --- the rate at which to-be-learned pairs appeared in the two structured (but not random) conditions. Entrainment to both exemplar and category pairs emerged within minutes throughout visual cortex and in frontal and temporal regions. Many electrode contacts were sensitive to only one level of structure, but a significant number encoded both levels.


## Description of the data and file structure

Each run of the task is associated with 3 datafiles (see below). The datafiles are anonymized and are labeled by participant and by task. 

The participant is specified by the "sub-" prefix. For example, files that start with "sub-6" correspond to Participant #6's files.

The task is specified by the "task-" infix. They are:
"task-categorySL1": a participant's first run of the category-level structured condition
"task-categorySL2": a participant's second run of the category-level structured condition
"task-exemplarSL1": a participant's exemplar-level structured condition
"task-random1": a participant's random condition

Each run has three corresponding data files. The datafiles are as follows:
- the .edf file contains the EEG data for each channel. Note that the date information in the metadata of the file has been modified to preserve anonymity.
- the .tsv file contains the list of all of the EEG channels. Several channels should be noted:
  - Any channel labeled "C", "DC", "OSAT", "ECG", "PR", or "Pleth" should be disregarded, as these do not contain EEG data. 
  - The TRIG channel contains the experimental events. Triggers were sent at the onset of each image; specifically, the trigger channel was set to be above 0 starting at the onset of the screen flip, and was set back to 0 at the end of a screen flip (when the image was presented).
- the .json file contains metadata about the recording.

allContacts_MNIcoords.csv contains the coordinates of each electrode contact (in MNI 2mm standard space) for all participants. The first column specifies the participant, the second column specifies the electrode label, the third column is the X coordinate, the fourth column is the Y coordinate, and the fifth column is the Z coordinate. 

