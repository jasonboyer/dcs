__author__ = 'jasonboyer'
''' Adapted from http://deeplearning.net/tutorial/code/DBN.py
'''

import dcsdbn
from dbn.DBN import DBN
import dbn.logistic_sgd
import numpy
import os
import pickle
import sys
import timeit


class DbnTrain:
    def __init__(self, number_of_inputs, datasets, batch_size,
                 pretraining_epochs, training_epochs,
                 finetune_lr=0.1, pretrain_lr=0.01):
        self.number_of_inputs = number_of_inputs
        self.datasets = datasets
        self.train_set = datasets[0]
        self.batch_size = batch_size
        self.pretraining_epochs = pretraining_epochs
        self.training_epochs = training_epochs
        self.finetune_lr = finetune_lr
        self.pretrain_lr = pretrain_lr
        self.shared_datasets = None
        # numpy random generator
        # hex value selected from random.org
        numpy_rng = numpy.random.RandomState(0x70f19182)
        print('... building the model')

        # construct the Deep Belief Network
        self.dbn = DBN(numpy_rng=numpy_rng, n_ins=number_of_inputs,
                       hidden_layers_sizes=[1000, 1000, 1000],
                       n_outs=50)

        # start-snippet-2
        #########################
        # PRETRAINING THE MODEL #
        #########################
        print('... getting the pretraining functions')

        # See comments in dbn.logistic_sgd.
        self.shared_datasets = [dbn.logistic_sgd.shared_dataset(self.datasets[0], borrow=True),
                                dbn.logistic_sgd.shared_dataset(self.datasets[1], borrow=True),
                                dbn.logistic_sgd.shared_dataset(self.datasets[2], borrow=True)]
        train_set_x, train_set_y = self.shared_datasets[0]
        # TODO: Determine whether k should ever be anything other than 1
        pretraining_fns = self.dbn.pretraining_functions(train_set_x=train_set_x,
                                                    batch_size=self.batch_size,
                                                    k=1)

        # compute number of minibatches for training, validation and testing
        n_train_batches = int(train_set_x.get_value(borrow=True).shape[0] / self.batch_size)

        print('... pre-training the model')
        start_time = timeit.default_timer()
        ## Pre-train layer-wise
        for i in range(self.dbn.n_layers):
            # go through pretraining epochs
            for epoch in range(pretraining_epochs):
                # go through the training set
                c = []
                for batch_index in range(n_train_batches):
                    c.append(pretraining_fns[i](index=batch_index,
                                                lr=self.pretrain_lr))
                print('Pre-training layer %i, epoch %d, cost ' % (i, epoch),)
                print(numpy.mean(c))

        end_time = timeit.default_timer()
        # end-snippet-2
        print(('The pretraining code for file ' +
               os.path.split(__file__)[1] +
               ' ran for %.2fm' % ((end_time - start_time) / 60.)),
              file=sys.stderr)

        ########################
        # FINETUNING THE MODEL #
        ########################

        # get the training, validation and testing function for the model
        print('... getting the finetuning functions')
        train_fn, validate_model, test_model = self.dbn.build_finetune_functions(
            datasets=self.shared_datasets,
            batch_size=self.batch_size,
            learning_rate=self.finetune_lr
        )

        print('... finetuning the model')
        # early-stopping parameters
        patience = 4 * n_train_batches  # look as this many examples regardless
        patience_increase = 2.    # wait this much longer when a new best is
                                  # found
        improvement_threshold = 0.995  # a relative improvement of this much is
                                       # considered significant
        validation_frequency = min(n_train_batches, patience / 2)
                                      # go through this many
                                      # minibatches before checking the network
                                      # on the validation set; in this case we
                                      # check every epoch

        best_validation_loss = numpy.inf
        test_score = 0.
        start_time = timeit.default_timer()

        done_looping = False
        epoch = 0

        while (epoch < training_epochs) and (not done_looping):
            epoch = epoch + 1
            for minibatch_index in range(n_train_batches):

                minibatch_avg_cost = train_fn(minibatch_index)
                iter = (epoch - 1) * n_train_batches + minibatch_index

                if (iter + 1) % validation_frequency == 0:

                    validation_losses = validate_model()
                    this_validation_loss = numpy.mean(validation_losses)
                    print(
                        'epoch %i, minibatch %i/%i, validation error %f %%'
                        % (
                            epoch,
                            minibatch_index + 1,
                            n_train_batches,
                            this_validation_loss * 100.
                        )
                    )

                    # if we got the best validation score until now
                    if this_validation_loss < best_validation_loss:

                        #improve patience if loss improvement is good enough
                        if (
                            this_validation_loss < best_validation_loss *
                            improvement_threshold
                        ):
                            patience = max(patience, iter * patience_increase)

                        # save best validation score and iteration number
                        best_validation_loss = this_validation_loss
                        best_iter = iter

                        # test it on the test set
                        test_losses = test_model()
                        test_score = numpy.mean(test_losses)
                        print(('     epoch %i, minibatch %i/%i, test error of '
                               'best model %f %%') %
                              (epoch, minibatch_index + 1, n_train_batches,
                               test_score * 100.))

                if patience <= iter:
                    done_looping = True
                    break

        end_time = timeit.default_timer()
        print(
            (
                'Optimization complete with best validation score of %f %%, '
                'obtained at iteration %i, '
                'with test performance %f %%'
            ) % (best_validation_loss * 100., best_iter + 1, test_score * 100.)
        )
        print(('The fine tuning code for file ' +
               os.path.split(__file__)[1] +
               ' ran for %.2fm' % ((end_time - start_time)/ 60.)),
              file=sys.stderr)

        pickle.dump((train_fn, pretraining_fns, validate_model, test_model),
                    'pickled_test_fn.pck')