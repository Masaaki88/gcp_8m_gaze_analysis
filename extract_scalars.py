import os
import xlrd
import cPickle
import numpy as np
import argparse
import scipy as sp
from scipy import stats, spatial
import sys
import platform
import traceback
if platform.system() == 'Windows':
    WINDOWS = True      # global system variable
else:
    WINDOWS = False
    site_packages_path = '/home/murakami/lib/python2.7/site-packages/'
    if os.path.exists(site_packages_path):
        sys.path.append(site_packages_path)
from tqdm import tqdm





###########################################################
#
#   Initialization
#
###########################################################    


FAILURE_RATE = None
parser = argparse.ArgumentParser()
parser.add_argument('-c', '--dt_cutoff', type=int, default=200, help='Cutoff value of saccade duration for filtering in ms')

args = parser.parse_args()
dt_cutoff = args.dt_cutoff
invalid_sessions = ['52.2', '10my6.2', '8m8.1', '24.3', '59.3', '8m15.3']
tamara_affices = ['msc_4_', 'msc4_', 'm4_15_', 'm5_15_', 'm_15_', 'm4_14_']





###########################################################
#
#   Functions:
#       get_user_args()
#       get_linebreak() returns linebreak
#       convert_number(number_with_comma) returns number_with_period
#       extract_subject_no(key_appendix) returns key_number, yoked
#       set_key_key_value(dic, sup_key, sub_key, value) returns dic
#       get_cell_entry(cell) returns entry
#       filter_dic(dic_total) returns dic_total
#       process_overviews() returns error, overview_dic
#       get_parameters(experiment_name, overview_dic) returns params_dic, error
#       extract_failure_rate(coordinates, functioning_side, subject_name) returns trigger_failure_rate
#       wrap_up(dic_total, R_times, L_times, im_times, white_times, all_times, L_pattern_im_times, R_pattern_im_times)
#           returns (dic_total, error_in_loop)
#       store_results(dic_total)
#       initialize_fixation_data() returns
#           (all_times, all_durations, R_times, R_durations, L_times, L_durations, im_times, im_durations, white_times,
#             white_durations, R_pattern_im_times, L_pattern_im_times, R_pattern_ex_times, L_pattern_ex_times, R_pattern_ex_eligible,
#             L_pattern_ex_eligible, gaze_pattern_ex_time_temp, all_gaze_events_times, all_gaze_events_durations, R_gaze_events_times,
#             R_gaze_events_durations, L_gaze_events_times, L_gaze_events_durations, im_gaze_events_times, im_gaze_events_durations,
#             white_gaze_events_times, white_gaze_events_durations)
#       process_message_files(files_msg, dic_total) returns (dic_total, error_in_loop)
#       process_fixation_files(files_fix, dic_total) returns (dic_total, error_in_loop)
#
###########################################################




def get_user_args():
    """
    function for getting parameters from user

    global: FAILURE_RATE (bool), True if failure rate will be calculated
    """
    global FAILURE_RATE

    while True:
        input_str = raw_input('Calculate failure rate? (y/n) ')
        if input_str in ['y', 'yes']:
            FAILURE_RATE = True
            break
        elif input_str in ['n', 'no']:
            FAILURE_RATE = False
            break
    return


###
#
###


def get_linebreak():
    """ 
    function for specifying linebreak encoding in current operating system

    global: WINDOWS (bool), True if script is executed in Windows

    output: linebreak (str), string encoding linebreak in current operating system
    """
    global WINDOWS


    if WINDOWS:
        linebreak = '\r\n'
    else:
        linebreak = '\n'


    return linebreak


###
#
###


def convert_number(number_with_comma):
    """
    function for modifying number strings so they can be cast into float:
        "4,5" -> "4.5"
    
    input: number_with_comma (str), string representing float number with comma

    output: number_with_period (str), string representing float number with period
    """
    if ',' in number_with_comma:
        int_decimals = number_with_comma.split(',')
        number_with_period = int_decimals[0]+'.'+int_decimals[1]
    else:
        number_with_period = number_with_comma

    return number_with_period


###
#
###


def extract_subject_no(key_appendix):
    """
    function for parsing session keys

    input: key_appendix (str), session key without age index, e.g. "35.4"

    output:
        key_number (int), subject number
        group (str), subject group (AA, AY, YA, or YY)
    """

    error = False

    if key_appendix[:2] == 'ay':
        key_appendix = key_appendix.split('ay')[1]
        group = 'AY'
    elif key_appendix[:2] == 'ya':
        key_appendix = key_appendix.split('ya')[1]
        group = 'YA'
    elif key_appendix[0] == 'y':
        key_appendix = key_appendix.split('y')[1]
        group = 'YY'
    else:
        group = 'AA'

    if key_appendix[0] == '_':
        key_appendix = key_appendix[1:]

    if '.' in key_appendix:      # get subject number (session name format vp[subject no.].[session no.]
        key_number_str = key_appendix.split('.')[0]
    elif '-' in key_appendix:
        key_number_str = key_appendix.split('-')[0]
    elif '_' in key_appendix:
        key_number_str = key_appendix.split('_')[0]
    else:       # first session not indicated explicitly
        key_number_str = key_appendix

    try:
        key_number = int(key_number_str)
    except ValueError:
        print 'Error: Key number {} not recognized (original: {})!'.format(key_number_str, key_appendix)
        key_number = -42
        error = True

    return key_number, group, error


###
#
###


def set_key_key_value(dic, sup_key, sub_key, value):
    """
    function for setting key-value of subdirectory of given directory

    input:
        dic (dictionary), total dictionary containing dictionaries of each subject session as subdictionaries
        -> structure: {'vp1':{param1:value1, param2:value2,...}, 'vp2':{param1:value1, param2:value2,...}...}
        sup_key (str), key of dictionary corresponding to subject session subdirectory ('vpX')
        sub_key (str), key of subject session subdirectory (paramX)
        value (any), value corresponding to sub_key (valueX)

    output: dic (dictionary), updated total dictionary
    """

    try:        # check whether dic is actually a dictionary
        keys = dic.keys()
    except AttributeError:
        print 'Error:', dic, 'is not a dictionary!'

    if sup_key in keys:     # check whether subdirectory already exists
        dic[sup_key].update({sub_key:value})
    else:       # create subdirectory with given key-value pair
        dic[sup_key] = {sub_key:value}

    return dic


###
#
###


def get_cell_entry(cell):
    """
    function for reading cell entry of given xls spreadsheet cell

    input: cell (xlrd.sheet.cell object), cell to be read from

    output: entry (any), value stored in cell
    """

    cell_str = str(cell)    # get cell description
    if 'text' in cell_str:  # typical text cell: text:u'L'
        entry = cell_str.split("'")[1]
    elif 'number' in cell_str:  # typical numerical cell: number:3.0
        entry = cell_str.split(':')[1].split('.')[0]
    else:
        entry = ''

    return entry


###
#
###


def filter_dic(dic_total):
    """
    function for removing invalid session data from data dic

    input: dic_total (dictionary), dictionary containing all data

    global: invalid_sessions (list), list of names of invalid sessions

    output: dic_total (dictionary), updated data dictionary
    """
    global invalid_sessions

    for session_key in invalid_sessions:
        try:
            del dic_total[session_key]
        except KeyError:
            continue

    return dic_total


###
#
###


def process_overviews():
    """
    function for parsing overview files for different age groups

    outputs:
        error (boolean), error encountered during function execution?
        overview_dic (dictionary), dictionary containing for each subject
            all relevant data extracted from overview files:
                - age (4, 6, 8, or 10)
                - group ('AA', 'AY', 'YA', or 'YY')
                - gender ('male' or 'female')
                - latency ('short' or 'long')
                - functioning_side ('R' or 'L')
                - lab_setup ('old' or 'new')
    """
    overview_dic = {}

    error = False
    while not error:

        overview_file4 = './overview/Overview_4m.xls'
        overview_file6 = './overview/Overview_6m.xls'
        overview_file8 = './overview/Overview.xls'
        overview_file10 = './overview/Overview_10m.xls'

        overview_files = [overview_file6, overview_file8, overview_file10]
        age_groups = ['6', '8', '10']
        N_age_groups = len(age_groups)
        condition_groups = ['AA', 'YY', 'AY', 'YA']     # for sheet loop
        N_conditions_groups = len(condition_groups)


        for i_age in xrange(N_age_groups):
            age = age_groups[i_age]
            overview_file = overview_files[i_age]
            if os.path.exists(overview_file):
                try:
                    overview_data = xlrd.open_workbook(overview_file)
                except:
                    error = True
                    print 'Error: Overview file {} could not be loaded!'.format(overview_file)
                    break
                sheets = overview_data.sheets()
                N_sheets = len(sheets)
                if N_sheets > N_conditions_groups:
                    N_sheets = N_conditions_groups

                for i_sheet in xrange(N_sheets):
                    current_condition = condition_groups[i_sheet]
                    try:
                        current_sheet = sheets[i_sheet]
                    except:
                        error = True
                        print 'Error: Sheet {} could not be accessed!'.format(i_sheet)
                        break

                    N_lines = current_sheet.nrows
                    for i_line in xrange(1,N_lines):    # first line is description
                        subject_dic = {}
                        line = current_sheet.row(i_line)
                        subject_name = get_cell_entry(line[0])
                        if get_cell_entry(line[2]) == '':
                            continue
                        else:
                            subject_dic.update({'age':age})
                            subject_dic.update({'group':current_condition})
                            gender = get_cell_entry(line[1])
                            if gender == 'm':
                                subject_dic.update({'gender':'male'})
                            elif gender == 'f':
                                subject_dic.update({'gender':'female'})
                            else:
                                print 'Warning: Gender of subject {} not recognized ({})!'.format(subject_name, gender)
                                subject_dic.update({'gender':'not recognized'})
                            latency = get_cell_entry(line[2])
                            if latency == '1':
                                subject_dic.update({'latency':'short'})
                            elif latency == '2':
                                subject_dic.update({'latency':'long'})
                            else:
                                print 'Warning: Latency of subject {} not recognized ({})!'.format(subject_name, latency)
                                subject_dic.update({'latency':'not recognized'})
                            functioning_side = get_cell_entry(line[3])
                            if functioning_side == 'R':
                                subject_dic.update({'functioning_side':'R'})
                            elif functioning_side == 'L':
                                subject_dic.update({'functioning_side':'L'})
                            else:
                                print 'Warning: Functioning side of subject {} not recognized ({})!'.format(subject_name,
                                    functioning_side)
                                subject_dic.update({'functioning_side':'not recognized'})
                            lab_setup = get_cell_entry(line[8])
                            if lab_setup == '0':
                                subject_dic.update({'lab_setup':'old'})
                            elif lab_setup == '1':
                                subject_dic.update({'lab_setup':'new'})
                            else:
                                print 'Warning: Lab setup of subject {} not recognized!'.format(subject_name, lab_setup)
                                subject_dic.update({'lab_setup':'not recognized'})

                            overview_dic.update({subject_name:subject_dic})
                        # end of line loop

                    if error:
                        break
                    # end of sheet loop

            if error:
                break
            # end of age loop

        break

    return error, overview_dic


###
#
###


def get_parameters(experiment_name, overview_dic):
    """
    function for reading subject session experiment parameters from overview file
    -> parameters are: gender, latency, functioning side, subject number, session number
    
    input: experiment_name (str), name of experiment session

    output: params_dic (dictionary), dictionary containing parameters
    """

    error = False
    params_dic = None

    while True:

        tamara = False
        for tamara_affix in tamara_affices:
            if tamara_affix in experiment_name:
                tamara = True
                subject_name = experiment_name
                session_number = '1'

        if not tamara:
            if 'm_' in experiment_name:
                experiment_name = experiment_name.split('_')[0]+experiment_name.split('_')[1]
            if 'm10_' in experiment_name:
                experiment_name = '10m'+experiment_name.split('m10_')[1]
            if 'm6_' in experiment_name:
                experiment_name = '6m'+experiment_name.split('m6_')[1]
            if 'Y' in experiment_name:
                experiment_name = experiment_name.split('Y')[0]+'y'+experiment_name.split('Y')[1]

            if '.' in experiment_name:      # session names have format vp[subject no.].[session no.], e.g. vpX.y
                subject_name, session_number = experiment_name.split('.')
            elif '-' in experiment_name:
                subject_name, session_number = experiment_name.split('-')
            elif '_' in experiment_name:
                try:
                    subject_name, session_number = experiment_name.split('_')
                except ValueError:
                    subject_name = experiment_name
                    session_number = '1'
            else:       # first session contains no suffix, e.g. vpX
                subject_name = experiment_name
                session_number = '1'

        try:
            subject_dic = overview_dic[subject_name]
        except:
            print 'Error: Failed to load data of subject {}!'.format(subject_name)
            error = True
            break

        group = subject_dic['group']

        if (group[0]=='Y' and session_number=='1') or (group[1]=='Y' and session_number=='2'):
            session_type = 'yoked'
        else:
            session_type = 'active'

        gender = subject_dic['gender']
        latency = subject_dic['latency']
        side = subject_dic['functioning_side']
        lab_setup = subject_dic['lab_setup']
        age = subject_dic['age']

        params_dic = {'gender':gender, 'latency':latency, 'functioning_side':side,
            'subject_name':subject_name, 'session_number':session_number, 'group':group, 'lab_setup':lab_setup,
            'session_type':session_type, 'age':age}
        break
    
    return params_dic, error


###
#
###


