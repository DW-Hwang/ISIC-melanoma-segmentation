import os
import numpy as np
from tqdm import tqdm
from skimage import io, transform
from paths import root_dir, mkdir_if_not_exist

ISIC2018_dir = os.path.join(root_dir, 'Datasets', 'ISIC2018')
data_dir = os.path.join('root_dir', 'data')
cached_data_dir = os.path.join(ISIC2018_dir, 'cache')

mkdir_if_not_exist(dir_list = [cached_data_dir])

task12_img = 'ISIC2018_Task1-2_Training_Input'
task12_validation_img = 'ISIC2018_Task1-2_Validation_Input'
task12_test_img = 'ISIC2018_Task1-2_Test_Input'
task1_gt = 'ISIC2018_Task1_Training_GroundTruth'

task12_img_dir = os.path.join(data_dir, task12_img)
task12_validation_img_dir = os.path.join(data_dir, task12_validation_img)
task12_test_img_dir = os.path.join(data_dir, task12_test_img)
task1_gt_dir = os.path.join(data_dir, task1_gt)

task12_image_ids = list()
if os.path.isdir(task12_img_dir):
    task12_image_ids = [fname.rsplit('.', maxsplit=1)[0] for fname in os.listdir(task12_img_dir)
                        if fname.startswith('ISIC') and fname.lower().endswith('.jpg')]
    task12_image_ids.sort()

task12_validation_image_ids = list()
if os.path.isdir(task12_validation_img_dir):
    task12_validation_image_ids = [fname.rsplit('.', maxsplit=1)[0] for fname in os.listdir(task12_validation_img_dir)
                                   if fname.startswith('ISIC') and fname.lower().endswith('.jpg')]
    task12_validation_image_ids.sort()

task12_test_image_ids = list()
if os.path.isdir(task12_test_img_dir):
    task12_test_image_ids = [fname.rsplit('.', maxsplit=1)[0] for fname in os.listdir(task12_test_img_dir)
                                   if fname.startswith('ISIC') and fname.lower().endswith('.jpg')]
    task12_test_image_ids.sort()

task12_images_npy_prefix = 'task12_images'
task12_validation_images_npy_prefix = 'task12_validation_images'
task12_test_images_npy_prefix = 'task12_test_images'
task1_gt_npy_prefix = 'task1_masks'

def load_image_by_id(image_id, fname_fn, from_dir, output_size=None, return_size=False):
    img_fnames = fname_fn(image_id)
    if isinstance(img_fnames, str):
        img_fnames = [img_fnames, ]

    assert isinstance(img_fnames, tuple) or isinstance(img_fnames, list)

    images = []
    image_sizes = []

    for img_fname in img_fnames:
        img_fname = os.path.join(from_dir, img_fname)
        if not os.path.exists(img_fname):
            raise FileNotFoundError('img %s not found' % img_fname)
        image = io.imread(img_fname)

        image_sizes.append(np.asarray(image.shape[:2]))

        if output_size:
            image = transform.resize(image, (output_size, output_size),
                                     order=1, mode='constant',
                                     cval=0, clip=True,
                                     preserve_range=True,
                                     anti_aliasing=True)
        image = image.astype(np.uint8)
        images.append(image)

    if return_size:
        if len(images) == 1:
            return images[0], image_sizes[0]
        else:
            return np.stack(images, axis=-1), image_sizes

    if len(images) == 1:
        return images[0]
    else:
        return np.stack(images, axis=-1)  # masks

def load_images(image_ids, from_dir, output_size=None, fname_fn=None, verbose=True, return_size=False):
    images = []

    if verbose:
        print('loading images from', from_dir)

    if return_size:

        image_sizes = []
        for image_id in tqdm(image_ids):
            image, image_size = load_image_by_id(image_id,
                                                 from_dir=from_dir,
                                                 output_size=output_size,
                                                 fname_fn=fname_fn,
                                                 return_size=True)
            images.append(image)
            image_sizes.append(image_size)

        return images, image_sizes


    else:
        for image_id in tqdm(image_ids):
            image = load_image_by_id(image_id,
                                     from_dir=from_dir,
                                     output_size=output_size,
                                     fname_fn=fname_fn)
            images.append(image)

        return images

def load_task12_training_images(output_size=None):
    suffix = '' if output_size is None else '_%d' % output_size
    images_npy_filename = os.path.join(cached_data_dir, '%s%s.npy' % (task12_images_npy_prefix, suffix))

    if os.path.exists(images_npy_filename):
        images = np.load(images_npy_filename)
    else:
        images = load_images(image_ids=task12_image_ids,
                             from_dir=task12_img_dir,
                             output_size=output_size,
                             fname_fn=lambda x: '%s.jpg' % x)
        images = np.stack(images).astype(np.uint8)
        np.save(images_npy_filename, images)
    return images


