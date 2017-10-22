import winsound
import time
notif_dur = 500  # millisecond
notif_freq_success = 600  # Hz
notif_freq_fail = int(float(220) / (9.0 / 8.0))  # Hz

def gen_sound(freq, dur, wait_after=0.0, count=1):
    for i in range(count):
        winsound.Beep(freq, dur)
        time.sleep(wait_after)


def sound_notif(succ):
    if succ:
        gen_sound(notif_freq_success, int(float(notif_dur) / 2.0), 0.1, 3)
    else:
        notif_freq_fail_low = int(float(notif_freq_fail) / (4.0 / 3.0))
        notif_freq_fail_high = int(float(notif_freq_fail) * 6.0 / 5.0)
        short_dur = int(float(notif_dur) / 4.0)
        medium_dur = int(float(notif_dur) / (4.0 / 3.0))
        gen_sound(notif_freq_fail, notif_dur, 0.1, 3)
        gen_sound(notif_freq_fail_low, medium_dur)
        gen_sound(notif_freq_fail_high, (short_dur))
        gen_sound(notif_freq_fail, (notif_dur), 0.1)
