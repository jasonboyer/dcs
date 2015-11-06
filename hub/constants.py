''' Constants shared by all modules
'''

import math

VERBOSE = False
REGION = 'us-east-1'

# SQS Queue names
HUB_QUEUE = 'dcs_hub_queue'

# Messages
# Requires ATTR_STREAM_NAME
START_COLLECTING = 'StartCollecting'
STOP_COLLECTING = 'StopCollecting'
START_TRAINING = 'StartTraining'
STOP_TRAINING = 'StopTraining'
# Requires ATTR_STREAM_NAME
START_OPERATING = 'StartOperating'
STOP_OPERATING = 'StopOperating'

# Message attributes
ATTR_COMMAND = 'Command'
ATTR_STREAM_NAME = 'StreamName'

# Audio processing parameters
RATE = 96000
CHUNK = int(RATE/40)  # 25 millis
STEP = int(RATE/100)  # 10 millis
SAMPLES_PER_RECORD = math.floor(25000/4)
RECORDS_PER_PUT = 4
