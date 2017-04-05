#
# Convert raw output of the Caffe 'time' command
# to the CK timing format.
#
# Developers:
#   - Grigori Fursin, cTuning foundation / dividiti, 2016
#   - Anton Lokhmotov, dividiti, 2016-2017
#

import json
import os
import re
import sys

import sys
import os.path
import glob
import argparse

#OPTIONS
# OpenCL vendor names and their short name
VENDOR_TRANSLATION_TABLE = {
  "GenuineIntel": "Intel",
  "Intel(R) Corporation": "Intel",
  "Advanced Micro Devices, Inc.": "AMD",
  "NVIDIA Corporation": "NVIDIA",
}



# Server storing a copy of the database
DATABASE_SERVER_URL = "https://raw.githubusercontent.com/CNugteren/CLBlast-database/master/database.json"
VERBOSE=0
def ck_postprocess(i):
    ck=i['ck_kernel']
    rt=i['run_time']
    deps=i['deps']

    d={}

    env=i.get('env',{})

    # Load both stderr and stdout. Concatenate into one list.
    # NB: This assumes that Caffe iterates only once (--iterations=1).
    # Otherwise, looping over the log would be required.
    rf1=rt['run_cmd_out1']
    rf2=rt['run_cmd_out2']
    rf3=rt['run_output_files'][0]
    rf4=rt['run_output_files'][1]
    print  "[postprocessing] Loading json output " + rt['run_output_files'][0]
    print  "[postprocessing] Loading json output " + rt['run_output_files'][1] 
    lst=[]
    r={}
    if os.path.isfile(rf1):
       r=ck.load_text_file({'text_file':rf1,'split_to_list':'yes'})
       if r['return']>0: return r
       lst+=r['lst']
    if os.path.isfile(rf2):
       r=ck.load_text_file({'text_file':rf2,'split_to_list':'yes'})
       if r['return']>0: return r
       lst+=r['lst']
    c1 = os.path.isfile(rf3)
    c2 = os.path.isfile(rf4)
    if c1:
	rj1 = json.loads(open(rf3).read())

    if c2:
        rj2= json.loads(open(rf4).read())

    if ((c1 == 0) and (c2 == 0)):
        r['return'] = 0
        print "[postprocessing] Unable to read json output"
        r['return'] = 1;
        return r;
    if ((c1)== 0):
        rj1 = rj2
    #### CREATE UNIQUE OUTPUT
    print "[postprocessing] Creating dictionary"
    d['post_processed']='yes'
#    mydict['device_core_clock'] = 'value from script'
#   SET ARCH INFORMATION
    d['device_vendor'] = rj1['device_vendor']
    d['device_type'] = rj1['device_type']
    d['device'] = rj1['device']
    d['device_compute_units'] = rj1['device_compute_units']
    # Notice that often is not really accurated; TBC 
    d['device_core_clock'] = rj1['device_core_clock']

    #Experiment Information
    kernel_family=rj1['kernel_family'].split("_")[0]
    if rj1['kernel_family'].split("_")[1] == "direct":
        #concut again special case
        kernel_family = kernel_family + "_" + "direct"
    d['kernel'] = kernel_family
    d['arg_beta'] = rj1['arg_beta']
    d['arg_m'] = rj1['arg_m']
    d['arg_n'] = rj1['arg_n']
    d['arg_k'] = rj1['arg_k']
    d['arg_alpha'] = rj1['arg_alpha']
    d['precision'] = rj1['precision']

    for target in VENDOR_TRANSLATION_TABLE:
            if d["device_vendor"] == target:
                d["device_vendor"] = VENDOR_TRANSLATION_TABLE[target]


    #### Add results per strategy
#    print "ADD RESULTs"
    l=[]
    if ( c1 ):
        tmp = {'strategy':'exhaustive', 'result': rj1['results']}
        l.append(tmp)
    if ( c2 ):
        tmp = {'strategy':'random', 'result': rj2['results']}
        l.append(tmp)

    d['data'] = l

    #GET DEFAULT VALUE from CLBlast
    deps_cb= deps['lib-clblast']
    b=deps_cb['cus']
    pl = b['path_lib']
    bench=d['kernel']
    bench +=".hpp"
    pl=pl.split("install")[0] #### VERIFY WITH INSTALL SCRIPT 
    pl_suff= "src/scripts/database/"
    pl += pl_suff

    sys.path.append(pl)
    ####
    import database.io as io
    import database.db as db
    import database.clblast as clblast
    import database.bests as bests
    import database.defaults as defaults
    database_filename=pl+"database.json"
    if not os.path.isfile(database_filename):
       io.download_database(database_filename, DATABASE_SERVER_URL)
    else:
       print "[database] DB found" 
    if os.path.isfile(database_filename):
       database = io.load_database(database_filename)


    # Retrieves the best performing results
    print("[database] Calculating the best results per device/kernel...")
    database_best_results = bests.get_best_results(database)
    search_vendor=d['device_vendor']
    search_device= d['device'] 
    search_device_type=d['device_type']
    search_kernel=d['kernel']
    search_precision= d['precision']
    # Determines the defaults for other vendors and per vendor
    print("[database] Calculating the default values...")
    database_defaults = defaults.calculate_defaults(database, 0) #second args denotes VERBOSE or NOT
    database_best_results["sections"].extend(database_defaults["sections"])
    database_best_filename='database_best.json'
    # Optionally outputs the database to disk
    if VERBOSE:
        io.save_database(database_best_results, database_best_filename)
    #### TEST to get best and default param 
    best = database_best_results['sections']
    ll = []
    for best_entries in best:
       #print best_entries['kernel_family'] + " " + search_kernel
       if( (best_entries['kernel_family'] == search_kernel)   and \
           (best_entries['device_vendor'] == search_vendor)   and \
           (best_entries['precision'] == search_precision)    and \
           (best_entries['device_type']== search_device_type) and \
           ((best_entries['device'] == search_device) or (best_entries['device']=='default')) ):
            if VERBOSE: print best_entries
            tmp=best_entries
            ll.append(tmp)

    if len(ll) > 0:
        if VERBOSE: print len(ll)
        d['db'] = ll
    else:
        d['db'] = 'na'
    rr={}
    rr['return']=0
#    output_filename='tmp-ck-clblast-tune-'+d['kernel']+'-'+d['arg_m']+'-'+d['arg_n']+'-'+d['arg_k']+'-'+d['precision'] +'.json' 
    output_filename='tmp-ck-clblast-tune.json'
##    print output_filename
    if d.get('post_processed','')=='yes':
        r=ck.save_json_to_file({'json_file':output_filename, 'dict':d})
        if r['return']>0: return r
    else:
        rr['return']=1
        rr['error']='FAIL'
        print(d)
#    print d['results'][1]
    return rr

# Do not add anything here!