def extract_failure_rate(coordinates, functioning_side, subject_name):
    """
    functiong for calculating empirical trigger failure rates:
        proportion of attempted disc fixations that actually fell within disc, as judged by eye tracker

    inputs:
        coordinates (ndarray) lists fixation x- and y-coordinate for each fixation
        functioning_side (string), 'R' or 'L'
        subject_name (string), name of subject

    output: trigger_failure_rate (float), empirical trigger failure rate
    """
    len_coord = len(coordinates[0])

    m1 = coordinates[0]
    m2 = coordinates[1]

    xmin = 0.0
    xmax = 1024.0
    ymin = 0.0
    ymax = 768.0

    # Perform a kernel density estimate on the data:

    X, Y = np.mgrid[xmin:xmax:1024j, ymin:ymax:768j]
    positions = np.vstack([X.ravel(), Y.ravel()])
    values = np.vstack([m1, m2])
    kernel = sp.stats.gaussian_kde(values, 0.1)
    Z = np.reshape(kernel(positions).T, X.shape)

    # Classify disc fixations

    Z_L = Z[:256]
    Z_R = Z[768:]
    coord_max_L = Z_L.argmax()
    coord_max_L = np.array(np.unravel_index(coord_max_L, Z_L.shape))
    coord_max_R = Z_R.argmax()
    coord_max_R = np.array(np.unravel_index(coord_max_R, Z_R.shape))
    coord_max_R += np.array([768.0,0.0])

    V = [1,1]   # euclidean weighting
    L_center = [100.0, 384.0]
    R_center = [924.0, 384.0]
    im_x_min = 312.0
    im_x_max = 712.0
    im_y_min = 250.0
    im_y_max = 518.0

    N_TrueNegatives = 0
    N_TruePositives = 0

    fixation_trajectory_est = []
    gaze_pattern_ex_trajectory_est = []
    gaze_pattern_ex_loc_temp = []

    for i_fix in xrange(len_coord):
        coord_i = [coordinates[0][i_fix], coordinates[1][i_fix]]
        # left disc
        if spatial.distance.seuclidean(coord_i, coord_max_L, V) < 90.0:
            fixation_trajectory_est.append('L')
            gaze_pattern_ex_loc_temp.append('L')
            if functioning_side == 'L':
                if spatial.distance.seuclidean(coord_i, L_center, V) < 90.0:
                    N_TruePositives += 1
                else:
                    N_TrueNegatives += 1
        # right disc
        elif spatial.distance.seuclidean(coord_i, coord_max_R, V) < 90.0:
            fixation_trajectory_est.append('R')
            gaze_pattern_ex_loc_temp.append('R')
            if functioning_side == 'R':
                if spatial.distance.seuclidean(coord_i, R_center, V) < 90.0:
                    N_TruePositives += 1
                else:
                    N_TrueNegatives += 1
        # image
        elif (coord_i[0] > im_x_min) and (coord_i[0] < im_x_max) and (coord_i[1] > im_y_min) and (coord_i[1] < im_y_max):
            fixation_trajectory_est.append('image')
            if len(gaze_pattern_ex_loc_temp) > 0:
                if 'image' in gaze_pattern_ex_loc_temp[0]:
                    if ('R' in gaze_pattern_ex_loc_temp) and not ('L' in gaze_pattern_ex_loc_temp):
                        gaze_pattern_ex_trajectory_est.append('R')
                    elif ('L' in gaze_pattern_ex_loc_temp) and not ('R' in gaze_pattern_ex_loc_temp):
                        gaze_pattern_ex_trajectory_est.append('L')
                    elif ('L' in gaze_pattern_ex_loc_temp) and ('R' in gaze_pattern_ex_loc_temp):
                        gaze_pattern_ex_trajectory_est.append('LR')
                gaze_pattern_ex_loc_temp = []
            gaze_pattern_ex_loc_temp.append('image')
        # white
        else:
            fixation_trajectory_est.append('white')


    try:
        trigger_failure_rate = 1.0*N_TrueNegatives/(N_TrueNegatives+N_TruePositives)
    except ZeroDivisionError:
        print 'Warning: No functioning disc fixations of session {}!'.format(subject_name)
        trigger_failure_rate = -42.0



    return trigger_failure_rate, fixation_trajectory_est, gaze_pattern_ex_trajectory_est


###
#
###


