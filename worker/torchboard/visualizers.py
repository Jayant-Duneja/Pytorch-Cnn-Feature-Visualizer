import os
import numpy as np

import torch
import torch.nn as nn
from torch.optim import Adam

from torchboard.img_functions import (
    preprocess_image,
    recreate_image,
    save_image,
)
import torchboard.utils as tbu


class CNNLayerVisualization:
    """
    Produces an image that minimizes the loss of a convolution
    operation for a specific layer and filter
    """

    def __init__(
        self,
        model,
        selected_layer,
        selected_filter,
        visualizations_dir="/generated",
    ):
        # print(model)
        self.model = model
        self.model.eval()
        self.selected_layer = selected_layer
        self.selected_filter = selected_filter
        self.conv_output = 0
        self.visualizations_dir = visualizations_dir
        # Create the folder to export images if not exists
        if not os.path.exists(
            f"{self.visualizations_dir}/{self.selected_layer}"
        ):
            os.makedirs(f"{self.visualizations_dir}/{self.selected_layer}")

    def hook_layer(self):
        def hook_function(module, grad_in, grad_out):
            # Gets the conv output of the selected filter (from selected layer)
            self.conv_output = grad_out[0, self.selected_filter]

        # Hook the selected layer
        tbu.get_from_module(
            self.model, self.selected_layer
        ).register_forward_hook(hook_function)

    def visualise_layer_with_hooks(self):
        # Hook the selected layer
        self.hook_layer()
        # Generate a random image
        random_image = np.uint8(np.random.uniform(150, 180, (224, 224, 3)))
        # Process image and return variable
        processed_image = preprocess_image(random_image, False)
        # Define optimizer for the image
        optimizer = Adam([processed_image], lr=0.1, weight_decay=1e-6)
        for i in range(1, 31):
            optimizer.zero_grad()
            # Assign create image to a variable to move forward in the model
            x = processed_image
            for index, layer in enumerate(self.model.children()):
                # Forward pass layer by layer
                # x is not used after this point because it is only needed to trigger
                # the forward hook function
                x = layer(x)
                # Only need to forward until the selected layer is reached
                if index == self.selected_layer:
                    # (forward hook function triggered)
                    break
            # Loss function is the mean of the output of the selected layer/filter
            # We try to minimize the mean of the output of that specific filter
            loss = -torch.mean(self.conv_output)
            # print(
            #     "Iteration:",
            #     str(i),
            #     "Loss:",
            #     "{0:.2f}".format(loss.data.numpy()),
            # )

            # Backward
            loss.backward()

            # Update image
            optimizer.step()

            # Recreate image
            self.created_image = recreate_image(processed_image)

        # Save image
        im_path = f"{self.visualizations_dir}/{self.selected_layer}/{self.selected_filter}.jpg"
        save_image(self.created_image, im_path)

    def visualise_layer_without_hooks(self):
        # Process image and return variable
        # Generate a random image
        random_image = np.uint8(np.random.uniform(150, 180, (224, 224, 3)))
        # Process image and return variable
        processed_image = preprocess_image(random_image, False)
        # Define optimizer for the image
        optimizer = Adam([processed_image], lr=0.1, weight_decay=1e-6)
        for i in range(1, 31):
            optimizer.zero_grad()
            # Assign create image to a variable to move forward in the model
            x = processed_image
            for index, layer in enumerate(self.model.children()):
                # Forward pass layer by layer
                x = layer(x)
                if index == self.selected_layer:
                    # Only need to forward until the selected layer is reached
                    # Now, x is the output of the selected layer
                    break
            # Here, we get the specific filter from the output of the convolution operation
            # x is a tensor of shape 1x512x28x28.(For layer 17)
            # So there are 512 unique filter outputs
            # Following line selects a filter from 512 filters so self.conv_output will become
            # a tensor of shape 28x28
            self.conv_output = x[0, self.selected_filter]
            # Loss function is the mean of the output of the selected layer/filter
            # We try to minimize the mean of the output of that specific filter
            loss = -torch.mean(self.conv_output)
            # print(
            #     "Iteration:",
            #     str(i),
            #     "Loss:",
            #     "{0:.2f}".format(loss.data.numpy()),
            # )

            # Backward
            loss.backward()

            # Update image
            optimizer.step()

            # Recreate image
            self.created_image = recreate_image(processed_image)

        # Save image
        im_path = f"{self.visualizations_dir}/{self.selected_layer}/{self.selected_filter}.jpg"
        save_image(self.created_image, im_path)
