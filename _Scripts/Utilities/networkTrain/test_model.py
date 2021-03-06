import tensorflow as tf
import tensorflow.keras as keras    
from tensorflow.keras.models import *
from tensorflow.keras.layers import *
from tensorflow.keras.optimizers import * 
from tensorflow.keras.layers import LeakyReLU, BatchNormalization
from tensorflow.keras.utils import multi_gpu_model
from tensorflow.keras.initializers import glorot_uniform 
from tensorflow.keras import regularizers
from tensorflow.python.keras.utils import losses_utils

## Customized weighted binary cross entropys
class WeightedBinaryCrossEntropy(keras.losses.Loss):
    """
    Args:
      pos_weight: Scalar to affect the positive labels of the loss function.
      weight: Scalar to affect the entirety of the loss function.
      from_logits: Whether to compute loss form logits or the probability.
      reduction: Type of tf.keras.losses.Reduction to apply to loss.
      name: Name of the loss function.
    """
    def __init__(self, pos_weight, weight, from_logits=False,
                 reduction=losses_utils.ReductionV2.AUTO,
                 name='weighted_binary_crossentropy'):
        super(WeightedBinaryCrossEntropy, self).__init__(reduction=reduction,
                                                         name=name)
        self.pos_weight = pos_weight
        self.weight = weight
        self.from_logits = from_logits

    def call(self, y_true, y_pred):
        if not self.from_logits:
            # Manually calculate the weighted cross entropy.
            # Formula is qz * -log(sigmoid(x)) + (1 - z) * -log(1 - sigmoid(x))
            # where z are labels, x is logits, and q is the weight.
            # Since the values passed are from sigmoid (assuming in this case)
            # sigmoid(x) will be replaced by y_pred

            # qz * -log(sigmoid(x)) 1e-6 is added as an epsilon to stop passing a zero into the log
            x_1 = y_true * self.pos_weight * -tf.math.log(y_pred + 1e-6)

            # (1 - z) * -log(1 - sigmoid(x)). Epsilon is added to prevent passing a zero into the log
            x_2 = (1 - y_true) * -tf.math.log(1 - y_pred + 1e-6)

            return tf.add(x_1, x_2) * self.weight 

        # Use built in function
        return tf.nn.weighted_cross_entropy_with_logits(y_true, y_pred, self.pos_weight) * self.weight


# This is the number of GPU you want to use
G = 1

# Coefficient for the leaky reLU activations 
alpha=0.05

