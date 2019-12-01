import argparse
import os
import time

import numpy

from callbacks import LearnLog
from iterators import Dataset, BatchGenerator, ImageIterator
from utilities import TT, np_append, change_ext


def task_train_filter(args):
    ff, mapper = getattr(__import__('dataset'), args.dataset)()
    dataset = Dataset(root_path=args.path, verbose=args.verbose, name='base-model',
                      mapper=mapper, filename_filter=ff, rotation=False)
    dataset_batches = BatchGenerator(dataset, args.batch)
    from mitosis import model_base
    TT.debug("Compile base model.")
    model = model_base(args.lr)
    model_saved_weights_path = os.path.join(args.path, 'base-model.weights.npy')
    if os.path.exists(model_saved_weights_path):
        TT.info("Loading weights from %s" % model_saved_weights_path)
        model.load_weights(model_saved_weights_path)
    train_start = time.time()
    log = LearnLog("filter", args.path)
    for epoch in xrange(args.epoch):
        TT.debug(epoch + 1, "of", args.epoch, "epochs")
        log.on_dataset_epoch_begin(epoch + 1)
        for x, y in dataset_batches:
            model.fit(x, y, batch_size=args.mini_batch, nb_epoch=1, validation_split=.1,
                      callbacks=[log], show_accuracy=True, shuffle=True)
        log.on_dataset_epoch_end(epoch + 1)
    log.on_dataset_train_end()
    TT.success("Training finished in %.2f hours." % ((time.time() - train_start) / 3600.))


def task_train_cnn(args):
    ff, mapper = getattr(__import__('dataset'), args.dataset)()
    dataset = Dataset(root_path=args.path, verbose=args.verbose, name='cnn',
                      mapper=mapper, filename_filter=ff, ratio=9)
    dataset_batches = BatchGenerator(dataset, args.batch)
    from mitosis import model_base, model_1, model_2
    TT.debug("Compile base model.")
    model = model_base(lr=0)
    TT.debug("Compile model 1.")
    model1 = model_1(args.lr)
    TT.debug("Compile model 2.")
    model2 = model_2(args.lr)
    model_saved_weights_path = os.path.join(args.path, 'base-model.weights.npy')
    model1_saved_weights_path = os.path.join(args.path, 'model1.weights.npy')
    model2_saved_weights_path = os.path.join(args.path, 'model2.weights.npy')
    if os.path.exists(model_saved_weights_path):
        TT.info("Loading weights from %s" % model_saved_weights_path)
        model.load_weights(model_saved_weights_path)
    if os.path.exists(model1_saved_weights_path):
        TT.info("Loading weights from %s" % model1_saved_weights_path)
        model1.load_weights(model1_saved_weights_path)
    if os.path.exists(model2_saved_weights_path):
        TT.info("Loading weights from %s" % model2_saved_weights_path)
        model2.load_weights(model2_saved_weights_path)
    train_start = time.time()
    log1 = LearnLog("model1", args.path)
    log2 = LearnLog("model2", args.path)
    for epoch in xrange(args.epoch):
        TT.debug(epoch + 1, "of", args.epoch, "epochs")
	
	model1_i_saved_weights_path = os.path.join(args.path, 'model1.%02d.weights.npy' %(epoch) )
	model2_i_saved_weights_path = os.path.join(args.path, 'model2.%02d.weights.npy' %(epoch) )
	if (os.path.exists(model1_i_saved_weights_path))&(os.path.exists(model1_saved_weights_path)):
        	TT.info("Loading weights from %s" % model1_i_saved_weights_path)
        	model1.load_weights(model1_i_saved_weights_path)
		model2.load_weights(model2_i_saved_weights_path)
		continue


        
	log1.on_dataset_epoch_begin(epoch + 1)
        log2.on_dataset_epoch_begin(epoch + 1)
        for x, y in dataset_batches:
            outputs = model.predict(x, batch_size=args.mini_batch, verbose=args.verbose)
            # Multiply each window with it's prediction and then pass it to the next layer
            # x_new = []
            # y_new = []
            x = 1. - x
            for i in range(len(outputs)):
                if y[i][0] < 1.:
                    # x_new.append(x[i])
                    # y_new.append(y[i])
                    x[i] *= outputs[i][0]

            TT.debug("Model 1 on epoch %d" % (epoch + 1))
            model1.fit(numpy.asarray(x), numpy.asarray(y), batch_size=args.mini_batch, nb_epoch=1, validation_split=.1,
                       callbacks=[log1], show_accuracy=True, shuffle=True)
            TT.debug("Model 2 on epoch %d" % (epoch + 1))
            model2.fit(numpy.asarray(x), numpy.asarray(y), batch_size=args.mini_batch, nb_epoch=1, validation_split=.1,
                       callbacks=[log2], show_accuracy=True, shuffle=True)
        log1.on_dataset_epoch_end(epoch + 1)
        log2.on_dataset_epoch_end(epoch + 1)
    log1.on_dataset_train_end()
    log2.on_dataset_train_end()
    TT.success("Training finished in %.2f hours." % ((time.time() - train_start) / 3600.))


