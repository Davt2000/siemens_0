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


def get_relative_name(s):
    """ parses long relative name of file or directory and returns it in 'upper_dir/current_file_or_dir' format """
    return '/'.join(s.split(sep='/')[-2:])


def fail_report(path, text, loc_r, glob_r):
    """ writes reports both in start directory(global) and in test directory at path"""
    print("FAIL: ", get_relative_name(path) + '/\n', text, sep='', file=glob_r)
    print(text, file=loc_r)
    loc_r.close()


if __name__ == '__main__':
    wdir = os.curdir
    if len(argv) == 2:
        wdir += '/' + argv[1]

    # assuming logs are organized like example ( work_directory/category/test_directory )
    # and there are only directories in wdir and in any category
    full_listdir = step_down_listdir(os.listdir(wdir), wdir + '/')
    full_listdir.sort()

    global_report = open(wdir + "/reference_results.txt", 'w')

    for test in full_listdir:
        local_report = open(test + '/report.txt', 'w')
        test_dirs = os.listdir(test)

        if 'ft_reference' not in test_dirs and 'ft_run' not in test_dirs:
            fail_report(test, "directories missing: ft_reference ft_run", local_report, global_report)
            continue
        elif 'ft_reference' not in test_dirs:
            fail_report(test, "directory missing: ft_reference", local_report, global_report)
            continue
        elif 'ft_run' not in test_dirs:
            fail_report(test, "directory missingL ft_run", local_report, global_report)
            continue

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
                               "present in ft_reference: {}".format(' '.join(missing_files))
                if extra_files:
                    report_text += '\n'
            if extra_files:
                report_text += "In ft_run there are extra files " \
                               "not present in ft_reference: {}".format(' '.join(extra_files))
            fail_report(test, report_text, local_report, global_report)
            continue

        run_files_alt = [test + '/ft_run/' + i for i in run_files]
        broken_files = 0
        for file in run_files_alt:
            f = open(file)
            found_finish = 0
            line_counter = 0
            for line in f:
                line_counter += 1
                line_lower = line.lower()
                if line_lower.find('error') != -1:
                    report_text = get_relative_name(file) + '{}:'.format(line_counter) + line[:-1]
                    fail_report(test, report_text, local_report, global_report)
                    broken_files = 1
                    break
                if not found_finish:
                    if line.find('Solver finished at') != -1:
                        found_finish = 1
            if not found_finish and not broken_files:
                fail_report(test, get_relative_name(file) + ": missing 'Solver finished at'",
                            local_report, global_report)
                broken_files = 1
            f.close()
            if broken_files:
                break
        if broken_files:
            continue

        ref_files_alt = [test + '/ft_reference/' + i for i in run_files]
        report_text = ''
        for ref, run in zip(ref_files_alt, run_files_alt):
            ref_memory, ref_total = get_data(ref)
            run_memory, run_total = get_data(run)

            if not (0.2 <= ref_memory / run_memory <= 5):
                report_text += '{}'.format(get_relative_name(ref))
                report_text += ": different 'Memory Working Set Peak' " \
                               "(ft_run={:.2f}, ft_reference={:.2f}, rel.diff={:.2f}, criterion=4)".format(
                                run_memory, ref_memory, ref_memory/run_memory)
                if not (1 / 1.1 <= ref_total / run_total <= 1.1):
                    report_text += '\n'
            if not (1 / 1.1 <= ref_total / run_total <= 1.1):
                report_text += '{}'.format(get_relative_name(ref))
                report_text += ": different 'Total' of bricks " \
                               "(ft_run={}, ft_reference={}, rel.diff={:.2f}, criterion=0.1)".format(
                                run_total, ref_total, ref_total/run_total)

        if report_text:
            fail_report(test, report_text, local_report, global_report)
        else:
            local_report.close()
            print("OK:", get_relative_name(test) + '/', file=global_report)

    global_report.close()