# Coefficient for the l2 regularizer 
beta = 0.01
def unet(numLabels:int, pretrained_weights = False,input_size = (256,256,1)):

    inputs = Input(input_size)
    conv1 = Conv2D(64, 3, activation = 'linear', padding = 'same', kernel_initializer = 'glorot_normal', kernel_regularizer=regularizers.l2(beta))(inputs)
    conv1 = LeakyReLU(alpha)(conv1)
    conv1 = BatchNormalization()(conv1)
    conv1 = Conv2D(64, 3, activation = 'linear', padding = 'same', kernel_initializer = 'glorot_normal', kernel_regularizer=regularizers.l2(beta))(conv1)
    conv1 = LeakyReLU(alpha)(conv1)
    conv1 = BatchNormalization()(conv1)
    
    pool1 = MaxPooling2D(pool_size=(2, 2))(conv1)
    
    conv2 = Conv2D(128, 3, activation = 'linear', padding = 'same', kernel_initializer = 'glorot_normal', kernel_regularizer=regularizers.l2(beta))(pool1)
    conv2 = LeakyReLU(alpha)(conv2)
    conv2 = BatchNormalization()(conv2)
    conv2 = Conv2D(128, 3, activation = 'linear', padding = 'same', kernel_initializer = 'glorot_normal', kernel_regularizer=regularizers.l2(beta))(conv2)
    conv2 = LeakyReLU(alpha)(conv2)
    conv2 = BatchNormalization()(conv2)
    
    pool2 = MaxPooling2D(pool_size=(2, 2))(conv2)
    
    conv3 = Conv2D(256, 3, activation = 'linear', padding = 'same', kernel_initializer = 'glorot_normal', kernel_regularizer=regularizers.l2(beta))(pool2)
    conv3 = LeakyReLU(alpha)(conv3)
    conv3 = BatchNormalization()(conv3)
    conv3 = Conv2D(256, 3, activation = 'linear', padding = 'same', kernel_initializer = 'glorot_normal', kernel_regularizer=regularizers.l2(beta))(conv3)
    conv3 = LeakyReLU(alpha)(conv3)
    conv3 = BatchNormalization()(conv3)
    
    pool3 = MaxPooling2D(pool_size=(2, 2))(conv3)
    
    conv4 = Conv2D(512, 3, activation = 'linear', padding = 'same', kernel_initializer = 'glorot_normal', kernel_regularizer=regularizers.l2(beta))(pool3)
    conv4 = LeakyReLU(alpha)(conv4)
    conv4 = BatchNormalization()(conv4)
    conv4 = Conv2D(512, 3, activation = 'linear', padding = 'same', kernel_initializer = 'glorot_normal', kernel_regularizer=regularizers.l2(beta))(conv4)
    conv4 = LeakyReLU(alpha)(conv4)
    conv4 = BatchNormalization()(conv4)
    drop4 = Dropout(0.5)(conv4)
    
    pool4 = MaxPooling2D(pool_size=(2, 2))(drop4)

    conv5 = Conv2D(1024, 3, activation = 'linear', padding = 'same', kernel_initializer = 'glorot_normal', kernel_regularizer=regularizers.l2(beta))(pool4)
    conv5 = LeakyReLU(alpha)(conv5)
    conv5 = BatchNormalization()(conv5)
    conv5 = Conv2D(1024, 3, activation = 'linear', padding = 'same', kernel_initializer = 'glorot_normal', kernel_regularizer=regularizers.l2(beta))(conv5)
    conv5 = LeakyReLU(alpha)(conv5)
    conv5 = BatchNormalization()(conv5)
    drop5 = Dropout(0.5)(conv5)

    up6 = Conv2D(512, 2, activation = 'relu', padding = 'same', kernel_initializer = 'glorot_normal', kernel_regularizer=regularizers.l2(beta))(UpSampling2D(size = (2,2))(drop5))
    up6 = BatchNormalization()(up6)
    merge6 = concatenate([drop4,up6], axis = 3)
    conv6 = Conv2D(512, 3, activation = 'relu', padding = 'same', kernel_initializer = 'glorot_normal', kernel_regularizer=regularizers.l2(beta))(merge6)
    conv6 = BatchNormalization()(conv6)
    conv6 = Conv2D(512, 3, activation = 'relu', padding = 'same', kernel_initializer = 'glorot_normal', kernel_regularizer=regularizers.l2(beta))(conv6)
    conv6 = BatchNormalization()(conv6)

    up7 = Conv2D(256, 2, activation = 'relu', padding = 'same', kernel_initializer = 'glorot_normal', kernel_regularizer=regularizers.l2(beta))(UpSampling2D(size = (2,2))(conv6))
    up7 = BatchNormalization()(up7)
    merge7 = concatenate([conv3,up7], axis = 3)
    conv7 = Conv2D(256, 3, activation = 'relu', padding = 'same', kernel_initializer = 'glorot_normal', kernel_regularizer=regularizers.l2(beta))(merge7)
    conv7 = BatchNormalization()(conv7)
    conv7 = Conv2D(256, 3, activation = 'relu', padding = 'same', kernel_initializer = 'glorot_normal', kernel_regularizer=regularizers.l2(beta))(conv7)
    conv7 = BatchNormalization()(conv7)

    up8 = Conv2D(128, 2, activation = 'relu', padding = 'same', kernel_initializer = 'glorot_normal', kernel_regularizer=regularizers.l2(beta))(UpSampling2D(size = (2,2))(conv7))
    up8 = BatchNormalization()(up8)
    merge8 = concatenate([conv2,up8], axis = 3)
    conv8 = Conv2D(128, 3, activation = 'relu', padding = 'same', kernel_initializer = 'glorot_normal', kernel_regularizer=regularizers.l2(beta))(merge8)
    conv8 = BatchNormalization()(conv8)
    conv8 = Conv2D(128, 3, activation = 'relu', padding = 'same', kernel_initializer = 'glorot_normal', kernel_regularizer=regularizers.l2(beta))(conv8)
    conv8 = BatchNormalization()(conv8)

    up9 = Conv2D(64, 2, activation = 'relu', padding = 'same', kernel_initializer = 'glorot_normal', kernel_regularizer=regularizers.l2(beta))(UpSampling2D(size = (2,2))(conv8))
    up9 = BatchNormalization()(up9)
    merge9 = concatenate([conv1,up9], axis = 3)
    conv9 = Conv2D(64, 3, activation = 'relu', padding = 'same', kernel_initializer = 'glorot_normal', kernel_regularizer=regularizers.l2(beta))(merge9)
    conv9 = BatchNormalization()(conv9)
    conv9 = Conv2D(64, 3, activation = 'relu', padding = 'same', kernel_initializer = 'glorot_normal', kernel_regularizer=regularizers.l2(beta))(conv9)
    conv9 = BatchNormalization()(conv9)
    conv9 = Conv2D(numLabels, 3, activation = 'relu', padding = 'same', kernel_initializer = 'glorot_normal', kernel_regularizer=regularizers.l2(beta))(conv9)
    conv9 = BatchNormalization()(conv9)
    conv10 = Conv2D(numLabels, 1, activation = 'sigmoid')(conv9)

    if(G == 1):
        cpuModel = None
        model = Model(inputs = inputs, outputs = conv10)
        model.compile(optimizer = Adam(lr = 1e-4), loss = WeightedBinaryCrossEntropy(2, 1), metrics = ['accuracy'])
        print(model.summary()) 
    else:
        with tf.device("/cpu:0"):
            cpuModel = Model(inputs = inputs, outputs = conv10)
            print(cpuModel.summary())
        
        model = multi_gpu_model(cpuModel, gpus=G)
        model.compile(optimizer = Adam(lr = 1e-4), loss = WeightedBinaryCrossEntropy(2, 1), metrics = ['accuracy'])
        
    return model, cpuModel