def wrap_up(dic_total, current_name, R_times, L_times, im_times, white_times, all_times, L_pattern_im_times, R_pattern_im_times,
    L_pattern_ex_times, R_pattern_ex_times, LR_pattern_ex_times, all_gaze_events_times, all_gaze_events_durations, 
    R_gaze_events_times, 
    R_gaze_events_durations, L_gaze_events_times, L_gaze_events_durations, im_gaze_events_times, im_gaze_events_durations, 
    white_gaze_events_times, white_gaze_events_durations, all_durations, R_durations, L_durations, im_durations, white_durations,
    fixation_trajectory, gaze_event_trajectory, N_full_gaze_pattern_R, N_full_gaze_pattern_L,
    fixation_trajectory_epochs, pattern_ex_epochs, gaze_event_trajectory_epochs, cutoff_data, overview_dic, coordinates):

    """
    function for processing fixation data and storing everything in total dictionary

    input:
        dic_total (dictionary), total dictionary containing data of each experiment in subdictionaries
        current_name (str), current experiment session label
        R_times (list), list of fixation times on right disc
        L_times (list), list of fixation times on left disc
        im_times (list), list of fixation times on image
        white_times (list), list of fixation times on rest of screen
        all_times (list), list of all recorded fixation times
        L_pattern_im_times (list), list of immediate left gaze pattern times
        R_pattern_im_times (list), list of immediate right gaze pattern times
        L_pattern_ex_times (list), list of extended left gaze pattern times
        R_pattern_ex_times (list), list of extended right gaze pattern times
        LR_pattern_ex_times (list), list of extended left&right gaze pattern times
        all_gaze_events_times (list), list of gaze event start times
        all_gaze_events_durations (list), list of gaze event durations
        R_gaze_events_times (list), list of right disc gaze event start times
        R_gaze_events_durations (list), list of right disc gaze event durations
        L_gaze_events_times (list), list of left disc gaze event start times
        L_gaze_events_durations (list), list of left disc gaze event durations
        im_gaze_events_times (list), list of image gaze event start times
        im_gaze_events_durations (list), list of image gaze event durations
        white_gaze_events_times (list), list of background gaze event start times
        white_gaze_events_durations (list), list of background gaze event durations
        all_durations (list), list of all fixation durations
        R_durations (list), list of right disc fixation durations
        L_durations (list), list of left disc fixation durations
        im_durations (list), list of image fixation durations
        white_durations (list), list of background fixation durations
        fixation_trajectory (list), sequence of fixated areas
        gaze_event_trajectory (list), sequence of gazed at areas
N_full_gaze_pattern_R, N_full_gaze_pattern_L,
    fixation_trajectory_epochs, pattern_ex_epochs, gaze_event_trajectory_epochs, cutoff_data, overview_dic, coordinates

    output:
        dic_total (dictionary), updated total dictionary
        error_in_loop (bool), True if error encountered in function
    """
    global invalid_sessions

    #print 'dic_total:', dic_total

    error = False
    while not error:

        '''
        if current_name in invalid_sessions:
            dic_total.update({current_name:None})
            break
        else:
        '''
        dic_params, error = get_parameters(current_name, overview_dic)   
            # call get_parameters() to get experiment parameters of current session
        if error:
            break
        coordinates = np.array(coordinates)
        functioning_side = dic_params['functioning_side']
        if FAILURE_RATE:
            failure_rate, fixation_trajectory_est, gaze_pattern_ex_trajectory_est = extract_failure_rate(coordinates, 
                functioning_side, current_name)
        else:
            failure_rate = 5
            fixation_trajectory_est = fixation_trajectory

        N_R = len(R_times)      # number of fixations on right disc
        N_L = len(L_times)      # number of fixations on left disc
        N_im = len(im_times)    # number of fixations on image
        N_white = len(white_times)  # number of fixation on rest of sreen
        N_all = len(all_times)      # number of all recorded fixations
        if N_all != (N_R+N_L+N_im+N_white):     
            # check whether fixations in all_times are captured in area fixation lists
            print 'Warning: number total fixations not equal to sum of fixations!'
            print ' N_all:', N_all
            print ' sum of fixations:', N_R+N_L+N_im+N_white
        N_R_est = fixation_trajectory_est.count('R')
        N_L_est = fixation_trajectory_est.count('L')
        N_white_est = fixation_trajectory_est.count('white')
        N_R_pattern_im = len(R_pattern_im_times)    # number of immediate right disc gaze patterns
        N_L_pattern_im = len(L_pattern_im_times)    # number of immediate left disc gaze patterns
        N_R_pattern_ex = len(R_pattern_ex_times)    # number of extended right disc gaze patterns
        N_L_pattern_ex = len(L_pattern_ex_times)    # number of extended left disc gaze patterns
        N_LR_pattern_ex = len(LR_pattern_ex_times)  # number of extended left-right disc gaze patterns
        N_pattern_ex_total = N_L_pattern_ex + N_R_pattern_ex + N_LR_pattern_ex
        if FAILURE_RATE:
            N_R_pattern_ex_est = gaze_pattern_ex_trajectory_est.count('R')
            N_L_pattern_ex_est = gaze_pattern_ex_trajectory_est.count('L')
            N_LR_pattern_ex_est = gaze_pattern_ex_trajectory_est.count('LR')
            N_pattern_ex_total_est = N_R_pattern_ex_est + N_L_pattern_ex_est + N_LR_pattern_ex_est
        else:
            N_R_pattern_ex_est = N_R_pattern_ex
            N_L_pattern_ex_est = N_L_pattern_ex
            N_LR_pattern_ex_est = N_LR_pattern_ex
            N_pattern_ex_total_est = N_pattern_ex_total
        N_gaze_all = len(all_gaze_events_times)     # number of total gaze events
        N_gaze_R = len(R_gaze_events_times)     # number of gaze events on right disc
        N_gaze_L = len(L_gaze_events_times)     # number of gaze events on left disc
        N_gaze_im = len(im_gaze_events_times)   # number of gaze events on image
        N_gaze_white = len(white_gaze_events_times) # number of gaze events on white background
        total_time = all_times[-1]-all_times[0]     # total session time

        N_epochs = len(fixation_trajectory_epochs)
        epochs_data = [{}, {}, {}, {}, {}]      

        if len(R_times) == 0 and len(L_times) > 0:
            first_fix = 'L'
        elif len(R_times) > 0 and len(L_times) == 0:
            first_fix = 'R'
        elif len(R_times) == 0 and len(L_times) == 0:
            first_fix = 'None'
        elif R_times[0] < L_times[0]:     # which disc was fixated first?
            first_fix = 'R'
        else:
            first_fix = 'L'

            # convert all fixation time lists into numpy arrays for computational efficiency
        R_times = np.array(R_times, dtype=int)
        L_times = np.array(L_times, dtype=int)
        all_times = np.array(all_times, dtype=int)
        im_times = np.array(im_times, dtype=int)
        white_times = np.array(white_times, dtype=int)
        all_durations = np.array(all_durations, dtype=int)
        R_durations = np.array(R_durations, dtype=int)
        L_durations = np.array(L_durations, dtype=int)
        im_durations = np.array(im_durations, dtype=int)
        white_durations = np.array(white_durations, dtype=int)
        R_pattern_im_times = np.array(R_pattern_im_times, dtype=int)
        L_pattern_im_times = np.array(L_pattern_im_times, dtype=int)
        R_pattern_ex_times = np.array(R_pattern_ex_times, dtype=int)
        L_pattern_ex_times = np.array(L_pattern_ex_times, dtype=int)
        LR_pattern_ex_times = np.array(LR_pattern_ex_times, dtype=int)
        all_gaze_events_times = np.array(all_gaze_events_times, dtype=int)
        all_gaze_events_durations = np.array(all_gaze_events_durations, dtype=int)
        R_gaze_events_times = np.array(R_gaze_events_times, dtype=int)
        R_gaze_events_durations = np.array(R_gaze_events_durations, dtype=int)
        L_gaze_events_times = np.array(L_gaze_events_times, dtype=int)
        L_gaze_events_durations = np.array(L_gaze_events_durations, dtype=int)
        im_gaze_events_times = np.array(im_gaze_events_times, dtype=int)
        im_gaze_events_durations = np.array(im_gaze_events_durations, dtype=int)
        white_gaze_events_times = np.array(white_gaze_events_times, dtype=int)
        white_gaze_events_durations = np.array(white_gaze_events_durations, dtype=int)

            # calculate mean frequencies in minutes (fixation times are stored in milliseconds)
        mean_R_freq = 60000.0 * N_R / total_time
        mean_L_freq = 60000.0 * N_L / total_time
        mean_all_freq = 60000.0 * N_all / total_time
        mean_im_freq = 60000.0 * N_im / total_time
        mean_white_freq = 60000.0 * N_white / total_time
        mean_L_pattern_im_freq = 60000.0 * N_L_pattern_im / total_time
        mean_R_pattern_im_freq = 60000.0 * N_R_pattern_im / total_time
        mean_L_pattern_ex_freq = 60000.0 * N_L_pattern_ex / total_time
        mean_R_pattern_ex_freq = 60000.0 * N_R_pattern_ex / total_time
        mean_LR_pattern_ex_freq = 60000.0 * N_LR_pattern_ex / total_time
        mean_pattern_ex_total_freq = 60000.0 * N_pattern_ex_total / total_time
        mean_all_gaze_events_freq = 60000.0 * N_gaze_all / total_time
        mean_R_gaze_events_freq = 60000.0 * N_gaze_R / total_time
        mean_L_gaze_events_freq = 60000.0 * N_gaze_L / total_time
        mean_im_gaze_events_freq = 60000.0 * N_gaze_im / total_time
        mean_white_gaze_events_freq = 60000.0 * N_gaze_white / total_time
        mean_R_freq_est = 60000.0 * N_R_est / total_time
        mean_L_freq_est = 60000.0 * N_L_est / total_time
        mean_white_freq_est = 60000.0 * N_white_est / total_time
        mean_R_pattern_ex_freq_est = 60000.0 * N_R_pattern_ex_est / total_time
        mean_L_pattern_ex_freq_est = 60000.0 * N_L_pattern_ex_est / total_time
        mean_LR_pattern_ex_freq_est = 60000.0 * N_LR_pattern_ex_est / total_time
        mean_pattern_ex_total_freq_est = 60000.0 * N_pattern_ex_total_est / total_time

            # calculate mean durations
        if len(R_durations) > 0:
            mean_R_dur = np.mean(R_durations)
        else:
            mean_R_dur = 0.0
        if len(L_durations) > 0:
            mean_L_dur = np.mean(L_durations)
        else:
            mean_L_dur = 0.0
        if len(all_durations) > 0:
            mean_all_dur = np.mean(all_durations)
        else:
            mean_all_dur = 0.0
        if len(im_durations) > 0:
            mean_im_dur = np.mean(im_durations)
        else:
            mean_im_dur = 0.0
        if len(white_durations) > 0:
            mean_white_dur = np.mean(white_durations)
        else:
            mean_white_dur = 0.0
        if len(all_gaze_events_durations) > 0:
            mean_all_gaze_events_dur = np.mean(all_gaze_events_durations)
        else:
            mean_all_gaze_events_dur = 0.0
        if len(R_gaze_events_durations) > 0:
            mean_R_gaze_events_dur = np.mean(R_gaze_events_durations)
        else:
            mean_R_gaze_events_dur = 0.0
        if len(L_gaze_events_durations) > 0:
            mean_L_gaze_events_dur = np.mean(L_gaze_events_durations)
        else:
            mean_L_gaze_events_dur = 0.0
        if len(im_gaze_events_durations) > 0:
            mean_im_gaze_events_dur = np.mean(im_gaze_events_durations)
        else:
            mean_im_gaze_events_dur = 0.0
        if len(white_gaze_events_durations) > 0:
            mean_white_gaze_events_dur = np.mean(white_gaze_events_durations)
        else:
            mean_white_gaze_events_dur = 0.0

        group = dic_params['group']
        age = dic_params['age']

            # we know the functioning side, so we can group the fixations across all subjects accordingly
        if functioning_side == 'R':
            funct_times = R_times.copy()
            nonfunct_times = L_times.copy()
            funct_durations = R_durations.copy()
            nonfunct_durations = L_durations.copy()
            N_funct = N_R
            N_nonfunct = N_L
            mean_funct_freq = mean_R_freq
            mean_nonfunct_freq = mean_L_freq
            mean_funct_dur = mean_R_dur
            mean_nonfunct_dur = mean_L_dur
            functioning_pattern_im_times = R_pattern_im_times.copy()
            N_functioning_pattern_im = N_R_pattern_im
            nonfunctioning_pattern_im_times = L_pattern_im_times.copy()
            N_nonfunctioning_pattern_im = N_L_pattern_im
            mean_funct_pattern_im_freq = mean_R_pattern_im_freq
            mean_nonfunct_pattern_im_freq = mean_L_pattern_im_freq
            functioning_pattern_ex_times = R_pattern_ex_times.copy()
            N_functioning_pattern_ex = N_R_pattern_ex
            nonfunctioning_pattern_ex_times = L_pattern_ex_times.copy()
            N_nonfunctioning_pattern_ex = N_L_pattern_ex
            mean_funct_pattern_ex_freq = mean_R_pattern_ex_freq
            mean_nonfunct_pattern_ex_freq = mean_L_pattern_ex_freq
            N_gaze_funct = N_gaze_R
            N_gaze_nonfunct = N_gaze_L
            funct_gaze_events_times = R_gaze_events_times.copy()
            nonfunct_gaze_events_times = L_gaze_events_times.copy()
            funct_gaze_events_durations = R_gaze_events_durations.copy()
            nonfunct_gaze_events_durations = L_gaze_events_durations.copy()
            mean_funct_gaze_events_freq = mean_R_gaze_events_freq
            mean_nonfunct_gaze_events_freq = mean_L_gaze_events_freq
            mean_funct_gaze_events_dur = mean_R_gaze_events_dur
            mean_nonfunct_gaze_events_dur = mean_L_gaze_events_dur
            N_full_gaze_funct = N_full_gaze_pattern_R
            N_full_gaze_nonfunct = N_full_gaze_pattern_L
            N_funct_est = N_R_est
            mean_funct_freq_est = mean_R_freq_est
            N_nonfunct_est = N_L_est
            mean_nonfunct_freq_est = mean_L_freq_est
            N_funct_pattern_ex_est = N_R_pattern_ex_est
            mean_funct_pattern_ex_freq_est = mean_R_pattern_ex_freq_est
            N_nonfunct_pattern_ex_est = N_L_pattern_ex_est
            mean_nonfunct_pattern_ex_freq_est = mean_L_pattern_ex_freq_est

            for i in xrange(5):     # epochs loop
                min_data = epochs_data[i]
                if i < N_epochs:
                    try:
                        fixation_trajectory_min = fixation_trajectory_epochs[i]
                        pattern_ex_min = pattern_ex_epochs[i]
                        gaze_event_trajectory_min = gaze_event_trajectory_epochs[i]

                        N_R_min = fixation_trajectory_min.count('right')
                        min_data.update({'N_R':N_R_min})
                        N_L_min = fixation_trajectory_min.count('left')
                        min_data.update({'N_L':N_L_min})
                        N_im_min = fixation_trajectory_min.count('image')
                        min_data.update({'N_im':N_im_min})
                        N_white_min = fixation_trajectory_min.count('background')
                        min_data.update({'N_white':N_white_min})
                        N_all_min = len(fixation_trajectory_min)
                        min_data.update({'N_all':N_all_min})
                        min_data.update({'N_funct':N_R_min})
                        min_data.update({'N_nonfunct':N_L_min})

                        N_R_pattern_ex_min = pattern_ex_min.count('R')
                        min_data.update({'N_R_pattern_ex':N_R_pattern_ex_min})
                        N_L_pattern_ex_min = pattern_ex_min.count('L')
                        min_data.update({'N_L_pattern_ex':N_L_pattern_ex_min})
                        N_LR_pattern_ex_min = pattern_ex_min.count('LR')
                        min_data.update({'N_LR_pattern_ex':N_LR_pattern_ex_min})
                        min_data.update({'N_funct_pattern_ex':N_R_pattern_ex_min})
                        min_data.update({'N_nonfunct_pattern_ex':N_L_pattern_ex_min})
                        min_data.update({'N_pattern_ex_total':N_R_pattern_ex_min+N_L_pattern_ex_min+N_LR_pattern_ex_min})

                        N_gaze_R_min = gaze_event_trajectory_min.count('right')
                        min_data.update({'N_gaze_R':N_gaze_R_min})
                        N_gaze_L_min = gaze_event_trajectory_min.count('left')
                        min_data.update({'N_gaze_L':N_gaze_L_min})
                        N_gaze_im_min = gaze_event_trajectory_min.count('image')
                        min_data.update({'N_gaze_im':N_gaze_im_min})
                        N_gaze_white_min = gaze_event_trajectory_min.count('background')
                        min_data.update({'N_gaze_white':N_gaze_white_min})
                        N_gaze_all_min = len(gaze_event_trajectory_min)
                        min_data.update({'N_gaze_all':N_gaze_all_min})
                        min_data.update({'N_gaze_funct':N_gaze_R_min})
                        min_data.update({'N_gaze_nonfunct':N_gaze_L_min})

                    except IndexError:
                        print 'Error: Number of epochs of {} doesn\'t match data! (N_epochs={}, current epoch={})'.format(current_name,
                            N_epochs, i)
                        error = True
                        break

                else:
                    min_data.update({'N_R':-42})
                    min_data.update({'N_L':-42})
                    min_data.update({'N_im':-42})
                    min_data.update({'N_white':-42})
                    min_data.update({'N_all':-42})
                    min_data.update({'N_R_pattern_ex':-42})
                    min_data.update({'N_L_pattern_ex':-42})
                    min_data.update({'N_LR_pattern_ex':-42})
                    min_data.update({'N_pattern_ex_total':-42})
                    min_data.update({'N_gaze_R':-42})
                    min_data.update({'N_gaze_L':-42})
                    min_data.update({'N_gaze_im':-42})
                    min_data.update({'N_gaze_white':-42})
                    min_data.update({'N_gaze_all':-42})
                    min_data.update({'N_funct':-42})
                    min_data.update({'N_nonfunct':-42})
                    min_data.update({'N_funct_pattern_ex':-42})
                    min_data.update({'N_nonfunct_pattern_ex':-42})
                    min_data.update({'N_gaze_funct':-42})
                    min_data.update({'N_gaze_nonfunct':-42})
                # end of epochs loop
            # end of functioning side == R clause

        elif functioning_side == 'L':
            funct_times = L_times.copy()
            funct_durations = L_durations.copy()
            N_funct = N_L
            nonfunct_times = R_times.copy()
            nonfunct_durations = R_durations.copy()
            N_nonfunct = N_R
            functioning_pattern_im_times = L_pattern_im_times.copy()
            N_functioning_pattern_im = N_L_pattern_im
            nonfunctioning_pattern_im_times = R_pattern_im_times.copy()
            N_nonfunctioning_pattern_im = N_R_pattern_im
            mean_funct_freq = mean_L_freq
            mean_nonfunct_freq = mean_R_freq
            mean_funct_dur = mean_L_dur
            mean_nonfunct_dur = mean_R_dur
            mean_funct_pattern_im_freq = mean_L_pattern_im_freq
            mean_nonfunct_pattern_im_freq = mean_R_pattern_im_freq
            functioning_pattern_ex_times = L_pattern_ex_times.copy()
            N_functioning_pattern_ex = N_L_pattern_ex
            nonfunctioning_pattern_ex_times = R_pattern_ex_times.copy()
            N_nonfunctioning_pattern_ex = N_R_pattern_ex
            mean_funct_pattern_ex_freq = mean_L_pattern_ex_freq
            mean_nonfunct_pattern_ex_freq = mean_R_pattern_ex_freq
            N_gaze_funct = N_gaze_L
            N_gaze_nonfunct = N_gaze_R
            funct_gaze_events_times = L_gaze_events_times.copy()
            nonfunct_gaze_events_times = R_gaze_events_times.copy()
            funct_gaze_events_durations = L_gaze_events_durations.copy()
            nonfunct_gaze_events_durations = R_gaze_events_durations.copy()
            mean_funct_gaze_events_freq = mean_L_gaze_events_freq
            mean_nonfunct_gaze_events_freq = mean_R_gaze_events_freq
            mean_funct_gaze_events_dur = mean_L_gaze_events_dur
            mean_nonfunct_gaze_events_dur = mean_R_gaze_events_dur
            N_full_gaze_funct = N_full_gaze_pattern_L
            N_full_gaze_nonfunct = N_full_gaze_pattern_R
            N_funct_est = N_L_est
            mean_funct_freq_est = mean_L_freq_est
            N_nonfunct_est = N_R_est
            mean_nonfunct_freq_est = mean_R_freq_est
            N_funct_pattern_ex_est = N_L_pattern_ex_est
            mean_funct_pattern_ex_freq_est = mean_L_pattern_ex_freq_est
            N_nonfunct_pattern_ex_est = N_R_pattern_ex_est
            mean_nonfunct_pattern_ex_freq_est = mean_R_pattern_ex_freq_est

            for i in xrange(5):     # epochs loop
                min_data = epochs_data[i]
                if i < N_epochs:
                    try:
                        fixation_trajectory_min = fixation_trajectory_epochs[i]
                        pattern_ex_min = pattern_ex_epochs[i]
                        gaze_event_trajectory_min = gaze_event_trajectory_epochs[i]

                        N_R_min = fixation_trajectory_min.count('right')
                        min_data.update({'N_R':N_R_min})
                        N_L_min = fixation_trajectory_min.count('left')
                        min_data.update({'N_L':N_L_min})
                        N_im_min = fixation_trajectory_min.count('image')
                        min_data.update({'N_im':N_im_min})
                        N_white_min = fixation_trajectory_min.count('background')
                        min_data.update({'N_white':N_white_min})
                        N_all_min = len(fixation_trajectory_min)
                        min_data.update({'N_all':N_all_min})
                        min_data.update({'N_funct':N_L_min})
                        min_data.update({'N_nonfunct':N_R_min})

                        N_R_pattern_ex_min = pattern_ex_min.count('R')
                        min_data.update({'N_R_pattern_ex':N_R_pattern_ex_min})
                        N_L_pattern_ex_min = pattern_ex_min.count('L')
                        min_data.update({'N_L_pattern_ex':N_L_pattern_ex_min})
                        N_LR_pattern_ex_min = pattern_ex_min.count('LR')
                        min_data.update({'N_LR_pattern_ex':N_LR_pattern_ex_min})
                        min_data.update({'N_funct_pattern_ex':N_L_pattern_ex_min})
                        min_data.update({'N_nonfunct_pattern_ex':N_R_pattern_ex_min})
                        min_data.update({'N_pattern_ex_total':N_R_pattern_ex_min+N_L_pattern_ex_min+N_LR_pattern_ex_min})

                        N_gaze_R_min = gaze_event_trajectory_min.count('right')
                        min_data.update({'N_gaze_R':N_gaze_R_min})
                        N_gaze_L_min = gaze_event_trajectory_min.count('left')
                        min_data.update({'N_gaze_L':N_gaze_L_min})
                        N_gaze_im_min = gaze_event_trajectory_min.count('image')
                        min_data.update({'N_gaze_im':N_gaze_im_min})
                        N_gaze_white_min = gaze_event_trajectory_min.count('background')
                        min_data.update({'N_gaze_white':N_gaze_white_min})
                        N_gaze_all_min = len(gaze_event_trajectory_min)
                        min_data.update({'N_gaze_all':N_gaze_all_min})
                        min_data.update({'N_gaze_funct':N_gaze_L_min})
                        min_data.update({'N_gaze_nonfunct':N_gaze_R_min})

                    except IndexError:
                        print 'Error: Number of epochs of {} doesn\'t match data! (N_epochs={}, current epoch={})'.format(current_name, N_epochs, i)
                        error = True
                        break

                else:
                    min_data.update({'N_R':-42})
                    min_data.update({'N_L':-42})
                    min_data.update({'N_im':-42})
                    min_data.update({'N_white':-42})
                    min_data.update({'N_all':-42})
                    min_data.update({'N_R_pattern_ex':-42})
                    min_data.update({'N_L_pattern_ex':-42})
                    min_data.update({'N_LR_pattern_ex':-42})
                    min_data.update({'N_pattern_ex_total':-42})
                    min_data.update({'N_gaze_R':-42})
                    min_data.update({'N_gaze_L':-42})
                    min_data.update({'N_gaze_im':-42})
                    min_data.update({'N_gaze_white':-42})
                    min_data.update({'N_gaze_all':-42})
                    min_data.update({'N_funct':-42})
                    min_data.update({'N_nonfunct':-42})
                    min_data.update({'N_funct_pattern_ex':-42})
                    min_data.update({'N_nonfunct_pattern_ex':-42})
                    min_data.update({'N_gaze_funct':-42})
                    min_data.update({'N_gaze_nonfunct':-42})
                # end of epochs loop
            # end of functioning side == L clause

        else:       # could not obtain valid functioning side from overview file
            print 'Error: functioning side', functioning_side, 'not recognized!'
            error_loop = True


        dic_current = {'N_all':N_all, 'N_R':N_R, 'N_L':N_L, 'N_im':N_im, 'N_white':N_white,
        'N_R_pattern_im':N_R_pattern_im, 'N_L_pattern_im':N_L_pattern_im, 'R_times':R_times, 'L_times':L_times,
        'all_times':all_times, 'im_times':im_times, 'white_times':white_times, 'first_fix':first_fix,
        'R_pattern_im_times':R_pattern_im_times, 'L_pattern_im_times':L_pattern_im_times, 'total_time':total_time,
        'funct_times':funct_times, 'N_funct':N_funct, 'nonfunct_times':nonfunct_times, 'N_nonfunct':N_nonfunct,
        'funct_pattern_im_times':functioning_pattern_im_times, 'N_funct_pattern_im':N_functioning_pattern_im,
        'nonfunct_pattern_im_times':nonfunctioning_pattern_im_times, 'N_nonfunct_pattern_im':N_nonfunctioning_pattern_im,
        'mean_all_freq':mean_all_freq, 'mean_im_freq':mean_im_freq, 'mean_white_freq':mean_white_freq,
        'mean_R_freq':mean_R_freq, 'mean_L_freq':mean_L_freq, 'mean_R_pattern_im_freq':mean_R_pattern_im_freq,
        'mean_L_pattern_im_freq':mean_L_pattern_im_freq, 'mean_funct_freq':mean_funct_freq,
        'mean_nonfunct_freq':mean_nonfunct_freq, 'mean_funct_pattern_im_freq':mean_funct_pattern_im_freq,
        'mean_nonfunct_pattern_im_freq':mean_nonfunct_pattern_im_freq,
        'N_R_pattern_ex':N_R_pattern_ex, 'N_L_pattern_ex':N_L_pattern_ex, 'N_LR_pattern_ex':N_LR_pattern_ex, 
        'N_pattern_ex_total':N_pattern_ex_total, 'R_pattern_ex_times':R_pattern_ex_times,
        'L_pattern_ex_times':L_pattern_ex_times, 'LR_pattern_ex_times':LR_pattern_ex_times, 
        'funct_pattern_ex_times':functioning_pattern_ex_times,
        'N_funct_pattern_ex':N_functioning_pattern_ex, 'nonfunct_pattern_ex_times':nonfunctioning_pattern_ex_times,
        'N_nonfunct_pattern_ex':N_nonfunctioning_pattern_ex, 'mean_R_pattern_ex_freq':mean_R_pattern_ex_freq,
        'mean_L_pattern_ex_freq':mean_L_pattern_ex_freq, 'mean_LR_pattern_ex_freq':mean_LR_pattern_ex_freq, 
        'mean_pattern_ex_total_freq':mean_pattern_ex_total_freq, 'mean_funct_pattern_ex_freq':mean_funct_pattern_ex_freq,
        'mean_nonfunct_pattern_ex_freq':mean_nonfunct_pattern_ex_freq, 'N_gaze_all':N_gaze_all, 'N_gaze_R':N_gaze_R,
        'N_gaze_L':N_gaze_L, 'N_gaze_im':N_gaze_im, 'N_gaze_white':N_gaze_white, 'N_gaze_funct':N_gaze_funct,
        'N_gaze_nonfunct':N_gaze_nonfunct, 'all_durations':all_durations, 'R_durations':R_durations, 'L_durations':L_durations,
        'im_durations':im_durations, 'white_durations':white_durations, 'funct_durations':funct_durations, 
        'nonfunct_durations':nonfunct_durations, 'all_gaze_events_durations':all_gaze_events_durations,
        'R_gaze_events_durations':R_gaze_events_durations, 'L_gaze_events_durations':L_gaze_events_durations,
        'im_gaze_events_durations':im_gaze_events_durations, 'white_gaze_events_durations':white_gaze_events_durations,
        'funct_gaze_events_durations':funct_gaze_events_durations, 'nonfunct_gaze_events_durations':nonfunct_gaze_events_durations,
        'all_gaze_events_times':all_gaze_events_times, 'R_gaze_events_times':R_gaze_events_times, 
        'L_gaze_events_times':L_gaze_events_times, 'im_gaze_events_times':im_gaze_events_times, 
        'white_gaze_events_times':white_gaze_events_times, 'funct_gaze_events_times':funct_gaze_events_times,
        'nonfunct_gaze_events_times':nonfunct_gaze_events_times, 'mean_all_gaze_events_freq':mean_all_gaze_events_freq,
        'mean_R_gaze_events_freq':mean_R_gaze_events_freq, 'mean_L_gaze_events_freq':mean_L_gaze_events_freq,
        'mean_im_gaze_events_freq':mean_im_gaze_events_freq, 'mean_white_gaze_events_freq':mean_white_gaze_events_freq,
        'mean_funct_gaze_events_freq':mean_funct_gaze_events_freq, 'mean_nonfunct_gaze_events_freq':mean_nonfunct_gaze_events_freq,
        'mean_all_gaze_events_dur':mean_all_gaze_events_dur, 'mean_R_gaze_events_dur':mean_R_gaze_events_dur,
        'mean_L_gaze_events_dur':mean_L_gaze_events_dur, 'mean_im_gaze_events_dur':mean_im_gaze_events_dur,
        'mean_white_gaze_events_dur':mean_white_gaze_events_dur, 'mean_funct_gaze_events_dur':mean_funct_gaze_events_dur,
        'mean_nonfunct_gaze_events_dur':mean_nonfunct_gaze_events_dur, 'mean_all_dur':mean_all_dur, 'mean_R_dur':mean_R_dur,
        'mean_L_dur':mean_L_dur, 'mean_im_dur':mean_im_dur, 'mean_white_dur':mean_white_dur, 'mean_funct_dur':mean_funct_dur,
        'mean_nonfunct_dur':mean_nonfunct_dur, 'fixation_trajectory':fixation_trajectory, 
        'gaze_event_trajectory':gaze_event_trajectory,
        'N_R_full_gaze_pattern':N_full_gaze_pattern_R, 'N_L_full_gaze_pattern':N_full_gaze_pattern_L,
        'N_funct_full_gaze_pattern':N_full_gaze_funct, 'N_nonfunct_full_gaze_pattern':N_full_gaze_nonfunct,
        'N_epochs':N_epochs, 'epochs_data':epochs_data, 'cutoff_data':cutoff_data, 'fix_coordinates':coordinates, 'age':age,
        'failure_rate':failure_rate, 'N_R_est':N_R_est, 'N_L_est':N_L_est, 'N_white_est':N_white_est, 'N_funct_est':N_funct_est,
        'N_nonfunct_est':N_nonfunct_est, 'mean_R_freq_est':mean_R_freq_est, 'mean_L_freq_est':mean_L_freq_est,
        'mean_white_freq_est':mean_white_freq_est, 'mean_funct_freq_est':mean_funct_freq_est,
        'mean_nonfunct_freq_est':mean_nonfunct_freq_est, 'N_R_pattern_ex_est':N_R_pattern_ex_est,
        'N_L_pattern_ex_est':N_L_pattern_ex_est, 'N_LR_pattern_ex_est':N_LR_pattern_ex_est, 
        'N_funct_pattern_ex_est':N_funct_pattern_ex_est, 'N_nonfunct_pattern_ex_est':N_nonfunct_pattern_ex_est,
        'N_pattern_ex_total_est':N_pattern_ex_total_est, 'mean_R_pattern_ex_freq_est':mean_R_pattern_ex_freq_est,
        'mean_L_pattern_ex_freq_est':mean_L_pattern_ex_freq_est, 'mean_LR_pattern_ex_freq_est':mean_LR_pattern_ex_freq_est,
        'mean_pattern_ex_total_freq_est':mean_pattern_ex_total_freq_est, 
        'mean_funct_pattern_ex_freq_est':mean_funct_pattern_ex_freq_est,
        'mean_nonfunct_pattern_ex_freq_est':mean_nonfunct_pattern_ex_freq_est}
            # dic_current contains all evaluated data of current experiment session to be stored in output file

        for key in dic_current:     # store dic_current in dic_total
            dic_total = set_key_key_value(dic_total, current_name, key, dic_current[key])
        for key in dic_params:      # store experiment parameters in dic_total
            dic_total = set_key_key_value(dic_total, current_name, key, dic_params[key])

        break

    return dic_total, error


