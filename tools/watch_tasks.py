import argparse
from datetime import datetime, timedelta
import subprocess
from time import sleep


class PodWatcher:
    def __init__(self, pod_name):
        self.pod_name = pod_name
        self.recorded_last_line = None
        self.update_last_line()

    def __repr__(self):
        return f"{self.__class__.__name__} {self.pod_name}"

    @property
    def last_line(self):
        return (
            subprocess.check_output(f"kubectl logs --tail=1 {self.pod_name}", shell=True)
            .decode()
            .strip("\n")
        )

    def update_last_line(self):
        self.recorded_last_line = self.last_line

    def watch(self):
        if self.recorded_last_line != self.last_line:
            print(f"{self.pod_name} Currently writing logs")
        else:
            try:
                timedelta_since_last_activity = (
                    datetime.now()
                    - timedelta(hours=2)
                    - datetime.strptime(self.recorded_last_line[:19], "%Y-%m-%d %H:%M:%S")
                )
                print(
                    f"{self.pod_name} {timedelta_since_last_activity.seconds // 60} min"
                    + f" {timedelta_since_last_activity.seconds % 60} seconds elapsed"
                    + " without writing a new log line"
                )
            except Exception as e:
                print(self.pod_name, "last log line does not contain a timestamp", e)
        print('test')
        self.update_last_line()


worker_pods = [
    PodWatcher(pod_name)
    for pod_name in subprocess.check_output(
        "kubectl get pods -n default --no-headers=true | awk '/worker/{print $1}'",
        shell=True,
    )
    .decode()
    .split("\n")
    if pod_name != ""
]

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("time_between_update", type=int, default=60)
    args = parser.parse_args()
    time_between_update = args.time_between_update
    while True:
        print("\n\n")
        print(f'Update {datetime.strftime(datetime.now(), "%H:%M:%S")}')
        for worker_pod in worker_pods:
            worker_pod.watch()
        print("\n\n")
        sleep(time_between_update)
