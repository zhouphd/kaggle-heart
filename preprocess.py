import numpy as np
import re
from configuration import config
from image_transform import resize_to_make_it_fit, resize_to_make_sunny_fit, resize_and_augment_sunny, \
    resize_and_augment


def uint_to_float(img):
    return img / np.float32(255.0)

def sample_augmentation_parameters():
    augmentation_params = config().augmentation_params
    res = dict()
    for key, (a, b) in augmentation_params.iteritems():
        res[key] = config().rng.uniform(a,b)
    return res


def put_in_the_middle(target_tensor, data_tensor):
    """
    put data_sensor with arbitrary number of dimensions in the middle of target tensor.
    if data_Sensor is bigger, data is cut off
    if target_sensor is bigger, original values (probably zeros) are kept
    :param target_tensor:
    :param data_tensor:
    :return:
    """
    target_shape = target_tensor.shape
    data_shape = data_tensor.shape

    def get_indices(target_width, data_width):
        if target_width>data_width:
            diff = target_width - data_width
            target_slice = slice(diff/2, target_width-(diff-diff/2))
            data_slice = slice(None, None)
        else:
            diff = data_width - target_width
            data_slice = slice(diff/2, data_width-(diff-diff/2))
            target_slice = slice(None, None)
        return target_slice, data_slice

    t_sh = [get_indices(l1,l2) for l1, l2 in zip(target_shape, data_shape)]
    target_indices, data_indices = zip(*t_sh)
    target_tensor[target_indices] = data_tensor[data_indices]


def sunny_preprocess(chunk_x, img, chunk_y, lbl):
    image = uint_to_float(img).astype(np.float32)
    chunk_x[:, :] = resize_to_make_sunny_fit(image, output_shape=chunk_x.shape[-2:])
    segmentation = lbl.astype(np.float32)
    chunk_y[:] = resize_to_make_sunny_fit(segmentation, output_shape=chunk_y.shape[-2:])


def sunny_preprocess_with_augmentation(chunk_x, img, chunk_y, lbl):

    augmentation_parameters = sample_augmentation_parameters()
    image = uint_to_float(img).astype(np.float32)
    chunk_x[:, :] = resize_and_augment_sunny(image, output_shape=chunk_x.shape[-2:], augment=augmentation_parameters)
    segmentation = lbl.astype(np.float32)
    chunk_y[:] = resize_and_augment_sunny(segmentation, output_shape=chunk_y.shape[-2:], augment=augmentation_parameters)


def sunny_preprocess_validation(chunk_x, img, chunk_y, lbl):
    image = uint_to_float(img).astype(np.float32)
    chunk_x[:, :] = resize_to_make_sunny_fit(image, output_shape=chunk_x.shape[-2:])
    segmentation = lbl.astype(np.float32)
    chunk_y[:] = resize_to_make_sunny_fit(segmentation, output_shape=chunk_y.shape[-2:])



def preprocess(patient_data, result, index):
    """
    Load the resulting data, augment it if needed, and put it in result at the correct index
    :param patient_data:
    :param result:
    :param index:
    :return:
    """
    for tag, data in patient_data.iteritems():
        desired_shape = result[tag][index].shape
        # try to fit data into the desired shape
        if tag.startswith("sliced:data:singleslice"):
            patient_4d_tensor = resize_to_make_it_fit([patient_data[tag]], output_shape=desired_shape[-2:])[0]
            put_in_the_middle(result[tag][index], patient_4d_tensor)

        elif tag.startswith("sliced:data"):
            # put time dimension first, then axis dimension
            patient_4d_tensor = np.swapaxes(
                                        resize_to_make_it_fit(patient_data[tag], output_shape=desired_shape[-2:])
                                        ,1,0)
            put_in_the_middle(result[tag][index], patient_4d_tensor)
        if tag.startswith("sliced:data:shape"):
            result[tag][index] = patient_data[tag]
        if tag.startswith("sliced:meta:"):
            # TODO: this probably doesn't work very well yet
            result[tag][index] = patient_data[tag]
    return


def preprocess_with_augmentation(patient_data, result, index):
    """
    Load the resulting data, augment it if needed, and put it in result at the correct index
    :param patient_data:
    :param result:
    :param index:
    :return:
    """
    augmentation_parameters = sample_augmentation_parameters()

    for tag, data in patient_data.iteritems():
        desired_shape = result[tag][index].shape
        # try to fit data into the desired shape
        if tag.startswith("sliced:data:singleslice"):
            patient_4d_tensor = resize_and_augment([patient_data[tag]], output_shape=desired_shape[-2:], augment=augmentation_parameters)[0]
            put_in_the_middle(result[tag][index], patient_4d_tensor)
        elif tag.startswith("sliced:data"):
            # put time dimension first, then axis dimension

            patient_4d_tensor = np.swapaxes(
                                        resize_and_augment(patient_data[tag], output_shape=desired_shape[-2:], augment=augmentation_parameters)
                                        ,1,0)
            put_in_the_middle(result[tag][index], patient_4d_tensor)
        if tag.startswith("sliced:data:shape"):
            result[tag][index] = patient_data[tag]
        if tag.startswith("sliced:meta:"):
            # TODO: this probably doesn't work very well yet
            result[tag][index] = patient_data[tag]
    return