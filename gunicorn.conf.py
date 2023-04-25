import multiprocessing

capture_output = True
loglevel = "info"

accesslog = "-"
errorlog = "-"
access_log_format = '%(t)s %({X-Forwarded-For}i)s %(s)s "%(r)s"'

proc_name = "ctf.skelmis.co.nz"

worker_tmp_dir = "/dev/shm"

bind = "[::]:8000"
workers = multiprocessing.cpu_count() * 2 + 1
