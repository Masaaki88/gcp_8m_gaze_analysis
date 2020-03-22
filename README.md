# gcp_8m_gaze_analysis
Underlying data processing of "Gaze-Contingent Learning and Retention in 8-month-old infants"

extract_scalars v1.9.4 by Max Murakami, December 8 2016

This script extracts data from fixation reports, message reports, saccade reports, and the overview file.
These data are then processed for additional information, which are finally stored
into two Excel files and one Python object file.

Version history:
- 1.9.4:
    - Fixed linebreak character for Windows.
    - Script now compatible for 4m subjects.
- 1.9.3:
    - General interception of crashes.
    - Detecting wrong report file formats.
- 1.9.2: 
    - Fixed linebreak character for different OS.
    - Intercepting crash due to inconsistent subject names while processing cutoff_data.

Input files:
All fixation, saccade, and message files must be created by Dataviewer, using the files in the 'dataviewer_files' folder.
-> In Dataviewer, load experiment sessions and import the interest areas from 'interest_areas.ias'.
   -> Message report:
        Create a message report using the parameters from 'msg_data.props'.
        The filename must end with '_msg.xls' (e.g. 'vp1_msg.xls').
        Store it into the 'reports' folder.
   -> Fixation report:
        Create a fixation report using the parameters from 'fix_data.props'.
        The filename must end with '_fix.xls'.
        You can name it like 'vpX_fix.xls'.
        Store it into the 'reports' folder.
   -> Saccade report:
        Create a saccade report using the parameters from 'sac_data.props'.
        The filename must end with '_sac.xls'.
        Store it into the 'reports' folder.
The overview files goes into the 'overview' folder.
    -> The overview file of the 8-months-olds must be named 'Overview.xls'.
    -> The overview file of the 6-months-olds must be named 'Overview_6m.xls'.
    -> The overview file of the 10-months-olds must be named 'Overview_10m.xls'.
-> Important: This program can only read the old .xls format! Save the overview file in that format!

Output files:
All output files are stored in the 'extracted_data' folder.

