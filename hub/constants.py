''' Constants shared by all modules
'''

import math

VERBOSE = False
REGION = 'us-east-1'

# SQS Queue names
HUB_QUEUE_UP = 'dcs_hub_queue'
HUB_QUEUE_DOWN = 'dcs_hub_queue_down'
BARK_QUEUE = 'dcs_bark_queue'
EVENT_QUEUE = 'dcs_rl_event_queue'

# Messages
# Requires ATTR_STREAM_NAME
START_COLLECTING = 'StartCollecting'
STOP_COLLECTING = 'StopCollecting'
START_TRAINING = 'StartTraining'
STOP_TRAINING = 'StopTraining'
# Requires ATTR_STREAM_NAME
START_OPERATING = 'StartOperating'
STOP_OPERATING = 'StopOperating'
PLAY_SOUND = 'PlaySound'


# Message attributes
ATTR_COMMAND = 'Command'
ATTR_STREAM_NAME = 'StreamName'
ATTR_DOG_STATE = 'DogState'

# Dog states
DOG_STATE_BARKING = 'Barking'
DOG_STATE_QUIET = 'Quiet'

# Audio processing parameters
RATE = 96000
CHUNK = int(RATE/40)  # 25 millis
STEP = int(RATE/100)  # 10 millis
SAMPLES_PER_RECORD = math.floor(25000/4)
RECORDS_PER_PUT = 4

# Feature processing parameters
MFCC_SIZE = 13
MFCCS_PER_RECORD = 10

# Sound playing parameters
ATTR_SOUND_FILE = 'SoundFile'
ATTR_VOLUME_LEVEL = 'VolumeLevel'

# Reinforcement learning parameters
RL_MESS_CHUNK = 10
REWARD_DOG_BARKING = -100
REWARE_DOG_QUIET = 1
REWARD_SOUND_LOUD = -20
REWARD_SOUND_MEDIUM = -10
REWARD_SOUND_LOW = -5
REWARD_SOUND_NONE = 0

EPISODE_TIME = 300
