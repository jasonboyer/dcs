__author__ = 'jasonboyer'

from audioin.chunks_from_s3 import ChunksFromS3
from dcsdbn.training.dbn_train import DbnTrain
from features import mfcc
from hub import constants
import numpy
import queue


if __name__ == '__main__':
    # execute only if run as a script
    # 'test_stream1446121778.355943'
    bucket = 'boyer-cs767-audio'
    rate = 96000
    batch_size = 10
    mfcc_size = constants.MFCC_SIZE
    mfccs_per_record = constants.MFCCS_PER_RECORD
    train_output_queue = queue.Queue()
    valid_output_queue = queue.Queue()
    test_output_queue = queue.Queue()
#    chunker = ChunksFromS3(bucket_name=bucket,
#                           year=2015, month=11, day=5, hour=12,
#                           rate=rate, samples_per_record=rate/100,
#                           chunk=96000/40, step=96000/100,
#                           output_queue=train_output_queue)
#    chunker.play_blob(45)

#    chunker = ChunksFromS3(bucket_name=bucket,
#                           year=2015, month=11, day=9, hour=12,
#                           rate=rate, samples_per_record=rate/100,
#                           chunk=96000/40, step=96000/100,
#                           output_queue=train_output_queue)
#    chunker.play_blob(45)

#    chunker = ChunksFromS3(bucket_name=bucket,
#                       year=2015, month=11, day=10, hour=15,
#                       rate=rate, samples_per_record=rate/100,
#                       chunk=96000/40, step=96000/100,
#                       output_queue=valid_output_queue)
#    chunker.play_blob(30)

#    chunker = ChunksFromS3(bucket_name=bucket,
#                           year=2015, month=11, day=9, hour=12,
#                           rate=rate, samples_per_record=rate/100,
#                           chunk=96000/40, step=96000/100,
#                           output_queue=train_output_queue)
#    chunker.play_blob(58)

#    chunker = ChunksFromS3(bucket_name=bucket,
#                       year=2015, month=11, day=10, hour=15,
#                       rate=rate, samples_per_record=rate/100,
#                       chunk=96000/40, step=96000/100,
#                       output_queue=valid_output_queue)
#    chunker.play_blob(58)

#    chunker = ChunksFromS3(bucket_name=bucket,
#                           year=2015, month=11, day=10, hour=12,
#                           rate=rate, samples_per_record=rate/100,
#                           chunk=96000/40, step=96000/100,
#                           output_queue=test_output_queue)
#    chunker.play_blob(49)

