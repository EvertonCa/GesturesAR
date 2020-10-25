from subprocess import Popen


def send_factor_to_slam(correction):
    # threshold for how many meters a horizontal plane can be considered
    meters = 0.01
    threshold = correction * meters
    p = Popen(['../cmake-build-debug/YoloCorrectionSender', str(threshold)])
