import os
import cv2
import librosa
import numpy as np
from moviepy.editor import AudioFileClip, VideoFileClip

audio_path = "StarWars60.wav"
image_path = 'F.jpg'
temp_video_path = 'TEMP_VID.mp4'
final_output_path ='final_vid2.mp4'

MIN_FREQ = 2000
MAX_FREQ = 10000
BAND_W  = 200  # Frequency band size this will result in number of bars beteen MIN_FREQ and MAX_FREQ 
BAR_COLOR = (180, 30, 50) # in BGR 

# Load the image
image = cv2.imread(image_path)
# Define the new width and height of the image

img_backup = image.copy()
img_height, img_width, img_channels = image.shape

spectrum_window_width, spectrum_window_height = 500, 500

def clamp(min_value, max_value, value):
    """this function helps to ensure the insensity are within the limits to be plotted """
    if value < min_value:
        return min_value

    if value > max_value:
        return max_value

    return value

def merge_video(input_video_path,input_audio_path,output_path):
    """ this takes input_video_path, input_audio_path & output_path as parameters
    it merges the newly created video with the Audio sample """
    # Load the video file
    video = VideoFileClip(input_video_path)
    # Load the audio file
    final_audio = AudioFileClip(input_audio_path)
    # Set the audio from the input audio file to the video
    final_video = video.set_audio(final_audio)
    # Generate the output video file
    final_video.write_videofile(output_path)
 

class AudioBar:
    """A bar object with variable height whic is proportional to the intensity of sound"""

    def __init__(
        self,
        x,
        y,
        freq,
        width=50,
        min_height=10,
        max_height=100,
        min_decibel=-80,
        max_decibel=0,
    ):
        self.x, self.y, self.freq = x, y, freq
        self.width, self.min_height, self.max_height = width, min_height, max_height
        self.height = min_height
        self.min_decibel, self.max_decibel = min_decibel, max_decibel

        self.__decibel_height_ratio = (self.max_height - self.min_height) / (
            self.max_decibel - self.min_decibel
        )
    def update(self, decibel):
        """The update method helps set the new values of the baar model"""

        desired_height = decibel * self.__decibel_height_ratio + self.max_height
        speed = (desired_height - self.height) / 0.1
        self.height += speed * 0.08
        self.height = clamp(self.min_height, self.max_height, self.height)


time_series, sample_rate = librosa.load(audio_path)  # getting information from the file


#**********************************************************************MY PROBLEM**************************************************************************
# getting a matrix which contains amplitude values according to frequency and time indexes
stft = np.abs(librosa.stft(time_series, hop_length=512, n_fft=2048*4))
spectrogram = librosa.amplitude_to_db(stft, ref=np.max)  # converting the matrix to decibel matrix
frequencies = librosa.core.fft_frequencies(n_fft=2048*4)  # getting an array of frequencies

# getting an array of time periodic
times = librosa.core.frames_to_time(
    np.arange(spectrogram.shape[1]), sr=sample_rate, hop_length=512, n_fft=2048 * 4
)
#**********************************************************************MY PROBLEM**************************************************************************



fps = time_index_ratio = len(times)/times[len(times) - 1] #the fps here is used to better match the video to the audio samples 
frequencies_index_ratio = len(frequencies)/frequencies[len(frequencies)-1]
period = 1/fps #how much time a frame needs to show in order to achieve the required fps 

def get_decibel(target_time, freq): 
    """ gets the decibel value for a particular time for a particular frequency range"""
    return spectrogram[int(freq * frequencies_index_ratio)][int(target_time * time_index_ratio)]


bars = []
frequencies = np.arange(MIN_FREQ, MAX_FREQ, BAND_W) # give us an array of frequencies between MIN_FREQ & MAX_FREQ at intervals of BAND_W
n = len(frequencies) # number of bars


width = int(spectrum_window_width/n) # the width of each bar
x = int((img_width - spectrum_window_width)/2) # the x coordinate of each bar 

# create bar objects to represent each frequency range  
for c in frequencies:
    bars.append(AudioBar(x, 300, c, max_height=700, width=width))
    x += width+1



# this section creates eaach video frame  and overlays the barchat plot on it  

fourcc = cv2.VideoWriter_fourcc(*'mp4v') # or use 'XVID' on Windows, 'MJPG' on Linux
output = cv2.VideoWriter(temp_video_path, fourcc, fps, (img_width, img_height))

time_stamp = 0 # this variable is used as index to get the intensity of sound for each frequency band 

while time_stamp <= times[len(times) - 1]:
    image = img_backup.copy()
    for b in bars: # iterate between each audio bar object
        b.update(get_decibel(time_stamp, b.freq)) # gets the decibel vaalue for 
        cv2.rectangle(
            image,
            (int(b.x + 1), int(b.max_height)),
            (int(b.x + b.width), int(b.max_height - b.height)),
            BAR_COLOR,
            -1,
            cv2.LINE_AA,
            0,
        )  # (0, 255, 0) is the color in BGR format, 2 is the thickness of the line
    time_stamp += period

    output.write(image)

output.release()
merge_video(temp_video_path,audio_path,final_output_path)
os.remove(temp_video_path)