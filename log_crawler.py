from sys import argv
import os


def step_down_listdir(current_listdir, start_dir=''):
    """ listdir with relative path"""
    out = []
    for path in current_listdir:
        sub_listdir = os.listdir(start_dir + path)
        out += [start_dir + path + '/' + j for j in sub_listdir]
    return out


#   memory check
#   *total* check
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


if __name__ == '__main__':
    # get wdir from argv
    wdir = os.curdir
    if len(argv) == 2:
        wdir += '/' + argv[1]
    # assuming logs are organized like example ( wdir/*category*/*test_directory* )
    # and there are only directories in wdir and in any *category*
    # get listdir
    full_listdir = step_down_listdir(os.listdir(wdir), wdir + '/')

    # for item in a list
    for test in full_listdir:
        # check dirs in a test
        test_dirs = os.listdir(test)
        if 'ft_reference' not in test_dirs or 'ft_run' not in test_dirs:
            print(test, "FAIL; missing directories;")
            continue
            # todo : specify message and write report
        # check missing files
        ref_dirs = step_down_listdir([test + '/ft_reference'])
        ref_files = []
        for ref_dir in ref_dirs:
            ref_files += [ref_dir.split(sep='/')[-1] + '/' + i for i in os.listdir(ref_dir)]

        run_dirs = step_down_listdir([test + '/ft_run'])
        run_files = []
        for run_dir in run_dirs:
            run_files += [run_dir.split(sep='/')[-1] + '/' + i for i in os.listdir(run_dir)]

        if ref_files != run_files:
            print(test, "FAIL; missing/extra files")
            continue
            # todo : specify message and write report

        # check *run* for errors and find an end
        run_files_alt = [test + '/ft_run/' + i for i in run_files]
        for file in run_files_alt:
            f = open(file)
            for line in f:
                line_lower = line.lower()
                if line_lower.find('error') != -1:
                    print(file, "FAIL; error found\n", line)
                    # todo : specify message and write report
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
                print(test, "OK")
            # write report
        # echo in stdout
        # todo: make appropriate messages and write report