def task_test_filter(args):
    dataset = ImageIterator(args.input, args.output)
    dataset_batches = BatchGenerator(dataset, args.batch)
    from mitosis import model_base
    TT.debug("Compile base model.")
    model = model_base(args.lr)
    model_saved_weights_path = os.path.join(args.path, 'base-model.weights.npy')
    TT.info("Loading weights from %s" % model_saved_weights_path)
    model.load_weights(model_saved_weights_path)
    test_start = time.time()
    out = None
    for x, y in dataset_batches:
        tmp = model.predict(x, args.mini_batch, args.verbose)
        out = np_append(out, tmp)
    width, height = dataset.image_size
    out = numpy.reshape(out[:, 0], (height, width))
    numpy.save(change_ext(args.input, 'predicted.npy'), out)
    numpy.save(change_ext(args.input, 'expected.npy'), dataset.output)
    TT.success("Testing finished in %.2f minutes." % ((time.time() - test_start) / 60.))


def task_test_cnn(args):
    dataset = ImageIterator(args.input, args.output)
    dataset_batches = BatchGenerator(dataset, args.batch)
    from mitosis import model_base, model_1, model_2
    TT.debug("Compile base model.")
    model = model_base(0)
    TT.debug("Compile model 1.")
    model1 = model_1(0)
    TT.debug("Compile model 2.")
    model2 = model_2(0)
    model_saved_weights_path = os.path.join(args.path, 'base-model.weights.npy')
    model1_saved_weights_path = os.path.join(args.path, 'model1.0.weights.npy')
    model2_saved_weights_path = os.path.join(args.path, 'model2.0.weights.npy')
    TT.info("Loading weights from %s" % model_saved_weights_path)
    model.load_weights(model_saved_weights_path)
    TT.info("Loading weights from %s" % model1_saved_weights_path)
    model1.load_weights(model1_saved_weights_path)
    TT.info("Loading weights from %s" % model2_saved_weights_path)
    model2.load_weights(model2_saved_weights_path)
    test_start = time.time()
    out = out1 = out2 = None
    for x, y in dataset_batches:
        tmp = model.predict(x, args.mini_batch, args.verbose)
        local1 = numpy.zeros(tmp.shape)
        local2 = numpy.zeros(tmp.shape)
        out = np_append(out, tmp)
        x = 1. - x 
        x_new = []
        indices = []
        for i in range(len(tmp)):
            if tmp[i][0] > .6:
                x_new.append(x[i])
                indices.append(i)

        x_new = numpy.asarray(x_new)
        if len(x_new):
            tmp1 = model1.predict(x_new, args.mini_batch, args.verbose)
            local1[indices] = tmp1
        out1 = np_append(out1, local1)

        if len(x_new):
            tmp2 = model2.predict(x_new, args.mini_batch, args.verbose)
            local2[indices] = tmp2
        out2 = np_append(out2, local2)
    width, height = dataset.image_size
    out = numpy.reshape(out[:, 0], (height, width))
    out1 = numpy.reshape(out1[:, 0], (height, width))
    out2 = numpy.reshape(out2[:, 0], (height, width))
    numpy.save(change_ext(args.input, 'predicted.npy'), out)
    numpy.save(change_ext(args.input, 'model1.predicted.npy'), out1)
    numpy.save(change_ext(args.input, 'model2.predicted.npy'), out2)
    numpy.save(change_ext(args.input, 'expected.npy'), dataset.output)
    TT.success("Testing finished in %.2f minutes." % ((time.time() - test_start) / 60.))


def parse_args():
    parser = argparse.ArgumentParser(description="Mitosis Detection Task Runner")
    parser.add_argument("task", help="Run task. (train-filter, train-cnn, test-filter, test-cnn)",
                        choices=['train-filter', 'test-cnn', 'train-cnn', 'test-filter'],
                        metavar="task")
    parser.add_argument("path", type=str, help="Directory containing mitosis images", metavar="path")
    parser.add_argument("--epoch", type=int, help="Number of epochs. (Default: 10)", default=10)
    parser.add_argument("--batch", type=int, help="Size of batch fits in memory. (Default: 3000)", default=3000)
    parser.add_argument("--mini-batch", type=int, help="Size of training batch. (Default: 100)", default=100)
    parser.add_argument("--lr", type=float, help="Learning Rate. (Default: .002)", default=.002)
    parser.add_argument("--output", type=str, help="output. (Default: None)", default=None)
    parser.add_argument("--input", type=str, help="input. (Default: None)", default=None)
    parser.add_argument("-v", action="store_true", help="Increase verbosity. (Default: Disabled)", default=False,
                        dest='verbose')
    parser.add_argument("--dataset", type=str, help="Dataset type: icpr2012", default='icpr2012')

    return parser, parser.parse_args()


def main():
    parser, args = parse_args()
    TT.verbose = args.verbose
    if args.task == 'train-filter':
        TT.debug("Running: Task Train Filter")
        task_train_filter(args)
    if args.task == 'train-cnn':
        TT.debug("Running: Task Train CNN")
        task_train_cnn(args)
    elif args.task == 'test-filter':
        TT.debug("Running: Task Test Filter")
        task_test_filter(args)
    elif args.task == 'test-cnn':
        TT.debug("Running: Task Test CNN")
        task_test_cnn(args)
    else:
        parser.print_help()
        exit(0)


if __name__ == '__main__':
    main()
