import torch

from transformers import WhisperForConditionalGeneration, WhisperTokenizer, WhisperFeatureExtractor, pipeline

class WhisperTranscriber:
    def __init__(self, model_name="openai/whisper-large-v3", language="russian"):
        """
        Инициализация модели Whisper для распознавания речи.
        """
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

        try:
            self.model = WhisperForConditionalGeneration.from_pretrained(model_name).to(self.device)
            self.tokenizer = WhisperTokenizer.from_pretrained(model_name, language=language, task="transcribe")
            self.feature_extractor = WhisperFeatureExtractor.from_pretrained(model_name)

            self.transcriber = pipeline(
                "automatic-speech-recognition",
                model=self.model,
                tokenizer=self.tokenizer,
                feature_extractor=self.feature_extractor,
                device=0 if self.device == "cuda" else -1,
                batch_size=4
            )
            print("[INFO] WhisperTranscriber успешно инициализирован.")
        except Exception as e:
            raise RuntimeError(f"Ошибка инициализации WhisperTranscriber: {e}")

    def transcribe_audio(self, audio):
        """
        Распознает текст из аудиозаписи (NumPy массив) с частотой дискретизации 16000 Гц.
        """
        try:
            result = self.transcriber(audio, return_timestamps=True)
            return result["text"], None

        except Exception as e:
            print(f"Ошибка транскрибации: {e}")
            return None, str(e)