def load_task12_validation_images(output_size=None):
    suffix = '' if output_size is None else '_%d' % output_size
    images_npy_filename = os.path.join(cached_data_dir, '%s%s.npy' % (task12_validation_images_npy_prefix, suffix))
    image_sizes_npy_filename = os.path.join(cached_data_dir, '%s_sizes.npy' % task12_validation_images_npy_prefix)

    if os.path.exists(images_npy_filename) and os.path.exists(image_sizes_npy_filename):

        images = np.load(images_npy_filename)
        image_sizes = np.load(image_sizes_npy_filename)

    else:

        images, image_sizes = load_images(image_ids=task12_validation_image_ids,
                                          from_dir=task12_validation_img_dir,
                                          output_size=output_size,
                                          fname_fn=lambda x: '%s.jpg' % x, return_size=True)
        images = np.stack(images).astype(np.uint8)
        image_sizes = np.stack(image_sizes)

        np.save(images_npy_filename, images)
        np.save(image_sizes_npy_filename, image_sizes)

    return images, image_sizes

def load_task12_test_images(output_size=None):
    suffix = '' if output_size is None else '_%d' % output_size
    images_npy_filename = os.path.join(cached_data_dir, '%s%s.npy' % (task12_test_images_npy_prefix, suffix))
    image_sizes_npy_filename = os.path.join(cached_data_dir, '%s_sizes.npy' % task12_test_images_npy_prefix)

    if os.path.exists(images_npy_filename) and os.path.exists(image_sizes_npy_filename):

        images = np.load(images_npy_filename)
        image_sizes = np.load(image_sizes_npy_filename)

    else:

        images, image_sizes = load_images(image_ids=task12_test_image_ids,
                                          from_dir=task12_test_img_dir,
                                          output_size=output_size,
                                          fname_fn=lambda x: '%s.jpg' % x, return_size=True)
        images = np.stack(images).astype(np.uint8)
        image_sizes = np.stack(image_sizes)

        np.save(images_npy_filename, images)
        np.save(image_sizes_npy_filename, image_sizes)

    return images, image_sizes

def load_task1_training_masks(output_size=None):
    suffix = '' if output_size is None else '_%d' % output_size
    npy_filename = os.path.join(cached_data_dir, 'task1_masks%s.npy' % suffix)
    if os.path.exists(npy_filename):
        masks = np.load(npy_filename)
    else:
        masks = load_images(image_ids=task12_image_ids,
                            from_dir=task1_gt_dir,
                            output_size=output_size,
                            fname_fn=lambda x: '%s_segmentation.png' % x)
        masks = np.stack(masks)
        np.save(npy_filename, masks)
    return masks

def load_training_data(output_size=None,
                       num_partitions=5,
                       idx_partition=0,
                       test_split=0.):
    train_X = load_task12_training_images(output_size=output_size)
    train_y = load_task1_training_masks(output_size=output_size)
    return partition_data(x=train_X, y=train_y, k=num_partitions, i=idx_partition, test_split=test_split)

def load_validation_data(output_size=None):
    images, image_sizes = load_task12_validation_images(output_size=output_size)
    return images, task12_validation_image_ids, image_sizes

def load_test_data(output_size=None):
    images, image_sizes = load_task12_test_images(output_size=output_size)
    return images, task12_test_image_ids, image_sizes

def partition_data(x, y, k=5, i=0, test_split=1. / 6, seed=42):
    assert isinstance(k, int) and isinstance(i, int) and 0 <= i < k

    n = x.shape[0]

    n_set = int(n * (1. - test_split)) // k
    # divide the data into (k + 1) sets, -1 is test set, [0, k) are for train and validation
    indices = np.array([i for i in range(k) for _ in range(n_set)] +
                       [-1] * (n - n_set * k),
                       dtype=np.int8)

    np.random.seed(seed)
    np.random.shuffle(indices)

    valid_indices = (indices == i)
    test_indices = (indices == -1)
    train_indices = ~(valid_indices | test_indices)

    x_valid = x[valid_indices]
    y_valid = y[valid_indices]

    x_train = x[train_indices]
    y_train = y[train_indices]

    x_test = x[test_indices]
    y_test = y[test_indices]

    return (x_train, y_train), (x_valid, y_valid), (x_test, y_test)
