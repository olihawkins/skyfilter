""" CNN models for image classification. """

# Imports ---------------------------------------------------------------------

import os
import pandas as pd
import torch
import torch.nn as nn
import torch.nn.functional as F

from firekit.predict import Predictor
from firekit.vision import ImagePathDataset
from firekit.vision.transforms import SquarePad
from torch import Tensor
from torchvision.transforms import Compose
from torchvision.transforms import Normalize
from torchvision.transforms import Resize

# Constants ------------------------------------------------------------------

MODEL_PATH = os.path.join("models", "visnet-5.1.pt")

# Model class ----------------------------------------------------------------

class VisNet(nn.Module):

    """ 
    A simple CNN for binary image classification that aims to have low memory 
    overhead and decent performance on the CPU. 
    """

    def __init__(self) -> None:

        super().__init__()

        self.conv1 = nn.Conv2d(3, 64, 7, padding="same")
        self.conv2 = nn.Conv2d(64, 64, 5, padding="same")
        self.conv3 = nn.Conv2d(64, 128, 5, padding="same")
        self.conv4 = nn.Conv2d(128, 128, 3, padding="same")
        self.conv5 = nn.Conv2d(128, 256, 3, padding="same")
        self.conv6 = nn.Conv2d(256, 256, 3, padding="same")
        self.conv7 = nn.Conv2d(256, 512, 3, padding="same")
        self.conv8 = nn.Conv2d(512, 512, 3, padding="same")
        self.conv9 = nn.Conv2d(512, 512, 3, padding="same")
        self.conv10 = nn.Conv2d(512, 512, 3, padding="same")
        self.conv11 = nn.Conv2d(512, 512, 3, padding="same")

        self.batchnorm1 = nn.BatchNorm2d(64)
        self.batchnorm2 = nn.BatchNorm2d(64)
        self.batchnorm3 = nn.BatchNorm2d(128)
        self.batchnorm4 = nn.BatchNorm2d(128)
        self.batchnorm5 = nn.BatchNorm2d(256)
        self.batchnorm6 = nn.BatchNorm2d(256)
        self.batchnorm7 = nn.BatchNorm2d(512)
        self.batchnorm8 = nn.BatchNorm2d(512)
        self.batchnorm9 = nn.BatchNorm2d(512)
        self.batchnorm10 = nn.BatchNorm2d(512)
        self.batchnorm11 = nn.BatchNorm2d(512)

        self.batchnorm_fc1 = nn.BatchNorm1d(128)
        self.batchnorm_fc2 = nn.BatchNorm1d(64)

        self.fc1 = nn.Linear(512 * 2 * 2, 128)
        self.fc2 = nn.Linear(128, 64)
        self.fc3 = nn.Linear(64, 1)

    def forward(self, x: Tensor) -> Tensor:

        # Input layer
        x1 = F.relu(self.batchnorm1(self.conv1(x)))
        x1_pooled = F.max_pool2d(x1, 2)

        # Scaling layers
        x2 = F.relu(self.batchnorm2(self.conv2(x1_pooled)))
        x2 = x2 + x1_pooled
        x2 = F.relu(self.batchnorm3(self.conv3(x2)))
        x2_pooled = F.max_pool2d(x2, 2)

        x3 = F.relu(self.batchnorm4(self.conv4(x2_pooled)))
        x3 = x3 + x2_pooled
        x3 = F.relu(self.batchnorm5(self.conv5(x3)))
        x3_pooled = F.max_pool2d(x3, 2)

        x4 = F.relu(self.batchnorm6(self.conv6(x3_pooled)))
        x4 = x4 + x3_pooled
        x4 = F.relu(self.batchnorm7(self.conv7(x4)))
        x4_pooled = F.max_pool2d(x4, 2)

        # Fixed layers
        x5 = F.relu(self.batchnorm8(self.conv8(x4_pooled)))
        x5 = F.relu(self.batchnorm9(self.conv9(x5)))
        x5 = x5 + x4_pooled
        x5_pooled = F.max_pool2d(x5, 2)

        x6 = F.relu(self.batchnorm10(self.conv10(x5_pooled)))
        x6 = F.relu(self.batchnorm11(self.conv11(x6)))
        x6 = x6 + x5_pooled
        x6_pooled = F.max_pool2d(x6, 2)

        # Pool and flatten
        x_avg_pooled = F.avg_pool2d(x6_pooled, 4)
        x_flat = torch.flatten(x_avg_pooled, 1)

        # Fully connected layers
        x_fc = F.relu(self.batchnorm_fc1(self.fc1(x_flat)))
        x_fc = F.relu(self.batchnorm_fc2(self.fc2(x_fc)))
        x_fc = self.fc3(x_fc)

        return x_fc
     
# Load model as predictor ----------------------------------------------------

def load_predictor(
        model_path: str = MODEL_PATH,
        device: str = "cpu") -> Predictor:
    
    """ Load the model as a predictor. """

    # Load model
    state_dict = torch.load(
        model_path, 
        map_location=torch.device("cpu"))
    model = VisNet()
    model.load_state_dict(state_dict)

    # Create and return predictor
    predictor = Predictor(model, device=device)
    return predictor

# Get image transform for prediction -----------------------------------------

def get_predict_transform():
    return Compose([
        SquarePad(),
        Resize((512, 512)),
        Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225])])

# Load images as dataset -----------------------------------------------------

def get_image_dataset(image_paths: list) -> ImagePathDataset:
    image_dataset = ImagePathDataset(
        pd.DataFrame({"path": image_paths, "label": -1}),
        read_mode="RGB",
        transform=get_predict_transform())
    return image_dataset