- scalars.xls: A tab-separated text file, which can be loaded with Excel.
   For each experiment session, it contains the following scalar data:
    Experiment parameters
    - subject name
    - session number
    - age in months
    - subject group: active-active (AA), active-yoked (AY), yoked-active (YA), yoked-yoked (YY)
    - session type (active or passive)
    - subject gender
    - latency: short (ca. 120 ms) or long (ca. 450 ms)
    - functioning side: left or right
    - lab setup: old or new
    - saccade cutoff duration: saccades that are longer than this were filtered out
    Measurements
    - first fixation side: which disc was fixated first?
    - failure rate: estimated empirical failure rate of intended trigger fixations
    - total time: time between first and last fixation in ms
    - trigger count: how many images were triggered?
    - mean trigger rate: trigger count divided by total time
    - fixation count: how many fixations were recorded in total?
    - mean fixation rate: fixation count divided by total time
    - mean fixation duration: how long did each fixation last on average?
    - image fixation count: how often was the image fixated?
    - mean image fixation rate: image fixation count divided by total time
    - mean image fixation durations: how long did each image fixation last on average?
    - right fixation count: how often was the right disc fixated?
    - mean right fixation rate: right fixation count divided by total time
    - mean right fixation durations: how long did each right disc fixation last on average?
    - left fixation count: how often was the left disc fixated?
    - mean left fixation rate: left fixation count divided by total time
    - mean left fixation duration: how long did each left disc fixation last on average?
    - white fixation count: how often was the white background fixated (everything except the discs and the image)?
    - mean white fixation rate: white fixation count divided by total time
    - mean white fixation duration: how long did each background fixation last on average?
    - functioning side fixation count: how often was the functioning disc fixated?
    - mean functioning side fixation rate: functioning side fixation count divided by total time
    - mean functioning side fixation duration: how long did each functioning side fixation last on average?
    - nonfunctioning side fixation count: how often was the nonfunctioning disc fixated?
    - mean nonfunctioning side fixation rate: nonfunctioning side fixation count divided by total time
    - mean nonfunctioning side fixation duration: how long did each nonfunctioning side fixation last on average?
    - right immediate gaze pattern count: how often did the fixation sequence "image -> right disc -> image" occur?
    - mean right immediate gaze pattern rate: right immediate gaze pattern count divided by total time
    - left immediate gaze pattern count: how often did the fixation sequence "image -> left disc -> image" occur?
    - mean left immediate gaze pattern rate: left immediate gaze pattern count divided by total time
    - functioning side immediate gaze pattern count: how often did the fixation sequence "image -> functioning disc -> image" occur?
    - mean functioning side immediate gaze pattern rate: functioning side immediate gaze pattern count divided by total time
    - nonfunctioning side immediate gaze pattern count: 
        how often did the fixation sequence "image -> nonfunctioning disc -> image" occur?
    - mean nonfunctioning side immediate gaze pattern rate: nonfunctioning side immediate gaze pattern count divided by total time
    - right extended gaze pattern count: how often did the fixation sequence 
        "image -> any number of fixations anywhere except on the left disc and at least once on the right disc -> image" occur?
    - mean right extended gaze pattern rate: right extended gaze pattern count divided by total time
    - left extended gaze pattern count: how often did the fixation sequence 
        "image -> any number of fixations anywhere except on the right disc and at least once on the left disc -> image" occur?
    - mean left extended gaze pattern rate: left extended gaze pattern count divided by total time
    - left-right extended gaze pattern count: how often did the fixation sequence
        "image -> any number of fixations anywhere and at least one on the left disc and one on the right disc -> image" occur?
    - mean left-right extended gaze pattern rate: left-right extended gaze pattern count divided by total time
    - total extended gaze pattern count: sum of left, right, and left-right extended gaze pattern counts
    - mean total extended gaze pattern rate: total extended gaze pattern rate divided by total time
    - functioning side extended gaze pattern count: how often did the fixation sequence "image -> 
            any number of fixations anywhere except on the nonfunctioning disc and at least once on the functioning disc -> 
            image" occur?
    - mean functioning side extended gaze pattern rate: functioning side extended gaze pattern count divided by total time
    - nonfunctioning side extended gaze pattern count: how often did the fixation sequence "image -> 
            any number of fixations anywhere except on the functioning disc and at least once on the nonfunctioning disc -> 
            image" occur?
    - mean nonfunctioning side extended gaze pattern rate: nonfunctioning side extended gaze pattern count divided by total time
    - gaze event count: 
        a gaze event is defined as a sequence of fixations on the same interest area and the saccades in between
        -> how many were there in total?
    - mean gaze event rate: gaze event count divided by total time
    - mean gaze event duration: how long did each gaze event last on average?
    - image gaze event count: how many continuous image fixation sequences were there?
    - mean image gaze event rate: image gaze event count divided by total time
    - mean image gaze event duration: how long did each image gaze event last on average?
    - right gaze event count: how many continuous right disc fixation sequences were there?
    - mean right gaze event rate: right gaze event count divided by total time
    - mean right gaze event duration: how long did each right disc gaze event last on average?
    - left gaze event count: how many continuous left disc fixation sequences were there?
    - mean left gaze event rate: left gaze event count divided by total time
    - mean left gaze event duration: how long did each left disc gaze event last on average?
    - white gaze event count: how many continuous background fixation sequences were there?
    - mean white gaze event rate: white gaze event count divided by total time
    - mean white gaze event duration: how long did each background gaze event last on average?
    - functioning side gaze event count: how many continuous functioning disc fixation sequences were there?
    - mean functioning side gaze event rate: functioning side gaze event count divided by total time
    - mean functioning side gaze event duration: how long did each functioning side gaze event last on average?
    - nonfunctioning side gaze event count: how many continuous nonfunctioning disc fixation sequences were there?
    - mean nonfunctioning side gaze event rate: nonfunctioning side gaze event count divided by total time
    - mean nonfunctioning side gaze event duration: how long did each nonfunctioning side gaze event last on average?
    - left full gaze pattern count: how often did the gaze event sequence "image -> 
            any number of fixations anywhere except on the right disc and at least once on the left disc -> 
            image" occur?
	- right full gaze pattern count: how often did the gaze event sequence "image -> 
            any number of fixations anywhere except on the left disc and at least once on the right disc -> 
            image" occur?
	- functioning side full gaze pattern count: how often did the gaze event sequence "image -> 
            any number of fixations anywhere except on the nonfunctioning disc and at least once on the functioning disc -> 
            image" occur?
	- nonfunctioning side full gaze pattern count: how often did the gaze event sequence "image -> 
            any number of fixations anywhere except on the functioning disc and at least once on the nonfunctioning disc -> 
            image" occur?
    - number of full minutes: how many minutes of the experiment has the subject completed?
    - epoch data: for minutes 1 to 5 of the experiment, various statistics are listed (see above for explanation)

