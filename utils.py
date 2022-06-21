#!/usr/bin/env python3
######################################################################
# Authors:      <s203005> Karol Bogumil Krzak
#                     <s202385> David Parham
#                     <s202468> Alejandro Martinez Senent
#                     <s202460> Christian Jannik Metz
#
# Course:        Deep Learning for Computer Vision
# Semester:    June 2022
# Institution:  Technical University of Denmark (DTU)
#
# Module: This module contain utility classes and functions
######################################################################

import os

import torch
import matplotlib.pyplot as plt
import itertools
import numpy as np
import albumentations as A
from albumentations.pytorch import ToTensorV2
from torch import nn, optim

from architectures import NestedUNet, UNet
from architectures.resnet101 import SegmentationModelOutputWrapper as resnet101
from loss import BinaryDiceLoss


class EarlyStopping:
    def __init__(self, tolerance=5, min_delta=0):

        self.tolerance = tolerance
        self.min_delta = min_delta
        self.counter = 0
        self.early_stop = False

    def __call__(self, train_loss, validation_loss):
        if (validation_loss - train_loss) > self.min_delta:
            self.counter += 1
            if self.counter >= self.tolerance:
                self.early_stop = True


class ImageTransformations:
    def __init__(self, is_train, img_size):
        self.is_train = is_train
        self.img_size = img_size
        self.augmentations = None

        if self.is_train:
            self.augmentations = A.Compose(
                [
                    A.Resize(*self.img_size),
                    A.HorizontalFlip(p=0.5),
                    A.VerticalFlip(p=0.5),
                    A.Transpose(p=0.5),
                    A.ShiftScaleRotate(
                        shift_limit=0.01, scale_limit=0.04, rotate_limit=0, p=0.25
                    ),
                    # # Pixels
                    A.RandomBrightnessContrast(p=0.5),
                    A.RandomGamma(p=0.25),
                    A.Blur(p=0.01, blur_limit=3),
                    # Affine
                    A.OneOf(
                        [
                            A.ElasticTransform(
                                p=0.5,
                                alpha=120,
                                sigma=120 * 0.05,
                                alpha_affine=120 * 0.03,
                            ),
                            A.GridDistortion(p=0.5),
                            A.OpticalDistortion(p=1, distort_limit=2, shift_limit=0.5),
                        ],
                        p=0.8,
                    ),
                    A.Normalize(
                        mean=[0.0, 0.0, 0.0],
                        std=[1.0, 1.0, 1.0],
                        max_pixel_value=255.0,
                    ),
                    ToTensorV2(),
                ],
            )
        else:
            self.augmentations = A.Compose(
                [
                    A.Resize(*self.img_size),
                    A.Normalize(
                        mean=[0.0, 0.0, 0.0],
                        std=[1.0, 1.0, 1.0],
                        max_pixel_value=255.0,
                    ),
                    ToTensorV2(),
                ],
            )

    def __names__(self):
        transformation_lst = []
        for transformation in self.augmentations:
            transformation_lst.append(str(transformation).split("(")[0])
        return transformation_lst


def models(_name):
    # changed to pass object not class
    model_dct = {
        "unet": UNet.UNet,
        "unet++": NestedUNet.NestedUNet,
        "resnet101": resnet101,
    }
    if _name.lower() in model_dct:
        return model_dct.get(_name.lower())
    else:
        raise ValueError(f"[ERROR] Model: '{_name}' hasn't been enabled.")


def optimizers(_name):
    optimizers = {
        "adam": optim.Adam,
        "sgd": optim.SGD,
        "adamw": optim.AdamW,
        "rmsprop": optim.RMSprop,
    }
    if _name.lower() in optimizers:
        return optimizers.get(_name.lower())
    else:
        raise ValueError(f"[ERROR] Optimizer: '{_name}' hasn't been enabled.")


def loss_fns(_name):
    functions = {
        "bcewithlogitsloss": nn.BCEWithLogitsLoss,
        "binarydiceloss": BinaryDiceLoss,
    }
    if _name.lower() in functions:
        return functions.get(_name.lower())
    else:
        raise ValueError(f"[ERROR] Loss: '{_name}' hasn't been enabled.")