###
#
###


def store_results(dic_total):
  """
  function for storing results into output files

  input: dic_total (dictionary), dictionary containing for each experiment session
            all parameters and evaluated data

  output: error_in_loop (bool), indicates whether error was encountered during function execution
  """
  global dt_cutoff

  while True:   # loop broken if storing successful or error encountered while processing session names

    print 'Storing results.'
   
        # extract and sort session names
    dic_total_keys = dic_total.keys()   # get all experiment session names

    m6keys_single_AA = []  # will contain session names with subject no. < 10 
    m6keys_single_AY = []  # will contain session names with subject no. > 9
                            # -> for sorting 10 after 9 and not between 1 and 2
    m6keys_single_YA = []
    m6keys_single_YY = []
    m6keys_double_AA = []
    m6keys_double_AY = []
    m6keys_double_YA = []
    m6keys_double_YY = []
    m8keys_single_AA = []
    m8keys_single_AY = []
    m8keys_single_YA = []
    m8keys_single_YY = []
    m8keys_double_AA = []
    m8keys_double_AY = []
    m8keys_double_YA = []
    m8keys_double_YY = []
    m10keys_single_AA = []
    m10keys_single_AY = []
    m10keys_single_YA = []
    m10keys_single_YY = []
    m10keys_double_AA = []
    m10keys_double_AY = []
    m10keys_double_YA = []
    m10keys_double_YY = []
    m4keys_single_AA = []
    m4keys_single_AY = []
    m4keys_single_YA = []
    m4keys_single_YY = []
    m4keys_double_AA = []
    m4keys_double_AY = []
    m4keys_double_YA = []
    m4keys_double_YY = []
    keys_single_act = []
    keys_single_yoked = []
    keys_double_act = []
    keys_double_yoked = []
    error = False   # indicates error encountered during processing of session names

    #print 'keys in dic_total:', dic_total_keys

    for key in dic_total_keys:  # loop over sessions

        tamara = False
        for tamara_affix in tamara_affices:
            if tamara_affix in key:
                #print 'Detected', tamara_affix, 'in key', key
                tamara = True
                yoked = False
                try:
                    key_number = int(key.split(tamara_affix)[1])
                    if key_number < 10 and not yoked:
                        keys_single_act.append(key)
                    elif key_number > 9 and not yoked:
                        keys_double_act.append(key)
                    elif key_number < 10 and yoked:
                        keys_single_yoked.append(key)
                    else:
                        keys_double_yoked.append(key)
                except:
                    print 'Error: Failed to load subject number of', key
                    error = True
                if error:
                    break
        if error:
            break
        if not tamara:
            if key[:2] == '6m':
                key_appendix = key.split('6m')[1]
                key_number, group, error = extract_subject_no(key_appendix)
                if key_number < 10:
                    if group == 'AA':
                        m6keys_single_AA.append(key)
                    elif group == 'AY':
                        m6keys_single_AY.append(key)
                    elif group == 'YA':
                        m6keys_single_YA.append(key)
                    elif group == 'YY':
                        m6keys_single_YY.append(key)
                    else:
                        print 'Error: Group {} of key {} not recognized!'.format(group, key)
                        error = True
                elif key_number > 9:
                    if group == 'AA':
                        m6keys_double_AA.append(key)
                    elif group == 'AY':
                        m6keys_double_AY.append(key)
                    elif group == 'YA':
                        m6keys_double_YA.append(key)
                    elif group == 'YY':
                        m6keys_double_YY.append(key)
                    else:
                        print 'Error: Group {} of key {} not recognized!'.format(group, key)
                        error = True
            elif key[:2] in ['8m', 'ts']:
                key_appendix = key[2:]
                key_number, group, error = extract_subject_no(key_appendix)
                if key_number < 10:
                    if group == 'AA':
                        m8keys_single_AA.append(key)
                    elif group == 'AY':
                        m8keys_single_AY.append(key)
                    elif group == 'YA':
                        m8keys_single_YA.append(key)
                    elif group == 'YY':
                        m8keys_single_YY.append(key)
                    else:
                        print 'Error: Group {} of key {} not recognized!'.format(group, key)
                        error = True
                elif key_number > 9:
                    if group == 'AA':
                        m8keys_double_AA.append(key)
                    elif group == 'AY':
                        m8keys_double_AY.append(key)
                    elif group == 'YA':
                        m8keys_double_YA.append(key)
                    elif group == 'YY':
                        m8keys_double_YY.append(key)
                    else:
                        print 'Error: Group {} of key {} not recognized!'.format(group, key)
                        error = True           
            elif key[:3] == '10m':
                key_appendix = key.split('10m')[1]
                key_number, group, error = extract_subject_no(key_appendix)
                if key_number < 10:
                    if group == 'AA':
                        m10keys_single_AA.append(key)
                    elif group == 'AY':
                        m10keys_single_AY.append(key)
                    elif group == 'YA':
                        m10keys_single_YA.append(key)
                    elif group == 'YY':
                        m10keys_single_YY.append(key)
                    else:
                        print 'Error: Group {} of key {} not recognized!'.format(group, key)
                        error = True
                elif key_number > 9:
                    if group == 'AA':
                        m10keys_double_AA.append(key)
                    elif group == 'AY':
                        m10keys_double_AY.append(key)
                    elif group == 'YA':
                        m10keys_double_YA.append(key)
                    elif group == 'YY':
                        m10keys_double_YY.append(key)
                    else:
                        print 'Error: Group {} of key {} not recognized!'.format(group, key)
                        error = True
            elif key[:3] == '4m':
                key_appendix = key.split('4m')[1]
                key_number, group, error = extract_subject_no(key_appendix)
                if key_number < 10:
                    if group == 'AA':
                        m4keys_single_AA.append(key)
                    elif group == 'AY':
                        m4keys_single_AY.append(key)
                    elif group == 'YA':
                        m4keys_single_YA.append(key)
                    elif group == 'YY':
                        m4keys_single_YY.append(key)
                    else:
                        print 'Error: Group {} of key {} not recognized!'.format(group, key)
                        error = True
                elif key_number > 9:
                    if group == 'AA':
                        m4keys_double_AA.append(key)
                    elif group == 'AY':
                        m4keys_double_AY.append(key)
                    elif group == 'YA':
                        m4keys_double_YA.append(key)
                    elif group == 'YY':
                        m4keys_double_YY.append(key)
                    else:
                        print 'Error: Group {} of key {} not recognized!'.format(group, key)
                        error = True
            elif key[:3] == 'm10':
                key_appendix = key.split('m10')[1]
                key_number, group, error = extract_subject_no(key_appendix)
                if key_number < 10:
                    if group == 'AA':
                        m10keys_single_AA.append(key)
                    elif group == 'AY':
                        m10keys_single_AY.append(key)
                    elif group == 'YA':
                        m10keys_single_YA.append(key)
                    elif group == 'YY':
                        m10keys_single_YY.append(key)
                    else:
                        print 'Error: Group {} of key {} not recognized!'.format(group, key)
                        error = True
                elif key_number > 9:
                    if group == 'AA':
                        m10keys_double_AA.append(key)
                    elif group == 'AY':
                        m10keys_double_AY.append(key)
                    elif group == 'YA':
                        m10keys_double_YA.append(key)
                    elif group == 'YY':
                        m10keys_double_YY.append(key)
                    else:
                        print 'Error: Group {} of key {} not recognized!'.format(group, key)
                        error = True
            elif key[:6] == 'm4_15_':
                key_number, group, error = extract_subject_no(key_appendix)
                if key_number < 10:
                    if group == 'AA':
                        m8keys_single_AA.append(key)
                    elif group == 'AY':
                        m8keys_single_AY.append(key)
                    elif group == 'YA':
                        m8keys_single_YA.append(key)
                    elif group == 'YY':
                        m8keys_single_YY.append(key)
                    else:
                        print 'Error: Group {} of key {} not recognized!'.format(group, key)
                        error = True
                elif key_number > 9:
                    if group == 'AA':
                        m8keys_double_AA.append(key)
                    elif group == 'AY':
                        m8keys_double_AY.append(key)
                    elif group == 'YA':
                        m8keys_double_YA.append(key)
                    elif group == 'YY':
                        m8keys_double_YY.append(key)
                    else:
                        print 'Error: Group {} of key {} not recognized!'.format(group, key)
                        error = True   
            else:
                #print 'storing data of', key
                key_appendix = key
                key_number, group, error = extract_subject_no(key_appendix)
                if key_number < 10:
                    if group == 'AA':
                        m8keys_single_AA.append(key)
                    elif group == 'AY':
                        m8keys_single_AY.append(key)
                    elif group == 'YA':
                        m8keys_single_YA.append(key)
                    elif group == 'YY':
                        m8keys_single_YY.append(key)
                    else:
                        print 'Error: Group {} of key {} not recognized!'.format(group, key)
                        error = True
                elif key_number > 9:
                    if group == 'AA':
                        m8keys_double_AA.append(key)
                    elif group == 'AY':
                        m8keys_double_AY.append(key)
                    elif group == 'YA':
                        m8keys_double_YA.append(key)
                    elif group == 'YY':
                        m8keys_double_YY.append(key)
                    else:
                        print 'Error: Group {} of key {} not recognized!'.format(group, key)
                        error = True   
            if error:
                break

        dic_total[key]['group'] = group

    m6keys_single_AA.sort()
    m6keys_single_AY.sort()
    m6keys_single_YA.sort()
    m6keys_single_YY.sort()
    m6keys_double_AA.sort()
    m6keys_double_AY.sort()
    m6keys_double_YA.sort()
    m6keys_double_YY.sort()
    m8keys_single_AA.sort()
    m8keys_single_AY.sort()
    m8keys_single_YA.sort()
    m8keys_single_YY.sort()
    m8keys_double_AA.sort()
    m8keys_double_AY.sort()
    m8keys_double_YA.sort()
    m8keys_double_YY.sort()
    m10keys_single_AA.sort()
    m10keys_single_AY.sort()
    m10keys_single_YA.sort()
    m10keys_single_YY.sort()
    m10keys_double_AA.sort()
    m10keys_double_AY.sort()
    m10keys_double_YA.sort()
    m10keys_double_YY.sort()
    m4keys_single_AA.sort()
    m4keys_single_AY.sort()
    m4keys_single_YA.sort()
    m4keys_single_YY.sort()
    m4keys_double_AA.sort()
    m4keys_double_AY.sort()
    m4keys_double_YA.sort()
    m4keys_double_YY.sort()
    keys_single_act.sort()
    keys_single_yoked.sort()
    keys_double_act.sort()
    keys_double_yoked.sort()

    dic_total_keys = m6keys_single_AA + m6keys_double_AA + m6keys_single_AY + m6keys_double_AY +\
        m6keys_single_YA + m6keys_double_YA + m6keys_single_YY + m6keys_double_YY +\
        keys_single_act + keys_double_act + m8keys_single_AA + m8keys_double_AA +\
        m8keys_single_AY + m8keys_double_AY +\
        keys_single_yoked + keys_double_yoked + m8keys_single_YY + m8keys_double_YY +\
        m10keys_single_AA + m10keys_double_AA + m10keys_single_AY + m10keys_double_AY +\
        m10keys_single_YA + m10keys_double_YA + m10keys_single_YY + m10keys_double_YY +\
        m4keys_single_AA + m4keys_double_AA +\
        m4keys_single_AY + m4keys_double_AY +\
        m4keys_single_YY + m4keys_double_YY

        # store data dictionary on hard disc as numpy object
    outputfilename_dic = './extracted_data/extracted_data_{}.dat'.format(dt_cutoff)
    outputfile_dic = open(outputfilename_dic, 'wb')
    cPickle.dump(dic_total, outputfile_dic)
    outputfile_dic.close()

        # store scalar data (no time series) in a tab-separated text file which can be read like an excel sheet
    outputfilename_xls = './extracted_data/scalars.xls'
    outputfile_xls = open(outputfilename_xls, 'w')
    first_line = ('subject name\tsession number\tage (months)\tsubject group\tsession type\tgender\tlatency\tfunctioning side\t'
                  'lab setup\t'
                  'saccade cutoff duration (ms)\tfirst fixation side\tfailure rate\ttotal time (ms)\t'
                  'trigger count\tmean trigger rate\tfixation count\tmean fixation rate\tmean fixation duration\t'
                  'image fixation count\tmean image fixation rate\tmean image fixation duration\tright fixation count\t'
                  'mean right fixation rate\tmean right fixation duration\tleft fixation count\tmean left fixation rate\t'
                  'mean left fixation duration\twhite fixation count\tmean white fixation rate\t'
                  'mean white fixation duration\tfunctioning side fixation count\t'
                  'mean functioning side fixation rate\t'
                  'mean functioning side fixation duration\tnonfunctioning side fixation count\t'
                  'mean nonfunctioning side fixation rate\tmean nonfunctioning side fixation duration\t'
                  'estimated right fixation count\testimated mean right fixation rate\testimated left fixation count\t'
                  'estimated mean left fixation rate\testimated white fixation count\testimated mean white fixation rate\t'
                  'estimated functioning fixation count\testimated mean functioning fixation rate\t'
                  'estimated nonfunctioning fixation count\testimated mean nonfunctioning fixation rate\t'
                  'right immediate gaze pattern count\t'
                  'mean right immediate gaze pattern rate\tleft immediate gaze pattern count\t'
                  'mean left immediate gaze pattern rate\tfunctioning side immediate gaze pattern count\t'
                  'mean functioning side immediate gaze pattern rate\tnonfunctioning side immediate gaze pattern count\t'
                  'mean nonfunctioning side immediate gaze pattern rate\tright extended gaze pattern count\t'
                  'mean right extended gaze pattern rate\tleft extended gaze pattern count\t'
                  'mean left extended gaze pattern rate\tleft-right extended gaze pattern count\t'
                  'mean left-right extended gaze pattern rate\ttotal number of extended gaze patterns\t'
                  'mean total extended gaze pattern rate\tfunctioning side extended gaze pattern count\t'
                  'mean functioning side extended gaze pattern rate\tnonfunctioning side extended gaze pattern count\t'
                  'mean nonfunctioning side extended gaze pattern rate\t'
                  'estimated right extended gaze pattern count\testimated mean right extended gaze pattern rate\t'
                  'estimated left extended gaze pattern count\testimated mean left extended gaze pattern rate\t'
                  'estimated left-right extended gaze pattern count\testimated mean left-right extended gaze pattern rate\t'
                  'estimated total extended gaze pattern count\testimated mean total extended gaze pattern rate\t'
                  'estimated functioning extended gaze pattern count\testimated mean functioning extended gaze pattern rate\t'
                  'estimated nonfunctioning extended gaze pattern count\t'
                  'estimated mean nonfunctioning extended gaze pattern rate\t'
                  'gaze event count\tmean gaze event rate\tmean gaze event duration\timage gaze event count\t'
                  'mean image gaze event rate\tmean image gaze event duration\tright gaze event count\t'
                  'mean right gaze event rate\tmean right gaze event duration\tleft gaze event count\t'
                  'mean left gaze event rate\tmean left gaze event duration\twhite gaze event count\tmean white gaze event rate\t'
                  'mean white gaze event duration\tfunctioning side gaze event count\tmean functioning side gaze event rate\t'
                  'mean functioning side gaze event duration\tnonfunctioning side gaze event count\t'
                  'mean nonfunctioning side gaze event rate\tmean nonfunctioning side gaze event duration\t'
                  'left full gaze pattern count\tright full gaze pattern count\tfunctioning side full gaze pattern count\t'
                  'nonfunctioning side full gaze pattern count\t'
                  'number of saccades\tmean saccade rate\tnumber of blinks\tblink ratio\t'
                  'number of full minutes\t1st minute\t'
                  'fixation count\timage fixation count\tleft fixation count\tright fixation count\twhite fixation count\t'
                  'functioning side fixation count\tnonfunctioning side fixation count\t'
                  'left extended gaze pattern count\tright extended gaze pattern count\t'
                  'functioning side extended gaze pattern count\tnonfunctioning side extended gaze pattern count\t'
                  'gaze event count\timage gaze event count\tleft gaze event count\tright gaze event count\twhite gaze event count\t'
                  'functioning side gaze event count\tnonfunctioning side gaze event count\t2nd minute\t'
                  'fixation count\timage fixation count\tleft fixation count\tright fixation count\twhite fixation count\t'
                  'functioning side fixation count\tnonfunctioning side fixation count\t'
                  'left extended gaze pattern count\tright extended gaze pattern count\t'
                  'functioning side extended gaze pattern count\tnonfunctioning side extended gaze pattern count\t'
                  'gaze event count\timage gaze event count\tleft gaze event count\tright gaze event count\twhite gaze event count\t'
                  'functioning side gaze event count\tnonfunctioning side gaze event count\t3rd minute\t'
                  'fixation count\timage fixation count\tleft fixation count\tright fixation count\twhite fixation count\t'
                  'functioning side fixation count\tnonfunctioning side fixation count\t'
                  'left extended gaze pattern count\tright extended gaze pattern count\t'
                  'functioning side extended gaze pattern count\tnonfunctioning side extended gaze pattern count\t'
                  'gaze event count\timage gaze event count\tleft gaze event count\tright gaze event count\twhite gaze event count\t'
                  'functioning side gaze event count\tnonfunctioning side gaze event count\t4th minute\t'
                  'fixation count\timage fixation count\tleft fixation count\tright fixation count\twhite fixation count\t'
                  'functioning side fixation count\tnonfunctioning side fixation count\t'
                  'left extended gaze pattern count\tright extended gaze pattern count\t'
                  'functioning side extended gaze pattern count\tnonfunctioning side extended gaze pattern count\t'
                  'gaze event count\timage gaze event count\tleft gaze event count\tright gaze event count\twhite gaze event count\t'
                  'functioning side gaze event count\tnonfunctioning side gaze event count\t5th minute\t'
                  'fixation count\timage fixation count\tleft fixation count\tright fixation count\twhite fixation count\t'
                  'functioning side fixation count\tnonfunctioning side fixation count\t'
                  'left extended gaze pattern count\tright extended gaze pattern count\t'
                  'functioning side extended gaze pattern count\tnonfunctioning side extended gaze pattern count\t'
                  'gaze event count\timage gaze event count\tleft gaze event count\tright gaze event count\twhite gaze event count\t'
                  'functioning side gaze event count\tnonfunctioning side gaze event count\t')

        # first row describes all stored parameters
    outputfile_xls.write(first_line)
    keys_to_store = ['subject_name', 'session_number', 'age', 'group', 'session_type', 'gender', 'latency',
        'functioning_side', 
        'lab_setup', 'dt_cutoff', 'first_fix', 'failure_rate', 'total_time',
        'N_triggers', 'mean_trigger_freq', 'N_all', 'mean_all_freq', 'mean_all_dur', 'N_im', 'mean_im_freq', 'mean_im_dur', 'N_R', 
        'mean_R_freq', 'mean_R_dur', 'N_L', 'mean_L_freq', 'mean_L_dur', 'N_white', 'mean_white_freq', 'mean_white_dur', 'N_funct', 
        'mean_funct_freq', 'mean_funct_dur', 'N_nonfunct', 'mean_nonfunct_freq', 'mean_nonfunct_dur', 
        'N_R_est', 'mean_R_freq_est', 'N_L_est', 'N_L_freq_est', 'N_white_est', 'mean_white_freq_est', 'N_funct_est',
        'mean_funct_freq_est', 'N_nonfunct_est', 'mean_nonfunct_freq_est', 
        'N_R_pattern_im', 
        'mean_R_pattern_im_freq', 'N_L_pattern_im', 'mean_L_pattern_im_freq', 'N_funct_pattern_im',
        'mean_funct_pattern_im_freq', 'N_nonfunct_pattern_im', 'mean_nonfunct_pattern_im_freq', 'N_R_pattern_ex',
        'mean_R_pattern_ex_freq', 'N_L_pattern_ex', 'mean_L_pattern_ex_freq', 'N_LR_pattern_ex', 'mean_LR_pattern_ex_freq',
        'N_pattern_ex_total', 'mean_pattern_ex_total_freq', 'N_funct_pattern_ex', 'mean_funct_pattern_ex_freq',
        'N_nonfunct_pattern_ex', 'mean_nonfunct_pattern_ex_freq',
        'N_R_pattern_ex_est', 'mean_R_pattern_ex_freq_est', 'N_L_pattern_ex_est', 'mean_L_pattern_ex_freq_est',
        'N_LR_pattern_ex_est', 'mean_LR_pattern_ex_freq_est', 'N_pattern_ex_total_est', 'mean_pattern_ex_total_freq_est',
        'N_funct_pattern_ex_est', 'mean_funct_pattern_ex_freq_est', 'N_nonfunct_pattern_ex_est', 'mean_nonfunct_pattern_ex_freq_est',
        'N_gaze_all', 'mean_all_gaze_events_freq', 
        'mean_all_gaze_events_dur', 'N_gaze_im', 'mean_im_gaze_events_freq', 'mean_im_gaze_events_dur', 'N_gaze_R',     
        'mean_R_gaze_events_freq', 'mean_R_gaze_events_dur', 'N_gaze_L', 'mean_L_gaze_events_freq', 'mean_L_gaze_events_dur', 
        'N_gaze_white', 'mean_white_gaze_events_freq', 'mean_white_gaze_events_dur', 'N_gaze_funct', 'mean_funct_gaze_events_freq', 
        'mean_funct_gaze_events_dur', 'N_gaze_nonfunct', 'mean_nonfunct_gaze_events_freq', 'mean_nonfunct_gaze_events_dur',
        'N_L_full_gaze_pattern', 'N_R_full_gaze_pattern', 'N_funct_full_gaze_pattern', 'N_nonfunct_full_gaze_pattern',
        'sac_N', 'sac_mean_freq', 'sac_N_blinks', 'sac_blink_ratio', 'N_epochs']
        # contains all keys of experiment session subdictionaries
    epochs_keys = ['N_all', 'N_im', 'N_L', 'N_R', 'N_white', 'N_funct', 'N_nonfunct', 'N_L_pattern_ex', 'N_R_pattern_ex',
        'N_funct_pattern_ex', 'N_nonfunct_pattern_ex', 'N_gaze_all', 'N_gaze_im', 'N_gaze_L', 'N_gaze_R', 'N_gaze_white',
        'N_gaze_funct', 'N_gaze_nonfunct']
    N_epochs_keys = len(epochs_keys)

    # small version
    outputfilename_small_xls = './extracted_data/scalars_small.xls'
    outputfile_small_xls = open(outputfilename_small_xls, 'w')
    first_line_small = ('subject name\tsession number\tage (months)\tsubject group\tsession type\tgender\tlatency\tfunctioning side\t'
                  'lab setup\t'
                  'failure rate\ttotal time (ms)\t'
                  'mean functioning side extended gaze pattern rate\t'
                  'mean nonfunctioning side extended gaze pattern rate\t')
        # first row describes all stored parameters
    outputfile_small_xls.write(first_line_small)
    keys_to_store_small = ['subject_name', 'session_number', 'age', 'group', 'session_type', 'gender', 'latency',
        'functioning_side', 
        'lab_setup', 'failure_rate', 'total_time',
        'mean_funct_pattern_ex_freq',
        'mean_nonfunct_pattern_ex_freq']


    for outer_key in dic_total_keys:    # loop over experiment sessions, i.e. rows of output file
        outputfile_xls.write('\n')
        for inner_key in keys_to_store:     # loop over session data, i.e. columns of output file
            try:    # check whether the datum was stored
                value = dic_total[outer_key][inner_key]
            except KeyError:    # put token where stored value couldn't be retrieved
                value = '.'
            write_string = str(value)
            outputfile_xls.write(write_string+'\t')     # put tab-separation
        N_epochs = dic_total[outer_key]['N_epochs']
        epochs_data = dic_total[outer_key]['epochs_data']
        for i_epoch in xrange(5):
            outputfile_xls.write('\t')
            if i_epoch < N_epochs:
                for epoch_key in epochs_keys:
                    try:
                        value = epochs_data[i_epoch][epoch_key]
                    except KeyError:
                        value = '.'
                    write_string = str(value)
                    outputfile_xls.write(write_string+'\t')
            else:
                for i in xrange(N_epochs_keys):
                    outputfile_xls.write('\t')

    outputfile_xls.close()

    for outer_key in dic_total_keys:    # loop over experiment sessions, i.e. rows of output file
        outputfile_small_xls.write('\n')
        for inner_key in keys_to_store_small:     # loop over session data, i.e. columns of output file
            try:    # check whether the datum was stored
                value = dic_total[outer_key][inner_key]
            except KeyError:    # put token where stored value couldn't be retrieved
                value = '.'
            write_string = str(value)
            outputfile_small_xls.write(write_string+'\t')     # put tab-separation

    outputfile_small_xls.close()

        # store inter trigger intervals in separate file, also tab-separated
    outputfilename_intertrigger = './extracted_data/inter_trigger_intervals.xls'
    outputfile_intertrigger = open(outputfilename_intertrigger, 'w')
    first_line = 'subject name\tsession number\tinter trigger intervals'
    outputfile_intertrigger.write(first_line+'\n')
    for outer_key in dic_total_keys:    # loop over experiment session, i.e. rows in output file
      if not dic_total[outer_key]['group'] == 'YY':
        group = dic_total[outer_key]['group']
        subject_number = str(dic_total[outer_key]['subject_name'])
        session = str(dic_total[outer_key]['session_number'])
        if group=='AA' or (group=='AY' and session!='2') or (group=='YA' and session!=1) or (group=='YY' and session=='3'):
            outputfile_intertrigger.write('{}\t{}'.format(subject_number, session))
            inter_trigger_intervals = dic_total[outer_key]['inter_trigger_intervals']
            for inter_trigger_time in inter_trigger_intervals:  # loop over inter trigger times
                outputfile_intertrigger.write('\t{}'.format(inter_trigger_time))
            outputfile_intertrigger.write('\n')
    outputfile_intertrigger.close()

    if not error:
        print 'Storing successful.'
    break

  return error