- inter_trigger_intervals.xls: A tab-separated text file, which can be loaded with Excel.
   It contains the following data:
    - subject number
    - session number
    - trigger intervals: the time differences between each image trigger and the next in ms.
        -> the precise computations measure the time difference between the playback between the ding sounds

- extracted_data.dat: A Python dictionary, which can be loaded with cPickle.
   For each experiment session, it contains a subdictionary with all stored data:
    Experiment parameters
    - subject_name
    - group: AA (active-active), AY (active-yoked), YA (yoked-active), or YY (yoked-yoked)
    - session_number
    - age (in months)
    - session_type (active or yoked)
    - gender
    - latency: short (ca. 120 ms) or long (ca. 450 ms)
    - functioning_side: left or right
    - lab_setup: old or new
    - dt_cutoff: cutoff value for fixation time filtering in ms
    Measurements, scalar values (all times in ms, rates in Hz)
    - first_fix: which disc was fixated first?
    - failure_rate: estimated empirical failure rate of intended trigger fixations
    - total_time: time between first and last fixation in ms
    - N_triggers: how many images were triggered?
    - mean_trigger_freq: trigger count divided by total time
    - N_all: how many fixations were recorded in total?
    - mean_all_freq: fixation count divided by total time
    - mean_all_dur: how long did each fixation last on average?
    - N_im: how often was the image fixated?
    - mean_im_freq: image fixation count divided by total time
    - mean_im_dur: how long did each image fixation last on average?
    - N_R: how often was the right disc fixated?
    - mean_R_freq: right fixation count divided by total time
    - mean_R_dur: how long did each right disc fixation last on average?
    - N_L: how often was the left disc fixated?
    - mean_L_freq: left fixation count divided by total time
    - mean_L_dur: how long did each left disc fixation last on average?
    - N_white: how often was the white background fixated (everything except the discs and the image)?
    - mean_white_freq: white fixation count divided by total time
    - mean_white_dur: how long did each background fixation last on average?
    - N_funct: how often was the functioning disc fixated?
    - mean_funct_freq: functioning side fixation count divided by total time
    - mean_funct_dur: how long did each functioning side fixation last on average?
    - N_nonfunct: how often was the nonfunctioning disc fixated?
    - mean_nonfunct_freq: nonfunctioning side fixation count divided by total time
    - mean_nonfunct_dur: how long did each nonfunctioning side fixation last on average?
    - N_R_pattern_im: how often did the fixation sequence "image -> right disc -> image" occur?
    - mean_R_pattern_im_freq: right immediate gaze pattern count divided by total time
    - N_L_pattern_im: how often did the fixation sequence "image -> left disc -> image" occur?
    - mean_L_pattern_im_freq: left immediate gaze pattern count divided by total time
    - N_funct_pattern_im: how often did the fixation sequence "image -> functioning disc -> image" occur?
    - mean_funct_pattern_im_freq: functioning side immediate gaze pattern count divided by total time
    - N_nonfunct_pattern_im: how often did the fixation sequence "image -> nonfunctioning disc -> image" occur?
    - mean_nonfunct_pattern_im_freq: nonfunctioning side immediate gaze pattern count divided by total time
    - N_R_pattern_ex: how often did the fixation sequence 
        "image -> any number of fixations anywhere except on the left disc and at least once on the right disc -> image" occur?
    - mean_R_pattern_ex_freq: right extended gaze pattern count divided by total time
    - N_L_pattern_ex: how often did the fixation sequence 
        "image -> any number of fixations anywhere except on the right disc and at least once on the left disc -> image" occur?
    - mean_L_pattern_ex_freq: left extended gaze pattern count divided by total time
    - N_LR_pattern_ex: how often did the fixation sequence
        "image -> any number of fixations anywhere and at least one on the left disc and one on the right disc -> image" occur?
    - mean_LR_pattern_ex_freq: left-right extended gaze pattern count divided by total time
    - N_pattern_ex_total: sum of left, right, and left-right extended gaze pattern counts
    - mean_pattern_ex_total_freq: total extended gaze pattern rate divided by total time
    - N_funct_pattern_ex: how often did the fixation sequence "image -> 
            any number of fixations anywhere except on the nonfunctioning disc and at least once on the functioning disc -> 
            image" occur?
    - mean_funct_pattern_ex_freq: functioning side extended gaze pattern count divided by total time
    - N_nonfunct_pattern_ex: how often did the fixation sequence "image -> 
            any number of fixations anywhere except on the functioning disc and at least once on the nonfunctioning disc -> 
            image" occur?
    - mean_nonfunct_pattern_ex_freq: nonfunctioning side extended gaze pattern count divided by total time
    - N_gaze_all: 
        a gaze event is defined as a sequence of fixations on the same interest area and the saccades in between
        -> how many were there in total?
    - mean_all_gaze_events_freq: gaze event count divided by total time
    - mean_all_gaze_events_dur: how long did each gaze event last on average?
    - N_gaze_im: how often was the image gazed at?
    - mean_im_gaze_events_freq: image gaze event count divided by total time
    - mean_im_gaze_events_dur: how long did each image gaze event last on average?
    - N_gaze_R: how often was the right disc gazed at?
    - mean_R_gaze_events_freq: right gaze event count divided by total time
    - mean_R_gaze_events_dur: how long did each right disc gaze event last on average?
    - N_gaze_L: how often was the left disc gazed at?
    - mean_L_gaze_events_freq: left gaze event count divided by total time
    - mean_L_gaze_events_dur: how long did each left disc gaze event last on average?
    - N_gaze_white: how often was the background gazed at?
    - mean_white_gaze_events_freq: white gaze event count divided by total time
    - mean_white_gaze_events_dur: how long did each background gaze event last on average?
    - N_gaze_funct: how often was the functioning disc gazed at?
    - mean_funct_gaze_events_freq: functioning side gaze event count divided by total time
    - mean_funct_gaze_events_dur: how long did each functioning side gaze event last on average?
    - N_gaze_nonfunct: how often was the nonfunctioning disc gazed at?
    - mean_nonfunct_gaze_events_freq: nonfunctioning side gaze event count divided by total time
    - mean_nonfunct_gaze_events_dur: how long did each nonfunctioning side gaze event last on average?
    - N_L_full_gaze_pattern: how often did the gaze event sequence "image -> 
            any number of fixations anywhere except on the right disc and at least once on the left disc -> 
            image" occur?
	- N_R_full_gaze_pattern: how often did the gaze event sequence "image -> 
            any number of fixations anywhere except on the left disc and at least once on the right disc -> 
            image" occur?
	- N_funct_full_gaze_pattern: how often did the gaze event sequence "image -> 
            any number of fixations anywhere except on the nonfunctioning disc and at least once on the functioning disc -> 
            image" occur?
	- N_nonfunct_full_gaze_pattern: how often did the gaze event sequence "image -> 
            any number of fixations anywhere except on the functioning disc and at least once on the nonfunctioning disc -> 
            image" occur?
    - N_epochs: how many minutes of the experiment has the subject completed?
    - epochs_data: for minutes 1 to 5 of the experiment, various statistics are listed (see above for explanation)
    Measurements, time series
    - all_times: the start times of all recorded fixations in ms
    - all_durations: the durations of all recorded fixations in ms
    - im_times: the start times of all fixations on the image in ms
    - im_durations: the durations of all fixations on the image in ms
    - L_times: the start times of all fixations on the left disc in ms
    - L_durations: the durations of all fixations on the left disc in ms
    - R_times: the start times of all fixation on the right disc in ms
    - R_durations: the durations of all fixations on the right disc in ms
    - white_times: the start times of all fixations on the white background (everything except the discs and the image) in ms
    - white_durations: the durations of all fixations the background in ms
    - funct_times: the start times of all fixations on the functioning disc in ms
    - funct_durations: the durations of all fixations on the functioning disc in ms
    - nonfunct_times: the start times of all fixations on the nonfunctioning disc in ms
    - nonfunct_durations: the durations of all fixations on the nonfunctioning disc in ms
    - trigger_times: the trigger times of the sounds preceding the images in ms
    - trigger_times_real: the unfiltered trigger times of the sounds preceding the images in ms
    - L_pattern_im_times: the start times of all fixation sequences "image -> left disc -> image" in ms
    - R_pattern_im_times: the start times of all fixation sequences "image -> right disc -> image" in ms
    - funct_pattern_im_times: the start times of all fixation sequences "image -> functioning disc -> image" in ms
    - nonfunct_pattern_im_times: the start times of all fixation sequences "image -> nonfunctioning disc -> image" in ms
    - L_pattern_ex_times: the start times of all fixation sequences "image -> 
        any number of fixations anywhere except on the right disc and at least once on the left disc -> image" in ms
    - R_pattern_ex_times: the start times of all fixation sequences "image -> 
        any number of fixations anywhere except on the left disc and at least once on the right disc -> image" in ms
    - LR_pattern_ex_times: the start times of all fixation sequences "image ->
        any number of fixations anywhere with at least one on the left disc and one on the right disc -> image" in ms
    - funct_pattern_ex_times: the start times of all fixation sequences "image -> 
        any number of fixations anywhere except on the nonfunctioning disc and at least once on the functioning disc -> image" in ms
    - nonfunct_pattern_ex_times: the start times of all fixation sequences "image -> 
        any number of fixations anywhere except on the functioning disc and at least once on the nonfunctioning disc -> image" in ms
    - all_gaze_events_times: the start times of all fixation and saccade sequences within the same interest area in ms
    - all_gaze_events_durations: the durations of all fixation and saccade sequences within the same interest area in ms
    - R_gaze_events_times: the start times of all continuous fixation and saccade sequences within the right disc in ms
    - R_gaze_events_durations: the durations of all continuous fixation and saccade sequences within the right disc in ms
    - L_gaze_events_times: the start times of all continuous fixation and saccade sequences within the left disc in ms
    - L_gaze_events_durations: the durations of all continuous fixation and saccade sequences within the left disc in ms
    - im_gaze_events_times: the start times of all continuous fixation and saccade sequences within the image in ms
    - im_gaze_events_durations: the durations of all continuous fixation and saccade sequences within the image in ms
    - white_gaze_events_times: the start times of all continuous fixation and saccade sequences within the background in ms
    - white_gaze_events_durations: the start times of all continuous fixation and saccade sequences within the background in ms
    - fixation_trajectory: the sequence of fixated areas
    - gaze_event_trajectory: the sequence of gazed at areas
    - cutoff_data: the start times, end times, and durations of excluded saccades in ms