def save_model(epoch, model, optimizer, path, new_best_model=False):
    if new_best_model:
        print("\n[INFO] Saving new best_model...\n")
    else:
        print(f"\n[INFO] Saving model as checkpoint -> epoch_{epoch+1}.pth\n")
        path = os.path.join(path, f"epoch_{epoch + 1}.pth")

    torch.save(
        {
            "epoch": epoch + 1,
            "model_state_dict": model.state_dict(),
            "optimizer_state_dict": optimizer.state_dict(),
        },
        path,
    )


def print_statistics(loss, pixAcc, mIoU, epoch=0, epochs=0, Training=True):
    if Training:
        print(
            f"Epoch {epoch+1}/{epochs} \n \tTraining:  "
            f" Loss={loss:.2f}\t pixAcc={pixAcc:.2f}%\t mIoU={mIoU:.2f}%\t"
        )
    else:
        print(
            f"\tTesting:    Loss={loss:.2f}\t pixAcc={pixAcc:.2f}%\t mIoU={mIoU:.2f}%\t"
        )


if __name__ == "__main__":
    pass


def unique_file(basename, ext):
    actualname = "%s.%s" % (basename, ext)
    c = itertools.count()
    while os.path.exists(actualname):
        actualname = "%s (%d).%s" % (basename, next(c), ext)
    return actualname


# def visualize_results_(images, predicted, label):
#     # print(f"Image: {images.shape} {type(images)} {len(images)}, predicted: {predicted.shape} {type(predicted)}, GT: {label.shape} {type(label)}")
#     plt.figure(figsize=(20,20))
#     subplots = [plt.subplot(1,len(images), k+1) for k in range(len(images))]

#     for k, (img, pred, gt) in enumerate(zip(images, predicted, label)):
#         # print(f"Image: {img.shape} {type(img)}, predicted: {pred.shape} {type(pred)}, GT: {gt.shape} {type(gt)}")
#         print(f"image {k} added to plot")
#         img = (img.permute(1, 2, 0) * 127.5 + 128).clamp(0, 255).to(torch.uint8)
#         pred = pred.permute(1, 2, 0).clamp(0, 255).to(torch.uint8).cpu().numpy()
#         pred_mask = ma.masked_array(pred > 0, pred)
#         gt = gt.permute(1, 2, 0).clamp(0, 255).to(torch.uint8).cpu().numpy()
#         gt_mask = ma.masked_array(gt > 0, gt)
#         subplots[k].imshow(img.cpu().numpy())
#         subplots[k].imshow(pred_mask, "hot", alpha=0.2)
#         subplots[k].imshow(gt_mask, "jet", alpha=0.2)
#         subplots[k].axis('off')
#     plt.savefig(unique_file("out/images/test_result","png"),bbox_inches = "tight")
#     print("saved_file")


def visualize_results(images, predicted, label):
    # print(f"Image: {images.shape} {type(images)} {len(images)}, predicted: {predicted.shape} {type(predicted)}, GT: {label.shape} {type(label)}")
    for k, (img, pred, gt) in enumerate(zip(images, predicted, label)):
        # print(f"Image: {img} {type(img)}, predicted: {pred} {type(pred)}, GT: {gt} {type(gt)}")
        plt.figure(figsize=(10, 10))
        subplots = [plt.subplot(1, 3, k + 1) for k in range(3)]
        print(f"image {k} added to plot")
        img = (img.permute(1, 2, 0) * 127.5 + 128).clamp(0, 255).to(torch.uint8)
        pred = pred.permute(1, 2, 0).to(torch.uint8).cpu().numpy()
        pred_mask = np.zeros_like(pred)
        mask = pred > 0.5
        pred_mask[mask] = 1
        # print(f"pred_mask: {pred_mask.shape}")
        gt = gt.permute(1, 2, 0).to(torch.uint8).cpu().numpy()
        # print(f"gt: {gt}")
        # gt_mask = np.zeros_like(pred)[gt>0.5]=1
        subplots[0].imshow(img.cpu().numpy())
        subplots[0].axis("off")
        subplots[0].set_title("Test image")
        subplots[1].imshow(gt, "gnuplot")
        subplots[1].axis("off")
        subplots[1].set_title("Ground truth")
        # plt.savefig(unique_file("out/images/test_result_gt","png"),bbox_inches = "tight")
        subplots[2].imshow(pred_mask, "turbo")
        subplots[2].axis("off")
        subplots[2].set_title("Predicted")
        plt.savefig(
            unique_file("out/images/test_result_all", "png"), bbox_inches="tight"
        )
    print("saved_file")