def unet_3d (numLabels:int, pretrained_weights = False,input_size = (128,128,60,1)):
    inputs = Input(input_size)
    conv1 = Conv3D(32, 3, activation = 'linear', padding = 'same', kernel_initializer = 'glorot_normal', kernel_regularizer=regularizers.l2(beta))(inputs)
    conv1 = LeakyReLU(alpha)(conv1)
    conv1 = BatchNormalization()(conv1)
    conv1 = Conv3D(64, 3, activation = 'linear', padding = 'same', kernel_initializer = 'glorot_normal', kernel_regularizer=regularizers.l2(beta))(conv1)
    conv1 = LeakyReLU(alpha)(conv1)
    conv1 = BatchNormalization()(conv1)
    
    pool1 = MaxPooling3D(pool_size=(2, 2, 2))(conv1)
    
    conv2 = Conv3D(64, 3, activation = 'linear', padding = 'same', kernel_initializer = 'glorot_normal', kernel_regularizer=regularizers.l2(beta))(pool1)
    conv2 = LeakyReLU(alpha)(conv2)
    conv2 = BatchNormalization()(conv2)
    conv2 = Conv3D(128, 3, activation = 'linear', padding = 'same', kernel_initializer = 'glorot_normal', kernel_regularizer=regularizers.l2(beta))(conv2)
    conv2 = LeakyReLU(alpha)(conv2)
    conv2 = BatchNormalization()(conv2)
    
    pool2 = MaxPooling3D(pool_size=(2, 2, 2))(conv2)
    
    conv3 = Conv3D(128, 3, activation = 'linear', padding = 'same', kernel_initializer = 'glorot_normal', kernel_regularizer=regularizers.l2(beta))(pool2)
    conv3 = LeakyReLU(alpha)(conv3)
    conv3 = BatchNormalization()(conv3)
    conv3 = Conv3D(256, 3, activation = 'linear', padding = 'same', kernel_initializer = 'glorot_normal', kernel_regularizer=regularizers.l2(beta))(conv3)
    conv3 = LeakyReLU(alpha)(conv3)
    conv3 = BatchNormalization()(conv3)
    
    pool3 = MaxPooling3D(pool_size=(2, 2, 2))(conv3)
    
    conv4 = Conv3D(256, 3, activation = 'linear', padding = 'same', kernel_initializer = 'glorot_normal', kernel_regularizer=regularizers.l2(beta))(pool3)
    conv4 = LeakyReLU(alpha)(conv4)
    conv4 = BatchNormalization()(conv4)
    conv4 = Conv3D(512, 3, activation = 'linear', padding = 'same', kernel_initializer = 'glorot_normal', kernel_regularizer=regularizers.l2(beta))(conv4)
    conv4 = LeakyReLU(alpha)(conv4)
    conv4 = BatchNormalization()(conv4)
    drop4 = Dropout(0.5)(conv4)

    up5 = UpSampling3D(size = (2, 2, 2))(drop4)
    up5 = Conv2D(512, 2, activation = 'relu', padding = 'same', kernel_initializer = 'glorot_normal', kernel_regularizer=regularizers.l2(beta))(up5)
    up5 = BatchNormalization()(up5)

    merge5 = concatenate([conv3,up5], axis = 4)
    conv5 = Conv3D(256, 3, activation = 'relu', padding = 'same', kernel_initializer = 'glorot_normal', kernel_regularizer=regularizers.l2(beta))(merge5)
    conv5 = BatchNormalization()(conv5)
    conv5 = Conv3D(256, 3, activation = 'relu', padding = 'same', kernel_initializer = 'glorot_normal', kernel_regularizer=regularizers.l2(beta))(conv5)
    conv5 = BatchNormalization()(conv5)

    up6 = UpSampling3D(size = (2, 2, 2))(conv5)
    up6 = Conv3D(256, 2, activation = 'relu', padding = 'same', kernel_initializer = 'glorot_normal', kernel_regularizer=regularizers.l2(beta))(up6)
    up6 = BatchNormalization()(up6)

    merge6 = concatenate([conv2,up6], axis = 4)
    conv6 = Conv3D(128, 3, activation = 'relu', padding = 'same', kernel_initializer = 'glorot_normal', kernel_regularizer=regularizers.l2(beta))(merge6)
    conv6 = BatchNormalization()(conv6)
    conv6 = Conv3D(128, 3, activation = 'relu', padding = 'same', kernel_initializer = 'glorot_normal', kernel_regularizer=regularizers.l2(beta))(conv6)
    conv6 = BatchNormalization()(conv6)

    up7 = UpSampling3D(size = (2, 2, 2))(conv6)
    up7 = Conv3D(128, 2, activation = 'relu', padding = 'same', kernel_initializer = 'glorot_normal', kernel_regularizer=regularizers.l2(beta))(up7)
    up7 = BatchNormalization()(up7)
    merge7 = concatenate([conv1,up7], axis = 4)
    conv7 = Conv3D(64, 3, activation = 'relu', padding = 'same', kernel_initializer = 'glorot_normal', kernel_regularizer=regularizers.l2(beta))(merge7)
    conv7 = BatchNormalization()(conv7)
    conv7 = Conv3D(64, 3, activation = 'relu', padding = 'same', kernel_initializer = 'glorot_normal', kernel_regularizer=regularizers.l2(beta))(conv7)
    conv7 = BatchNormalization()(conv7)

    conv7 = Conv3D(numLabels, 3, activation = 'relu', padding = 'same', kernel_initializer = 'glorot_normal', kernel_regularizer=regularizers.l2(beta))(conv7)
    conv7 = BatchNormalization()(conv7)

    conv8 = Conv3D(numLabels, 1, activation = 'sigmoid')(conv7)

    if(G == 1):
        cpuModel = None
        model = Model(inputs = inputs, outputs = conv10)
        model.compile(optimizer = Adam(lr = 1e-4), loss = WeightedBinaryCrossEntropy(1.5, 1), metrics = ['accuracy'])
        print(model.summary()) 
    else:
        with tf.device("/cpu:0"):
            cpuModel = Model(inputs = inputs, outputs = conv10)
            print(cpuModel.summary())
        
        model = multi_gpu_model(cpuModel, gpus=G)
        model.compile(optimizer = Adam(lr = 1e-4), loss = WeightedBinaryCrossEntropy(1.5, 1), metrics = ['accuracy'])
        
    return model, cpuModel