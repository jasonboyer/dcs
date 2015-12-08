''' Runs the DCS.
    Communicates via SQS to the remote hub.
    Starts and stops local modules and dispatches messages to them.
'''

import boto.kinesis
import boto.sqs
from boto.sqs.message import MHMessage
import boto3
from hub import constants
from hub.local import store_kinesis, store_firehose
import pyaudio
import time

if __name__ == '__main__':
    # execute only if run as a script
    run_time = 3600*7
    conn = boto.sqs.connect_to_region(constants.REGION)
    dcs_queues = conn.get_all_queues(prefix='dcs')
    if constants.VERBOSE:
        print(dcs_queues)
    #if constants.HUB_QUEUE not in dcs_queues:
        # setup_dcs.setup_dcs()
    #    print('Hub queue is not set up')
    #    exit(-1)
    hub_queue_up = conn.get_queue(constants.HUB_QUEUE_UP)
    hub_queue_down = conn.get_queue(constants.HUB_QUEUE_DOWN)
    hose = boto3.client('firehose')
    delivery_stream_name = 'audio_in'
    # Create a stream, and wait for it to become active
#    hose.create_delivery_stream(DeliveryStreamName=test_delivery_stream_name,
#                                     S3DestinationConfiguration={
#                                         'RoleARN':'arn:aws:iam::814050614726:role/firehose_delivery_role',
#                                         'BucketARN':'arn:aws:s3:::boyer-cs767-audio'
#                                     }
#                                     )
    while True:
        status = hose.describe_delivery_stream(DeliveryStreamName=delivery_stream_name)
        if status['DeliveryStreamDescription']['DeliveryStreamStatus'] == 'ACTIVE':
            print('Stream ACTIVE: ' + delivery_stream_name)
            break
        time.sleep(1.0)

    # Start recording audio
    store = store_firehose.StoreFirehose(pyaudio.paFloat32, 1, constants.RATE, constants.SAMPLES_PER_RECORD, 1, test_delivery_stream_name)
    store.start_storing()
    store.run()

    time.sleep(run_time)
    store.stop_storing()





    ''' Can also store to a Kinesis stream instead of Firehose,
        but it's more expensive.


    data_stream_name = 'data_stream' + str(time.time())
    # Create a data stream, and wait for it to become active
    kin = boto.kinesis.connect_to_region(constants.REGION)
    kin.create_stream(data_stream_name, 1)
    while True:
        status = kin.describe_stream(data_stream_name)
        if status['StreamDescription']['StreamStatus'] == 'ACTIVE':
            print('Created stream: ' + data_stream_name)
            break
        time.sleep(1.0)

    store = store_kinesis.StoreKinesis(pyaudio.paFloat32, 1, constants.RATE,
                                       constants.SAMPLES_PER_RECORD, 1,
                                       data_stream_name)
    store.start_storing()
    '''

    m = MHMessage(hub_queue)
    m[constants.ATTR_COMMAND] = constants.START_OPERATING
    m[constants.ATTR_STREAM_NAME] = data_stream_name
    hub_queue.write(m)

    time.sleep(3600*7)
    store.stop_storing()
