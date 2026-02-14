import torch
import numpy as np
import soundfile as sf

from silero_vad import (
    load_silero_vad,
    get_speech_timestamps
)

model = load_silero_vad()


def has_speech(audio_path, min_duration=0.8):

    wav, sr = sf.read(audio_path)

    wav = torch.from_numpy(wav)

    speech = get_speech_timestamps(
        wav,
        model,
        sampling_rate=sr
    )

    total = 0

    for seg in speech:
        total += (seg["end"] - seg["start"]) / sr

    return total > min_duration
