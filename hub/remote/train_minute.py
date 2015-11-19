__author__ = 'jasonboyer'

from audioin.chunks_from_s3 import ChunksFromS3
from dcsdbn.training.dbn_train import DbnTrain
from features import mfcc
import numpy
import queue


if __name__ == '__main__':
    # execute only if run as a script
    # 'test_stream1446121778.355943'
    bucket = 'boyer-cs767-audio'
    rate = 96000
    batch_size = 100
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

    chunker = ChunksFromS3(bucket_name=bucket,
                           year=2015, month=11, day=9, hour=12,
                           rate=rate, samples_per_record=rate/100,
                           chunk=96000/40, step=96000/100,
                           output_queue=train_output_queue)
    chunker.play_blob(58)

    chunker = ChunksFromS3(bucket_name=bucket,
                       year=2015, month=11, day=10, hour=15,
                       rate=rate, samples_per_record=rate/100,
                       chunk=96000/40, step=96000/100,
                       output_queue=valid_output_queue)
    chunker.play_blob(58)

#    chunker = ChunksFromS3(bucket_name=bucket,
#                           year=2015, month=11, day=10, hour=12,
#                           rate=rate, samples_per_record=rate/100,
#                           chunk=96000/40, step=96000/100,
#                           output_queue=test_output_queue)
#    chunker.play_blob(49)

    chunker = ChunksFromS3(bucket_name=bucket,
                           year=2015, month=11, day=10, hour=12,
                           rate=rate, samples_per_record=rate/100,
                           chunk=96000/40, step=96000/100,
                           output_queue=test_output_queue)
    chunker.play_blob(58)


    # TODO: Use a non-default number of MFCCs
    datasets = dict()
    queue_num = 0
    for a_queue in train_output_queue, valid_output_queue, test_output_queue:
        mfcc_feat_array = []
        while a_queue.not_empty:
            print(len(mfcc_feat_array))
            chunk = a_queue.get(True, 10)
            if chunk is None:
                break
            # Do the math
            mfcc_set = mfcc(chunk, rate)[0]
            mfcc_feat_array.append(mfcc_set)
            # fbank_feat = logfbank(my_y_subset, self.rate)
            a_queue.task_done()

        datasets[queue_num] = numpy.array(mfcc_feat_array), numpy.zeros(len(mfcc_feat_array))
        queue_num += 1

    trainer = DbnTrain(13, datasets, batch_size=batch_size,
                       pretraining_epochs=100, training_epochs=1000,
                       finetune_lr=0.1, pretrain_lr=0.01)
