# data.py --- 
# 
# Filename: data.py
# Description: 
# Author: Jonathan Chung,
# Maintainer: 
# Created: Tue Mar  3 20:54:11 2015 (-0500)
# Version: 
# Package-Requires: (pydub, pyaudio, ffmpeg, scipy)

# Code:
from __future__ import division

from scipy.io import wavfile
import wave
import os
import glob
import matplotlib.pyplot as plt

class Kdatabase():
    '''
    docs
    '''
    def __init__(self, directory, is_mk1_data = False, debug=False):
        self._kdatas = []
        extension_list = map(lambda x: "*." + x, Kdata.supported_file_types)
        os.chdir(directory)
        for extension in extension_list:
            for video in glob.glob(extension):
                if video[0] == "_":
                    continue
                if debug:
                    print "Opening filename {0}".format(video)
                data = Kdata(video, is_mk1_data=is_mk1_data)
                self._kdatas.append(data)

    def get(self):
        for kdata in self._kdatas:
            yield kdata

    def get_data(self, kstring="input"):
        for kdata in self._kdatas:
            yield kdata[kstring]
    
    def _check_name_exist(self, kstring):
        return kstring in self._kdatas[0].data.keys

    def _get_all_name(self):
        return self._kdatas[0].data.keys

class Kdata():
    '''
    docs
    '''
    required_properties = {"frame_rate": 16,
                           "channels": 1}
    supported_file_types = ["wav", "mp3", "ogg", "flv", "mp4", "wma", "aac"]
    def __init__(self, filename, is_mk1_data = False):
        self._data = {}
        if is_mk1_data:
            vocal, background = self._separate_wav_channel(filename)
            self._data["vocal"] = vocal
            self._data["background"] = background
        filetype = filename[-3:]
        if "wav" == filetype:     
            wave_data, filename, sample_width = self.read_wav(filename)
        elif filetype in self.supported_file_types:
            new_filename = self._convert_filename(filename)
            if os.path.isfile(new_filename):
                wave_data, filename, sample_width = self.read_wav(new_filename)
            else:
                wave_data, filename, sample_width = self.convert_audio_to_wav(filename)
        else:
            raise "Unsupported file"

        self.is_mk1_data = is_mk1_data
        self.fs = int(wave_data[0])
        self.normaliser = max(abs(wave_data[1]))
        self._data["input"] = wave_data[1] /  self.normaliser
        self.filename = filename
        self.sample_width = sample_width

    def __getitem__(self, kstring):
        return self._data[kstring]

    def __setitem__(self, kstring, val):
        self._data[kstring] = val

    def read_wav(self, filename):
        # Check properties of the wave file
        wav_file = wave.open(filename)
        wav_properties = {"frame_rate": wav_file.getframerate() / 1000,
                          "channels": wav_file.getnchannels()}
  
        if self.required_properties == wav_properties:
            wave_data = wavfile.read(filename)
            filename = filename
            sample_width = wav_file.getsampwidth()
        else:
            wave_data, filename, sample_width = self.convert_audio_to_wav(filename)
        return wave_data, filename, sample_width

    @staticmethod
    def _convert_filename(filename):
        path, filename = os.path.split(filename)
        if path == '':
            path = os.getcwd()
        return path + "/_" + filename[0:-3] + "wav"

    @staticmethod
    def _separate_wav_channel(filename):
        wave_data = wavfile.read(filename)
        vocal = wave_data[1][:, 0]
        background = wave_data[1][:, 1]
        return vocal, background
        
    def convert_audio_to_wav(self, filename):
        filetype = filename[-3:]
        new_filename = self._convert_filename(filename)
        from pydub import AudioSegment
        supported_file = AudioSegment.from_file(filename, filetype)
        if supported_file.frame_rate / 1000 != self.required_properties["frame_rate"]:
            supported_file = supported_file.set_frame_rate(1000 * self.required_properties["frame_rate"])
        if supported_file.channels != self.required_properties["channels"]:     
            supported_file = supported_file.set_channels(self.required_properties["channels"])
        sample_width = supported_file.sample_width
        supported_file.export(new_filename, format="wav")
        wave_data = wavfile.read(new_filename)
        filename = new_filename
        return wave_data, filename, sample_width
    
    def play(self, data_type="input"):    
        if data_type != "input" and self.is_mk1_data:
            raise "Error, {0} does not exist".format(data_type)

        data = self._data[data_type] * self.normaliser
        import numpy as np
        data_int = data.astype(np.int16)
        data_play = data_int.tostring()
        from pyaudio import PyAudio
        p = PyAudio()
        stream = p.open(
            format=p.get_format_from_width(self.sample_width),
            channels=self.required_properties["channels"],
            rate=self.fs,
            output=True)

        stream.write(data_play)
        stream.stop_stream()
        stream.close()
        p.terminate()

    def save(self, filename, data_type="input"):
        from scipy.io import wavfile
        rate = self.required_properties["frame_rate"] * 1000
        wavfile.write(filename, rate, self._data[data_type])

    def view(self, data_type="input"):
        from utils.pyNumpyViewer import pyNumpyViewer
        pyNumpyViewer(self._data[data_type])

    def plot(self, data_type="input"):
        import numpy as np
        x = self._data[data_type]
        t = np.arange(1, x.shape[0] + 1)/16000.00
        plt.plot(t, x)
        plt.ylabel("Amplitude")
        plt.xlabel("Time (secs)")
        plt.show()

# data.py ends here