###
#
###


def initialize_fixation_data():
    """
    function for resetting the data that are processed during fixation file extraction
    -> variables and lists are reset for each experiment session

    output: see below
    """

    all_times = []          # this will contain all fixation start times
    all_durations = []      # this will contain all fixation durations
    R_times = []            # this will contain all start times of fixations on the right disc
    R_durations = []        # this will contain all durations of fixations on the right disc
    L_times = []            # this will contain all start times of fixations on the left disc
    L_durations = []        # this will contain all durations of fixations on the left disc
    im_times = []           # this will contain all start times of fixations on the image
    im_durations = []       # this will contain all durations of fixations on the image
    white_times = []        # this will contain all start times of fixations on the white background
    white_durations = []    # this will contain all durations of fixations on the white background
    R_pattern_im_times = []    # this will contain all start times of the fixation sequence "image -> right disc -> image"
    L_pattern_im_times = []    # this will contain all start times of the fixation sequence "image -> left disc -> image"
    R_pattern_ex_times = []    # this will contain all start times of fixation sequences 
                               #  "image -> arbitrary number of fixations with at least one on right disc and none on left disc
                               #    -> image"
    L_pattern_ex_times = []    # this will contain all start times of fixation sequences 
                               #  "image -> arbitrary number of fixations with at least one on left disc and none on right disc
                               #    -> image"
    LR_pattern_ex_times = []    # this will contain all start times of fixation sequences
                                # "image" -> arbitrary number of fixations with at least one on right and one on left disc -> "image"
    gaze_pattern_ex_time_temp = -42     # some initial dummy value for start time of current extended gaze pattern
    gaze_pattern_ex_loc_temp = []   # this will contain the fixation areas since last image fixation 
                                    # -> used for processing extended gaze patterns
    all_gaze_events_times = []      # this will contain all gaze event start times
    all_gaze_events_durations = []  # this will contain all gaze event durations
    R_gaze_events_times = []        # this will contain all start times of gaze events on the right disc
    R_gaze_events_durations = []    # this will contain all durations of gaze events on the right disc
    L_gaze_events_times = []        # this will contain all start times of gaze events on the left disc
    L_gaze_events_durations = []    # this will contain all durations of gaze events on the left disc
    im_gaze_events_times = []       # this will contain all start times of gaze events on the image
    im_gaze_events_durations = []   # this will contain all durations of gaze events on the image
    white_gaze_events_times = []    # this will contain all start times of gaze events on the white background
    white_gaze_events_durations = []    # this will contain all durations of gaze events on the white background
    fixation_trajectory = []        # this will contain the sequence of fixated areas
    gaze_event_trajectory = []      # this will contain the sequence of gazed at areas
    fixation_trajectory_epochs = []
    pattern_ex_epochs = []
    gaze_event_trajectory_epochs = []
    coordinates = [[],[]]

    return (all_times, all_durations, R_times, R_durations, L_times, L_durations, im_times, im_durations, white_times,
        white_durations, R_pattern_im_times, L_pattern_im_times, R_pattern_ex_times, L_pattern_ex_times, LR_pattern_ex_times, 
        gaze_pattern_ex_time_temp, 
        gaze_pattern_ex_loc_temp, all_gaze_events_times, all_gaze_events_durations, R_gaze_events_times,
        R_gaze_events_durations, L_gaze_events_times, L_gaze_events_durations, im_gaze_events_times, im_gaze_events_durations,
        white_gaze_events_times, white_gaze_events_durations, fixation_trajectory, gaze_event_trajectory,
        fixation_trajectory_epochs, pattern_ex_epochs, gaze_event_trajectory_epochs, coordinates)


