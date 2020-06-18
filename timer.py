import time
class Timer():
    def __init__(self):
        self.time_history = []
        self.time_start = None
        self.time_end = None
        self.cnt = 0

    def __enter__(self):
        self.time_start = time.time()

    def __exit__(self, type, value, traceback):
        if type == KeyboardInterrupt:
            print('')
            print('aborted by KeyboardInterrupt')
            quit()
        self.time_end = time.time()
        time_elapsed = self.time_end - self.time_start
        print(f'[timer] {time_elapsed:.4f}s')
        self.time_history.append(time_elapsed)
        self.cnt += 1

    def show_stats(self):
        time_history = self.time_history
        if len(time_history) > 0:
            tot_time = sum(time_history)
            avg_time = sum(time_history) / len(time_history)
            avg_step_time = sum(time_history) / self.cnt
            print('[timer] tot_time =', tot_time)
            print('[timer] avg_time =', avg_time)
            print('[timer] avg_step_time =', avg_step_time)
        else:
            print('[timer] no stats available.')
