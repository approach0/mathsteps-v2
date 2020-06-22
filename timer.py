import time
class Timer():
    def __init__(self):
        self.time_history = []
        self.time_start = None
        self.time_end = None

    def __enter__(self):
        self.time_start = time.time()

    def __exit__(self, type, value, traceback):
        if type == KeyboardInterrupt:
            print('')
            print('aborted by KeyboardInterrupt')
            return
        self.time_end = time.time()
        time_elapsed = self.time_end - self.time_start
        print(f'[timer] {time_elapsed:.4f}s')
        self.time_history.append(time_elapsed)

    def show_stats(self, n_steps=1):
        time_history = self.time_history
        tot_time = sum(time_history)
        if len(time_history) > 0:
            tot_time = tot_time
            avg_time = tot_time / len(time_history)
            avg_step_time = tot_time / n_steps
            print('[timer] tot_time =', tot_time)
            print('[timer] avg_time =', avg_time)
            if n_steps != 1:
                print('[timer] total_steps =', n_steps)
                print('[timer] avg_step_time =', avg_step_time)
        else:
            print('[timer] no stats available.')