###
#
###


def process_message_files(files_msg, dic_total):
    """
    function for extracting and processing data from message report files

    input:
        files_msg (list): list of message report files found in reports folder
        dic_total (dictionary): total dictionary which stores all data
            -> contains a subdictionary with all data for each experiment session

    output:
        dic_total (dictionary): updated total dictionary
        error_in_loop (bool): indicates whether an error was encountered during function execution
    """

    print 'Processing messages.'
    error_in_loop = False   # indicates something went wrong in one of the following loops

    for report_msg in files_msg:    # loop over message reports
        if not error_in_loop:
            print 'Extracting data from', report_msg

            inputfile_msg = open(reports_folder+report_msg, 'r')
            inputdata_msg = inputfile_msg.read()    # load message report as text file
            inputfile_msg.close()

            lines_msg = inputdata_msg.split('\n')[1:-1]
#            lines_msg = inputdata_msg.split(linebreak)[1:-1]    
                # lines_msg is a list of all rows containing data
                # -> first row contains descriptions, last row is empty
    
            try:
                current_label = lines_msg[0].split('\t')[0]
                    # all report files are basically tab-separated text files
                    # -> splitting each line by \t yields a list of the different data
                    # -> first item is "RECORDING_SESSION_LABEL" and contains the session name in the format vpX.y or X.y
                    #       where X is subject number and y is session number
            except IndexError:
                print '\n\nError: could not load message file!\nMake sure file format is right.'
                error_in_loop = True
                break
            if 'vp' in current_label:
                current_name = current_label[2:]    # get session label in the form X.y
            else:
                current_name = current_label
            #print 'current_name:', current_name
            #print 'current_dic:', dic_total[current_name]
            #print 'cutoff_data:', dic_total[current_name]['cutoff_data']

            # saccade filter time transformation
            try:
                current_dic = dic_total[current_name]
                cutoff_data = current_dic['cutoff_data']
                #print 'retrieving cutoff_data: success'
            except KeyError:
            #    cutoff_data = [[0,0,0]]
                cutoff_data = [[]]
            #if len(cutoff_data) == 0:
            #    cutoff_data = [[0,0,0]]
                #print 'retrieving cutoff_data: fail.\ncreating new cutoff_data.'
            cutoff_data = [[0,0,0]] + cutoff_data
            N_cutoffs = len(cutoff_data)
            i_cutoff = 0
            cutoff_start = cutoff_data[0][0]
            cutoff_end = cutoff_data[0][1]
            t_correct = cutoff_data[0][2]

            trigger_times = []      # this will contain all trigger times of one session
            trigger_times_real = []
            inter_trigger_intervals = []    # this will contain all inter trigger intervals of one session

            for i_line in tqdm(xrange(len(lines_msg))):   # loop over messages

                line = lines_msg[i_line].split('\t')    # yields list [session label, time, message text]
                try:
                    label = line[0]
                    time = line[1]
                    message = line[2]
                except IndexError:
                    print '\n\nError: message file could not be loaded!\nMake sure the file format is right.'
                    error_in_loop = True
                    break
                
                try:        # check whether time is a numerical value
                    time = int(time)
                except ValueError:
                    print '\n\nError: {} not recognized as number! (file {}, line {})'.format(time, report_msg, i_line)
                    error_in_loop = True
                    break   
                

                # actual time transformation
                real_time = time        # unfiltered time for plotting
                if i_cutoff < N_cutoffs-1:
                    while time > cutoff_end:
                        if i_cutoff < N_cutoffs-1:
                            i_cutoff += 1
                            #print 'cutoff_data:', cutoff_data
                            #print 'i_cutoff:', i_cutoff
                            try:
                                cutoff_start = cutoff_data[i_cutoff][0]
                                cutoff_end = cutoff_data[i_cutoff][1]
                                t_correct = cutoff_data[i_cutoff-1][2]
                            except IndexError:
                                print '\n\nError: could not access cutoff_data of subject {}!'.format(current_name)
                                print 'Make sure subjects are labelled consistently in all report files!'
                                error_in_loop = True
                                break
                        else:
                            break
                    if time > cutoff_start:
                        time = cutoff_start + 10    # residual saccade after filtering has duration 10 ms                    
                time -= t_correct
#                print 'real time: {}\tt_correct: {}\tcorrected time: {}'.format(real_time, t_correct, time)

                if current_label != label:      # triggered whenever line contains data of a new session

                    N_triggers = len(trigger_times)

                    try:        # check whether the number of triggers of current session was stored before
                        total_time = dic_total[current_name]['total_time']
                        mean_trigger_freq = 1000.0 * N_triggers / total_time    # mean trigger frequency
                    except KeyError:
                        print '\nWarning: could not load session duration.'
                        mean_trigger_freq = -42     # some dummy value
                    except TypeError:
                        print '\nWarning: session duration in wrong format.'
                        mean_trigger_freq = -42

                    trigger_times = np.array(trigger_times, dtype=int)  # convert lists into numpy array for computational reasons
                    trigger_times_real = np.array(trigger_times_real, dtype=int)
                    inter_trigger_intervals = np.array(inter_trigger_intervals, dtype=int)
                        # call function set_key_key_value() to store values of current experiment session
#                    print 'trigger times: {}'.format(trigger_times)
                    dic_total = set_key_key_value(dic_total, current_name, 'trigger_times', trigger_times)
#                    print 'trigger times real: {}'.format(trigger_times_real)
                    dic_total = set_key_key_value(dic_total, current_name, 'trigger_times_real', trigger_times_real)
                    dic_total = set_key_key_value(dic_total, current_name, 'N_triggers', N_triggers)
                    dic_total = set_key_key_value(dic_total, current_name, 'inter_trigger_intervals', inter_trigger_intervals)
                    dic_total = set_key_key_value(dic_total, current_name, 'mean_trigger_freq', mean_trigger_freq)

                    # saccade filter time transformation
                    #print 'current_name:', current_name
                    try:
                        current_dic = dic_total[current_name]
                        cutoff_data = current_dic['cutoff_data']
                    #    print 'retrieving cutoff_data: success'
                    except KeyError:
                    #    cutoff_data = [[0,0,0]]
                        cutoff_data = [[]]
                    #if len(cutoff_data) == 0:
                    #    cutoff_data = [[0,0,0]]
                    #    print 'retrieving cutoff_data: fail\ncreating new cutoff_data'
                    cutoff_data = [[0,0,0]] + cutoff_data
                    N_cutoffs = len(cutoff_data)
                    i_cutoff = 0
                    try:
                        cutoff_start = cutoff_data[i_cutoff][0]
                        cutoff_end = cutoff_data[i_cutoff][1]
                        t_correct = cutoff_data[i_cutoff-1][2]
                    except IndexError:
                        print '\n\nError: could not access cutoff_data of subject {}!'.format(current_name)
                        print 'Make sure subjects are labelled consistently in all report files!'
                        error_in_loop = True
                        break
    
                    trigger_times = []      # reinitialization for next session
                    trigger_times_real = []
                    inter_trigger_intervals = []
    
                    current_label = line[0]     # get new session label
                    if 'vp' in current_label:
                        current_name = current_label[2:]
                    else:
                        current_name = current_label
    
                if 'PLAY_SOUND_b' in message:      # message for sound playback signals image trigger
                    if len(trigger_times) == 0:
                        trigger_times.append(time)
                        trigger_times_real.append(real_time)
                    elif len(trigger_times) > 0:    # image triggers after the first image is shown
                        inter_trigger_time = time-trigger_times[-1]
                        inter_trigger_intervals.append(inter_trigger_time)
                        trigger_times.append(time)
                        trigger_times_real.append(real_time)
                    else:       # other cases should not occur
                        print 'Error: len(trigger_times)={} and t_0={}! (file {}, line {})'.format(len(trigger_times),
                                 t_0, report_msg, i_line)
                        error_in_loop = True
                        break

            # end of message loop

        if len(files_msg) > 0:      
            # if the previous message loop was executed at least once, we have to store the data of the last processed session

            N_triggers = len(trigger_times)

            try:        # check whether the number of triggers of current session was stored before
                total_time = dic_total[current_name]['total_time']
                mean_trigger_freq = 1000.0 * N_triggers / total_time    # mean trigger frequency
            except KeyError:
                mean_trigger_freq = -42     # some dummy value
    
            trigger_times = np.array(trigger_times, dtype=int)
            trigger_times_real = np.array(trigger_times_real, dtype=int)
            inter_trigger_intervals = np.array(inter_trigger_intervals, dtype=int)
            dic_total = set_key_key_value(dic_total, current_name, 'inter_trigger_intervals', inter_trigger_intervals)
#            print 'trigger times: {}'.format(trigger_times)
            dic_total = set_key_key_value(dic_total, current_name, 'trigger_times', trigger_times)
