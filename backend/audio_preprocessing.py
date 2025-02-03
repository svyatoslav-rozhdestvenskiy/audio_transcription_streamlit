import librosa
import numpy as np
from scipy.signal import butter, lfilter
import noisereduce as nr

class AdvancedAudioProcessor:
    '''Набор статичных методов для предобработки аудио'''
    @staticmethod
    def preprocess_audio_volume(audio, target_rms=0.05, threshold_multiplier=3):
        rms = np.sqrt(np.mean(audio**2))
        spikes = AdvancedAudioProcessor.find_spikes(audio, threshold_multiplier=threshold_multiplier)
        if spikes:
            audio = AdvancedAudioProcessor.remove_spikes(audio, spikes)
        if rms < target_rms:
            audio = AdvancedAudioProcessor.increase_volume(audio, current_rms=rms, target_rms=target_rms)
        return audio

    @staticmethod
    def find_spikes(audio, threshold_multiplier=3):
        abs_audio = np.abs(audio)
        perc_90 = np.percentile(abs_audio, 90)
        perc_99 = np.percentile(abs_audio, 99)
        threshold = perc_90 + threshold_multiplier * perc_99
        spike_indices = np.where(abs_audio > threshold)[0]
        spikes = []
        if len(spike_indices) > 0:
            start = spike_indices[0]
            for i in range(1, len(spike_indices)):
                if spike_indices[i] > spike_indices[i - 1] + 1:
                    spikes.append((start, spike_indices[i - 1]))
                    start = spike_indices[i]
            spikes.append((start, spike_indices[-1]))
        return spikes

    @staticmethod
    def remove_spikes(audio, spikes):
        audio_copy = audio.copy()
        for start, end in spikes:
            pre_value = audio[start - 1] if start > 0 else 0
            post_value = audio[end + 1] if end < len(audio) - 1 else 0
            mean_value = (pre_value + post_value) / 2
            audio_copy[start:end + 1] = mean_value
        return audio_copy

    @staticmethod
    def increase_volume(audio, current_rms, target_rms=0.01):
        gain = target_rms / current_rms if current_rms > 0 else 1
        amplified_audio = np.clip(audio * gain, -1.0, 1.0)
        return amplified_audio

    @staticmethod
    def bandpass_filter(audio, sr=16000, lowcut=80, highcut=7500, order=4):
        nyquist = 0.5 * sr
        low = lowcut / nyquist
        high = highcut / nyquist
        b, a = butter(order, [low, high], btype="band")
        return lfilter(b, a, audio)

    @staticmethod
    def find_quiet_segments(audio, sr, frame_size=8192, hop_length=2048, min_duration=1.0, max_gap=3):
        rms = librosa.feature.rms(y=audio, frame_length=frame_size, hop_length=hop_length).flatten()
        rms_high = np.percentile(rms, 20)
        quiet_indices = np.where(rms <= rms_high)[0]
        quiet_segments = []
        start = None
        count = 0
        gap = 0
        min_quiet_frames = int((sr / hop_length) * min_duration)
        for i in range(len(quiet_indices)):
            if start is None:
                start = quiet_indices[i] * hop_length
                count = 1
                gap = 0
            elif quiet_indices[i] == quiet_indices[i - 1] + 1:
                count += 1
                gap = 0
            else:
                if (quiet_indices[i] - quiet_indices[i - 1]) <= max_gap:
                    count += 1
                    gap += 1
                else:
                    if count >= min_quiet_frames:
                        end = quiet_indices[i - 1] * hop_length
                        quiet_segments.append((start, end))
                    start = quiet_indices[i] * hop_length
                    count = 1
                    gap = 0
        if start is not None and count >= min_quiet_frames:
            end = quiet_indices[-1] * hop_length
            quiet_segments.append((start, end))
        return quiet_segments

    @staticmethod
    def find_noisiest_segment(audio, sr, quiet_segments, max_noise_duration=1.5):
        best_segment = None
        max_zcr = 0
        max_noise_samples = int(sr * max_noise_duration)
        for start, end in quiet_segments:
            segment = audio[start:end]
            zcr = np.mean(librosa.feature.zero_crossing_rate(y=segment))
            if zcr > max_zcr:
                max_zcr = zcr
                best_segment = segment[:max_noise_samples]
        return best_segment

    @staticmethod
    def remove_noise(audio, sr, frame_size=8192, hop_length=2048, min_duration=1.0, max_noise_duration=1.5, max_gap=3):
        quiet_segments = AdvancedAudioProcessor.find_quiet_segments(audio, sr, frame_size, hop_length, min_duration, max_gap)
        if not quiet_segments:
            return audio
        noise_segment = AdvancedAudioProcessor.find_noisiest_segment(audio, sr, quiet_segments, max_noise_duration)
        if noise_segment is None:
            return audio
        return nr.reduce_noise(y=audio, sr=sr, y_noise=noise_segment, prop_decrease=0.8)