#    chunker = ChunksFromS3(bucket_name=bucket,
#                           year=2015, month=11, day=10, hour=12,
#                           rate=rate, samples_per_record=rate/100,
#                           chunk=96000/40, step=96000/100,
#                           output_queue=test_output_queue)
#    chunker.play_blob(58)


    queues = []

    # Vetted samples - dog barking
    player = ChunksFromS3(bucket_name=bucket,
                          year=2015, month=11, day=10, hour=12,
                          rate=96000, samples_per_record=96000/100,
                          chunk=96000/40, step=96000/100,
                          output_queue=train_output_queue)
    player.play_blob(50, 23, 20)

    # Vetted samples - dog barking
    player = ChunksFromS3(bucket_name=bucket,
                          year=2015, month=11, day=10, hour=12,
                          rate=96000, samples_per_record=96000/100,
                          chunk=96000/40, step=96000/100,
                          output_queue=valid_output_queue)
    player.play_blob(50, 53, 2)

    # Vetted samples - dog barking
    player = ChunksFromS3(bucket_name=bucket,
                          year=2015, month=11, day=10, hour=12,
                          rate=96000, samples_per_record=96000/100,
                          chunk=96000/40, step=96000/100,
                          output_queue=test_output_queue)
    player.play_blob(50, 43, 10)

    queues.append((train_output_queue, valid_output_queue, test_output_queue))

    train_background_output_queue = queue.Queue()
    valid_background_output_queue = queue.Queue()
    test_background_output_queue = queue.Queue()

    # Vetted samples - background noise
    player = ChunksFromS3(bucket_name=bucket,
                          year=2015, month=11, day=17, hour=17,
                          rate=96000, samples_per_record=96000/100,
                          chunk=96000/40, step=96000/100,
                          output_queue=train_background_output_queue)
    player.play_blob(0, 0, 240)

    # Vetted samples - background noise
    player = ChunksFromS3(bucket_name=bucket,
                          year=2015, month=11, day=17, hour=17,
                          rate=96000, samples_per_record=96000/100,
                          chunk=96000/40, step=96000/100,
                          output_queue=valid_background_output_queue)
    player.play_blob(5, 0, 30)

    # Vetted samples - background noise
    player = ChunksFromS3(bucket_name=bucket,
                          year=2015, month=11, day=17, hour=17,
                          rate=96000, samples_per_record=96000/100,
                          chunk=96000/40, step=96000/100,
                          output_queue=test_background_output_queue)
    player.play_blob(5, 30, 10)

    queues.append((train_background_output_queue, valid_background_output_queue, test_background_output_queue))

    train_quiet_output_queue = queue.Queue()
    valid_quiet_output_queue = queue.Queue()
    test_quiet_output_queue = queue.Queue()

    # Vetted samples - quiet
    player = ChunksFromS3(bucket_name=bucket,
                          year=2015, month=11, day=17, hour=18,
                          rate=96000, samples_per_record=96000/100,
                          chunk=96000/40, step=96000/100,
                          output_queue=train_quiet_output_queue)
    player.play_blob(0, 0, 240)

    # Vetted samples - quiet
    player = ChunksFromS3(bucket_name=bucket,
                          year=2015, month=11, day=17, hour=18,
                          rate=96000, samples_per_record=96000/100,
                          chunk=96000/40, step=96000/100,
                          output_queue=valid_quiet_output_queue)
    player.play_blob(5, 0, 30)

    # Vetted samples - quiet
    player = ChunksFromS3(bucket_name=bucket,
                          year=2015, month=11, day=17, hour=18,
                          rate=96000, samples_per_record=96000/100,
                          chunk=96000/40, step=96000/100,
                          output_queue=test_quiet_output_queue)
    player.play_blob(5, 30, 10)

    queues.append((train_quiet_output_queue, valid_quiet_output_queue, test_quiet_output_queue))

    # TODO: Use a non-default number of MFCCs
    datasets = dict()
    # each tuple contains a queue of training samples,
    # validation samples, and tet samples. We will use
    # the tuple number as the target for the logistic
    # regression
    tuple_num = -1
    target_arrays = [[], [], []]
    mfcc_feat_arrays = [[], [], []]
    for queue_tuple in queues:
        tuple_num += 1
        queue_num = -1
        for a_queue in queue_tuple:
            queue_num += 1
            num_elements = 0
            # mfcc_feat_array = []
            while a_queue.not_empty:
                print(num_elements)
                # Each input to the DBN will be a set of n MFCCs
                # which gives some change over time characteristics
                # to the model
                mfcc_sets = []
                for i in range(mfccs_per_record):
                    chunk = a_queue.get(True, 10)
                    if chunk is None:
                        break
                    # Do the math
                    mfcc_sets.append(mfcc(chunk, rate)[0])
                if chunk is None:
                    break
                mfcc_feat_arrays[queue_num].append(numpy.concatenate(mfcc_sets))
                num_elements += 1
                # fbank_feat = logfbank(my_y_subset, self.rate)
                a_queue.task_done()

            target_arr = numpy.empty(num_elements)
            target_arr.fill(tuple_num)
            target_arrays[queue_num].append(target_arr)
            # keep the datasets tuple a single tuple with
            # the train, valid, and test arrays concatenated
            # if queue_num not in datasets.keys():
            #    datasets[queue_num] = \
            #        numpy.array(mfcc_feat_array), target_arr
            #else:
            #    datasets[queue_num][0] = \
            #        numpy.concatenate((datasets[queue_num][0],
            #                          numpy.array(mfcc_feat_array)))
            #    datasets[queue_num][1] = \
            #        numpy.concatenate((datasets[queue_num][1],
            #                          target_arr))
    # munge all the data together into 3 tuples of numpy arrays,
    # one tuple for training data, one tuple for validation data,
    # and one tuple for test data
    for i in range(3):
        datasets[i] = (numpy.array(mfcc_feat_arrays[i]),
                       numpy.concatenate(target_arrays[i]))

    trainer = DbnTrain(mfcc_size * mfccs_per_record, datasets, batch_size=batch_size,
                       pretraining_epochs=100, training_epochs=1000,
                       finetune_lr=0.1, pretrain_lr=0.1)
