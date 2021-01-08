from sys import argv
import os


def step_down_listdir(current_listdir, start_dir=''):
    """ listdir with relative path"""
    out = []
    for path in current_listdir:
        sub_listdir = os.listdir(start_dir + path)
        out += [start_dir + path + '/' + j for j in sub_listdir]
    return out


def get_data(file):
    """ parses input file and gets maximum memory usage and last number of bricks in mesh"""
    f = open(file)
    max_peak = 0
    total = 0

    for line in f:
        if line.find("Memory Working Set Peak") != -1:
            peak = float(line.split()[-2])  # assuming all values are Mb
            if peak > max_peak:
                max_peak = peak
        if line.find("MESH::Bricks:") != -1:
            total = int(line.split()[1].split('=')[1])

    f.close()

    return max_peak, total


def fail_report(path, text,  loc_r, glob_r):
    """ writes reports both in start directory(global) and in test directory at path"""
    print("FAIL: ", path+'\n', text+'\n', sep='', file=glob_r)
    print("FAIL: ", path+'\n', text+'\n', sep='', file=loc_r)
    loc_r.close()


if __name__ == '__main__':
    wdir = os.curdir
    if len(argv) == 2:
        wdir += '/' + argv[1]

    # assuming logs are organized like example ( wdir/category/test_directory )
    # and there are only directories in wdir and in any category
    full_listdir = step_down_listdir(os.listdir(wdir), wdir + '/')

    global_report = open(wdir + "/reference_results.txt", 'w')

    for test in full_listdir:
        local_report = open(test + '/report.txt', 'w')
        test_dirs = os.listdir(test)

        if 'ft_reference' not in test_dirs and 'ft_run' not in test_dirs:
            fail_report(test, "directories missing: ft_reference ft_run", local_report, global_report)
        elif 'ft_reference' not in test_dirs:
            fail_report(test, "directory missing: ft_reference", local_report, global_report)
        elif 'ft_run' not in test_dirs:
            fail_report(test, "directory missingL ft_run", local_report, global_report)

        ref_dirs = step_down_listdir([test + '/ft_reference'])
        ref_files = []
        for ref_dir in ref_dirs:
            ref_files += [ref_dir.split(sep='/')[-1] + '/' + i for i in os.listdir(ref_dir)]

        run_dirs = step_down_listdir([test + '/ft_run'])
        run_files = []
        for run_dir in run_dirs:
            run_files += [run_dir.split(sep='/')[-1] + '/' + i for i in os.listdir(run_dir)]

        if ref_files != run_files:
            missing_files = set(ref_files) - set(run_files)
            extra_files = set(run_files) - set(ref_files)
            report_text = ''
            if missing_files:
                report_text += "In ft_run there are missing files " \
                               "present in ft_reference: {}\n".format(' '.join(missing_files))
            if extra_files:
                report_text += "In ft_run there are extra files " \
                               "not present in ft_reference: {}\n".format(' '.join(extra_files))
            fail_report(test, report_text, local_report, global_report)
            continue

        run_files_alt = [test + '/ft_run/' + i for i in run_files]
        for file in run_files_alt:
            f = open(file)
            line_counter = 0
            for line in f:
                line_counter += 1
                line_lower = line.lower()
                if line_lower.find('error') != -1:
                    report_text = '/'.join(file.split(sep='/')[-2:]) + '{}:'.format(line_counter) + line
                    fail_report(test, report_text, local_report, global_report)
                    break
            f.close()

        ref_files_alt = [test + '/ft_reference/' + i for i in run_files]
        for ref, run in zip(ref_files_alt, run_files_alt):
            ref_memory, ref_total = get_data(ref)
            run_memory, run_total = get_data(run)
            failed = 0

            if not (0.2 <= ref_memory/run_memory <= 5):
                print(test, "FAIL; different memory criterion 4\n")
                failed = 1
            if not(1/1.1 <= ref_total/run_total <= 1.1):
                print(test, "FAIL; different bricks criterion 0.1\n")
                failed = 1
            if not failed:
                print("OK:", test, file=global_report)

    global_report.close()



