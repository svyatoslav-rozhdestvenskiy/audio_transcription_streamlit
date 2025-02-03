import io
import ffmpeg
import librosa

from audio_preprocessing import AdvancedAudioProcessor

class AudioProcessor:
    def __init__(self, audio_bytes):
        """
        Класс для обработки аудио
        """
        self.audio_bytes = audio_bytes
        self.output_audio = None

    def convert_to_wav(self):
        """Конвертирует аудио/видеофайл в WAV (16-bit PCM, 16000 Hz)."""
        try:
            process = (
                ffmpeg.input('pipe:0')
                .output('pipe:1', format='wav', ar=16000, ac=1, sample_fmt="s16")
                .run(input=self.audio_bytes, capture_stdout=True, capture_stderr=True)
            )
            self.output_audio = process[0]
            return self.output_audio, None

        except Exception as e:
            print(f"Ошибка конвертации аудиофайла: {e}")
            return None, str(e)

    def preprocess(self):
        """Предобработка аудиофайл"""
        if not self.output_audio:
            return None, "Нет выходного аудиофайла после конвертации"

        try:
            y, sr = librosa.load(io.BytesIO(self.output_audio), sr=16000)

            # Изменение громкости и удаление пиков
            y = AdvancedAudioProcessor.preprocess_audio_volume(y)

            # Полосовой фильтр с проверкой корректности частот
            y = AdvancedAudioProcessor.bandpass_filter(y, sr)

            # Спектральное вычитание (поиск тихого участка и удаление шума)
            y = AdvancedAudioProcessor.remove_noise(y, sr)

            return y, None

        except Exception as e:
            print(f"Ошибка предобработки аудиопотока: {e}")
            return None, str(e)

    def process(self):
        """Полный цикл обработки аудиофайла: конвертация, предобработка."""
        # Конфертируем в wav
        converted_audio, error = self.convert_to_wav()
        if not converted_audio:
            return None, error

        # Делаем предобработку аудиозаписи
        preprocessed_audio, error = self.preprocess()
        if preprocessed_audio is None or preprocessed_audio.size == 0:
            return None, error

        return preprocessed_audio, error
