"""
HW6: Understanding CNNs and Generative Adversarial Networks.

Part-1: Training a GAN on CIFAR10

@author: Zhenye Na
"""

import os
import torch
import argparse
import torch.optim
import torch.nn as nn
import torch.backends.cudnn as cudnn

from train import Trainer_D, Trainer_GD
from utils import cifar10_loader
from model import Discriminator, Generator


def parse_args():
    """Parse parameters."""
    parser = argparse.ArgumentParser()

    # trainig command
    parser.add_argument('--option', type=str, default="option1",
                        help='training discriminator with / without generator')

    # directory
    parser.add_argument('--dataroot', type=str,
                        default="../../../data", help='path to dataset')
    parser.add_argument('--ckptroot', type=str,
                        default="../model/", help='path to checkpoint')

    # hyperparameters settings
    parser.add_argument('--lr', type=float, default=0.0001,
                        help='learning rate')
    parser.add_argument('--beta1', type=float, default=0., help='beta1')
    parser.add_argument('--beta2', type=float, default=0.9, help='beta2')
    parser.add_argument('--weight_decay', type=float,
                        default=1e-5, help='weight decay (L2 penalty)')

    parser.add_argument('--epochs1', type=int, default=120,
                        help='number of epochs to train without generator')
    parser.add_argument('--epochs2', type=int, default=200,
                        help='number of epochs to train with generator')

    parser.add_argument('--start_epoch', type=int,
                        default=0, help='pre-trained epochs')
    parser.add_argument('--batch_size_train', type=int,
                        default=128, help='training set input batch size')
    parser.add_argument('--batch_size_test', type=int,
                        default=128, help='test set input batch size')

    # parameters for training discriminator and generator gen_train
    parser.add_argument('--n_z', type=int, default=100,
                        help='number of hidden units')
    parser.add_argument('--gen_train', type=int, default=5,
                        help='# epochs that trains discriminator with generator')

    # training settings
    parser.add_argument('--resume', type=bool, default=False,
                        help='whether re-training from ckpt')
    parser.add_argument('--cuda', type=bool, default=True,
                        help='whether training using cudatoolkit')

    # parse the arguments
    args = parser.parse_args()

    return args


def main():
    """Main pipleline implements Generative Adversarial Networks in Pytorch."""
    args = parse_args()

    # load cifar10 dataset
    trainloader, testloader = cifar10_loader(
        args.dataroot, args.batch_size_train, args.batch_size_test)

    # Train the Discriminator without the Generator
    if args.option == "option1":
        print("Train the Discriminator without the Generator ...")
        model = Discriminator()
        if args.cuda:
            model = nn.DataParallel(model).cuda()
            cudnn.benchmark = True
        criterion = nn.CrossEntropyLoss()
        optimizer = torch.optim.Adam(model.parameters(),
                                     lr=args.lr,
                                     weight_decay=args.weight_decay)

        # train
        trainer_d = Trainer_D(model, criterion, optimizer,
                              trainloader, testloader,
                              args.start_epoch, args.epochs1,
                              args.cuda, args.batch_size_train, args.lr)
        trainer_d.train()

    # Train the Discriminator with the Generator
    else:
        # instantiate discriminator and generator
        aD, aG = Discriminator(), Generator()

        # resume training from the last time
        if args.resume:
            # Load checkpoint
            print('==> Resuming training from checkpoint ...')
            g_ckpt_pth = os.path.join(args.ckptroot, "tempG.model")
            d_ckpt_pth = os.path.join(args.ckptroot, "tempD.model")

            checkpoint_g = torch.load(g_ckpt_pth)
            checkpoint_d = torch.load(d_ckpt_pth)

            args.start_epoch = checkpoint_d['epoch']

            aG.load_state_dict(checkpoint_g['state_dict'])
            aD.load_state_dict(checkpoint_d['state_dict'])

        else:
            # start over
            print("Train the Discriminator with the Generator ...")

        if args.cuda:
            aD, aG = nn.DataParallel(aD).cuda(), nn.DataParallel(aG).cuda()
            cudnn.benchmark = True

        optimizer_g = torch.optim.Adam(aG.parameters(),
                                       lr=args.lr,
                                       betas=(args.beta1, args.beta2))
        optimizer_d = torch.optim.Adam(aD.parameters(),
                                       lr=args.lr,
                                       betas=(args.beta1, args.beta2))

        criterion = nn.CrossEntropyLoss()

        # train
        trainer_gd = Trainer_GD(aD, aG, criterion,
                                optimizer_d, optimizer_g,
                                trainloader, testloader,
                                args.batch_size_train, args.gen_train,
                                args.cuda, args.n_z,
                                args.start_epoch, args.epochs2)
        trainer_gd.train()


if __name__ == '__main__':
    main()