#            print 'trigger times real: {}'.format(trigger_times_real)
            dic_total = set_key_key_value(dic_total, current_name, 'trigger_times_real', trigger_times_real)
            dic_total = set_key_key_value(dic_total, current_name, 'N_triggers', len(trigger_times))
            dic_total = set_key_key_value(dic_total, current_name, 'mean_trigger_freq', mean_trigger_freq)
        
    return dic_total, error_in_loop


###
#
###


def process_fixation_files(files_fix, dic_total, dt_cutoff, overview_dic):
    """
    function for extracting and processing data from fixation report files

    input:
        files_fix (list): list of fixation report files found in reports folder
        dic_total (dictionary): total dictionary which stores all data
            -> contains a subdictionary with all data for each experiment session

    output:
        dic_total (dictionary): updated total dictionary
        error_in_loop (bool): indicates whether an error was encountered during function execution
    """

    print 'Processing fixations.'
    error_in_loop = False       # indicates something went wrong in one of the following loops
    for report_fix in files_fix:    # loop over fixation files
      if not error_in_loop:     # only continue if no errors encountered
        print 'Extracting data from', report_fix

        inputfile = open(reports_folder+report_fix, 'r')
        inputdata = inputfile.read()    # load fixation report as text file
        inputfile.close()

        lines = inputdata.split('\n')[1:-1]
#        lines = inputdata.split(linebreak)[1:-1]
            # lines is a list of all rows containing data
            # -> first row contains descriptions, last row is empty
        N_lines = len(lines)

        print 'Processing fixation times.'

        current_label = lines[0].split('\t')[0]
            # all report files are basically tab-separated text files
            # -> splitting each line by \t yields a list of the different data
            # -> first item is "RECORDING_SESSION_LABEL" and contains the session name in the format vpX.y or X.y
            #       where X is subject number and y is session number
        if 'vp' in current_label:
            current_name = current_label[2:]
        else:
            current_name = current_label
       
        current_min = 0
        fixation_trajectory_min = []
        pattern_ex_min = []
        gaze_event_trajectory_min = []

        t_correct = 0
        cutoff_data = []
        previous_end_time = 10000

            # get empty lists and initialized parameters for data processing
        (all_times, all_durations, R_times, R_durations, L_times, L_durations, im_times, im_durations, white_times,
            white_durations, R_pattern_im_times, L_pattern_im_times, R_pattern_ex_times, L_pattern_ex_times, LR_pattern_ex_times,
            gaze_pattern_ex_time_temp, gaze_pattern_ex_loc_temp, all_gaze_events_times, all_gaze_events_durations, R_gaze_events_times,
            R_gaze_events_durations, L_gaze_events_times, L_gaze_events_durations, im_gaze_events_times, im_gaze_events_durations,
            white_gaze_events_times, white_gaze_events_durations, fixation_trajectory, gaze_event_trajectory,
            fixation_trajectory_epochs, pattern_ex_epochs, gaze_event_trajectory_epochs,
            coordinates) = initialize_fixation_data()

        for i_line in tqdm(xrange(N_lines)):   # loop over fixations

            line = lines[i_line].split('\t')    
                # yields list [session label, fixation start time, current interest area, previous interest area, 
                #               next interest area, fixation duration]
            #print 'i_line:', i_line, '\nline:', line
            try:
                label = line[0]
                time = line[1]
                duration = line[5]
                IA_current = line[2]        # interest area of current fixation
                IA_previous = line[3]       # interest area of previous fixation
                IA_next = line[4]           # interest area of next fixation
                x_coord_str = convert_number(line[6])
                y_coord_str = convert_number(line[7])
            except IndexError:
                print 'Error: could not load fixation file!\nMake sure the file format is right.'
                error_in_loop = True
                break

            try:        # check whether time is a numerical value
                time = int(time)
            except ValueError:
                print 'Error: time {} not recognized as number! (file {}, line {})'.format(time, report_fix, i_line)
                error_in_loop = True
                break

            try:        # check whether duration is a numerical value
                duration = int(duration)
            except ValueError:
                print 'Error: duration {} not recognized as a number! (file {}, line {})'.format(duration, report_fix, i_line)
                error_in_loop = True
                break

            try:
                x_coord = float(x_coord_str)
            except ValueError:
                print 'Error: x coordinate {} not recognized as a number! (file {}, line {})'.format(x_coord_str, report_fix, i_line)
                error_in_loop = True
                break
            try:
                y_coord = float(y_coord_str)
            except ValueError:
                print 'Error: y coordinate {} not recognized as a number! (file {}, line {})'.format(y_coord_str, report_fix, i_line)
                error_in_loop = True
                break

            if current_label != label:      # triggered whenever line contains data of a new session

                gaze_duration = previous_fix_start + previous_fix_duration - all_gaze_events_times[-1]
                    # gaze duration is end of last fixation in current area minus start of first fixation in that area
                    # -> takes into account saccades in between these fixations                
                all_gaze_events_durations.append(gaze_duration)
                if 'R' in previous_IA:           # right disc gaze event
                    R_gaze_events_durations.append(gaze_duration) 
                elif 'L' in previous_IA:         # left disc gaze event
                    L_gaze_events_durations.append(gaze_duration)
                elif 'image' in previous_IA:     # image gaze event
                    im_gaze_events_durations.append(gaze_duration)
                else:                           # background gaze event
                    white_gaze_events_durations.append(gaze_duration)

                # process full gaze patterns
    
                N_gaze = len(gaze_event_trajectory)
                N_full_gaze_pattern_R = 0
                N_full_gaze_pattern_L = 0
                for i in xrange(N_gaze-2):
                    current_gaze_area = gaze_event_trajectory[i]
                    area_after_next_gaze_area = gaze_event_trajectory[i+2]
                    if current_gaze_area == 'image' and area_after_next_gaze_area == 'image':
                        area_in_between = gaze_event_trajectory[i+1]
                        if area_in_between == 'right':
                            N_full_gaze_pattern_R += 1
                        elif area_in_between == 'left':
                            N_full_gaze_pattern_L += 1

#                print 'storing fixation_trajectory_epochs:', fixation_trajectory_epochs

                dic_total = set_key_key_value(dic_total, current_name, 'dt_cutoff', dt_cutoff)
                dic_total, error = wrap_up(dic_total, current_name, R_times, L_times, im_times, 
                    white_times, all_times, L_pattern_im_times, R_pattern_im_times, L_pattern_ex_times, R_pattern_ex_times,
                    LR_pattern_ex_times,
                    all_gaze_events_times, all_gaze_events_durations, R_gaze_events_times, R_gaze_events_durations, 
                    L_gaze_events_times, L_gaze_events_durations, im_gaze_events_times, im_gaze_events_durations, 
                    white_gaze_events_times, white_gaze_events_durations, all_durations, R_durations, L_durations, im_durations,
                    white_durations, fixation_trajectory, gaze_event_trajectory, N_full_gaze_pattern_R, N_full_gaze_pattern_L,
                    fixation_trajectory_epochs, pattern_ex_epochs, gaze_event_trajectory_epochs, cutoff_data, overview_dic,
                    coordinates)
                if error:
                    error_in_loop = True
                    break

                    # call function wrap_up() to process fixation data and store in dic_total

                    # reinitialize containers
                (all_times, all_durations, R_times, R_durations, L_times, L_durations, im_times, im_durations, white_times,
                    white_durations, R_pattern_im_times, L_pattern_im_times, R_pattern_ex_times, L_pattern_ex_times,
                    LR_pattern_ex_times,
                    gaze_pattern_ex_time_temp, gaze_pattern_ex_loc_temp, all_gaze_events_times, 
                    all_gaze_events_durations, R_gaze_events_times, R_gaze_events_durations, L_gaze_events_times, 
                    L_gaze_events_durations, im_gaze_events_times, im_gaze_events_durations, white_gaze_events_times, 
                    white_gaze_events_durations, fixation_trajectory, gaze_event_trajectory,
                    fixation_trajectory_epochs, pattern_ex_epochs, gaze_event_trajectory_epochs,
                    coordinates) = initialize_fixation_data()

                current_min = 0
                fixation_trajectory_min = []
                pattern_ex_min = []
                gaze_event_trajectory_min = []

                t_correct = 0
                cutoff_data = []
                previous_end_time = 10000
                # end of current_label != label clause


            # process coordinates
            coordinates[0].append(x_coord)
            coordinates[1].append(y_coord)

            # process saccade duration filter
            dt = time - previous_end_time
            if dt > dt_cutoff:
                t_correct += dt - 10    # shorten saccade duration to 10 ms
                cutoff_data.append([previous_end_time, time, t_correct])
            previous_end_time = time + duration
            time -= t_correct

            # process epoch data
            i_min = time // 60000   # minute index
#            print 'i_min:', i_min
            if i_min != current_min:    # minute completed
#                print 'minute completed.'
                fixation_trajectory_epochs.append(fixation_trajectory_min)
                pattern_ex_epochs.append(pattern_ex_min)
                gaze_event_trajectory_epochs.append(gaze_event_trajectory_min)
#                print 'fixation_trajectory_epochs:', fixation_trajectory_epochs
            
                fixation_trajectory_min = []
                pattern_ex_min = []
                gaze_event_trajectory_min = []
                current_min = i_min

            current_label = line[0]     # get new session label
            if 'vp' in current_label:
                current_name = current_label[2:]
            else:
                current_name = current_label

                # process fixations
            all_times.append(time)
            all_durations.append(duration)
            if 'R' in IA_current:       # look at current fixation interest area for appending to fixation times list
                R_times.append(time)
                R_durations.append(duration)
                fixation_trajectory.append('right')
                fixation_trajectory_min.append('right')
            elif 'L' in IA_current:
                L_times.append(time)
                L_durations.append(duration)
                fixation_trajectory.append('left')
                fixation_trajectory_min.append('left')
            elif 'image' in IA_current:
                im_times.append(time)
                im_durations.append(duration)
                fixation_trajectory.append('image')
                fixation_trajectory_min.append('image')
            else:
                white_times.append(time)
                white_durations.append(duration)
                fixation_trajectory.append('background')
                fixation_trajectory_min.append('background')

                # process immediate gaze patterns
            if ('image' in IA_previous) and ('image' in IA_next):
                # fixation sequence "image -> X -> image" might be immediate fixation pattern
                if 'R' in IA_current:   # right immediate fixation pattern "image -> right disc -> image"
                    R_pattern_im_times.append(time)
                elif 'L' in IA_current: # left immediate fixation pattern "image -> left disc -> image"
                    L_pattern_im_times.append(time)

                # process extended gaze patterns
            #print '\ntime:', time
            #print 'IA_current:', IA_current
            
            if 'image' in IA_current:   # if image is fixated, it can start or finish an extended pattern
              if len(gaze_pattern_ex_loc_temp) > 0:
                if 'image' in gaze_pattern_ex_loc_temp[0]:      
                    # disregards the beginning of the session when the image hasn't been fixated yet
                    if ((('R' in gaze_pattern_ex_loc_temp) or ('R ' in gaze_pattern_ex_loc_temp)) and not (('L' in gaze_pattern_ex_loc_temp) or ('L ' in gaze_pattern_ex_loc_temp))):   
                            # requirement for R pattern
                        #print 'R pattern detected.'
                        R_pattern_ex_times.append(gaze_pattern_ex_time_temp)
                        pattern_ex_min.append('R')
                    elif ((('L' in gaze_pattern_ex_loc_temp) or ('L ' in gaze_pattern_ex_loc_temp)) and not (('R ' in gaze_pattern_ex_loc_temp) or ('R' in gaze_pattern_ex_loc_temp))): 
                        # requirement for L pattern
                        #print 'L pattern detected.'
                        L_pattern_ex_times.append(gaze_pattern_ex_time_temp)
                        pattern_ex_min.append('L')
                    elif ((('L' in gaze_pattern_ex_loc_temp) or ('L ' in gaze_pattern_ex_loc_temp)) and (('R' in gaze_pattern_ex_loc_temp) or ('R ' in gaze_pattern_ex_loc_temp))):
                        LR_pattern_ex_times.append(gaze_pattern_ex_time_temp)
                        pattern_ex_min.append('LR')
                gaze_pattern_ex_loc_temp = []       # reset the areas fixated since last image fixation
                gaze_pattern_ex_time_temp = time    # potential start time of next extended pattern
            gaze_pattern_ex_loc_temp.append(IA_current)     # update the list of fixated areas
            #print 'gaze_pattern_ex_loc_temp:', gaze_pattern_ex_loc_temp

                # process gaze events
            if len(all_gaze_events_times) == 0:     # the first gaze event starts with the first fixation
                all_gaze_events_times.append(time)
                if 'R' in IA_current:           # right disc gaze event
                    R_gaze_events_times.append(time)
                    gaze_event_trajectory.append('right')
                    gaze_event_trajectory_min.append('right')
                elif 'L' in IA_current:         # left disc gaze event
                    L_gaze_events_times.append(time)
                    gaze_event_trajectory.append('left')
                    gaze_event_trajectory_min.append('left')
                elif 'image' in IA_current:     # image gaze event
                    im_gaze_events_times.append(time)
                    gaze_event_trajectory.append('image')
                    gaze_event_trajectory_min.append('image')
                else:                           # background gaze event
                    white_gaze_events_times.append(time)
                    gaze_event_trajectory.append('background')
                    gaze_event_trajectory_min.append('background')
            elif IA_previous != IA_current:     # gaze events are defined by successive fixations of the same interest area
                                                # -> new gaze event starts whenever the fixated area changes
                gaze_duration = previous_fix_start + previous_fix_duration - all_gaze_events_times[-1]
                    # gaze duration is end of last fixation in current area minus start of first fixation in that area
                    # -> takes into account saccades in between these fixations                
                all_gaze_events_durations.append(gaze_duration)
                all_gaze_events_times.append(time)
                if 'R' in IA_current:           # right disc gaze event
                    R_gaze_events_times.append(time)
                    gaze_event_trajectory.append('right')
                    gaze_event_trajectory_min.append('right')
                elif 'L' in IA_current:         # left disc gaze event
                    L_gaze_events_times.append(time)
                    gaze_event_trajectory.append('left')
                    gaze_event_trajectory_min.append('left')
                elif 'image' in IA_current:     # image gaze event
                    im_gaze_events_times.append(time)
                    gaze_event_trajectory.append('image')
                    gaze_event_trajectory_min.append('image')
                else:                           # background gaze event
                    white_gaze_events_times.append(time)
                    gaze_event_trajectory.append('background')
                    gaze_event_trajectory_min.append('background')

                if 'R' in IA_previous:           # right disc gaze event
                    R_gaze_events_durations.append(gaze_duration) 
                elif 'L' in IA_previous:         # left disc gaze event
                    L_gaze_events_durations.append(gaze_duration)
                elif 'image' in IA_previous:     # image gaze event
                    im_gaze_events_durations.append(gaze_duration)
                else:                           # background gaze event
                    white_gaze_events_durations.append(gaze_duration)

            previous_fix_start = time           # store fixation start times and durations
            previous_fix_duration = duration    # -> needed for gaze duration evaluation in case gaze event ends after current fixation
            previous_IA = IA_current
            # end of fixation loop


        if len(files_fix) > 0:      
            # if the previous fixation loop was executed at least once, we have to store the data of the last processed session

            gaze_duration = previous_fix_start + previous_fix_duration - all_gaze_events_times[-1]
                # gaze duration is end of last fixation in current area minus start of first fixation in that area
                # -> takes into account saccades in between these fixations                
            all_gaze_events_durations.append(gaze_duration)
            if 'R' in IA_previous:           # right disc gaze event
                R_gaze_events_durations.append(gaze_duration) 
            elif 'L' in IA_previous:         # left disc gaze event
                L_gaze_events_durations.append(gaze_duration)
            elif 'image' in IA_previous:     # image gaze event
                im_gaze_events_durations.append(gaze_duration)
            else:                           # background gaze event
                white_gaze_events_durations.append(gaze_duration)

            # process full gaze patterns    
            N_gaze = len(gaze_event_trajectory)
            N_full_gaze_pattern_R = 0
            N_full_gaze_pattern_L = 0
            for i in xrange(N_gaze-2):
                current_gaze_area = gaze_event_trajectory[i]
                area_after_next_gaze_area = gaze_event_trajectory[i+2]
                if current_gaze_area == 'image' and area_after_next_gaze_area == 'image':
                    area_in_between = gaze_event_trajectory[i+1]
                    if area_in_between == 'right':
                        N_full_gaze_pattern_R += 1
                    elif area_in_between == 'left':
                        N_full_gaze_pattern_L += 1

            dic_total = set_key_key_value(dic_total, current_name, 'dt_cutoff', dt_cutoff)
            dic_total, error = wrap_up(dic_total, current_name, R_times, L_times, im_times, 
                white_times, all_times, L_pattern_im_times, R_pattern_im_times, L_pattern_ex_times, R_pattern_ex_times, 
                LR_pattern_ex_times,
                all_gaze_events_times, all_gaze_events_durations, R_gaze_events_times, R_gaze_events_durations, L_gaze_events_times, 
                L_gaze_events_durations, im_gaze_events_times, im_gaze_events_durations, white_gaze_events_times, 
                white_gaze_events_durations, all_durations, R_durations, L_durations, im_durations, white_durations,
                fixation_trajectory, gaze_event_trajectory, N_full_gaze_pattern_R, N_full_gaze_pattern_L,
                fixation_trajectory_epochs, pattern_ex_epochs, gaze_event_trajectory_epochs, cutoff_data, overview_dic, coordinates)
                    # call function wrap_up() to process fixation data and store in dic_total
            if error:
                error_in_loop = True
                break

    return dic_total, error_in_loop


