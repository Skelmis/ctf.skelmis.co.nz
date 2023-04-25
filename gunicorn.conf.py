import multiprocessing

capture_output = True
loglevel = "info"

accesslog = "-"
errorlog = "-"
access_log_format = '%(h) %(t) "%(r)"'

proc_name = "ctf.skelmis.co.nz"

worker_tmp_dir = "/dev/shm"

bind = "[::]:8000"
workers = multiprocessing.cpu_count() * 2 + 1