##
#
##


def process_saccade_files(files_sac, dic_total):
    """
    function for extracting and processing data from message report files

    input:
        files_msg (list): list of message report files found in reports folder
        dic_total (dictionary): total dictionary which stores all data
            -> contains a subdictionary with all data for each experiment session

    output:
        dic_total (dictionary): updated total dictionary
        error_in_loop (bool): indicates whether an error was encountered during function execution
    """

    print 'Processing messages.'
    error_in_loop = False   # indicates something went wrong in one of the following loops

    for report_sac in files_sac:    # loop over message reports
        if not error_in_loop:
            print 'Extracting data from', report_sac

            inputfile_sac = open(reports_folder+report_sac, 'r')
            inputdata_sac = inputfile_sac.read()    # load message report as text file
            inputfile_sac.close()

            lines_sac = inputdata_sac.split('\n')[1:-1]   
#            lines_sac = inputdata_sac.split(linebreak)[1:-1]  
                # lines_msg is a list of all rows containing data
                # -> first row contains descriptions, last row is empty
    
            current_label = lines_sac[0].split('\t')[0]
                # all report files are basically tab-separated text files
                # -> splitting each line by \t yields a list of the different data
                # -> first item is "RECORDING_SESSION_LABEL" and contains the session name in the format vpX.y or X.y
                #       where X is subject number and y is session number
            if 'vp' in current_label:
                current_name = current_label[2:]    # get session label in the form X.y
            else:
                current_name = current_label

            # saccade filter time transformation
            try:
                current_dic = dic_total[current_name]
                cutoff_data = current_dic['cutoff_data']
            except KeyError:
                cutoff_data = [[]]
            cutoff_data = [[0,0,0]] + cutoff_data
            N_cutoffs = len(cutoff_data)
            i_cutoff = 0
            cutoff_start = cutoff_data[0][0]
            cutoff_end = cutoff_data[0][1]
            t_correct = cutoff_data[0][2]

            sac_times = []      # this will contain all trigger times of one session
            durations = []
            amplitudes = []
            angles = []
            velocities_avg = []
            velocities_peak = []
            blinks = []
            N_blinks = 0

            for i_line in tqdm(xrange(len(lines_sac))):   # loop over messages

                line = lines_sac[i_line].split('\t')    # yields list [session label, time, message text]
                try:
                    label = line[0]
                    time = line[1]
                    start_IA = line[2]
                    end_IA = line[3]
                    duration = line[4]
                    amplitude = convert_number(line[5])
                    angle = convert_number(line[6])
                    velocity_avg = convert_number(line[7])
                    velocity_peak = convert_number(line[8])
                    contains_blink = line[9]
                except IndexError:
                    print 'Error: could not load saccade file!\nMake sure file format is right.'
                    error_in_loop = True
                    break
                try:        # check whether time is a numerical value
                    time = int(time)
                except ValueError:
                    print 'Error: time {} not recognized as number! (file {}, line {})'.format(time, report_sac, i_line)
                    error_in_loop = True
                    break   
                try:        # check whether time is a numerical value
                    duration = int(duration)
                except ValueError:
                    print 'Error: duration {} not recognized as number! (file {}, line {})'.format(duration, report_sac, i_line)
                    error_in_loop = True
                    break 
                try:        # check whether time is a numerical value
                    amplitude = float(amplitude)
                except ValueError:
                    if amplitude == '.':
                        amplitude = 0.0
                    else:
                        print 'Error: amplitude {} not recognized as number! (file {}, line {})'.format(amplitude, report_sac, i_line)
                        print 'line: {}'.format(line)
                        error_in_loop = True
                        break 
                try:        # check whether time is a numerical value
                    angle = float(angle)
                except ValueError:
                    if angle == '.':
                        angle = 0.0
                    else:
                        print 'Error: angle {} not recognized as number! (file {}, line {})'.format(angle, report_sac, i_line)
                        error_in_loop = True
                        break 
                try:        # check whether time is a numerical value
                    velocity_avg = float(velocity_avg)
                except ValueError:
                    if velocity_avg == '.':
                        velocity_avg = 0.0
                    else:
                        print 'Error: average velocity {} not recognized as number! (file {}, line {})'.format(velocity_avg, report_sac, i_line)
                        error_in_loop = True
                        break 
                try:        # check whether time is a numerical value
                    velocity_peak = float(velocity_peak)
                except ValueError:
                    if velocity_peak == '.':
                        velocity_peak = 0.0
                    else:
                        print 'Error: peak velocity {} not recognized as number! (file {}, line {})'.format(velocity_peak, report_sac, i_line)
                        error_in_loop = True
                        break 
                if 'true' in contains_blink:
                    blink = True
                    N_blinks += 1
                elif 'false' in contains_blink:
                    blink = False
                else:
                    print 'Error: {} not recognized as boolean! (file {}, line {})'.format(contains_blink, report_sac, i_line)
                    error_in_loop = True
                    break

                # actual time transformation
                real_time = time        # unfiltered time for plotting
                if i_cutoff < N_cutoffs-1:
                    while time > cutoff_end:
                        if i_cutoff < N_cutoffs-1:
                            i_cutoff += 1
                            cutoff_start = cutoff_data[i_cutoff][0]
                            cutoff_end = cutoff_data[i_cutoff][1]
                            t_correct = cutoff_data[i_cutoff-1][2]
                        else:
                            break
                    if time > cutoff_start:
                        time = cutoff_start + 10    # residual saccade after filtering has duration 10 ms                    
                time -= t_correct
#                print 'real time: {}\tt_correct: {}\tcorrected time: {}'.format(real_time, t_correct, time)


                if current_label != label:      # triggered whenever line contains data of a new session

                    N_saccades = len(sac_times)
                    if N_saccades > 0:
                        blink_ratio = 1.0 * N_blinks / N_saccades
                    else:
                        blink_ratio = 0.0

                    try:        # check whether the number of triggers of current session was stored before
                        total_time = dic_total[current_name]['total_time']
                        mean_sac_freq = 1000.0 * N_saccades / total_time    # mean trigger frequency
                    except KeyError:
                        mean_sac_freq = -42     # some dummy value
            
                    sac_times = np.array(sac_times, dtype=int)
                    dic_total = set_key_key_value(dic_total, current_name, 'sac_times', sac_times)
                    dic_total = set_key_key_value(dic_total, current_name, 'sac_durations', durations)
                    dic_total = set_key_key_value(dic_total, current_name, 'sac_amplitudes', amplitudes)
                    dic_total = set_key_key_value(dic_total, current_name, 'sac_angles', angles)
                    dic_total = set_key_key_value(dic_total, current_name, 'sac_velocities_avg', velocities_avg)
                    dic_total = set_key_key_value(dic_total, current_name, 'sac_velocities_peak', velocities_peak)
                    dic_total = set_key_key_value(dic_total, current_name, 'sac_blinks', blinks)
                    dic_total = set_key_key_value(dic_total, current_name, 'sac_N', N_saccades)
                    dic_total = set_key_key_value(dic_total, current_name, 'sac_mean_freq', mean_sac_freq)
                    dic_total = set_key_key_value(dic_total, current_name, 'sac_blink_ratio', blink_ratio)
                    dic_total = set_key_key_value(dic_total, current_name, 'sac_N_blinks', N_blinks)

                    # saccade filter time transformation
                    try:
                        current_dic = dic_total[current_name]
                        cutoff_data = current_dic['cutoff_data']
                    except KeyError:
                        cutoff_data = [[]]
                    cutoff_data = [[0,0,0]] + cutoff_data
                    N_cutoffs = len(cutoff_data)
                    i_cutoff = 0
                    cutoff_start = cutoff_data[0][0]
                    cutoff_end = cutoff_data[0][1]
                    t_correct = cutoff_data[0][2]
    
                    sac_times = []      # this will contain all trigger times of one session
                    durations = []
                    amplitudes = []
                    angles = []
                    velocities_avg = []
                    velocities_peak = []
                    blinks = []
                    N_blinks = 0
    
                    current_label = line[0]     # get new session label
                    if 'vp' in current_label:
                        current_name = current_label[2:]
                    else:
                        current_name = current_label
    
                sac_times.append(time)
                durations.append(duration)
                amplitudes.append(amplitude)
                angles.append(angle)
                velocities_avg.append(velocity_avg)
                velocities_peak.append(velocity_peak)
                blinks.append(blink)



            # end of message loop

        if len(files_msg) > 0:      
            # if the previous message loop was executed at least once, we have to store the data of the last processed session

            N_saccades = len(sac_times)
            if N_saccades > 0:
                blink_ratio = 1.0 * N_blinks / N_saccades
            else:
                blink_ratio = 0.0

            try:        # check whether the number of triggers of current session was stored before
                total_time = dic_total[current_name]['total_time']
                mean_sac_freq = 1000.0 * N_saccades / total_time    # mean trigger frequency
            except KeyError:
                mean_sac_freq = -42     # some dummy value
    
            sac_times = np.array(sac_times, dtype=int)
            dic_total = set_key_key_value(dic_total, current_name, 'sac_times', sac_times)
            dic_total = set_key_key_value(dic_total, current_name, 'sac_durations', durations)
            dic_total = set_key_key_value(dic_total, current_name, 'sac_amplitudes', amplitudes)
            dic_total = set_key_key_value(dic_total, current_name, 'sac_angles', angles)
            dic_total = set_key_key_value(dic_total, current_name, 'sac_velocities_avg', velocities_avg)
            dic_total = set_key_key_value(dic_total, current_name, 'sac_velocities_peak', velocities_peak)
            dic_total = set_key_key_value(dic_total, current_name, 'sac_blinks', blinks)
            dic_total = set_key_key_value(dic_total, current_name, 'sac_N', N_saccades)
            dic_total = set_key_key_value(dic_total, current_name, 'sac_mean_freq', mean_sac_freq)
            dic_total = set_key_key_value(dic_total, current_name, 'sac_blink_ratio', blink_ratio)
            dic_total = set_key_key_value(dic_total, current_name, 'sac_N_blinks', N_blinks)
        
    return dic_total, error_in_loop





###########################################################
#
#   Main Script
#
###########################################################




try:
    while True:     
        # loop broken if script terminated successfully or error encountered during:
        #   time extraction of message reports or 
        #   inter trigger interval extraction of message reports or
        #   time extraction of fixation reports        
        
        get_user_args()
        linebreak = get_linebreak()     # get linebreak encoding characters in current operating system
        reports_folder = './reports/'
        files = os.listdir(reports_folder)  # get all files in reports folder
        files_fix = []      # this will contain all fixation reports
        files_msg = []      # this will contain all message reports
        files_sac = []
        for file in files:      # loop over files
            if file[-8:] == '_msg.xls':     # message reports must end with _msg.xls
                files_msg.append(file)
            elif file[-8:] == '_fix.xls':       # fixation reporst must end with .xls but not with _msg.xls
                files_fix.append(file)
            elif file[-8:] == '_sac.xls':
                files_sac.append(file)
            
        print '\nExtracting data from report files.'
        print 'Cutoff value for saccade filtering: {} ms.'.format(dt_cutoff)
        print 'Found fixation data files:', files_fix
        print 'Found message data files:', files_msg
        print 'Found saccade data files:', files_sac

    #    error, subject_index_dic = get_subject_index_dic()
        error, overview_dic = process_overviews()
        if error:
            break

        dic_total = {}      # this will contain all data for each experiment session as subdictionaries

        dic_total, error = process_fixation_files(files_fix, dic_total, dt_cutoff, overview_dic)
            # call function process_fixation_files() to extract and process data from fixation report files
        if error:
            break

        dic_total, error = process_message_files(files_msg, dic_total)
            # call function process_message_files() to extract and process data from message report files
        if error:
            break

        dic_total, error = process_saccade_files(files_sac, dic_total)
        if error:
            break

        dic_total = filter_dic(dic_total)
        if error:
            break

        error = store_results(dic_total)    # call function store_results() to send data in dic_total to hard disc
        if error:
            break

        print 'Success.'
        break
        # end of while loop

    if error:
        print 'Extraction failed!'    
except:
    print '\n\nExtraction failure!\n'
    traceback.print_exc(file=sys.stdout)
finally:
    raw_input('\nPress Enter to exit.')
